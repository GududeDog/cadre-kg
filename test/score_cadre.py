"""
score_cadre.py
=========================================================
目的: 读取 .doc/.docx 述职报告, 抽取指定编号干部的段,
      按《组织干部评价指标体系 6.3.md》53 个三级指标用 LLM 评分,
      生成一份 Markdown 评分报告.

用法:
  python score_cadre.py                       # 默认 015
  python score_cadre.py --target 001         # 指定其他编号
  python score_cadre.py --file path/to.doc   # 指定文件
  python score_cadre.py --model qwen-max     # 指定模型
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 复用项目内 doc_parser (olefile 解析 .doc)
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, r"E:\ZKSJ_project\CYRS_test\demo\cadre_kg\ingestion")
try:
    from doc_parser import parse_doc  # type: ignore
except Exception:  # 独立运行时跳过
    parse_doc = None  # type: ignore

from openai import OpenAI
# docx 包延迟导入 (test 目录下存在 docx.py 影子, 模块级 import 会冲突)

# ============================================================
# 配置
# ============================================================
DEFAULT_DOC = Path(
    "E:\\大模型工作内容\\朝阳人事\\朝阳人事数据\\训练数据\\10考核评价\\"
    "01班子及干部综合考核\\2025综合考核\\述职报告\\干部一科\\乡\\"
    "1.南磨房乡班子总结及区管领导个人述职报告2025.01.19\\"
    "2025年度个人述职报告-001.doc"
)
RUBRIC_PATH = SCRIPT_DIR / "组织干部评价指标体系6.3.md"
OUTPUT_DIR = SCRIPT_DIR / "pingfen"
OUTPUT_DIR.mkdir(exist_ok=True)

LLM_CONFIG = {
    "api_key": os.environ.get(
        "DASHSCOPE_API_KEY", "sk-df9f397d047546d78741f0a0a478bf65"
    ),
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-max",  # 可用: qwen-turbo/plus/max/long; qwen2.5-* 403 access denied
    "temperature": 0.1,
    "max_tokens": 6000,
}

# ============================================================
# 1. 解析评分指标 (6.3.md)
# ============================================================
def load_rubric(rubric_path: Path) -> List[Dict[str, str]]:
    """解析 6.3.md 第一张大表 → 53 个三级指标 dict 列表.

    列: 一级维度 | 二级指标 | 三级指标 | 主要识别内容 | 文本提取线索/关键词
       | 满分（100分） | 较高分（85分） | 中等分（60分） | 低分（50分）
    """
    text = rubric_path.read_text(encoding="utf-8")
    rows: List[Dict[str, str]] = []
    in_table = False
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells and cells[0] in ("一级维度", "评价指标"):
            in_table = True
            continue
        if in_table and cells[0].startswith("---"):
            continue
        if in_table and len(cells) >= 9:
            # dim1 通常是 "德：政治坚定" 形式, 提取前缀大写字符
            dim1_raw = cells[0]
            dim1 = dim1_raw.split("：")[0].strip() if "：" in dim1_raw else dim1_raw
            rows.append({
                "dim1": dim1,
                "dim1_full": dim1_raw,
                "dim2": cells[1],
                "dim3": cells[2],
                "identify": cells[3],
                "keywords": cells[4],
                "anchor_100": cells[5],
                "anchor_85": cells[6],
                "anchor_60": cells[7],
                "anchor_50": cells[8],
            })
    if not rows:
        raise RuntimeError(f"未从 {rubric_path} 解析到评分指标, 请检查文件格式")
    return rows


# ============================================================
# 2. 解析 .doc / .docx
# ============================================================
def parse_any(path: Path) -> str:
    """统一返回纯文本, 支持 .doc (olefile) 和 .docx (python-docx)."""
    suffix = path.suffix.lower()
    if suffix == ".doc":
        if parse_doc is None:
            raise RuntimeError("doc_parser 不可用, 无法解析 .doc 文件")
        ext = parse_doc(str(path))
        return ext.raw_text
    if suffix == ".docx":
        # 绕过 test 目录下的 docx.py 影子文件, 强制从 site-packages 加载真正的 python-docx
        import importlib
        import sys as _sys
        _test_dir = str(SCRIPT_DIR)
        _saved = list(_sys.path)
        _sys.path = [p for p in _saved if os.path.abspath(p) != os.path.abspath(_test_dir)]
        _sys.modules.pop("docx", None)  # 清掉可能缓存的影子
        try:
            _docx_pkg = importlib.import_module("docx")
        finally:
            _sys.path = _saved
        d = _docx_pkg.Document(str(path))
        parts: List[str] = []
        for p in d.paragraphs:
            if p.text.strip():
                parts.append(p.text)
        for t in d.tables:
            for row in t.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        parts.append(cell.text)
        return "\n".join(parts)
    raise RuntimeError(f"不支持的文件类型: {suffix}")


# ============================================================
# 3. 切分干部段
# ============================================================
def extract_target_from_filename(path: Path) -> Optional[str]:
    """从文件名中提取 -NNN 形式的 3 位编号.

    匹配规则 (按优先级):
      1) `-NNN` 或 `_NNN` 在文件名末尾 (扩展名前), 例: 'xxx报告-004.docx' -> '004'
      2) 全文件名即 'NNN.doc' (部分老文件)
      3) 任意位置出现的 `编号-NNN` 或 `NNN号` 模式
    """
    name = path.stem  # 不含扩展名
    # 1) 末尾 -NNN / _NNN
    m = re.search(r"[-_](\d{3})$", name)
    if m:
        return m.group(1)
    # 2) 整个文件名就是 3 位数
    if re.fullmatch(r"\d{3}", name):
        return name
    # 3) 中间出现 -NNN-
    m = re.search(r"[-_](\d{3})[-_.]", name)
    if m:
        return m.group(1)
    return None


def find_cadre_ids(text: str) -> List[str]:
    """找出文中可能出现的 3 位编号 (排除年份 19xx/20xx 和电话号段).

    启发式: 出现 3 位数字且前后不是数字, 且不在常见的统计/百分号语境中.
    """
    candidates: List[str] = []
    for m in re.finditer(r"(?<!\d)(\d{3})(?!\d)", text):
        s = m.group(0)
        # 排除年份/百分号
        sidx = m.start()
        prev1 = text[sidx - 1] if sidx > 0 else ""
        next1 = text[m.end()] if m.end() < len(text) else ""
        if prev1 in "％%." or next1 in "％%.":
            continue
        candidates.append(s)
    # 保留出现频次 ≥1 的, 去重保序
    seen = set()
    out: List[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def extract_cadre_section(
    text: str,
    target_id: str,
    strict: bool = False,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """从全文中切出 target_id 编号对应段.

    strict=False (默认, 单干部 doc 场景):
        全文当 section, 仅校验 target_id 出现在文中.
        适用于一份 .doc 只描述一位干部的场景.

    strict=True (多干部 doc 场景, 旧行为):
        A) 找"职务词 + 3位编号"标题模式, 锁定 target_id 的位置
        B) 结束位置 = 下一个相同模式的标题位置
        C) 若文中只有一个这种标题, 结束 = 文末
        若找不到 → 返回 None, 报错.
    """
    # 通用诊断
    diag: Dict[str, Any] = {"target_id": target_id, "strict": strict}

    if not strict:
        # 单干部 doc 模式: 全文当 section
        diag["method"] = "full_doc"
        if target_id not in text:
            return None, {**diag, "method": "full_doc_id_missing",
                          "warn": f"target_id={target_id} 不在文中"}
        return text, diag

    # strict=True: 旧"职务词 + 编号"严格切分逻辑
    title_pat = re.compile(
        r"(书记|副书记|主任|副主任|乡长|副乡长|委员|部长|调研员|局长|处长|科长|主任科员)"
        r"[\s\u3000\u2003]*"
        r"(\d{3})"
    )
    titles = [(m.start(), m.group(2)) for m in title_pat.finditer(text)]
    diag["titles_found"] = [t[1] for t in titles]

    if not titles:
        return None, {**diag, "method": "no_title_pattern"}

    target_title = None
    for pos, tid in titles:
        if tid == target_id:
            target_title = pos
            break
    if target_title is None:
        return None, {**diag, "method": "target_not_in_titles"}

    next_titles = [p for p, t in titles if p > target_title + 10]
    end = next_titles[0] if next_titles else len(text)
    diag["method"] = "title"
    diag["start_position"] = target_title
    diag["end_position"] = end
    diag["n_titles_after"] = len(next_titles)

    section = text[target_title:end].strip()
    return section, diag


# ============================================================
# 4. Prompt 拼装
# ============================================================
SYSTEM_PROMPT = """你是中共北京市委组织部干部考核评估专家, 严格按照《组织干部评价指标体系 6.3》(德能勤绩廉 5 大维度 53 个三级指标) 对干部述职报告进行结构化评分.

【评分铁律 - 不可违反】
1. 评分必须从 {100, 85, 60, 50} 中四选一, 禁止出现其他任何数值.
2. 评分必须严格比对"评分锚点"原文, 不可主观臆断.
3. 评分依据必须直接引用材料原句 (带双引号), 不少于 20 字, 不允许编造.
4. 满分 (100) 标准: 需同时具备"具体场景 + 关键举措 + 量化结果/标志性成效".
5. 较高分 (85) 标准: 提及且有举措, 但缺少量化结果或标志性成效.
6. 中等分 (60) 标准: 仅笼统提及, 缺少具体内容和落实表现; 或材料完全未提及该指标.
7. 低分 (50) 标准: 出现负向锚点 (消极/推诿/敷衍/不力/不深/动摇/退缩/不严/不公/失职/失察 等).
8. 一岗双责/廉政类指标如无负面记录, 默评 85 分 (前提是述职中有"落实一岗双责/廉洁自律"等正向表述).
9. 严格区分"满分锚点"和"较高分锚点" - 不要把"有具体内容"就直接给满分.
10. 输出必须为严格 JSON, 不允许任何额外解释/前言/后语.

【输出 JSON Schema】
{
  "scores": [
    {
      "dim1": "德/能/勤/绩/廉 (一字)",
      "dim2": "二级指标原文",
      "dim3": "三级指标原文",
      "score": 100 | 85 | 60 | 50,
      "reason": "评分依据, 必须含材料原句引用"
    }
  ]
}
"""


def build_user_prompt(rubric: List[Dict[str, str]], cadre_text: str, cadre_id: str) -> str:
    """生成 user prompt: 53 指标 JSON + 述职全文."""
    rubric_json = json.dumps(
        [
            {
                "dim1": r["dim1"],
                "dim2": r["dim2"],
                "dim3": r["dim3"],
                "identify": r["identify"],
                "anchor_100": r["anchor_100"],
                "anchor_85": r["anchor_85"],
                "anchor_60": r["anchor_60"],
                "anchor_50": r["anchor_50"],
            }
            for r in rubric
        ],
        ensure_ascii=False,
    )
    # 述职截断到 12000 字符 (72b 上下文充足, 留空间给指标)
    cadre_text_trim = cadre_text[:12000]
    return f"""【干部编号】{cadre_id}

【述职报告全文】(共 {len(cadre_text)} 字, 此处取前 {len(cadre_text_trim)} 字)
{cadre_text_trim}

【评分指标体系】(共 {len(rubric)} 个三级指标, 严格按此 53 项逐项评分)
{rubric_json}

【输出要求】
1. 严格按上述 53 项逐一输出, dim1/dim2/dim3 字段值与指标体系完全一致, 不得省略
2. score 仅允许 100/85/60/50
3. reason 必含材料原句引用 (双引号包裹)
4. 仅输出 JSON, 不要任何额外文字
"""


def group_rubric_by_dim(rubric: List[Dict[str, str]]) -> "Dict[str, List[Dict[str, str]]]":
    """按一级维度分组: {'德': [...], '能': [...], '勤': [...], '绩': [...], '廉': [...]}"""
    groups: Dict[str, List[Dict[str, str]]] = {}
    for r in rubric:
        groups.setdefault(r["dim1"], []).append(r)
    return groups


def build_user_prompt_for_dim(
    rubric_subset: List[Dict[str, str]],
    cadre_text: str,
    cadre_id: str,
    dim_name: str,
) -> str:
    """生成单维度 user prompt (用于 5 次分批调用)."""
    rubric_json = json.dumps(
        [
            {
                "dim1": r["dim1"],
                "dim2": r["dim2"],
                "dim3": r["dim3"],
                "identify": r["identify"],
                "anchor_100": r["anchor_100"],
                "anchor_85": r["anchor_85"],
                "anchor_60": r["anchor_60"],
                "anchor_50": r["anchor_50"],
            }
            for r in rubric_subset
        ],
        ensure_ascii=False,
    )
    cadre_text_trim = cadre_text[:12000]
    return f"""【本次评分维度】{dim_name} ({len(rubric_subset)} 个三级指标)

【干部编号】{cadre_id}

【述职报告全文】(共 {len(cadre_text)} 字, 此处取前 {len(cadre_text_trim)} 字)
{cadre_text_trim}

【本维度指标体系】(共 {len(rubric_subset)} 项, 严格按此逐一评分)
{rubric_json}

【输出要求】
1. 严格按本维度的 {len(rubric_subset)} 项逐一输出, dim1 一律为 "{dim_name}", dim2/dim3 与指标体系完全一致, 不得省略
2. score 仅允许 100/85/60/50
3. reason 必含材料原句引用 (双引号包裹)
4. 仅输出 JSON, 不要任何额外文字
"""


# ============================================================
# 5. 调用 LLM
# ============================================================
def call_llm(sys_p: str, usr_p: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": sys_p},
            {"role": "user", "content": usr_p},
        ],
        temperature=cfg["temperature"],
        max_tokens=cfg["max_tokens"],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    return json.loads(content)


def call_llm_per_dim(
    rubric: List[Dict[str, str]],
    cadre_text: str,
    cadre_id: str,
    cfg: Dict[str, Any],
    parallel: bool = True,
) -> List[Dict[str, Any]]:
    """按维度分批调 LLM, 合并 5 批结果返回 52 项 list.

    parallel=True (默认): 5 维度并发调用 (ThreadPoolExecutor, 5 workers).
    parallel=False: 顺序调用.
    单维度失败 → 该维度所有项标"未评分", 不阻塞其他维度.
    """
    groups = group_rubric_by_dim(rubric)
    # 保持 德/能/勤/绩/廉 顺序, 输出更可读
    dim_order = ["德", "能", "勤", "绩", "廉"]
    ordered = [(d, groups.get(d, [])) for d in dim_order if groups.get(d)]
    # 若有未知维度 (兜底)
    for d in groups:
        if d not in dim_order:
            ordered.append((d, groups[d]))

    all_scores: List[Dict[str, Any]] = []
    n_workers = min(5, len(ordered)) if parallel else 1

    def _run_one(dim_name: str, sub_rubric: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
        if not sub_rubric:
            return dim_name, [], None
        try:
            usr_p = build_user_prompt_for_dim(sub_rubric, cadre_text, cadre_id, dim_name)
            result = call_llm(SYSTEM_PROMPT, usr_p, cfg)
            return dim_name, result.get("scores", []), None
        except Exception as e:
            placeholders = [
                {
                    "dim1": r["dim1"],
                    "dim2": r["dim2"],
                    "dim3": r["dim3"],
                    "score": "未评分",
                    "reason": f"LLM 调用失败: {e}",
                }
                for r in sub_rubric
            ]
            return dim_name, placeholders, str(e)

    if parallel:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = {
                ex.submit(_run_one, d, sub): d for d, sub in ordered
            }
            results_map: Dict[str, Tuple[List[Dict[str, Any]], Optional[str]]] = {}
            for fut in as_completed(futures):
                dim_name = futures[fut]
                d, scores, err = fut.result()
                results_map[dim_name] = (scores, err)
        # 按既定顺序合并
        for d, _ in ordered:
            scores, err = results_map[d]
            all_scores.extend(scores)
    else:
        for dim_name, sub_rubric in ordered:
            d, scores, err = _run_one(dim_name, sub_rubric)
            all_scores.extend(scores)

    return all_scores


# ============================================================
# 6. 渲染 Markdown (复用原 6.3.md, 末尾追加 LLM评分/评分依据 两列)
# ============================================================
def render_rubric_with_scores(
    rubric_path: Path,
    scores: List[Dict[str, Any]],
    cadre_id: str,
    cadre_text_len: int,
) -> str:
    """读取 6.3.md 原文件, 在主表格末尾追加 LLM评分/评分依据 两列.

    保留原文件的所有结构 (一级/二级/三级标题, 引言, 表格 1/2/3/4, ...),
    只对第一张主表 (52 行 9 列) 追加列.
    """
    original = rubric_path.read_text(encoding="utf-8")
    score_map: Dict[Tuple[str, str, str], Tuple[Any, str]] = {}
    for s in scores:
        key = (s.get("dim1", ""), s.get("dim2", ""), s.get("dim3", ""))
        score_map[key] = (s.get("score", "未评分"), (s.get("reason") or "").strip())

    lines = original.splitlines()
    out_lines: List[str] = []
    in_main_table = False
    main_table_seen = False  # 仅第一张主表追加, 后续表 (民主测评等) 不动
    in_skip_section = False  # 命中"## 二、其他"等无评分小节后, 全文跳过
    import datetime as _dt
    metadata_block = [
        "",
        f"> **本表由评分脚本自动追加** | 干部编号: {cadre_id} | "
        f"述职文本: {cadre_text_len} 字 | "
        f"模型: {LLM_CONFIG['model']} | "
        f"时间: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # 标记需跳过的二级标题 (原 6.3.md 中 3 个空占位小节, 评分用不到)
    SKIP_HEADERS = ("## 二、其他", "## 三、民主测评表", "## 四、德的反向评价表")

    def _append_two_cols(line: str, c1: str, c2: str) -> str:
        """行尾去尾随 | + 空白, 再补 | c1 | c2 |, 避免出现空单元格."""
        stripped = line.rstrip(" |")
        return f"{stripped} | {c1} | {c2} |"

    for line in lines:
        s = line.strip()
        # 进入跳过小节 → 整段丢弃 (直到文末)
        if any(line.startswith(h) for h in SKIP_HEADERS):
            in_skip_section = True
            continue
        if in_skip_section:
            continue
        if not s.startswith("|"):
            in_main_table = False
            out_lines.append(line)
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        # 仅处理主表 (一级维度表头), 其他 3 个空占位表 (民主测评/德的反向评价/其他) 不动
        if cells and cells[0] == "一级维度":
            # 表头前先插元信息
            if not main_table_seen:
                out_lines.extend(metadata_block)
            new_line = _append_two_cols(line, "LLM 评分", "评分依据")
            out_lines.append(new_line)
            in_main_table = True
            main_table_seen = True
            continue
        if in_main_table and cells[0].startswith("---"):
            new_line = _append_two_cols(line, "---", "---")
            out_lines.append(new_line)
            continue
        if in_main_table and len(cells) >= 9:
            # 数据行: 找对应评分
            dim1_raw = cells[0]
            dim1 = dim1_raw.split("：")[0].strip() if "：" in dim1_raw else dim1_raw
            dim2 = cells[1]
            dim3 = cells[2]
            score, reason = score_map.get((dim1, dim2, dim3), ("未评分", ""))
            # 清洗 reason 中可能破坏表格的字符
            reason_clean = (
                reason.replace("|", "/").replace("\r", " ").replace("\n", " ")
            )
            if len(reason_clean) > 300:
                reason_clean = reason_clean[:300] + "..."
            score_cell = f"**{score}**" if isinstance(score, int) else str(score)
            new_line = _append_two_cols(line, score_cell, reason_clean)
            out_lines.append(new_line)
            continue
        out_lines.append(line)

    return "\n".join(out_lines)


# ============================================================
# 7. main
# ============================================================
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=DEFAULT_DOC, help="述职报告文件路径")
    parser.add_argument(
        "--target", type=str, default=None,
        help="目标干部 3 位编号 (默认从文件名末尾的 -NNN 模式自动提取, 例: 'xxx报告-004.docx' -> '004')"
    )
    parser.add_argument("--model", type=str, default=LLM_CONFIG["model"], help="LLM 模型")
    parser.add_argument("--parallel", action="store_true", default=True,
                        help="5 维度并行调用 (默认开启, 5 workers 并发, 提速 ~5x). "
                             "传 --no-parallel 关闭.")
    parser.add_argument("--no-parallel", dest="parallel", action="store_false",
                        help="禁用并行, 顺序调用 5 维度.")
    parser.add_argument("--strict-split", action="store_true", default=False,
                        help="严格按『职务词+编号』标题模式切分干部段 (默认 False: 全文当 section, "
                             "适用于一份 .doc 只描述一位干部的场景).")
    parser.add_argument("--output", type=Path, default=None, help="输出 md 路径 (默认 pingfen/<id>.md)")
    args = parser.parse_args()

    # 若 --target 未提供, 从文件名自动提取
    target_source = "命令行"
    if args.target is None:
        extracted = extract_target_from_filename(args.file)
        if extracted:
            args.target = extracted
            target_source = "文件名"
        else:
            print("✗ 未指定 --target 且无法从文件名提取, 请显式传入 --target NNN")
            return 1

    cfg = dict(LLM_CONFIG)
    cfg["model"] = args.model

    print(f"=== 评分脚本启动 ===")
    print(f"文件: {args.file}")
    print(f"目标编号: {args.target} (来源: {target_source})")
    print(f"模型: {cfg['model']}")

    # 1. 加载指标
    print("\n[1/5] 加载评分指标 ...")
    rubric = load_rubric(RUBRIC_PATH)
    print(f"  解析到 {len(rubric)} 个三级指标")
    dim1_set = sorted({r["dim1"] for r in rubric})
    print(f"  一级维度: {dim1_set}")

    # 2. 解析文档
    print(f"\n[2/5] 解析文档 ...")
    text = parse_any(args.file)
    print(f"  文本长度: {len(text)} 字")
    ids = find_cadre_ids(text)
    print(f"  文中候选 3 位编号: {ids[:20]}{'...' if len(ids) > 20 else ''}")

    # 3. 切分目标段
    split_mode = "严格切分 (职务词+编号)" if args.strict_split else "全文当段 (单干部 doc)"
    print(f"\n[3/5] 切分编号 {args.target} 段 ({split_mode}) ...")
    section, diag = extract_cadre_section(text, args.target, strict=args.strict_split)
    if not section:
        print(f"  ✗ 切分失败, 诊断: {diag}")
        print(f"  候选 3 位编号: {ids}")
        if args.strict_split:
            print(f"  提示: 当前为 --strict-split 严格切分模式, 可去掉该标志走默认全文模式")
        print(f"  请检查文件或使用 --target 指定其他编号")
        return 1
    print(f"  ✓ 切分成功, 段长 {len(section)} 字, 方法: {diag.get('method')}")
    print(f"  诊断: {diag}")

    # 4. 调 LLM (按维度分批, 默认 5 维度并行)
    import time as _time
    parallel_mode = "并行 (5 workers)" if args.parallel else "顺序"
    print(f"\n[4/5] 调用 LLM 评分 ({len(rubric)} 项, 5 维度{parallel_mode}) ...")
    _t0 = _time.time()
    scores = call_llm_per_dim(
        rubric=rubric,
        cadre_text=section,
        cadre_id=args.target,
        cfg=cfg,
        parallel=args.parallel,
    )
    elapsed = _time.time() - _t0
    print(f"  耗时: {elapsed:.1f}s")
    # 按维度统计
    dim_counts: Dict[str, int] = {}
    for s in scores:
        d = s.get("dim1", "?")
        dim_counts[d] = dim_counts.get(d, 0) + 1
    for d in ["德", "能", "勤", "绩", "廉"]:
        if d in dim_counts:
            print(f"  ✓ {d}: {dim_counts[d]} 项")
    # 校验
    valid_keys = {(r["dim1"], r["dim2"], r["dim3"]) for r in rubric}
    matched = sum(1 for s in scores if (s.get("dim1"), s.get("dim2"), s.get("dim3")) in valid_keys)
    print(f"  匹配指标体系: {matched}/{len(rubric)}")

    # 5. 写 md
    print(f"\n[5/5] 写 Markdown ...")
    out_path = args.output or (OUTPUT_DIR / f"{args.file.stem}.md")
    md = render_rubric_with_scores(
        rubric_path=RUBRIC_PATH,
        scores=scores,
        cadre_id=args.target,
        cadre_text_len=len(section),
    )
    out_path.write_text(md, encoding="utf-8")
    print(f"  ✓ 已写入: {out_path}")
    print(f"\n=== 完成 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

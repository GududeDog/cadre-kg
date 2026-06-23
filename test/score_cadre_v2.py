"""
score_cadre_v2.py  (优化版)
=========================================================
目的: 读取 .doc/.docx 述职报告, 抽取指定编号干部的段,
      按《组织干部评价指标体系 6.3.md》53 个三级指标用 LLM 评分,
      生成一份 Markdown 评分报告.

核心优化:
  1. SYSTEM_PROMPT 改为"决策树"结构, 模型更易遵循
  2. 每个维度注入 2~3 个边界案例 (85 vs 100 对比)
  3. 输出后校验: score 合法性 / reason 原文引用 / 编造检测
  4. 段落级截断, 不切断句子
  5. LLM 调用带指数退避重试 + temperature=0.0
  6. 空 anchor_50 默认兜底 60 分, 不触发低分

用法:
  python score_cadre_v2.py                       # 默认 015
  python score_cadre_v2.py --target 001         # 指定其他编号
  python score_cadre_v2.py --file path/to.doc   # 指定文件
  python score_cadre_v2.py --model qwen-max     # 指定模型
"""

import argparse
import json
import os
import random
import re
import sys
import time
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
    "model": "qwen-max",
    "temperature": 0.0,          # 确定性输出, 减少波动
    "max_tokens": 8000,
    "max_retries": 3,            # 指数退避重试次数
    "retry_base_delay": 2.0,     # 基础退避秒数
}

# ============================================================
# 0. 边界案例库 (每个维度 2~3 个 85 vs 100 对比)
# ============================================================
BOUNDARY_CASES: Dict[str, str] = {
    "德": """
【边界案例 - 德维度】
▶ 100分案例 (三要素齐全):
  "始终以习近平新时代中国特色社会主义思想为指导，深入学习贯彻党的二十大和二十届历次全会精神，团结带领地区广大党员干部，锚定工作目标，强化党建引领、聚力实干担当，扎实推动各项工作不断取得新的成效。"
  → 满分: 具体理论(习近平新时代中国特色社会主义思想) + 部署贯彻(深入学习...精神) + 工作成效(扎实推动...取得新的成效)

▶ 85分案例 (缺量化成效):
  "015同志政治素质好，注重学习邓小平理论、'三个代表'重要思想、科学发展观和习近平新时代中国特色社会主义思想，深入贯彻习近平总书记系列重要讲话精神和党的十九大精神，认真贯彻执行党的路线、方针、政策，落实区委的各项决议比较坚决。"
  → 较高分: 有具体学习内容 + 有贯彻表态，但无"工作成效"的量化描述

▶ 60分案例 (仅笼统表态):
  "本人不断加强理论学习，主动担当作为，助力区域经济发展，取得了一定成绩。"
  → 中等分: 仅笼统提及"加强理论学习""主动担当"，无具体内容
""",
    "能": """
【边界案例 - 能维度】
▶ 100分案例 (三要素齐全):
  "通过专题研讨、固定学习日、党课等形式加大党员干部学习教育力度。今年共参加组织集中学习10次，专题党课2次，交流研讨4次，实地参观学习3次"
  → 满分: 具体形式(专题研讨/党课) + 关键举措(加大...力度) + 量化频次(10次/2次/4次/3次)

▶ 85分案例 (有举措无量化):
  "抽调期间除了认真参加市委巡视组的专题培训外，主动学习巡视工作的制度要求、规范流程、工作重点，同时加强对被巡视对象的了解，掌握工作的主动性和精准性。"
  → 较高分: 有具体学习内容(制度要求/规范流程/工作重点)，但无量化频次或成效数据

▶ 60分案例 (仅笼统表态):
  "一年来，本人始终坚持把学习放在首要位置，努力在提高自身的理论修养、职业素养和综合素质上下功夫。"
  → 中等分: 仅笼统表态"坚持学习""提高素养"，无具体学习内容或举措
""",
    "勤": """
【边界案例 - 勤维度】
▶ 100分案例 (三要素齐全):
  "积极履行组织部门疫情防控职责，发挥组织引领力，注重对上沟通、对下协调，组织全乡各基层党组织、党员及志愿者开展疫情防控工作，尤其在新发地疫情发生后，连夜抽调35名机关干部骨干开展万余名密接人员数据排查、管控等工作，确保地区安全稳定。"
  → 满分: 具体场景(新发地疫情) + 关键举措(连夜抽调35名干部/万余名密接排查) + 量化结果(确保地区安全稳定)

▶ 85分案例 (有场景缺量化):
  "工作务实，经常深入一线了解情况，帮助基层、群众解决实际困难。发现苗头性诉求，及时协调涉及部门进行专项调度，集思广益，在大量诉求爆发之前将问题解决"
  → 较高分: 有具体场景(深入一线/苗头性诉求)，有举措(协调部门/专项调度)，但无量化数据

▶ 60分案例 (仅笼统表态):
  "为人诚恳，做事认真，团结关心同事，勤奋好学，事业心和责任感强，自身要求严格，廉洁自律，群众基础较好。"
  → 中等分: 仅笼统评价"做事认真""勤奋好学"，无具体事件或成效支撑
""",
    "绩": """
【边界案例 - 绩维度】
▶ 100分案例 (三要素齐全):
  "2020年全年接收案件7759件，全部100%响应、100%回复，解决率为95.9%，满意率为94.5%，全年综合得分97分，排全区第一，扭转了2019年排名落后的局面。"
  → 满分: 具体场景(全年接诉即办) + 关键举措(100%响应/回复) + 量化结果(7759件/95.9%/94.5%/全区第一)

▶ 85分案例 (有举措缺排名/对比):
  "在发生'蛋壳公寓'事件后，每天到接待点盯守，对来登记的人员耐心细致接待宣传政策，对有争议的充分发挥调解作用，成功帮助房主和租客化解纠纷，平息矛盾，解决涉及蛋壳公寓纠纷963间。"
  → 较高分: 有具体场景(蛋壳公寓事件) + 有举措(盯守/接待/调解) + 有量化(963间)，但无"排名/表彰/推广"等标志性成效

▶ 60分案例 (仅笼统提及):
  "积极协调公安、城管、急救等多方力量共同参与拆违、控违等重点难点工作，较好完成了甘露园东里、园艺场等违建拆除，实现辖区违法建设'动态清零'"
  → 中等分: 有具体工作(拆违/控违)但"较好完成""动态清零"表述笼统，无具体面积/户数/排名数据
""",
    "廉": """
【边界案例 - 廉维度】
▶ 100分案例 (三要素齐全):
  "完善在重大决策、人事任免、项目安排和大额资金使用等方面的议事规则、工作程序和规章制度。严格执行中央八项规定及其实施细则，进一步加强对理论学习、考核考勤、岗位责任、公车管理等方面的具体要求，持之以恒防止'四风'问题的反弹。"
  → 满分: 具体场景(重大决策/人事任免/项目安排/大额资金) + 关键举措(完善议事规则/严格执行八项规定) + 制度成效(防止四风反弹)

▶ 85分案例 (有表态缺制度细节):
  "始终坚持履行党风廉政建设责任，履行'一岗双责'，自觉加强党纪党规的学习。"
  → 较高分: 有具体责任(一岗双责/党纪党规)，但无制度机制或具体执行细节

▶ 60分案例 (仅笼统提及):
  "坚持'反对四风、服务群众'，坚决执行好中央八项规定、市委十五条意见和区委'两个从严''四个坚决不允许'等各项规定要求，切实做到从严要求、从严管理，坚决不出现有令不行、有禁不止的现象。"
  → 中等分: 仅罗列规定名称和表态，无具体执行举措或成效
""",
}


# ============================================================
# 1. 解析评分指标 (6.3.md)
# ============================================================
def load_rubric(rubric_path: Path) -> List[Dict[str, str]]:
    """解析 6.3.md 第一张大表 → 三级指标 dict 列表."""
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
        import importlib
        import sys as _sys
        _test_dir = str(SCRIPT_DIR)
        _saved = list(_sys.path)
        _sys.path = [p for p in _saved if os.path.abspath(p) != os.path.abspath(_test_dir)]
        _sys.modules.pop("docx", None)
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
    """从文件名中提取 -NNN 形式的 3 位编号."""
    name = path.stem
    m = re.search(r"[-_](\d{3})$", name)
    if m:
        return m.group(1)
    if re.fullmatch(r"\d{3}", name):
        return name
    m = re.search(r"[-_](\d{3})[-_.]", name)
    if m:
        return m.group(1)
    return None


def find_cadre_ids(text: str) -> List[str]:
    """找出文中可能出现的 3 位编号."""
    candidates: List[str] = []
    for m in re.finditer(r"(?<!\d)(\d{3})(?!\d)", text):
        s = m.group(0)
        sidx = m.start()
        prev1 = text[sidx - 1] if sidx > 0 else ""
        next1 = text[m.end()] if m.end() < len(text) else ""
        if prev1 in "％%." or next1 in "％%.":
            continue
        candidates.append(s)
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
    """从全文中切出 target_id 编号对应段."""
    diag: Dict[str, Any] = {"target_id": target_id, "strict": strict}

    if not strict:
        diag["method"] = "full_doc"
        if target_id not in text:
            return None, {**diag, "method": "full_doc_id_missing",
                          "warn": f"target_id={target_id} 不在文中"}
        return text, diag

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
# 4. Prompt 拼装 (优化版)
# ============================================================
SYSTEM_PROMPT_V2 = """你是中共北京市委组织部干部考核评估专家。你的唯一任务是：对干部述职报告的每一个三级指标，从 {100, 85, 60, 50} 中选择一个分数。

## 评分决策树（必须按此顺序判断）

```
Step 1: 材料中是否出现该指标的【负向锚点关键词】？
    ├── 是 → 50分（低分）
    └── 否 → 进入 Step 2

Step 2: 材料中是否同时满足【满分三要素】？
    ├── 是 → 100分（满分）
    └── 否 → 进入 Step 3

Step 3: 材料中是否有【较高分两要素】？
    ├── 是 → 85分（较高分）
    └── 否 → 60分（中等分/未提及）
```

### 满分三要素（必须同时满足）
1. **具体场景**：有明确的时间/地点/事件/项目名称
2. **关键举措**：干部本人做了什么（动词开头，如"组织""推动""协调"）
3. **量化结果**：有数字、比例、排名、荣誉称号、典型案例推广

### 较高分两要素（满足其一即可）
1. 有具体场景 + 关键举措，但**无量化结果**
2. 有量化结果，但**举措描述笼统**（如"积极推进""认真落实"）

### 低分触发词（出现任一即50分）
- 德维度：立场动摇、临阵退缩、逃避推诿、处置力弱、政治不坚定
- 能维度：推进不力、成效不明显、专业欠缺、思路不多、不熟悉、有所欠缺
- 勤维度：消极懈怠、推诿扯皮、责任心不强、拖延工作
- 绩维度：未完成、滞后、排名靠后、被通报批评
- 廉维度：问责、通报、处分、投诉查实、风险较高、整改不到位

## 输出格式（严格JSON）

{
  "scores": [
    {
      "dim1": "德",           // 仅允许: 德/能/勤/绩/廉
      "dim2": "政治判断力",    // 必须与指标体系完全一致
      "dim3": "政治站位与大局意识", // 必须与指标体系完全一致
      "score": 85,            // 仅允许: 100/85/60/50
      "reason": "材料中...（此处必须包含≥20字的原文引用，用双引号标注）"
    }
  ]
}

## 自检清单（输出前必须核对）
□ score 值在 {100,85,60,50} 中
□ reason 包含用双引号包裹的原文，且≥20字
□ dim1/dim2/dim3 与输入的指标体系完全一致
□ 没有编造材料中不存在的原文
□ 没有给"仅笼统提及"的指标打100分
"""


def _trim_text_by_paragraph(text: str, max_chars: int = 12000) -> str:
    """按段落截断, 不切断句子."""
    if len(text) <= max_chars:
        return text
    # 找到 max_chars 之前的最后一个换行符
    cut = text.rfind("\n", 0, max_chars)
    if cut == -1:
        cut = max_chars
    return text[:cut]


def build_user_prompt_for_dim_v2(
    rubric_subset: List[Dict[str, str]],
    cadre_text: str,
    cadre_id: str,
    dim_name: str,
) -> str:
    """生成单维度 user prompt (用于 5 次分批调用)."""
    # 清洗 rubric: anchor_50 为空或"——"时, 标注为"无", 避免模型误判低分
    cleaned_rubric = []
    for r in rubric_subset:
        cr = dict(r)
        anchor_50 = cr.get("anchor_50", "").strip()
        if not anchor_50 or anchor_50 in ("——", "-", "/"):
            cr["anchor_50"] = "【无负向锚点，默认不触发低分】"
        cleaned_rubric.append(cr)

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
            for r in cleaned_rubric
        ],
        ensure_ascii=False,
    )
    cadre_text_trim = _trim_text_by_paragraph(cadre_text, 12000)
    boundary = BOUNDARY_CASES.get(dim_name, "")

    return f"""【本次评分维度】{dim_name} ({len(rubric_subset)} 个三级指标)

【干部编号】{cadre_id}

【述职报告全文】(共 {len(cadre_text)} 字, 此处取前 {len(cadre_text_trim)} 字, 按段落截断不切断句子)
{cadre_text_trim}

【本维度指标体系】(共 {len(rubric_subset)} 项, 严格按此逐一评分)
{rubric_json}

【边界案例 - 用于校准 85分 vs 100分 的边界】
{boundary}

【输出要求】
1. 严格按本维度的 {len(rubric_subset)} 项逐一输出, dim1 一律为 "{dim_name}", dim2/dim3 与指标体系完全一致, 不得省略
2. score 仅允许 100/85/60/50
3. reason 必含材料原句引用 (双引号包裹, ≥20字)
4. 仅输出 JSON, 不要任何额外文字
"""


# ============================================================
# 5. 调用 LLM (带指数退避重试)
# ============================================================
def call_llm_with_retry(
    sys_p: str,
    usr_p: str,
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """调用 LLM, 失败时指数退避重试."""
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    max_retries = cfg.get("max_retries", 3)
    base_delay = cfg.get("retry_base_delay", 2.0)
    last_err: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
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
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"    LLM 调用失败 (attempt {attempt + 1}/{max_retries + 1}): {e}, {delay:.1f}s 后重试...")
                time.sleep(delay)
            else:
                raise last_err
    raise RuntimeError("LLM 调用全部失败")


def group_rubric_by_dim(rubric: List[Dict[str, str]]) -> "Dict[str, List[Dict[str, str]]]":
    """按一级维度分组."""
    groups: Dict[str, List[Dict[str, str]]] = {}
    for r in rubric:
        groups.setdefault(r["dim1"], []).append(r)
    return groups


def call_llm_per_dim_v2(
    rubric: List[Dict[str, str]],
    cadre_text: str,
    cadre_id: str,
    cfg: Dict[str, Any],
    parallel: bool = True,
) -> List[Dict[str, Any]]:
    """按维度分批调 LLM, 合并 5 批结果返回."""
    groups = group_rubric_by_dim(rubric)
    dim_order = ["德", "能", "勤", "绩", "廉"]
    ordered = [(d, groups.get(d, [])) for d in dim_order if groups.get(d)]
    for d in groups:
        if d not in dim_order:
            ordered.append((d, groups[d]))

    all_scores: List[Dict[str, Any]] = []
    n_workers = min(3, len(ordered)) if parallel else 1  # 降级到3并发, 避免RPM超限

    def _run_one(dim_name: str, sub_rubric: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
        if not sub_rubric:
            return dim_name, [], None
        try:
            usr_p = build_user_prompt_for_dim_v2(sub_rubric, cadre_text, cadre_id, dim_name)
            result = call_llm_with_retry(SYSTEM_PROMPT_V2, usr_p, cfg)
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
            futures = {ex.submit(_run_one, d, sub): d for d, sub in ordered}
            results_map: Dict[str, Tuple[List[Dict[str, Any]], Optional[str]]] = {}
            for fut in as_completed(futures):
                dim_name = futures[fut]
                d, scores, err = fut.result()
                results_map[dim_name] = (scores, err)
        for d, _ in ordered:
            scores, err = results_map[d]
            all_scores.extend(scores)
    else:
        for dim_name, sub_rubric in ordered:
            d, scores, err = _run_one(dim_name, sub_rubric)
            all_scores.extend(scores)

    return all_scores


# ============================================================
# 6. 输出后校验与修正 (新增)
# ============================================================
def validate_and_fix_scores(
    scores: List[Dict[str, Any]],
    rubric: List[Dict[str, str]],
    cadre_text: str,
) -> List[Dict[str, Any]]:
    """后处理：校验并修正LLM输出."""
    valid_scores = {100, 85, 60, 50}
    rubric_keys = {(r["dim1"], r["dim2"], r["dim3"]) for r in rubric}
    # 构建 keyword → rubric item 映射, 用于模糊匹配
    rubric_lookup: Dict[Tuple[str, str, str], Dict[str, str]] = {
        (r["dim1"], r["dim2"], r["dim3"]): r for r in rubric
    }
    fixed = []
    fix_log: List[str] = []

    for s in scores:
        # 1. 校验 dim1/dim2/dim3 是否匹配
        key = (s.get("dim1", ""), s.get("dim2", ""), s.get("dim3", ""))
        matched_key = None

        if key in rubric_keys:
            matched_key = key
        else:
            # 模糊匹配: dim2+dim3 相同即认为匹配
            for rk, rv in rubric_lookup.items():
                if rv["dim2"] == s.get("dim2") and rv["dim3"] == s.get("dim3"):
                    matched_key = rk
                    s["dim1"] = rv["dim1"]
                    fix_log.append(f"模糊匹配修正 dim1: {s.get('dim2')}/{s.get('dim3')}")
                    break

        if matched_key is None:
            s["score"] = "未匹配"
            s["reason"] = f"指标名称与体系不匹配: {key}"
            fixed.append(s)
            fix_log.append(f"未匹配指标: {key}")
            continue

        # 2. 校验 score 合法性
        score = s.get("score")
        if score not in valid_scores:
            if isinstance(score, (int, float)):
                old_score = score
                s["score"] = min(valid_scores, key=lambda x: abs(x - score))
                fix_log.append(f"分数修正: {old_score} → {s['score']} ({s.get('dim3')})")
            else:
                s["score"] = "非法值"
                fixed.append(s)
                fix_log.append(f"非法分数: {score} ({s.get('dim3')})")
                continue

        # 3. 校验 reason 是否有原文引用 (双引号包裹 ≥20字)
        reason = s.get("reason", "")
        quotes = re.findall(r'"([^"]{20,})"', reason)
        if not quotes:
            # 尝试从 cadre_text 中补全: 找与 keywords 相关的句子
            rubric_item = rubric_lookup.get(matched_key)
            if rubric_item:
                keywords = rubric_item.get("keywords", "")
                matched_quote = _find_best_quote(cadre_text, keywords)
                if matched_quote:
                    s["reason"] = f'材料中"{matched_quote}" {reason}'
                    fix_log.append(f"补全引用: {s.get('dim3')}")
                else:
                    s["reason"] = f"[原文引用缺失] {reason}"
                    fix_log.append(f"引用缺失: {s.get('dim3')}")

        # 4. 校验 reason 中引用的原文是否真实存在于材料中
        for quote in quotes:
            if quote not in cadre_text:
                s["score"] = "待复核"
                s["reason"] += f" [警告: 引用原文未在材料中找到]"
                fix_log.append(f"编造引用: {s.get('dim3')}")
                break

        fixed.append(s)

    if fix_log:
        print(f"  [校验修正] 共 {len(fix_log)} 处调整:")
        for log in fix_log[:10]:
            print(f"    - {log}")
        if len(fix_log) > 10:
            print(f"    ... 等共 {len(fix_log)} 处")

    return fixed


def _find_best_quote(text: str, keywords: str) -> Optional[str]:
    """根据 keywords 在 text 中找到最匹配的句子."""
    if not keywords or not text:
        return None
    kw_list = [k.strip() for k in keywords.replace("、", " ").replace(",", " ").split() if len(k.strip()) > 1]
    if not kw_list:
        return None

    sentences = re.split(r'[。；！？\n]', text)
    best_score = 0
    best_sent = None
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 10:
            continue
        score = sum(1 for kw in kw_list if kw in sent)
        if score > best_score:
            best_score = score
            best_sent = sent
    # 返回最长不超过 120 字的句子
    if best_sent and len(best_sent) > 120:
        best_sent = best_sent[:120] + "..."
    return best_sent


# ============================================================
# 7. 渲染 Markdown
# ============================================================
def render_rubric_with_scores(
    rubric_path: Path,
    scores: List[Dict[str, Any]],
    cadre_id: str,
    cadre_text_len: int,
    fix_log_summary: str = "",
) -> str:
    """读取 6.3.md 原文件, 在主表格末尾追加 LLM评分/评分依据 两列."""
    original = rubric_path.read_text(encoding="utf-8")
    score_map: Dict[Tuple[str, str, str], Tuple[Any, str]] = {}
    for s in scores:
        key = (s.get("dim1", ""), s.get("dim2", ""), s.get("dim3", ""))
        score_map[key] = (s.get("score", "未评分"), (s.get("reason") or "").strip())

    lines = original.splitlines()
    out_lines: List[str] = []
    in_main_table = False
    main_table_seen = False
    in_skip_section = False
    import datetime as _dt
    metadata_block = [
        "",
        f"> **本表由评分脚本(score_cadre_v2)自动追加** | 干部编号: {cadre_id} | "
        f"述职文本: {cadre_text_len} 字 | "
        f"模型: {LLM_CONFIG['model']} | "
        f"时间: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> **校验摘要**: {fix_log_summary}" if fix_log_summary else "",
        "",
    ]

    SKIP_HEADERS = ("## 二、其他", "## 三、民主测评表", "## 四、德的反向评价表")

    def _append_two_cols(line: str, c1: str, c2: str) -> str:
        stripped = line.rstrip(" |")
        return f"{stripped} | {c1} | {c2} |"

    for line in lines:
        s = line.strip()
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
        if cells and cells[0] == "一级维度":
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
            dim1_raw = cells[0]
            dim1 = dim1_raw.split("：")[0].strip() if "：" in dim1_raw else dim1_raw
            dim2 = cells[1]
            dim3 = cells[2]
            score, reason = score_map.get((dim1, dim2, dim3), ("未评分", ""))
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
# 8. main
# ============================================================
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=DEFAULT_DOC, help="述职报告文件路径")
    parser.add_argument(
        "--target", type=str, default=None,
        help="目标干部 3 位编号 (默认从文件名末尾的 -NNN 模式自动提取)"
    )
    parser.add_argument("--model", type=str, default=LLM_CONFIG["model"], help="LLM 模型")
    parser.add_argument("--parallel", action="store_true", default=True, help="5 维度并行调用 (默认开启, 3 workers)")
    parser.add_argument("--no-parallel", dest="parallel", action="store_false", help="禁用并行")
    parser.add_argument("--strict-split", action="store_true", default=False, help="严格按『职务词+编号』切分")
    parser.add_argument("--output", type=Path, default=None, help="输出 md 路径 (默认 pingfen/<id>.md)")
    args = parser.parse_args()

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

    print(f"=== score_cadre_v2 启动 ===")
    print(f"文件: {args.file}")
    print(f"目标编号: {args.target} (来源: {target_source})")
    print(f"模型: {cfg['model']} | temperature: {cfg['temperature']} | max_retries: {cfg['max_retries']}")

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

    # 4. 调 LLM (按维度分批, 默认并行)
    import time as _time
    parallel_mode = "并行 (3 workers)" if args.parallel else "顺序"
    print(f"\n[4/5] 调用 LLM 评分 ({len(rubric)} 项, 5 维度{parallel_mode}) ...")
    _t0 = _time.time()
    scores = call_llm_per_dim_v2(
        rubric=rubric,
        cadre_text=section,
        cadre_id=args.target,
        cfg=cfg,
        parallel=args.parallel,
    )
    elapsed = _time.time() - _t0
    print(f"  耗时: {elapsed:.1f}s")

    # 5. 输出校验与修正
    print(f"\n[5/5] 输出校验与修正 ...")
    scores_fixed = validate_and_fix_scores(scores, rubric, section)
    fix_summary = f"共 {len(scores_fixed)} 项, 其中修正 {sum(1 for s in scores_fixed if isinstance(s.get('score'), str))} 项异常"
    print(f"  {fix_summary}")

    # 按维度统计
    dim_counts: Dict[str, int] = {}
    for s in scores_fixed:
        d = s.get("dim1", "?")
        dim_counts[d] = dim_counts.get(d, 0) + 1
    for d in ["德", "能", "勤", "绩", "廉"]:
        if d in dim_counts:
            print(f"  ✓ {d}: {dim_counts[d]} 项")

    # 校验匹配度
    valid_keys = {(r["dim1"], r["dim2"], r["dim3"]) for r in rubric}
    matched = sum(1 for s in scores_fixed if (s.get("dim1"), s.get("dim2"), s.get("dim3")) in valid_keys)
    print(f"  匹配指标体系: {matched}/{len(rubric)}")

    # 6. 写 md
    print(f"\n[6/6] 写 Markdown ...")
    out_path = args.output or (OUTPUT_DIR / f"{args.file.stem}_v2.md")
    md = render_rubric_with_scores(
        rubric_path=RUBRIC_PATH,
        scores=scores_fixed,
        cadre_id=args.target,
        cadre_text_len=len(section),
        fix_log_summary=fix_summary,
    )
    out_path.write_text(md, encoding="utf-8")
    print(f"  ✓ 已写入: {out_path}")
    print(f"\n=== 完成 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

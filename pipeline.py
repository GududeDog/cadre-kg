"""Cadre Knowledge Graph Pipeline.

支持两种运行模式：
  - run()                  批量处理 SOURCE_DIR 下所有文件（main.py 用）
  - run_for_category()     单文件、按类目分流（server.py 上传接口用）
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from config import SOURCE_DIR
from ingestion.parser import DocumentParser, Document
from chunking.chunker import Chunker
from extraction.extractor import Extractor, ExtractionResult
from alignment.aligner import EntityAligner
from graph_db.writer import GraphWriter

import config


class Pipeline:
    def __init__(self, skip_llm: bool = False, dry_run: bool = False):
        self.skip_llm = skip_llm
        self.dry_run = dry_run
        self.parser = DocumentParser()
        self.chunker = Chunker(
            chunk_size=config.CHUNK_SIZE,
            overlap=config.CHUNK_OVERLAP,
        )
        self.extractor = Extractor() if not skip_llm else None
        self.aligner = EntityAligner()
        self.writer = GraphWriter() if not dry_run else None

    def run(self):
        t0 = time.time()

        # 1. Ingest
        print("[1/6] 文档接入 ...")
        docs = self._ingest()
        print(f"  → {len(docs)} docs loaded")

        # 2. Parse
        print("[2/6] 文本解析 ...")
        for d in docs:
            _ = d.raw_text
        print("  ✓ done")

        # 3. Chunk
        print("[3/6] 分块 ...")
        all_chunks = []
        for d in docs:
            chunks = self.chunker.chunk(d)
            all_chunks.extend(chunks)
        print(f"  → {len(all_chunks)} chunks")

        # 4. LLM Extract
        print("[4/6] LLM 抽取实体/关系/标签 ...")
        if self.skip_llm or self.extractor is None:
            result = ExtractionResult()
            print("  ⏭ skipped (--skip-llm)")
        else:
            result = self.extractor.extract_batch(all_chunks)
            print(f"  → {len(result.entities)} entities, "
                  f"{len(result.relations)} relations, {len(result.tags)} tags")

        # 5. Align
        print("[5/6] 实体对齐 ...")
        aligned_entities = self.aligner.align_entities(result.entities)
        aligned_relations = self.aligner.align_relations(result.relations)
        result.tags = self.aligner.normalize_tags(result.tags)
        print(f"  → {len(aligned_entities)} entities (deduped), "
              f"{len(aligned_relations)} relations (deduped), "
              f"{len(result.tags)} tags (normalized)")

        # 6. Graph DB write
        print("[6/6] 写入图数据库 ...")
        if self.dry_run or self.writer is None:
            self._dump(aligned_entities, aligned_relations, result.tags)
        else:
            self._write(aligned_entities, aligned_relations, result.tags)

        elapsed = time.time() - t0
        print(f"\n✓ Pipeline 完成，耗时 {elapsed:.1f}s")

    def run_for_category(
        self,
        file_path,
        doc_type: str,
        category_code: str,
        cadre_id_hint: Optional[str] = None,
    ) -> dict:
        """单文件、按类目分流的处理入口（上传接口用）。

        返回摘要: {filename, doc_type, category_code, cadre_id,
                  entities, relations, tags, chunks, raw_extracted, ...}
        """
        from category_router import CATEGORY_LIST

        path = Path(file_path)
        profile = next(
            (c for c in CATEGORY_LIST if c["code"] == category_code), None
        )
        if profile is None:
            return {
                "filename": path.name,
                "error": f"未知类目: {category_code}",
            }

        use_llm = profile.get("use_llm", True) and not self.skip_llm

        # 1. Parse
        doc = self.parser.parse(path)
        if doc is None:
            return {
                "filename": path.name,
                "category_code": category_code,
                "doc_type": doc_type,
                "skipped": True,
                "reason": "解析失败或格式不支持",
            }

        # 2. 强制覆盖 doc_type
        doc.doc_type = doc_type

        # 3. 注入 cadre_id: 表单输入 > 文件名解析（非年度考核）> LLM 识别
        if not cadre_id_hint and category_code != "annual_assessment":
            import re as _re
            m = _re.search(r'(\d{3,4})', path.stem)
            if m:
                cadre_id_hint = m.group(1)
                print(f"  [信息] 从文件名解析干部编号: {cadre_id_hint}")
        if cadre_id_hint:
            doc.metadata = doc.metadata or {}
            doc.metadata["cadre_id"] = cadre_id_hint

        # 4. Chunk
        chunks = self.chunker.chunk(doc)

        # 5. Extract
        if category_code == "basic_info" and self.extractor is not None:
            # ── 基础信息：2次 LLM 调用 ──
            cid = cadre_id_hint or "unknown"
            print(f"  [1/3] 文档解析 → 纯文本 ({len(doc.raw_text)} 字符)")

            print(f"  [2/3] LLM #1 → 抽取表单字段 ...")
            result = self.extractor.extract_basic_info(doc.raw_text, cid)
            etypes = set(e.get("type", "?") for e in result.entities)
            print(f"        实体: {len(result.entities)} 个 ({', '.join(sorted(etypes))})")

            # 读 YAML 拿简历抽取规则，全文发给 LLM #2
            import yaml as _yaml
            rules_path = Path(__file__).parent / "extraction_rules" / "basic_info.yaml"
            with open(rules_path, encoding="utf-8") as _f:
                resume_rules = _yaml.safe_load(_f).get("resume_rules", [])

            print(f"  [3/3] LLM #2 → 抽取简历条目 ...")
            llm_result = self.extractor.extract_resume(
                doc.raw_text, cid, resume_rules)
            print(f"        简历: {len(llm_result.entities)} 条")
            result.merge(llm_result)
        elif category_code == "annual_assessment" and self.extractor is not None:
            # ── 年度考核：1次 LLM 抽取所有维度 ──
            cid = cadre_id_hint or ""
            print(f"  [1/3] 文档解析 → 纯文本 ({len(doc.raw_text)} 字符)")

            # 读 YAML 拿4组规则
            import yaml as _yaml
            rules_path = Path(__file__).parent / "extraction_rules" / "annual_assessment.yaml"
            with open(rules_path, encoding="utf-8") as _f:
                rules = _yaml.safe_load(_f)

            print(f"  [2/3] LLM → 抽取编号/文风/分工/作风/成绩变化 ...")
            result = self.extractor.extract_annual_report(
                doc.raw_text, cid,
                writing_style_rules=rules.get("writing_style_rules", []),
                division_rules=rules.get("division_rules", []),
                ability_style_rules=rules.get("ability_style_rules", []),
                performance_change_rules=rules.get("performance_change_rules", []),
            )

            # 从 LLM 返回的 Cadre 实体取编号
            if not cadre_id_hint:
                for e in result.entities:
                    if e.get("type") == "Cadre":
                        cid = (e.get("properties") or {}).get("cadre_id")
                        if cid:
                            cadre_id_hint = cid
                            print(f"  [信息] LLM 识别干部编号: {cid}")
                            break
                if not cadre_id_hint:
                    cadre_id_hint = "unknown"

            etypes = set(e.get("type", "?") for e in result.entities)
            print(f"        实体: {len(result.entities)} 个 ({', '.join(sorted(etypes))})")

            # 确保 Cadre 节点存在
            if not any(e.get("type") == "Cadre" for e in result.entities):
                result.entities.insert(0, {
                    "type": "Cadre", "name": cid,
                    "properties": {"cadre_id": cid, "name": cid},
                })

            # 文档分块 → Chroma
            print(f"  [3/3] 文档分块 → Chroma 向量库 ...")
            from chroma_store.writer import ChromaWriter
            try:
                cw = ChromaWriter()
                cw.store_document(doc.raw_text, cadre_id=cid, doc_name=path.name)
                cw.close()
                print(f"        Chroma 写入成功")
            except Exception as e:
                print(f"        Chroma 写入失败: {e}")
        elif category_code == "org_evaluation" and self.extractor is not None:
            # ── 组织评价材料：按干部编号拆分 → 逐干部 LLM 提取 ──
            cid = cadre_id_hint or ""
            full_text = doc.raw_text

            # 提取考察年份
            import re as _re4
            year_match = _re4.search(r'考察组?于?\s*(\d{4})\s*年', full_text)
            inspection_year = year_match.group(1) if year_match else "unknown"
            print(f"  [信息] 考察年份: {inspection_year}")

            # 正则拆分：按行首的"编号，"模式切分每个干部段落
            pattern = r'^(\d{2,5}|[A-Za-z]{1,3})[，,:：]'
            matches = list(_re4.finditer(pattern, full_text, _re4.MULTILINE))
            print(f"  [信息] 识别到 {len(matches)} 个编号候选，正在过滤...")

            # 读取 YAML 规则
            import yaml as _yaml
            rules_path = Path(__file__).parent / "extraction_rules" / "org_evaluation.yaml"
            with open(rules_path, encoding="utf-8") as _f:
                rules = _yaml.safe_load(_f)

            result = ExtractionResult()
            cadre_count = 0
            max_cadres = 20  # 安全上限

            for i, m in enumerate(matches):
                if cadre_count >= max_cadres:
                    break

                start = m.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
                section_text = full_text[start:end].strip()
                section_id = m.group(1)

                # 过滤：该行必须包含个人基本信息特征（男/女）
                first_line = section_text.split('\n')[0]
                if '男' not in first_line and '女' not in first_line:
                    print(f"  [跳过] \"{section_id}\" → 非干部段落（无性别信息）")
                    continue

                # 截断过长段落（保留前后各3000字符）
                if len(section_text) > 6000:
                    section_text = section_text[:3000] + "\n...\n" + section_text[-3000:]
                    print(f"  [截断] \"{section_id}\" 段落过长，已截取前后各3000字")

                cadre_count += 1
                print(f"  [{cadre_count}/{len(matches)}] LLM → 提取干部 {section_id} ...")
                single_result = self.extractor.extract_org_evaluation(
                    section_text, section_id,
                    inspection_time_rules=rules.get("inspection_time_rules", []),
                    core_traits_rules=rules.get("core_traits_rules", []),
                    trait_evidence_rules=rules.get("trait_evidence_rules", []),
                    performance_rules=rules.get("performance_rules", []),
                    shortcoming_rules=rules.get("shortcoming_rules", []),
                    familiar_field_rules=rules.get("familiar_field_rules", []),
                    style_tag_rules=rules.get("style_tag_rules", []),
                )
                etypes = set(e.get("type", "?") for e in single_result.entities)
                print(f"        实体: {len(single_result.entities)} 个 ({', '.join(sorted(etypes))})")

                # 注入考察年份到 Profile 实体
                for e in single_result.entities:
                    if e.get("type") == "Profile":
                        props = e.get("properties", {}) or {}
                        if not props.get("assessment_year"):
                            props["assessment_year"] = inspection_year

                result.merge(single_result)
                if not cadre_id_hint and cadre_count == 1:
                    cadre_id_hint = section_id

            print(f"  ── 总计 {cadre_count} 个干部, {len(result.entities)} 实体")

            # 文档分块 → Chroma
            print(f"  [Chroma] 文档分块 → 向量库 ...")
            from chroma_store.writer import ChromaWriter
            try:
                cw = ChromaWriter()
                cw.store_document(doc.raw_text, cadre_id=cid or "org_eval",
                                  doc_name=path.name)
                cw.close()
                print(f"        Chroma 写入成功")
            except Exception as e:
                print(f"        Chroma 写入失败: {e}")
        elif category_code == "research" and self.extractor is not None:
            # ── 组织部大调研：按章节拆分，每章1次LLM ──
            cid = ""  # 空字符串，由 LLM 自主识别编号
            full_text = doc.raw_text
            print(f"  [1/4] 文档解析 → 纯文本 ({len(full_text)} 字符)")

            # 读取 YAML 规则
            import yaml as _yaml
            rules_path = Path(__file__).parent / "extraction_rules" / "research.yaml"
            with open(rules_path, encoding="utf-8") as _f:
                rules = _yaml.safe_load(_f)

            # 按大章节标题拆分（一、二、三、四、五）
            import re as _re5
            sections = _re5.split(r'\n(?=[一二三四五]、)', full_text)
            section_labels = ["前言", "一（班子评价）", "二（主要负责人）", "三（党委其他班子）", "四（其他副职）", "五（纪检监察）"]

            print(f"  [2/4] 章节拆分 → {len(sections)} 个章节")
            for i in range(len(sections)):
                label = section_labels[i] if i < len(section_labels) else f"章节{i}"
                print(f"        [{'跳过' if i not in (2,3,4) else '处理'}] {label}: {len(sections[i])} 字符")

            # 构建处理任务列表: (section_text, label)
            tasks = []
            for idx in [2, 3]:  # 二、三 → 各1次调用
                text = sections[idx]
                if len(text.strip()) >= 50:
                    tasks.append((text, section_labels[idx]))
            # 四拆分为2段（人数最多，各4人）
            sec4 = sections[4]
            sub4 = _re5.split(r'\n（五）', sec4)
            if len(sub4) >= 2:
                if len(sub4[0].strip()) >= 50:
                    tasks.append((sub4[0], "四（副职-前半）"))
                if len(sub4[1].strip()) >= 50:
                    tasks.append(("（五）" + sub4[1], "四（副职-后半）"))
            elif len(sec4.strip()) >= 50:
                tasks.append((sec4, section_labels[4]))

            result = ExtractionResult()
            for call_idx, (section_text, label) in enumerate(tasks):
                print(f"  [3/4-{call_idx+1}/{len(tasks)}] LLM → 提取{label} ({len(section_text)}字符) ...")
                single_result = self.extractor.extract_research(
                    section_text, cid,
                    personality_rules=rules.get("personality_rules", []),
                    ability_rules=rules.get("ability_rules", []),
                )
                etypes = set(e.get("type", "?") for e in single_result.entities)
                cadre_ids_in_section = set()
                for e in single_result.entities:
                    if e.get("type") == "Cadre":
                        eid = (e.get("properties") or {}).get("cadre_id", "")
                        if eid:
                            cadre_ids_in_section.add(eid)
                print(f"        {label}: {len(single_result.entities)} 实体 ({', '.join(sorted(etypes))})")
                print(f"        被评价人: {len(cadre_ids_in_section)} 个 → {sorted(cadre_ids_in_section)}")
                result.merge(single_result)

            total_cadres = set()
            for e in result.entities:
                if e.get("type") == "Cadre":
                    eid = (e.get("properties") or {}).get("cadre_id", "")
                    if eid:
                        total_cadres.add(eid)
            print(f"  ── 总计: {len(total_cadres)} 个干部, {len(result.entities)} 实体")

            # 文档分块 → Chroma
            print(f"  [4/4] 文档分块 → Chroma 向量库 ...")
            from chroma_store.writer import ChromaWriter
            try:
                cw = ChromaWriter()
                cw.store_document(doc.raw_text, cadre_id=cid,
                                  doc_name=path.name)
                cw.close()
                print(f"        Chroma 写入成功")
            except Exception as e:
                print(f"        Chroma 写入失败: {e}")
        elif use_llm and self.extractor is not None:
            result = self.extractor.extract_batch(chunks)
        else:
            result = ExtractionResult()

        raw_entity_count = len(result.entities)
        raw_relation_count = len(result.relations)

        # 6. Align
        print(f"  [合并] → {raw_entity_count} 实体, {raw_relation_count} 关系")
        entities = self.aligner.align_entities(result.entities)
        relations = self.aligner.align_relations(result.relations)
        result.tags = self.aligner.normalize_tags(result.tags)
        print(f"  [去重] → {len(entities)} 实体, {len(relations)} 关系")

        # 7. Write
        write_ok = False
        write_error = None
        if not self.dry_run and self.writer is not None:
            try:
                self.writer.init_schema()
                self.writer.write_entities(entities)
                self.writer.write_relations(relations)
                self.writer.write_tags(result.tags)
                write_ok = True
                print(f"  [写入] → Neo4j 成功")
            except Exception as e:
                write_error = f"{type(e).__name__}: {e}"
                print(f"[错误] 写入失败: {write_error}")

        status = "成功" if write_ok else ("演示模式" if self.dry_run else "失败")
        print(f"  ── 处理完成: {path.name} → {len(entities)} 实体, {len(relations)} 关系, 写入={status}\n")
        return {
            "filename": path.name,
            "category_code": category_code,
            "category_name": profile["name"],
            "doc_type": doc_type,
            "cadre_id": cadre_id_hint,
            "use_llm": use_llm,
            "chunks": len(chunks),
            "raw_entities": raw_entity_count,
            "raw_relations": raw_relation_count,
            "entities": len(entities),
            "relations": len(relations),
            "tags": len(result.tags),
            "write_ok": write_ok,
            "write_error": write_error,
            "sample_entities": [
                {"type": e.get("type"), "name": e.get("name"),
                 "cadre_id": (e.get("properties") or {}).get("cadre_id")}
                for e in entities[:3]
            ],
            "skipped": False,
        }

    def _ingest(self) -> List[Document]:
        docs = []
        for fp in sorted(SOURCE_DIR.iterdir()):
            doc = self.parser.parse(fp)
            if doc:
                docs.append(doc)
        return docs

    def _dump(self, entities, relations, tags):
        out = {
            "entities": entities,
            "relations": relations,
            "tags": tags,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2)[:5000])
        print("... (dry-run, truncated)")

    def _write(self, entities, relations, tags):
        self.writer.init_schema()
        self.writer.write_entities(entities)
        self.writer.write_relations(relations)
        self.writer.write_tags(tags)
        self.writer.close()


def main():
    parser = argparse.ArgumentParser(description="干部知识图谱 Pipeline")
    parser.add_argument("--skip-llm", action="store_true", help="跳过 LLM 抽取")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不写入 Neo4j")
    args = parser.parse_args()

    pipeline = Pipeline(skip_llm=args.skip_llm, dry_run=args.dry_run)
    pipeline.run()


if __name__ == "__main__":
    main()

"""
单文件入库测试工具
用法:
    python test_ingest.py                                          # 测试全部文件
    python test_ingest.py --file "干部审批表001.doc"                # 测试单个文件
    python test_ingest.py --file "归档考察-020同志的考察材料.doc"   # 测试单个文件
    python test_ingest.py --file "考核评价-个人述职报告 - 009.docx"
    python test_ingest.py --list                                    # 列出所有可测文件
    python test_ingest.py --clear                                   # 清空Neo4j全部数据
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
from embedding.embedder import Embedder

import config


class SingleFileTester:
    def __init__(self, skip_llm: bool = False):
        self.skip_llm = skip_llm
        self.parser = DocumentParser()
        self.chunker = Chunker(config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        self.extractor = None if skip_llm else Extractor()
        self.aligner = EntityAligner()
        self.writer = GraphWriter()

    def close(self):
        self.writer.close()

    # ─────────────────────────────────────────────
    # 入口：测试单个文件
    # ─────────────────────────────────────────────
    def test_one(self, filename: str) -> dict:
        fp = SOURCE_DIR / filename
        if not fp.exists():
            print(f"[ERROR] 文件不存在: {fp}")
            return {"status": "error", "msg": "file not found"}

        print(f"{'='*60}")
        print(f"测试文件: {filename}")
        print(f"{'='*60}")

        # 0. 从文件名提取 cadre_id (e.g. "011.doc" → "011")
        import re as _re
        m = _re.match(r"^(\d{3,4})", Path(filename).stem)
        file_cadre_id = m.group(1) if m else None
        print(f"  [推断] cadre_id = {file_cadre_id} (from filename)")

        # 1. 文档接入
        print(f"\n[1/6] 文档接入 ...")
        doc = self.parser.parse(fp)
        if doc is None:
            print(f"  [ERROR] 无法解析")
            return {"status": "error", "msg": "parse failed"}
        print(f"  类型: {doc.doc_type}")
        print(f"  大小: {len(doc.raw_text)} 字符")
        if doc.tables:
            print(f"  表格: {len(doc.tables)} 个")
        if doc.sheets:
            print(f"  Sheet: {list(doc.sheets.keys())}")

        # 2. 文本预览
        print(f"\n[2/6] 文本预览 (前500字) ...")
        print(f"  {doc.raw_text[:500].replace(chr(10), chr(10)+'  ')}")

        # 3. 分块
        print(f"\n[3/6] 分块 ...")
        chunks = self.chunker.chunk(doc)
        print(f"  生成 {len(chunks)} 个chunk")
        for i, c in enumerate(chunks):
            print(f"  chunk[{i}]: {len(c.text)}字 → {c.text[:80]}...")
            if i >= 4:
                print(f"  ... 共 {len(chunks)} 个")
                break

        # 4. LLM抽取
        print(f"\n[4/6] LLM 抽取实体/关系/标签 ...")
        t0 = time.time()
        result = ExtractionResult()
        if self.skip_llm:
            print("  [跳过] (--skip-llm)")
        else:
            for i, chunk in enumerate(chunks):
                print(f"\n  正在抽取 chunk[{i}] ...")
                try:
                    doc_type = getattr(chunk, "doc_type", "")
                    metadata = getattr(chunk, "metadata", {}) or {}
                    # Fallback: use cadre_id from filename if metadata doesn't have it
                    cadre_id = metadata.get("cadre_id") or file_cadre_id
                    r = self.extractor.extract(
                        chunk.text, doc_type=doc_type, cadre_id=cadre_id)
                    self._print_detail(r, chunk.text)
                    result.merge(r)
                    print(f"  >> chunk[{i}] 完成: +{len(r.entities)}实体 "
                          f"+{len(r.relations)}关系 +{len(r.tags)}标签"
                          f"{' (干部:'+cadre_id+')' if cadre_id else ''}")
                except Exception as e:
                    print(f"  [失败] {e}")
        elapsed = time.time() - t0
        print(f"\n  总计: {len(result.entities)} 实体, {len(result.relations)} 关系, {len(result.tags)} 标签 (耗时 {elapsed:.1f}s)")

        # 详细打印抽取结果
        self._print_entities(result.entities)
        self._print_relations(result.relations)
        self._print_tags(result.tags)

        # 5. 实体对齐
        print(f"\n[5/6] 实体对齐 ...")
        aligned_entities = self.aligner.align_entities(result.entities)
        aligned_relations = self.aligner.align_relations(result.relations)
        # 标签同义归一化
        before_tags = len(result.tags)
        result.tags = self.aligner.normalize_tags(result.tags)
        after_tags = len(result.tags)
        print(f"  对齐后: {len(aligned_entities)} 实体, {len(aligned_relations)} 关系")
        if before_tags != after_tags:
            print(f"  标签归一: {before_tags} -> {after_tags} (同义合并)")

        # 6. 写入Neo4j
        print(f"\n[6/6] 写入 Neo4j ...")
        try:
            self.writer.init_schema()
            self.writer.write_entities(aligned_entities)
            self.writer.write_relations(aligned_relations)
            self.writer.write_tags(result.tags)
            print(f"  [OK] 写入完成")
        except Exception as e:
            print(f"  [ERROR] 写入失败: {e}")
            import traceback
            traceback.print_exc()

        summary = {
            "status": "ok",
            "file": filename,
            "doc_type": doc.doc_type,
            "chars": len(doc.raw_text),
            "chunks": len(chunks),
            "entities": len(result.entities),
            "aligned_entities": len(aligned_entities),
            "relations": len(result.relations),
            "aligned_relations": len(aligned_relations),
            "tags": len(result.tags),
            "elapsed_s": round(elapsed, 1),
        }
        print(f"\n{'─'*60}")
        print(f"结果汇总: {json.dumps(summary, ensure_ascii=False, indent=2)}")
        return summary

    # ─────────────────────────────────────────────
    # 打印抽取结果
    # ─────────────────────────────────────────────
    @staticmethod
    def _print_entities(entities: list):
        if not entities:
            print("  [实体] 无")
            return
        by_type = {}
        for e in entities:
            by_type.setdefault(e.get("type","?"), []).append(e)
        for t, items in by_type.items():
            print(f"  [{t}] x{len(items)}")
            for e in items[:5]:
                name = e.get("name", "")
                props = e.get("properties", {})
                prop_str = " ".join(f"{k}={v}" for k, v in props.items() if v)
                print(f"    - {name}  {prop_str}")
            if len(items) > 5:
                print(f"    ... 共 {len(items)} 个")

    @staticmethod
    def _print_relations(relations: list):
        if not relations:
            print("  [关系] 无")
            return
        by_rel = {}
        for r in relations:
            by_rel.setdefault(r.get("relation","?"), []).append(r)
        for rel, items in by_rel.items():
            print(f"  [{rel}] x{len(items)}")
            for r in items[:5]:
                print(f"    ({r.get('source_name','')}) -[{rel}]-> ({r.get('target_name','')})")
            if len(items) > 5:
                print(f"    ... 共 {len(items)} 个")

    @staticmethod
    def _print_tags(tags: list):
        if not tags:
            print("  [标签] 无")
            return
        by_cat = {}
        for t in tags:
            by_cat.setdefault(t.get("type","?"), []).append(t)
        for cat, items in by_cat.items():
            print(f"  [{cat}标签] x{len(items)}")
            for t in items[:5]:
                print(f"    - {t.get('name','')} → {t.get('target','')}")
            if len(items) > 5:
                print(f"    ... 共 {len(items)} 个")


    # ─────────────────────────────────────────────
    # 打印每个chunk的详细抽取结果
    # ─────────────────────────────────────────────
    def _print_detail(self, r: ExtractionResult, text: str):
        if not r.entities and not r.relations and not r.tags:
            print("    (无抽取结果)")
            return

        # 实体
        if r.entities:
            print("    -- 实体 --")
            by_type = {}
            for e in r.entities:
                by_type.setdefault(e.get("type", "?"), []).append(e)
            for t, items in by_type.items():
                for e in items:
                    name = e.get("name", "")
                    props = e.get("properties", {})
                    prop_str = "  ".join(f"{k}={v}" for k, v in props.items() if v)
                    line = f"      [{t}] {name}"
                    if prop_str:
                        line += f"  ({prop_str})"
                    print(line)

        # 关系
        if r.relations:
            print("    -- 关系 --")
            for rel in r.relations:
                print(f"      ({rel.get('source_name','')}) -[{rel.get('relation','')}]-> ({rel.get('target_name','')})")

        # 标签
        if r.tags:
            print("    -- 标签 --")
            for tag in r.tags:
                print(f"      [{tag.get('type','?')}] {tag.get('name','')} -> {tag.get('target','')}")

        # 原始JSON预览(仅显示前600字符)
        raw = {"entities": r.entities, "relations": r.relations, "tags": r.tags}
        import json
        print(f"    (原始JSON: {json.dumps(raw, ensure_ascii=False)[:600]})")


# ─────────────────────────────────────────────
# 辅助：列出所有可测试文件
# ─────────────────────────────────────────────
def list_files():
    print("可测试的文件列表:")
    for fp in sorted(SOURCE_DIR.iterdir()):
        if fp.suffix.lower() in DocumentParser.SUPPORTED:
            doc = DocumentParser.parse(fp)
            size = len(doc.raw_text) if doc else 0
            print(f"  {fp.name:50s}  type={doc.doc_type if doc else '?':20s}  {size:>6} chars")


# ─────────────────────────────────────────────
# 清空Neo4j数据
# ─────────────────────────────────────────────
def clear_neo4j():
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=config.NEO4J_AUTH)
    with driver.session() as session:
        # 统计
        counts = session.run("""
            MATCH (n) 
            RETURN count(n) as nodes, 
                   (CALL { MATCH ()-[r]->() RETURN count(r) }) as rels
        """).single()
        print(f"当前图数据库: {counts['nodes']} 节点, {counts['rels']} 关系")
        confirm = input("确认清空所有数据? (yes/no): ")
        if confirm.lower() == "yes":
            session.run("MATCH (n) DETACH DELETE n")
            print("已清空所有数据.")
        else:
            print("已取消.")
    driver.close()


# ─────────────────────────────────────────────
# 批量测试 & 汇总报告
# ─────────────────────────────────────────────
def test_all(skip_llm=False):
    results = []
    total_t0 = time.time()
    for fp in sorted(SOURCE_DIR.iterdir()):
        if fp.suffix.lower() not in DocumentParser.SUPPORTED:
            continue
        tester = SingleFileTester(skip_llm=skip_llm)
        try:
            summary = tester.test_one(fp.name)
            results.append(summary)
        finally:
            tester.close()
        print("\n")

    elapsed = time.time() - total_t0
    print(f"{'='*60}")
    print(f"批量测试完成 (总耗时 {elapsed:.1f}s)")
    print(f"{'='*60}")
    print(f"{'文件':50s} {'类型':20s} {'chunks':>6s} {'实体':>6s} {'关系':>6s} {'标签':>6s} {'耗时':>6s}")
    print(f"{'─'*100}")
    for r in results:
        fname = r.get("file","")[:48]
        print(f"{fname:50s} {r.get('doc_type',''):20s} {r.get('chunks',0):>6d} "
              f"{r.get('aligned_entities',0):>6d} {r.get('aligned_relations',0):>6d} "
              f"{r.get('tags',0):>6d} {r.get('elapsed_s',0):>6.1f}")
    print(f"{'─'*100}")


# ─────────────────────────────────────────────
# 查库验证：看 Neo4j 里有什么
# ─────────────────────────────────────────────
def query_neo4j():
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=config.NEO4J_AUTH)
    with driver.session() as session:
        print("=== Neo4j 数据概览 ===")
        # 各类型节点数
        result = session.run("""
            MATCH (n) 
            RETURN labels(n)[0] as label, count(n) as cnt 
            ORDER BY cnt DESC
        """)
        for r in result:
            print(f"  [{r['label']:20s}] {r['cnt']:>4d} 节点")

        # 各类型关系数
        result = session.run("""
            MATCH ()-[r]->() 
            RETURN type(r) as rel_type, count(r) as cnt 
            ORDER BY cnt DESC
        """)
        for r in result:
            print(f"  ({r['rel_type']:20s}) {r['cnt']:>4d} 关系")

        # 样例查询
        print("\n=== 干部列表 ===")
        result = session.run("""
            MATCH (c:Cadre) 
            RETURN c.name as name, c.gender as gender, c.birth_date as birth, c.political_status as status
            LIMIT 10
        """)
        for r in result:
            print(f"  {r['name']:10s} {r.get('gender','') or '':4s} {r.get('birth','') or '':12s} {r.get('status','') or ''}")

        print("\n=== 能力标签列表 ===")
        result = session.run("""
            MATCH (t:AbilityTag)
            RETURN t.tag_category as cat, t.tag_name as name, count{(c:Cadre)-[:HAS_ABILITY]->(t)} as refs
            ORDER BY cat, refs DESC
            LIMIT 20
        """)
        for r in result:
            print(f"  [{r['cat']:8s}] {r['name']:15s} 被引用 {r['refs']} 次")

        print("\n=== 任职关系样例 ===")
        result = session.run("""
            MATCH (c:Cadre)-[r:HOLDS]->(p:Position)
            RETURN c.name, type(r), p.position_name, r.is_current
            LIMIT 10
        """)
        for r in result:
            cur = "现任" if r.get('is_current') == 'true' else ""
            print(f"  {r['c.name']:10s} → {r['p.position_name']:20s} {cur}")
    driver.close()


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="单文件入库测试工具")
    parser.add_argument("--file", "-f", type=str, default=None,
                        help="测试单个文件（文件名）")
    parser.add_argument("--skip-llm", action="store_true",
                        help="跳过 LLM 抽取（仅测试解析+分块+入库）")
    parser.add_argument("--list", "-l", action="store_true",
                        help="列出所有可测试文件")
    parser.add_argument("--clear", action="store_true",
                        help="清空 Neo4j 全部数据")
    parser.add_argument("--query", "-q", action="store_true",
                        help="查询 Neo4j 当前数据概览")
    parser.add_argument("--all", "-a", action="store_true",
                        help="测试全部文件")
    args = parser.parse_args()

    if args.list:
        list_files()
        return
    if args.clear:
        clear_neo4j()
        return
    if args.query:
        query_neo4j()
        return
    skip_llm = args.skip_llm
    if args.all:
        test_all(skip_llm)
        return
    if args.file:
        tester = SingleFileTester(skip_llm=skip_llm)
        try:
            tester.test_one(args.file)
        finally:
            tester.close()
        return

    # 默认：交互菜单
    print("1. 测试全部文件")
    print("2. 测试单个文件")
    print("3. 列出所有可测试文件")
    print("4. 清空 Neo4j")
    print("5. 查询 Neo4j 当前数据")
    choice = input("\n请选择 (1-5): ").strip()
    if choice == "1":
        test_all(skip_llm)
    elif choice == "2":
        list_files()
        fname = input("\n输入文件名: ").strip()
        if fname:
            tester = SingleFileTester(skip_llm=skip_llm)
            try:
                tester.test_one(fname)
            finally:
                tester.close()
    elif choice == "3":
        list_files()
    elif choice == "4":
        clear_neo4j()
    elif choice == "5":
        query_neo4j()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()

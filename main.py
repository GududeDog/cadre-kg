"""Cadre Knowledge Graph Pipeline.

Usage:
    python main.py                     # run full pipeline
    python main.py --skip-llm          # skip LLM extraction (ingestion + chunking only)
    python main.py --dry-run           # print extracted data, don't write to Neo4j
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List

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
            _ = d.raw_text  # ensure parsed
        print("  ✓ done")

        # 3. Chunk
        print("[3/6] 分块 ...")
        all_chunks = []
        for d in docs:
            chunks = self.chunker.chunk(d)
            all_chunks.extend(chunks)
        print(f"  → {len(all_chunks)} chunks")

        # 4. LLM Extract (entities / relations / tags)
        print("[4/6] LLM 抽取实体/关系/标签 ...")
        if self.skip_llm:
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
        if self.dry_run:
            self._dump(aligned_entities, aligned_relations, result.tags)
        else:
            self._write(aligned_entities, aligned_relations, result.tags)

        elapsed = time.time() - t0
        print(f"\n✓ Pipeline 完成，耗时 {elapsed:.1f}s")

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

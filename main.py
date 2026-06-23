"""Cadre Knowledge Graph Pipeline — 命令行入口。

Usage:
    python main.py                     # run full pipeline
    python main.py --skip-llm          # skip LLM extraction
    python main.py --dry-run           # print extracted data, don't write to Neo4j
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser(description="干部知识图谱 Pipeline")
    parser.add_argument("--skip-llm", action="store_true", help="跳过 LLM 抽取")
    parser.add_argument("--dry-run", action="store_true", help="仅打印，不写入 Neo4j")
    args = parser.parse_args()

    pipeline = Pipeline(skip_llm=args.skip_llm, dry_run=args.dry_run)
    pipeline.run()


if __name__ == "__main__":
    main()

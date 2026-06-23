import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import jieba

from config import CHUNK_HARD_MAX


@dataclass
class Chunk:
    text: str
    tokens: List[str] = field(default_factory=list)
    source_file: str = ""
    doc_type: str = ""
    chunk_index: int = 0
    metadata: Dict = field(default_factory=dict)


class Chunker:
    def __init__(self, chunk_size: int = 2048, overlap: int = 64,
                 hard_max: int = CHUNK_HARD_MAX):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.hard_max = hard_max
        for w in ["南磨房乡", "高碑店乡", "组织委员", "地区工委",
                   "民主测评", "考察材料", "述职报告", "一级调研员"]:
            jieba.add_word(w)

    @staticmethod
    def _extract_cadre_id(file_path: str) -> Optional[str]:
        """Extract cadre ID (e.g. 001, 009, 020) from filename."""
        stem = Path(file_path).stem
        # Skip collective documents
        skip_keywords = ["民主测评汇总", "领导班子", "民主测评结果", "功能需求"]
        if any(k in stem for k in skip_keywords):
            return None
        # Pattern 1: 审批表001 → 001
        m = re.search(r'(?:审批表|考察|述职报告)[-_]?(\d{3})', stem)
        if m:
            return m.group(1)
        # Pattern 2: 归档考察-020同志 → 020
        m = re.search(r'(\d{3})同志', stem)
        if m:
            return m.group(1)
        # Pattern 3: 考核评价-个人述职报告 - 009 → 009
        m = re.search(r'(\d{3})\)?$', stem)
        if m:
            return m.group(1)
        return None

    def chunk(self, doc) -> List[Chunk]:
        strategy = self._pick_strategy(doc.doc_type)
        chunks = strategy(doc)
        cadre_id = self._extract_cadre_id(str(doc.file_path))
        for c in chunks:
            if cadre_id:
                c.metadata["cadre_id"] = cadre_id
        return chunks

    def _pick_strategy(self, doc_type: str):
        table_types = {"evaluation_summary", "evaluation_result",
                       "evaluation_team", "work_division_table"}
        if doc_type in table_types:
            return self._table_chunk
        if doc_type in ("investigation", "report", "txt", "work_division"):
            return self._semantic_chunk
        return self._semantic_chunk

    def _table_chunk(self, doc) -> List[Chunk]:
        chunks = []
        idx = 0
        # data from tables first
        for t in getattr(doc, "tables", []):
            for row in t.get("rows", []):
                text = " | ".join(str(v) for v in row.values()) if isinstance(row, dict) else " | ".join(row)
                if not text.strip():
                    continue
                tokens = list(jieba.cut(text))
                chunks.append(Chunk(
                    text=text, tokens=tokens,
                    source_file=str(doc.file_path), doc_type=doc.doc_type,
                    chunk_index=idx))
                idx += 1
        # sheet data
        for sheet_name, records in getattr(doc, "sheets", {}).items():
            for rec in records:
                text = " | ".join(str(v) for v in rec.values()) if isinstance(rec, dict) else " | ".join(rec)
                if not text.strip():
                    continue
                tokens = list(jieba.cut(text))
                chunks.append(Chunk(
                    text=text, tokens=tokens,
                    source_file=str(doc.file_path), doc_type=doc.doc_type,
                    chunk_index=idx, metadata={"sheet": sheet_name}))
                idx += 1
        return chunks

    def _semantic_chunk(self, doc) -> List[Chunk]:
        text = doc.raw_text
        if not text.strip():
            return []
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if len(paragraphs) <= 1 and len(text) > self.chunk_size:
            paragraphs = [p.strip() for p in re.split(r"\n", text) if p.strip()]
        chunks: List[Chunk] = []
        current: List[str] = []
        current_len = 0
        idx = 0

        def emit(text_: str):
            nonlocal idx
            if not text_.strip():
                return
            tokens = list(jieba.cut(text_))
            chunks.append(Chunk(
                text=text_, tokens=tokens,
                source_file=str(doc.file_path), doc_type=doc.doc_type,
                chunk_index=idx))
            idx += 1

        for para in paragraphs:
            if len(para) > self.hard_max:
                if current:
                    emit("\n\n".join(current))
                    current, current_len = [], 0
                for i in range(0, len(para), self.hard_max):
                    emit(para[i:i + self.hard_max])
                continue
            para_len = len(para)
            if current_len + para_len > self.chunk_size and current:
                emit("\n\n".join(current))
                overlap_text = ""
                overlap_len = 0
                for p in reversed(current):
                    if overlap_len + len(p) >= self.overlap:
                        overlap_text = p + "\n\n" + overlap_text
                        break
                    overlap_text = p + "\n\n" + overlap_text
                    overlap_len += len(p)
                current = [overlap_text.strip()] if overlap_text.strip() else []
                current_len = len(overlap_text)
            current.append(para)
            current_len += para_len
        if current:
            emit("\n\n".join(current))
        return chunks

    def _force_split(self, text: str, max_size: int) -> List[str]:
        """Force-split a long text at safe boundaries (date/sentence/newline)."""
        if len(text) <= max_size:
            return [text]
        boundaries = re.compile(r"(?<=\n)|(?<=[。；])|(?=\d{4}[./-]\d{2})")
        parts = [p for p in boundaries.split(text) if p]
        pieces: List[str] = []
        cur = ""
        for p in parts:
            if len(cur) + len(p) > max_size and cur:
                pieces.append(cur)
                cur = p
            else:
                cur += p
        if cur:
            pieces.append(cur)
        for piece in pieces:
            if len(piece) > max_size:
                step = max_size
                idx = pieces.index(piece)
                pieces[idx:idx + 1] = [piece[i:i + step] for i in range(0, len(piece), step)]
                break
        return pieces

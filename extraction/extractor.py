import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, TAG_TAXONOMY
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .tag_extractor import TagExtractor


@dataclass
class ExtractionResult:
    entities: List[Dict] = field(default_factory=list)
    relations: List[Dict] = field(default_factory=list)
    tags: List[Dict] = field(default_factory=list)

    def merge(self, other: "ExtractionResult"):
        self.entities.extend(other.entities)
        self.relations.extend(other.relations)
        self.tags.extend(other.tags)


class Extractor:
    def __init__(self):
        self.client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        self.model = LLM_MODEL
        self.tag_extractor = TagExtractor()

    def extract(self, text: str, doc_type: str = "",
                cadre_id: Optional[str] = None) -> ExtractionResult:
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(text, cadre_id)},
            ],
            temperature=0.1,
        )
        try:
            resp = self.client.chat.completions.create(
                **kwargs, response_format={"type": "json_object"}
            )
        except Exception:
            resp = self.client.chat.completions.create(**kwargs)
        raw = resp.choices[0].message.content
        result = self._parse(raw)

        # Tag extraction via dedicated tag_extractor
        tag_result = self.tag_extractor.extract(
            text=text, doc_type=doc_type, cadre_id=cadre_id)
        if tag_result:
            result.tags = tag_result

        return result

    def extract_batch(self, chunks: List[Any]) -> ExtractionResult:
        combined = ExtractionResult()
        for chunk in chunks:
            try:
                doc_type = getattr(chunk, "doc_type", "")
                metadata = getattr(chunk, "metadata", {}) or {}
                cadre_id = metadata.get("cadre_id")
                result = self.extract(
                    chunk.text, doc_type=doc_type, cadre_id=cadre_id)
                combined.merge(result)
            except Exception as e:
                print(f"[WARN] extract failed for chunk #{chunk.chunk_index}: {e}")
        return combined

    @staticmethod
    def _parse(raw: str) -> ExtractionResult:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return ExtractionResult(
            entities=data.get("entities", []),
            relations=data.get("relations", []),
            tags=data.get("tags", []),
        )

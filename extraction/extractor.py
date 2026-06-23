import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, TAG_TAXONOMY
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .prompts import RESUME_PROMPT, build_resume_prompt_with_rules
from .prompts import BASIC_INFO_PROMPT, build_basic_info_prompt
from .prompts import ANNUAL_REPORT_PROMPT, build_annual_report_prompt
from .prompts import ORG_EVALUATION_PROMPT, build_org_evaluation_prompt
from .prompts import RESEARCH_PROMPT, build_research_prompt
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
        self.client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            timeout=120.0,
        )
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
            max_tokens=4096,
        )
        if "deepseek" in self.model.lower():
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(3):
            try:
                try:
                    resp = self.client.chat.completions.create(
                        **kwargs, response_format={"type": "json_object"}
                    )
                except Exception:
                    resp = self.client.chat.completions.create(**kwargs)
                raw = resp.choices[0].message.content or ""
                if raw.strip():
                    result = self._parse(raw)
                    if cadre_id:
                        self._enforce_cadre_id(result, cadre_id)
                    tag_result = self.tag_extractor.extract(
                        text=text, doc_type=doc_type, cadre_id=cadre_id)
                    if tag_result:
                        result.tags = tag_result
                    return result
                print(f"  [retry {attempt+1}/3] empty content, retrying...")
                import time as _t
                _t.sleep(2 + attempt * 2)
            except Exception as e:
                last_error = e
                print(f"  [retry {attempt+1}/3] LLM/parse failed: {e}")
                import time as _t
                _t.sleep(2 + attempt * 2)

        print(f"  [FAIL] after 3 attempts. last_error={last_error}")
        return ExtractionResult()

    @staticmethod
    def _enforce_cadre_id(result: "ExtractionResult", cadre_id: str):
        """Override LLM-hallucinated cadre_id with the user-provided value."""
        if not cadre_id or not str(cadre_id).strip():
            return  # 上游未提供编号，保留 LLM 自身的识别结果
        cadre_id = str(cadre_id)
        # Entity types with cadre_id in properties + named like {prefix}_{cadre_id}_{NN}
        cadred_entities = {
            "Education": ("edu_id", "edu"),
            "PositionStatus": ("position_status_id", "ps"),
            "RewardPunish": ("reward_punish_id", "rp"),
            "AnnualAssessment": ("assessment_id", "assess"),
            "Resume": ("resume_id", "resume"),
            "Relation": ("relation_id", "rel"),
            "Profile": ("profile_id", "profile"),
            "Performance": ("performance_id", "perf"),
            "Shortcoming": ("shortcoming_id", "short"),
            "FamiliarField": ("field_id", "field"),
            "Tag": ("tag_id", "tag"),
            "Personality": ("personality_id", "personality"),
        }
        for ent in result.entities:
            etype = ent.get("type", "")
            props = ent.get("properties", {}) or {}
            # Always fix cadre_id in properties
            if props.get("cadre_id"):
                props["cadre_id"] = cadre_id
            if etype == "Cadre":
                if ent.get("name") != cadre_id:
                    ent["name"] = cadre_id
            elif etype in cadred_entities:
                id_field, prefix = cadred_entities[etype]
                old_id = props.get(id_field, "")
                m = re.match(rf"^{prefix}_(\d+)_(\d+)$", str(old_id))
                if m:
                    props[id_field] = f"{prefix}_{cadre_id}_{m.group(2)}"
                old_name = ent.get("name", "")
                m2 = re.match(rf"^{prefix}_(\d+)_(\d+)$", str(old_name))
                if m2:
                    ent["name"] = f"{prefix}_{cadre_id}_{m2.group(2)}"

        for rel in result.relations:
            if rel.get("source_type") == "Cadre" and rel.get("source_name") != cadre_id:
                rel["source_name"] = cadre_id
            if rel.get("target_type") == "Cadre" and rel.get("target_name") != cadre_id:
                rel["target_name"] = cadre_id

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

    def extract_basic_info(self, text: str, cadre_id: str) -> ExtractionResult:
        """Extract all basic info fields from cadre form using LLM."""
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": BASIC_INFO_PROMPT},
                {"role": "user", "content": build_basic_info_prompt(
                    text, cadre_id)},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        if "deepseek" in self.model.lower():
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(3):
            try:
                try:
                    resp = self.client.chat.completions.create(
                        **kwargs, response_format={"type": "json_object"}
                    )
                except Exception:
                    resp = self.client.chat.completions.create(**kwargs)
                raw = resp.choices[0].message.content or ""
                if raw.strip():
                    result = self._parse(raw)
                    self._enforce_cadre_id(result, cadre_id)

                    # 兜底：确保全日制和在职两个Education实体都存在
                    edu_entities = [e for e in result.entities if e.get("type") == "Education"]
                    has_fulltime = any((e.get("properties") or {}).get("edu_type") == "全日制" for e in edu_entities)
                    has_inservice = any((e.get("properties") or {}).get("edu_type") == "在职" for e in edu_entities)
                    if not has_inservice:
                        idx = len(edu_entities) + 1
                        fallback = {
                            "type": "Education",
                            "name": f"edu_{cadre_id}_{idx:02d}",
                            "properties": {"edu_id": f"edu_{cadre_id}_{idx:02d}",
                                "cadre_id": cadre_id, "edu_type": "在职",
                                "edu_level": "", "degree": "", "school": "", "major": ""}}
                        result.entities.append(fallback)
                        result.relations.append({
                            "source_type": "Cadre", "source_name": cadre_id,
                            "relation": "HAS_EDUCATION", "target_type": "Education",
                            "target_name": f"edu_{cadre_id}_{idx:02d}", "properties": {}})
                    if not has_fulltime:
                        idx = len(edu_entities) + 2
                        fallback = {
                            "type": "Education",
                            "name": f"edu_{cadre_id}_{idx:02d}",
                            "properties": {"edu_id": f"edu_{cadre_id}_{idx:02d}",
                                "cadre_id": cadre_id, "edu_type": "全日制",
                                "edu_level": "", "degree": "", "school": "", "major": ""}}
                        result.entities.append(fallback)
                        result.relations.append({
                            "source_type": "Cadre", "source_name": cadre_id,
                            "relation": "HAS_EDUCATION", "target_type": "Education",
                            "target_name": f"edu_{cadre_id}_{idx:02d}", "properties": {}})
                    print(f"  [basic_info] 教育经历: {len(edu_entities)} 条 LLM + 兜底补充")
                    return result
                import time as _t
                _t.sleep(2 + attempt * 2)
            except Exception as e:
                last_error = e
                print(f"  [retry {attempt+1}/3] basic_info LLM/parse failed: {e}")
                import time as _t
                _t.sleep(2 + attempt * 2)

        print(f"  [FAIL] basic_info after 3 attempts. last_error={last_error}")
        return ExtractionResult()

    def extract_annual_report(self, text: str, cadre_id: str,
                              writing_style_rules: list = None,
                              division_rules: list = None,
                              ability_style_rules: list = None,
                              performance_change_rules: list = None) -> ExtractionResult:
        """Extract 4 entity types from annual report using LLM."""
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": ANNUAL_REPORT_PROMPT},
                {"role": "user", "content": build_annual_report_prompt(
                    text, cadre_id,
                    writing_style_rules or [],
                    division_rules or [],
                    ability_style_rules or [],
                    performance_change_rules or [],
                )},
            ],
            temperature=0.1,
            max_tokens=8192,
        )
        if "deepseek" in self.model.lower():
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(3):
            try:
                try:
                    resp = self.client.chat.completions.create(
                        **kwargs, response_format={"type": "json_object"})
                except Exception:
                    resp = self.client.chat.completions.create(**kwargs)
                raw = resp.choices[0].message.content or ""
                if raw.strip():
                    result = self._parse(raw)
                    self._enforce_cadre_id(result, cadre_id)
                    return result
                import time as _t
                _t.sleep(2 + attempt * 2)
            except Exception as e:
                last_error = e
                print(f"  [retry {attempt+1}/3] annual_report LLM/parse failed: {e}")
                import time as _t
                _t.sleep(2 + attempt * 2)

        print(f"  [FAIL] annual_report after 3 attempts. last_error={last_error}")
        return ExtractionResult()

    def extract_resume(self, text: str, cadre_id: str, rules: list = None) -> ExtractionResult:
        """Extract Resume entities from 简历 text using LLM with dynamic rules."""
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": RESUME_PROMPT},
                {"role": "user", "content": build_resume_prompt_with_rules(
                    text, cadre_id, rules or ["从履历文本中提取所有任职记录"]
                )},
            ],
            temperature=0.1,
            max_tokens=8192,
        )
        if "deepseek" in self.model.lower():
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(3):
            try:
                try:
                    resp = self.client.chat.completions.create(
                        **kwargs, response_format={"type": "json_object"}
                    )
                except Exception:
                    resp = self.client.chat.completions.create(**kwargs)
                raw = resp.choices[0].message.content or ""
                if raw.strip():
                    result = self._parse(raw)
                    self._enforce_cadre_id(result, cadre_id)
                    return result
                import time as _t
                _t.sleep(2 + attempt * 2)
            except Exception as e:
                last_error = e
                print(f"  [retry {attempt+1}/3] resume LLM/parse failed: {e}")
                import time as _t
                _t.sleep(2 + attempt * 2)

        print(f"  [FAIL] resume after 3 attempts. last_error={last_error}")
        return ExtractionResult()

    def extract_org_evaluation(self, text: str, cadre_id: str,
                               inspection_time_rules: list = None,
                               core_traits_rules: list = None,
                               trait_evidence_rules: list = None,
                               performance_rules: list = None,
                               shortcoming_rules: list = None,
                               familiar_field_rules: list = None,
                               style_tag_rules: list = None) -> ExtractionResult:
        """Extract evaluation entities from cadre inspection report."""
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": ORG_EVALUATION_PROMPT},
                {"role": "user", "content": build_org_evaluation_prompt(
                    text, cadre_id,
                    inspection_time_rules or [],
                    core_traits_rules or [],
                    trait_evidence_rules or [],
                    performance_rules or [],
                    shortcoming_rules or [],
                    familiar_field_rules or [],
                    style_tag_rules or [],
                )},
            ],
            temperature=0.1,
            max_tokens=8192,
        )
        if "deepseek" in self.model.lower():
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(3):
            try:
                try:
                    resp = self.client.chat.completions.create(
                        **kwargs, response_format={"type": "json_object"})
                except Exception:
                    resp = self.client.chat.completions.create(**kwargs)
                raw = resp.choices[0].message.content or ""
                if raw.strip():
                    result = self._parse(raw)
                    self._enforce_cadre_id(result, cadre_id)
                    return result
                import time as _t
                _t.sleep(2 + attempt * 2)
            except Exception as e:
                last_error = e
                print(f"  [retry {attempt+1}/3] org_evaluation LLM/parse failed: {e}")
                import time as _t
                _t.sleep(2 + attempt * 2)

        print(f"  [FAIL] org_evaluation after 3 attempts. last_error={last_error}")
        return ExtractionResult()

    def extract_research(self, text: str, cadre_id: str,
                         personality_rules: list = None,
                         ability_rules: list = None) -> ExtractionResult:
        """Extract personality and ability from research talk summary."""
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": RESEARCH_PROMPT},
                {"role": "user", "content": build_research_prompt(
                    text, cadre_id,
                    personality_rules or [],
                    ability_rules or [],
                )},
            ],
            temperature=0.1,
            max_tokens=8192,
        )
        if "deepseek" in self.model.lower():
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(3):
            try:
                try:
                    resp = self.client.chat.completions.create(
                        **kwargs, response_format={"type": "json_object"})
                except Exception:
                    resp = self.client.chat.completions.create(**kwargs)
                raw = resp.choices[0].message.content or ""
                if raw.strip():
                    result = self._parse(raw)
                    self._enforce_cadre_id(result, cadre_id)
                    return result
                import time as _t
                _t.sleep(2 + attempt * 2)
            except Exception as e:
                last_error = e
                print(f"  [retry {attempt+1}/3] research LLM/parse failed: {e}")
                import time as _t
                _t.sleep(2 + attempt * 2)

        print(f"  [FAIL] research after 3 attempts. last_error={last_error}")
        return ExtractionResult()

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

import json
import re
from typing import Dict, List, Optional, Tuple

from openai import OpenAI

from config import TAG_TAXONOMY, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from .prompts import SYSTEM_PROMPT_TAG, build_tag_taxonomy_str


class TagExtractor:
    """Two-stage tag extraction: keyword rules → LLM refinement."""

    def __init__(self):
        self.client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        self.model = LLM_MODEL
        self.taxonomy_str = build_tag_taxonomy_str()

    def extract(self, text: str, doc_type: str = "",
                cadre_id: Optional[str] = None) -> List[Dict]:
        # Stage 1: keyword rule scan
        rule_tags = self._rule_scan(text, doc_type, cadre_id)
        # Stage 2: LLM refinement
        llm_tags = self._llm_refine(text, doc_type, cadre_id, rule_tags)
        # Merge: prefer LLM, fallback to rule
        return llm_tags or rule_tags

    def _rule_scan(self, text: str, doc_type: str,
                   cadre_id: Optional[str] = None) -> List[Dict]:
        """Keyword-based candidate tag scan."""
        tags = []
        target = cadre_id or "unknown"
        text_lower = text

        for category, info in TAG_TAXONOMY.items():
            # source check
            allowed = info["sources"]
            if doc_type not in allowed and "*" not in str(allowed):
                continue
            # keyword match
            matched = []
            for kw in info["keywords"]:
                if kw in text_lower:
                    matched.append(kw)
            if not matched:
                continue
            # pick best fixed tag for matched keywords
            for fixed_tag in info["fixed_tags"]:
                for kw in matched:
                    if any(c in fixed_tag for c in kw):
                        tags.append({
                            "type": category,
                            "name": fixed_tag,
                            "target": target,
                            "source": "rule",
                        })
                        break
        # dedup
        seen = set()
        deduped = []
        for t in tags:
            key = (t["type"], t["name"], t["target"])
            if key not in seen:
                seen.add(key)
                deduped.append(t)
        return deduped[:10]

    def _llm_refine(self, text: str, doc_type: str,
                    cadre_id: Optional[str] = None,
                    rule_candidates: Optional[List[Dict]] = None) -> List[Dict]:
        """Use LLM to select final tags from taxonomy."""
        target = cadre_id or "unknown"
        rule_hint = ""
        if rule_candidates:
            names = list(set(t["name"] for t in rule_candidates))
            rule_hint = f"规则初筛候选标签：{', '.join(names)}\n"

        user_msg = f"""文档类型：{doc_type}
所属干部：{target}
{rule_hint}
文本：
{text[:1500]}  # truncate to avoid token limit

请从控词表中选择最匹配的标签，输出JSON格式。"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_TAG.format(
                        tag_taxonomy=self.taxonomy_str)},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
            )
            raw = resp.choices[0].message.content
            return self._parse_tags(raw, target)
        except Exception as e:
            print(f"    LLM标签精调失败: {e}")
            return rule_candidates or []

    @staticmethod
    def _parse_tags(raw: str, default_target: str) -> List[Dict]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        try:
            data = json.loads(raw)
            tags = data.get("tags", [])
            for t in tags:
                if "target" not in t or not t["target"]:
                    t["target"] = default_target
            return tags[:10]
        except json.JSONDecodeError:
            return []

import re
from pathlib import Path
from typing import Dict, List

import yaml


class RuleEngine:
    def __init__(self):
        self.rules_dir = Path(__file__).parent

    def load_rules(self, category_code: str) -> dict:
        path = self.rules_dir / f"{category_code}.yaml"
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def extract_llm_sections(self, text: str, category_code: str) -> List[Dict]:
        """Find LLM-targeted sections in text, return [{name, text, entity_type, relation, rules}]."""
        rules = self.load_rules(category_code)
        sections = []
        for sec in rules.get("llm_sections", []):
            trigger = sec["trigger"]
            m = re.search(r"(" + trigger + r")", text)
            if not m:
                continue
            start = m.start()
            tail = text[start:]
            sections.append({
                "name": sec["name"],
                "text": tail.strip(),
                "entity_type": sec["entity_type"],
                "relation": sec["relation"],
                "rules": sec.get("rules", []),
            })
        return sections

import re
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config import TAG_SYNONYM
from embedding.embedder import Embedder


class EntityAligner:
    """Align & deduplicate entities across chunks by embedding + rules."""

    def __init__(self, threshold: float = 0.92):
        self.embedder = Embedder()
        self.threshold = threshold
        # alias rules: short name → canonical name
        self.alias_rules = {}

    def build_alias_rules(self, all_entities: List[Dict]):
        for ent in all_entities:
            name = ent.get("name", "")
            if not name:
                continue
            if ent.get("type") == "Cadre":
                short = re.sub(r"[同志]", "", name).strip()
                if short and short != name:
                    self.alias_rules[short] = name
                # "001" patterns
                m = re.match(r"(\d{3})", name)
                if m:
                    self.alias_rules[m.group(1)] = name
            if ent.get("type") == "Department":
                short = re.sub(r"[（(].*?[）)]", "", name).strip()
                if short and short != name:
                    self.alias_rules[short] = name

    def normalize_name(self, name: str) -> str:
        return self.alias_rules.get(name, name)

    def align_entities(self, entities: List[Dict]) -> List[Dict]:
        self.build_alias_rules(entities)
        # dedup by normalized name
        seen: Dict[str, Dict] = {}
        for ent in entities:
            name = self.normalize_name(ent.get("name", ""))
            etype = ent.get("type", "")
            key = f"{etype}::{name}"
            if key in seen:
                self._merge_props(seen[key], ent)
            else:
                normalized = dict(ent)
                normalized["name"] = name
                seen[key] = normalized
        result = list(seen.values())
        # embedding-based fuzzy merge for similar entities
        result = self._fuzzy_merge(result)
        return result

    def _merge_props(self, target: Dict, source: Dict):
        tp = target.get("properties", {})
        sp = source.get("properties", {})
        for k, v in sp.items():
            if k not in tp or not tp[k]:
                tp[k] = v
        target["properties"] = tp
        # merge source file list
        sources = target.setdefault("_sources", [])
        sf = source.get("_sources", [str(source.get("source_file", ""))])
        for s in sf:
            if s and s not in sources:
                sources.append(s)

    def _fuzzy_merge(self, entities: List[Dict]) -> List[Dict]:
        names = []
        indices = []
        for i, ent in enumerate(entities):
            n = ent.get("name", "")
            if n:
                names.append(n)
                indices.append(i)
        if len(names) < 2:
            return entities
        embs = self.embedder.embed(names)
        sim = cosine_similarity(embs)
        merged_out = set()
        result = []
        for i in range(len(names)):
            if indices[i] in merged_out:
                continue
            cluster = [indices[i]]
            for j in range(i + 1, len(names)):
                if indices[j] not in merged_out and sim[i][j] >= self.threshold:
                    cluster.append(indices[j])
            # keep first, discard rest
            keep = entities[cluster[0]]
            for ci in cluster[1:]:
                self._merge_props(keep, entities[ci])
                merged_out.add(ci)
            result.append(keep)
            merged_out.add(cluster[0])
        return result

    def normalize_tags(self, tags: List[Dict]) -> List[Dict]:
        """Normalize tag names via TAG_SYNONYM map, dedup."""
        result = []
        seen = set()
        for t in tags:
            name = t.get("name", "")
            target = t.get("target", "")
            category = t.get("type", "")
            # synonym resolution
            for canonical, variants in TAG_SYNONYM.items():
                if name in variants:
                    name = canonical
                    break
            key = (category, name, target)
            if key not in seen:
                seen.add(key)
                t["name"] = name
                result.append(t)
        return result

    def align_relations(self, relations: List[Dict]) -> List[Dict]:
        for rel in relations:
            rel["source_name"] = self.normalize_name(rel.get("source_name", ""))
            rel["target_name"] = self.normalize_name(rel.get("target_name", ""))
        seen = set()
        deduped = []
        for rel in relations:
            key = (rel.get("source_type", ""), rel.get("source_name", ""),
                   rel.get("relation", ""), rel.get("target_type", ""),
                   rel.get("target_name", ""))
            if key not in seen:
                seen.add(key)
                deduped.append(rel)
        return deduped

import re
from typing import Dict, List, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config import TAG_SYNONYM
from embedding.embedder import Embedder


class EntityAligner:
    """Align & deduplicate entities across chunks by embedding + rules."""

    # 带显式唯一ID前缀的实体，跳过模糊合并（ID本身就保证唯一）
    _SKIP_FUZZY_PREFIXES = (
        "edu_", "ps_", "rp_", "assess_", "resume_",
        "per_", "ab_", "ff_", "tag_", "perf_", "sc_",
        "evo_", "wr_", "dv_", "pr_", "ev_", "ind_",
        "rel_", "perf_", "apt_",
    )

    def __init__(self, threshold: float = 0.92):
        self.embedder = Embedder()
        self.threshold = threshold
        self.alias_rules = {}

    def build_alias_rules(self, all_entities: List[Dict]):
        for ent in all_entities:
            name = ent.get("name", "")
            if not name:
                continue
            if ent.get("type") == "Cadre":
                # cadre_id patterns
                m = re.match(r"(\d{3,4})", name)
                if m:
                    self.alias_rules[m.group(1)] = name

    def normalize_name(self, name: str) -> str:
        return self.alias_rules.get(name, name)

    def align_entities(self, entities: List[Dict]) -> List[Dict]:
        self.build_alias_rules(entities)
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
        result = self._fuzzy_merge(result)
        return result

    def _merge_props(self, target: Dict, source: Dict):
        tp = target.get("properties", {})
        sp = source.get("properties", {})
        for k, v in sp.items():
            if k not in tp or not tp[k]:
                tp[k] = v
        target["properties"] = tp
        sources = target.setdefault("_sources", [])
        sf = source.get("_sources", [str(source.get("source_file", ""))])
        for s in sf:
            if s and s not in sources:
                sources.append(s)

    def _fuzzy_merge(self, entities: List[Dict]) -> List[Dict]:
        names = []
        indices = []
        skipped_indices = set()
        for i, ent in enumerate(entities):
            n = ent.get("name", "")
            if not n:
                continue
            if n.startswith(self._SKIP_FUZZY_PREFIXES):
                skipped_indices.add(i)
                continue
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
            keep = entities[cluster[0]]
            for ci in cluster[1:]:
                self._merge_props(keep, entities[ci])
                merged_out.add(ci)
            result.append(keep)
            merged_out.add(cluster[0])
        # 把跳过模糊合并的实体加回结果
        for i in skipped_indices:
            if i not in merged_out:
                result.append(entities[i])
        return result

    def normalize_tags(self, tags: List[Dict]) -> List[Dict]:
        """Normalize tag names via TAG_SYNONYM map, dedup."""
        result = []
        seen = set()
        for t in tags:
            name = t.get("name", "")
            target = t.get("target", "")
            category = t.get("type", "")
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

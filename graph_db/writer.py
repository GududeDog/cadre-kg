import json
from collections import defaultdict
from typing import Any, Dict, List

from neo4j import GraphDatabase

from config import NEO4J_URI, NEO4J_AUTH


# ─── MERGE key mapping by entity type ───
MERGE_KEY_MAP = {
    "Cadre": lambda props, ent: props.get("cadre_id") or ent.get("name", ""),
    "Position": lambda props, ent: props.get("position_id") or ent.get("name", ""),
    "Resume": lambda props, ent: props.get("resume_id") or ent.get("name", ""),
    "Education": lambda props, ent: props.get("edu_id") or ent.get("name", ""),
    "Relation": lambda props, ent: props.get("relation_id") or ent.get("name", ""),
    "RewardPunish": lambda props, ent: props.get("reward_punish_id") or ent.get("name", ""),
    "Performance": lambda props, ent: props.get("performance_id") or ent.get("name", ""),
    "Evaluation": lambda props, ent: props.get("evaluation_id") or ent.get("name", ""),
    "Shortcoming": lambda props, ent: props.get("shortcoming_id") or ent.get("name", ""),
    "Personality": lambda props, ent: props.get("personality_id") or ent.get("name", ""),
    "Ability": lambda props, ent: props.get("ability_id") or ent.get("name", ""),
    "FamiliarField": lambda props, ent: props.get("field_id") or ent.get("name", ""),
    "Tag": lambda props, ent: props.get("tag_id") or ent.get("name", ""),
    "WritingStyle": lambda props, ent: props.get("writing_id") or ent.get("name", ""),
    "AnnualAssessment": lambda props, ent: props.get("assessment_id") or ent.get("name", ""),
    "Profile": lambda props, ent: props.get("profile_id") or ent.get("name", ""),
    "PositionStatus": lambda props, ent: props.get("position_status_id") or ent.get("name", ""),
    "Division": lambda props, ent: props.get("division_id") or ent.get("name", ""),
    "AbilityEvolution": lambda props, ent: props.get("evolution_id") or ent.get("name", ""),
    "ExcellenceIndicator": lambda props, ent: props.get("indicator_id") or ent.get("name", ""),
}


class GraphWriter:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    def close(self):
        self.driver.close()

    # ───────────────────── Schema Init ─────────────────────

    def init_schema(self):
        """Create all vertex labels and edge labels in TuGraph.
        Uses ``db.createVertexLabelByJson`` / ``db.createEdgeLabelByJson``
        so all fields are defined in ONE call each.
        """
        from graph_db.models import NODE_SCHEMA, REL_SCHEMA

        with self.driver.session(database="default") as s:
            # ── Vertex labels ──
            for label, schema in NODE_SCHEMA.items():
                props = schema["properties"]
                primary = props[0]
                specs = []
                for p in props:
                    specs.append({
                        "name": p,
                        "type": "STRING",
                        "optional": (p != primary),
                    })
                meta = json.dumps({
                    "label": label,
                    "type": "VERTEX",
                    "primary": primary,
                    "properties": specs,
                }, ensure_ascii=False)
                cypher = f"CALL db.createVertexLabelByJson('{meta}')"
                try:
                    s.run(cypher)
                    print(f"  [schema] vertex: {label} ({len(props)} fields)")
                except Exception as e:
                    msg = str(e)
                    if any(w in msg.lower() for w in ("already exist", "duplicate")):
                        pass
                    else:
                        print(f"  [WARN] vertex {label}: {e}")

            # ── Edge labels ──
            for rel_name, rel_info in REL_SCHEMA.items():
                src = rel_info["source"]
                tgt = rel_info["target"]
                constraints = [[src, tgt]]
                edge_props = rel_info.get("properties", [])
                specs = [
                    {"name": p, "type": "STRING", "optional": True}
                    for p in edge_props
                ]
                meta = json.dumps({
                    "label": rel_name,
                    "type": "EDGE",
                    "constraints": constraints,
                    "properties": specs,
                }, ensure_ascii=False)
                cypher = f"CALL db.createEdgeLabelByJson('{meta}')"
                try:
                    s.run(cypher)
                    print(f"  [schema] edge: {rel_name} ({src}->{tgt})")
                except Exception as e:
                    msg = str(e)
                    if any(w in msg.lower() for w in ("already exist", "duplicate")):
                        pass
                    else:
                        print(f"  [WARN] edge {rel_name}: {e}")

    # ───────────────────── Entity Write (upsertVertex) ─────────────────────

    def write_entities(self, entities: List[Dict]):
        if not entities:
            return
        with self.driver.session(database="default") as s:
            grouped = defaultdict(list)
            for ent in entities:
                grouped[ent.get("type", "Entity")].append(ent)
            for etype, group in grouped.items():
                self._upsert_vertices(s, etype, group)

    def _upsert_vertices(self, session, etype: str, group: List[Dict]):
        rows = []
        for ent in group:
            props = ent.get("properties", {}) or {}
            # Ensure primary-key field is populated from the merge key
            key_fn = MERGE_KEY_MAP.get(etype)
            if key_fn:
                merge_val = key_fn(props, ent)
                pk = merge_val  # primary field value
            else:
                pk = ent.get("name") or props.get("name", "")
            if not pk:
                continue
            props["name"] = pk

            row = {}
            for k, v in props.items():
                if v is None or v == "":
                    continue
                row[k] = v
            if not row:
                continue
            rows.append(row)

        if not rows:
            return

        formatted = _format_upsert_rows(rows)
        cypher = f"CALL db.upsertVertex('{etype}', [{formatted}])"
        try:
            session.run(cypher)
        except Exception as e:
            print(f"[WARN] upsertVertex {etype}: {e}")

    # ───────────────────── Relation Write (upsertEdge) ─────────────────────

    def write_relations(self, relations: List[Dict]):
        if not relations:
            return
        with self.driver.session(database="default") as s:
            grouped = defaultdict(list)
            for rel in relations:
                grouped[rel.get("relation", "")].append(rel)
            for rtype, group in grouped.items():
                if not rtype:
                    continue
                self._upsert_edges(s, rtype, group)

    def _upsert_edges(self, session, rtype: str, group: List[Dict]):
        src_type = ""
        tgt_type = ""
        rows = []
        for rel in group:
            st = rel.get("source_type", "")
            tt = rel.get("target_type", "")
            sk = rel.get("source_name", "")
            tk = rel.get("target_name", "")
            if not st or not tt or not sk or not tk:
                continue
            src_type = st or src_type
            tgt_type = tt or tgt_type
            row = {"sid": sk, "tid": tk}
            # Edge properties
            props = rel.get("properties", {}) or {}
            for k, v in props.items():
                if v is not None and v != "":
                    row[k] = v
            rows.append(row)

        if not rows:
            return

        formatted = _format_upsert_rows(rows)
        cypher = (
            f'CALL db.upsertEdge("{rtype}", '
            f'{{type:"{src_type}", key:"sid"}}, '
            f'{{type:"{tgt_type}", key:"tid"}}, '
            f'[{formatted}])'
        )
        try:
            session.run(cypher)
        except Exception as e:
            print(f"[WARN] upsertEdge {rtype}: {e}")

    # ───────────────────── Tags ─────────────────────

    def write_tags(self, tags: List[Dict]):
        entities = []
        relations = []
        for tag in tags:
            tcategory = tag.get("type", "专业技能")
            tname = tag.get("name", "")
            target = tag.get("target", "")
            if not tname or not target:
                continue
            tag_id = f"tag_{target}_{tname}"
            entities.append({
                "type": "Tag",
                "name": tag_id,
                "properties": {
                    "tag_id": tag_id,
                    "cadre_id": target,
                    "style_tag": tname if tcategory == "风格标签" else None,
                    "issue_tag": tname if tcategory == "负面" else None,
                },
            })
            relations.append({
                "source_type": "Cadre",
                "source_name": target,
                "relation": "HAS_TAG",
                "target_type": "Tag",
                "target_name": tag_id,
                "properties": {},
            })
        self.write_entities(entities)
        self.write_relations(relations)


# ───────────────────── Helpers ─────────────────────

def _fmt_val(v):
    """Format a value for inline Cypher literal.  TuGraph accepts
    string values quoted, numbers/bools unquoted."""
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    escaped = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _format_upsert_rows(rows: List[Dict]) -> str:
    parts = []
    for row in rows:
        kvs = [f"{k}: {_fmt_val(v)}" for k, v in row.items()]
        parts.append("{" + ", ".join(kvs) + "}")
    return ", ".join(parts)

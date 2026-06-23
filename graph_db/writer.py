import json
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from config import NEO4J_URI, NEO4J_AUTH
from embedding.embedder import Embedder


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
        self.embedder = Embedder()

    def close(self):
        self.driver.close()

    def init_schema(self):
        with self.driver.session() as session:
            for stmt in [
                "CREATE CONSTRAINT cadre_cadre_id IF NOT EXISTS FOR (n:Cadre) REQUIRE n.cadre_id IS UNIQUE",
                "CREATE INDEX idx_cadre_name IF NOT EXISTS FOR (n:Cadre) ON (n.name)",
            ]:
                try:
                    session.run(stmt)
                except Exception as e:
                    if "already exists" in str(e) or "EquivalentSchemaRuleAlreadyExists" in str(e):
                        pass  # Neo4j 4.x doesn't support IF NOT EXISTS
                    else:
                        print(f"[WARN] init_schema: {e}")

    def write_entities(self, entities: List[Dict]):
        with self.driver.session() as session:
            for ent in entities:
                self._write_entity(session, ent)

    def _write_entity(self, session, ent: Dict):
        etype = ent.get("type", "Entity")
        props = ent.get("properties", {}) or {}

        # Pick MERGE key by entity type
        key_fn = MERGE_KEY_MAP.get(etype)
        if key_fn:
            merge_val = key_fn(props, ent)
        else:
            merge_val = ent.get("name") or props.get("name", "")

        if not merge_val:
            return
        props["name"] = merge_val

        # Optional: generate embedding for Cadre
        if etype == "Cadre":
            embed_text = f"{merge_val} {' '.join(str(v) for v in props.values() if v)}"
            try:
                embedding = self.embedder.embed_one(embed_text)
            except Exception as e:
                print(f"[WARN] embed {etype}:{merge_val} -> {e}")
                embedding = None
        else:
            embedding = None

        set_parts = []
        params = {"merge_val": merge_val, "name": merge_val}
        for k, v in props.items():
            if v is None or v == "":
                continue
            if isinstance(v, (list, tuple)):
                v = json.dumps(v, ensure_ascii=False)
            elif isinstance(v, bool):
                v = str(v).lower()
            param_key = f"p_{k}"
            params[param_key] = v
            set_parts.append(f"n.{k} = ${param_key}")
        if embedding is not None:
            params["embedding"] = embedding
            set_parts.append("n.embedding = $embedding")

        if not set_parts:
            return
        set_str = ", ".join(set_parts)
        cypher = f"""
        MERGE (n:{etype} {{name: $merge_val}})
        ON CREATE SET {set_str}
        ON MATCH SET {set_str}
        """
        try:
            session.run(cypher, **params)
        except Exception as e:
            print(f"[WARN] write {etype}:{merge_val} -> {e}")

    def write_relations(self, relations: List[Dict]):
        with self.driver.session() as session:
            for rel in relations:
                self._write_relation(session, rel)

    def _write_relation(self, session, rel: Dict):
        rtype = rel.get("relation", "")
        src_type = rel.get("source_type", "Entity")
        src_key = rel.get("source_name", "")
        tgt_type = rel.get("target_type", "Entity")
        tgt_key = rel.get("target_name", "")
        props = rel.get("properties", {}) or {}
        if not all([rtype, src_key, tgt_key]):
            return

        # Build SET for relation properties
        set_parts = []
        params = {"src_key": src_key, "tgt_key": tgt_key}
        for k, v in props.items():
            if v is None or v == "":
                continue
            if isinstance(v, (list, tuple)):
                v = json.dumps(v, ensure_ascii=False)
            elif isinstance(v, bool):
                v = str(v).lower()
            param_key = f"p_{k}"
            params[param_key] = v
            set_parts.append(f"r.{k} = ${param_key}")

        if set_parts:
            set_str = "SET " + ", ".join(set_parts)
            cypher = f"""
            MATCH (s:{src_type} {{name: $src_key}})
            MATCH (t:{tgt_type} {{name: $tgt_key}})
            MERGE (s)-[r:{rtype}]->(t)
            {set_str}
            """
        else:
            cypher = f"""
            MATCH (s:{src_type} {{name: $src_key}})
            MATCH (t:{tgt_type} {{name: $tgt_key}})
            MERGE (s)-[r:{rtype}]->(t)
            """
        try:
            session.run(cypher, **params)
        except Exception as e:
            print(f"[WARN] write rel {rtype} {src_key}->{tgt_key}: {e}")

    def write_tags(self, tags: List[Dict]):
        """Write tag as Tag node + HAS_TAG relation."""
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

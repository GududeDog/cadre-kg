import json
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from config import NEO4J_URI, NEO4J_AUTH
from embedding.embedder import Embedder


class GraphWriter:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        self.embedder = Embedder()

    def close(self):
        self.driver.close()

    def init_schema(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT cadre_cadre_id IF NOT EXISTS FOR (n:Cadre) REQUIRE n.cadre_id IS UNIQUE")
            session.run("CREATE CONSTRAINT org_org_id IF NOT EXISTS FOR (n:Organization) REQUIRE n.org_id IS UNIQUE")
            session.run("CREATE INDEX idx_cadre_name IF NOT EXISTS FOR (n:Cadre) ON (n.name)")
            session.run("CREATE INDEX idx_org_name IF NOT EXISTS FOR (n:Organization) ON (n.org_name)")
            session.run("CREATE INDEX idx_pos_name IF NOT EXISTS FOR (n:Position) ON (n.position_name)")

    def write_entities(self, entities: List[Dict]):
        with self.driver.session() as session:
            for ent in entities:
                self._write_entity(session, ent)

    def _write_entity(self, session, ent: Dict):
        etype = ent.get("type", "Entity")
        props = ent.get("properties", {})
        # Use name or cadre_id as merge key
        merge_key = "name"
        merge_val = props.get("name") or props.get("cadre_id") or props.get("org_name") or ent.get("name", "")
        if not merge_val:
            return
        props["name"] = merge_val

        # Optional: generate embedding for Cadre / Document
        if etype in ("Cadre", "Document", "DocumentChunk"):
            embed_text = f"{merge_val} {' '.join(str(v) for v in props.values() if v)}"
            embedding = self.embedder.embed_one(embed_text)
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
            print(f"[WARN] write {etype}:{merge_val} → {e}")

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
            print(f"[WARN] write rel {rtype} {src_key}→{tgt_key}: {e}")

    def write_tags(self, tags: List[Dict]):
        """Write tag as AbilityTag node + HAS_ABILITY relation."""
        entities = []
        relations = []
        for tag in tags:
            tcategory = tag.get("type", "专业技能")
            tname = tag.get("name", "")
            target = tag.get("target", "")
            if not tname or not target:
                continue
            entities.append({
                "type": "AbilityTag",
                "name": tname,
                "properties": {"tag_name": tname, "tag_category": tcategory, "tag_weight": 0.5},
            })
            relations.append({
                "source_type": "Cadre",
                "source_name": target,
                "relation": "HAS_ABILITY",
                "target_type": "AbilityTag",
                "target_name": tname,
                "properties": {"proficiency": "了解", "source": "AI推断", "confidence": 0.7},
            })
        self.write_entities(entities)
        self.write_relations(relations)

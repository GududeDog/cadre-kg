"""
FastAPI 后端 — 干部画像数据接口（从 Neo4j 读真实数据）
用法: cd front && python server.py
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from neo4j import GraphDatabase

NEO4J_URI = "neo4j://localhost"
NEO4J_AUTH = ("neo4j", "12345678")

app = FastAPI(title="干部画像系统 API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

FRONT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)


def fetch_one(driver, query, **params):
    with driver.session() as s:
        rec = s.run(query, **params).single()
        return dict(rec) if rec else None


def fetch_all(driver, query, **params):
    with driver.session() as s:
        return [dict(r) for r in s.run(query, **params)]


@app.get("/api/cadre/{cadre_id}")
def get_cadre(cadre_id: str):
    driver = get_driver()
    try:
        # 1. 基本信息
        info = fetch_one(driver,
            "MATCH (c:Cadre {cadre_id: $id}) RETURN c", id=cadre_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"干部 {cadre_id} 不存在")

        cadre = info["c"]

        # 2. 学历
        cadres_edu = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:STUDIED_AT]->(e:Education)
            RETURN e.school_name AS school, e.major AS major,
                   e.education_level AS level, e.degree AS degree,
                   e.is_full_time AS is_full_time,
                   e.start_date AS start_date, e.end_date AS end_date
        """, id=cadre_id)

        # 3. 家庭
        cadres_family = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_RELATION]->(p:Person)
            RETURN p.person_name AS name, p.relation_to_cadre AS relation,
                   p.work_unit AS work_unit, p.political_status AS political_status,
                   p.position AS position
        """, id=cadre_id)

        # 4. 任职 (Appointment)
        appointments = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_APPOINTMENT]->(a:Appointment)
            RETURN a.name AS name, a.start_date AS start_date,
                   a.end_date AS end_date, a.is_current AS is_current,
                   a.appointment_type AS type
            ORDER BY a.start_date
        """, id=cadre_id)

        # 5. Position
        positions = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HOLDS]->(p:Position)
            RETURN p.position_name AS name, p.position_level AS level,
                   p.is_leading_position AS is_leading
        """, id=cadre_id)

        # 6. 考核
        assessments = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_ASSESSMENT]->(a:Assessment)
            RETURN a.name AS name, a.assessment_type AS type,
                   a.assessment_year AS year, a.result AS result
        """, id=cadre_id)

        # 7. 能力标签
        ability_tags = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[r:HAS_ABILITY]->(t:AbilityTag)
            RETURN t.tag_name AS tag, t.tag_category AS category,
                   r.confidence AS confidence, r.source AS source
        """, id=cadre_id)

        return {
            "cadre": cadre,
            "education": cadres_edu,
            "family": cadres_family,
            "appointments": appointments,
            "positions": positions,
            "assessments": assessments,
            "ability_tags": ability_tags,
        }
    finally:
        driver.close()


@app.get("/api/graph/stats")
def graph_stats():
    driver = get_driver()
    try:
        nodes = {r["label"]: r["cnt"] for r in fetch_all(driver,
            "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC")}
        return {"nodes": nodes}
    finally:
        driver.close()


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONT_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("启动干部画像系统 API: http://localhost:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

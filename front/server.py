"""
FastAPI 后端 — 干部画像数据接口（从 Neo4j 读真实数据）
用法: cd front && python server.py
"""
import io
import sys
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from neo4j import GraphDatabase

NEO4J_URI = "bolt://192.168.3.171:5687"
NEO4J_AUTH = ("admin", "qwe_321@UV")

app = FastAPI(title="干部画像系统 API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

FRONT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(FRONT_DIR)
sys.path.insert(0, BACKEND_DIR)

from category_router import CATEGORY_LIST, get_category  # noqa: E402
from pipeline import Pipeline  # noqa: E402

def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)


def fetch_one(driver, query, **params):
    with driver.session(database="default") as s:
        rec = s.run(query, **params).single()
        return dict(rec) if rec else None


def fetch_all(driver, query, **params):
    with driver.session(database="default") as s:
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

        # 2. 教育经历
        educations = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_EDUCATION]->(e:Education)
            RETURN e.edu_id AS edu_id, e.edu_level AS edu_level,
                   e.degree AS degree, e.school AS school, e.major AS major
        """, id=cadre_id)

        # 3. 关系人
        relatives = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_RELATIVE]->(r:Relation)
            RETURN r.relation_id AS relation_id, r.relation_type AS relation_type,
                   r.name AS name, r.age AS age,
                   r.political_status AS political_status,
                   r.work_unit_position AS work_unit_position
        """, id=cadre_id)

        # 4. 简历 / 任职记录
        resumes = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_RESUME]->(r:Resume)
            RETURN r.resume_id AS resume_id, r.period AS period,
                   r.unit AS unit, r.department AS department,
                   r.position AS position, r.region AS region,
                   r.dept AS dept, r.rank AS rank
        """, id=cadre_id)

        # 5. 职务情况
        position_statuses = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_POSITION_STATUS]->(ps:PositionStatus)
            RETURN ps.position_status_id AS position_status_id,
                   ps.current_position AS current_position,
                   ps.proposed_position AS proposed_position,
                   ps.proposed_removal AS proposed_removal
        """, id=cadre_id)

        # 6. 年度考核
        annual_assessments = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_ANNUAL_ASSESSMENT]->(a:AnnualAssessment)
            RETURN a.assessment_id AS assessment_id, a.result AS result,
                   a.commendation AS commendation
        """, id=cadre_id)

        # 7. 能力特征
        abilities = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_ABILITY]->(a:Ability)
            RETURN a.ability_id AS ability_id, a.time AS time,
                   a.ability_trait AS ability_trait, a.source_doc AS source_doc
        """, id=cadre_id)

        # 8. 标签
        tags = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_TAG]->(t:Tag)
            RETURN t.tag_id AS tag_id, t.style_tag AS style_tag,
                   t.special_tag AS special_tag, t.issue_tag AS issue_tag,
                   t.assessment_year AS assessment_year,
                   t.source_doc AS source_doc
        """, id=cadre_id)

        # 9. 性格特征
        personalities = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_PERSONALITY]->(p:Personality)
            RETURN p.personality_id AS personality_id, p.time AS time,
                   p.trait AS trait, p.source_doc AS source_doc,
                   p.shortcoming AS shortcoming,
                   p.positive_eval AS positive_eval,
                   p.negative_eval AS negative_eval,
                   p.issue_tag_1 AS issue_tag_1, p.issue_tag_2 AS issue_tag_2,
                   p.time_2 AS time_2, p.source_doc_2 AS source_doc_2
        """, id=cadre_id)

        # 10. 主要不足
        shortcomings = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_SHORTCOMING]->(s:Shortcoming)
            RETURN s.shortcoming_id AS shortcoming_id,
                   s.assessment_year AS assessment_year,
                   s.content AS content, s.source_doc AS source_doc
        """, id=cadre_id)

        # 11. 熟悉领域
        familiar_fields = fetch_all(driver, """
            MATCH (c:Cadre {cadre_id: $id})-[:HAS_FAMILIAR_FIELD]->(f:FamiliarField)
            RETURN f.field_id AS field_id, f.assessment_year AS assessment_year,
                   f.field_name AS field_name, f.source_doc AS source_doc
        """, id=cadre_id)

        return {
            "cadre": cadre,
            "educations": educations,
            "relatives": relatives,
            "resumes": resumes,
            "position_statuses": position_statuses,
            "annual_assessments": annual_assessments,
            "abilities": abilities,
            "tags": tags,
            "personalities": personalities,
            "shortcomings": shortcomings,
            "familiar_fields": familiar_fields,
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


@app.get("/api/debug/cadres")
def debug_cadres():
    """诊断用：列出所有 Cadre 节点 + 关键字段。"""
    driver = get_driver()
    try:
        rows = fetch_all(driver, """
            MATCH (c:Cadre)
            OPTIONAL MATCH (c)-[:HAS_POSITION_STATUS]->(ps:PositionStatus)
            OPTIONAL MATCH (c)-[:HAS_RESUME]->(r:Resume)
            RETURN c.cadre_id AS cadre_id, c.name AS name,
                   c.gender AS gender, c.birth_date AS birth_date,
                   count(DISTINCT ps) AS position_status_count,
                   count(DISTINCT r) AS resume_count
            ORDER BY c.cadre_id
        """)
        return {"count": len(rows), "cadres": rows}
    finally:
        driver.close()


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONT_DIR, "index.html"))


# ─── 上传 & 类目路由 ───

@app.get("/upload.html")
def serve_upload():
    return FileResponse(os.path.join(FRONT_DIR, "upload.html"))


@app.get("/api/categories")
def list_categories():
    return {"categories": CATEGORY_LIST}


@app.post("/api/upload")
async def api_upload(
    files: list[UploadFile] = File(...),
    category_code: str = Form(...),
    cadre_id_hint: str = Form(""),
):
    if get_category(category_code) is None:
        raise HTTPException(status_code=400, detail=f"未知类目: {category_code}")

    # Pipeline 提到循环外，复用 Extractor/Aligner/Writer（避免每个文件重新加载）
    pipeline = Pipeline()
    results = []
    tmpdir = Path(tempfile.mkdtemp(prefix="upload_"))

    try:
        # 首次写库前初始化 schema
        if pipeline.writer is not None:
            try:
                pipeline.writer.init_schema()
            except Exception as e:
                print(f"[WARN] init_schema failed: {e}")

        for f in files:
            suffix = Path(f.filename).suffix
            save_path = tmpdir / f"{Path(f.filename).stem}{suffix}"
            content = await f.read()
            save_path.write_bytes(content)

            try:
                summary = pipeline.run_for_category(
                    file_path=save_path,
                    doc_type=get_category(category_code)["doc_type"],
                    category_code=category_code,
                    cadre_id_hint=cadre_id_hint or None,
                )
            except Exception as e:
                summary = {
                    "filename": f.filename,
                    "category_code": category_code,
                    "error": f"{type(e).__name__}: {e}",
                }
            print(f"[UPLOAD] {f.filename} → {summary.get('entities', 0)} entities, "
                  f"raw={summary.get('raw_entities', 0)}, "
                  f"write_ok={summary.get('write_ok')}, "
                  f"err={summary.get('write_error') or summary.get('error')}")
            results.append(summary)
    finally:
        for p in tmpdir.iterdir():
            try:
                p.unlink()
            except Exception:
                pass
        try:
            tmpdir.rmdir()
        except Exception:
            pass
        try:
            if pipeline.writer is not None:
                pipeline.writer.close()
        except Exception:
            pass

    return {
        "category_code": category_code,
        "category_name": get_category(category_code)["name"],
        "cadre_id_hint": cadre_id_hint,
        "results": results,
    }


if __name__ == "__main__":
    import uvicorn
    print("启动干部画像系统 API: http://localhost:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

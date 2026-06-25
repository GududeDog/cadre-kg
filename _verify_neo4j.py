from neo4j import GraphDatabase
import config

d = GraphDatabase.driver(config.NEO4J_URI, auth=config.NEO4J_AUTH)
with d.session(database="default") as s:
    print("=== Cadre 011 final state ===")
    for r in s.run('MATCH (c:Cadre {cadre_id:$x}) RETURN c', x='011'):
        d1 = dict(r['c'])
        d1.pop('embedding', None)
        print({k: (v[:60] + '...' if isinstance(v, str) and len(v) > 60 else v) for k, v in d1.items()})

    print("\n=== Cadre 011's appointments ===")
    rs = s.run('''
        MATCH (c:Cadre {cadre_id:$x})-[:HAS_APPOINTMENT]->(a:Appointment)
        RETURN a.appointment_id AS aid, a.cadre_id AS cid,
               a.position_name AS pos, a.position_short AS ps,
               a.org_name AS org, a.start_date AS sd, a.end_date AS ed,
               a.is_current AS cur, a.tenure_index AS ti
        ORDER BY a.tenure_index
    ''', x='011')
    for r in rs:
        d1 = dict(r)
        d1 = {k: (v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v) for k, v in d1.items()}
        print(d1)

    print("\n=== Cadre 011's relations ===")
    rs = s.run('''
        MATCH (c:Cadre {cadre_id:$x})-[r]->(t)
        RETURN type(r) AS rel, labels(t)[0] AS target_type, t.name AS target_name
    ''', x='011')
    for r in rs:
        d1 = dict(r)
        d1 = {k: (v[:40] + '...' if isinstance(v, str) and len(v) > 40 else v) for k, v in d1.items()}
        print(d1)

    print("\n=== Count check ===")
    for r in s.run('''
        MATCH (c:Cadre {cadre_id:$x})
        OPTIONAL MATCH (c)-[r1:HAS_APPOINTMENT]->(a:Appointment)
        OPTIONAL MATCH (c)-[r2]->(t)
        RETURN count(DISTINCT a) AS appts, count(DISTINCT r2) AS rels
    ''', x='011'):
        print(f"  Cadre 011 has {r['appts']} appointments, {r['rels']} total relations")

    print("\n=== Any Organization left? ===")
    rs = s.run('MATCH (o:Organization) RETURN o')
    n = sum(1 for _ in rs)
    print(f"  Organization nodes: {n}")

    print("\n=== Any Cadre with cadre_id != 011 besides 001,002? ===")
    rs = s.run('MATCH (c:Cadre) WHERE NOT c.cadre_id IN ["001","002","011"] RETURN c.cadre_id, c.name')
    for r in rs:
        print(f"  {dict(r)}")

    print("\n=== Tags for 011 ===")
    rs = s.run('''
        MATCH (c:Cadre {cadre_id:$x})-[r:HAS_ABILITY]->(t:AbilityTag)
        RETURN t.name AS tag, r.tag_category AS cat
    ''', x='011')
    for r in rs:
        print(f"  [{r['cat']}] {r['tag']} -> 011")
d.close()

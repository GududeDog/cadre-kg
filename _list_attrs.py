from neo4j import GraphDatabase
import config
d = GraphDatabase.driver(config.NEO4J_URI, auth=config.NEO4J_AUTH)
with d.session(database="default") as s:
    rs = s.run('MATCH (c:Cadre {cadre_id:$x}) RETURN c', x='011')
    for r in rs:
        props = dict(r['c'])
        keys = [k for k in props if k != 'embedding']
        non_null = [k for k in keys if props.get(k) is not None]
        print(f'属性总数（不含embedding）: {len(keys)}')
        print(f'有值的属性: {len(non_null)}')
        print(f'空值属性: {len(keys)-len(non_null)}')
        print()
        for k in sorted(keys):
            v = props[k]
            if isinstance(v, str) and len(v) > 80:
                v = v[:80] + '...'
            null_flag = ' (NULL)' if v is None else ''
            print(f'  {k:30s} = {v}{null_flag}')
d.close()

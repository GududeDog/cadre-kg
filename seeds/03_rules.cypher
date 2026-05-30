// ============================================================
// seeds/03_rules.cypher
// 标签注入规则 — 字段值映射 + 履历规则 + 关键词规则 + 统计规则
// 共 ~55条规则，按规则类型分组
// ============================================================

// ─── 约束 ───
CREATE CONSTRAINT rule_id_unique IF NOT EXISTS FOR (n:Rule) REQUIRE n.rule_id IS UNIQUE;

// ═══════════════════════════════════════════════════════════
// PART A: 字段值映射规则 (25条) — rule_type: field_value
// ═══════════════════════════════════════════════════════════

// --- 重要职务 ---
MERGE (r:Rule {rule_id: 'TV-01'})
SET r.rule_name = '正处级→县处级正职',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '县处级正职领导职务',
    r.target_dimension = '重要职务',
    r.condition_json = '{"field":"current_position_level","operator":"eq","value":"正处级"}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'TV-02'})
SET r.rule_name = '副处级→县处级党政副职',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '县处级党政副职',
    r.target_dimension = '重要职务',
    r.condition_json = '{"field":"current_position_level","operator":"eq","value":"副处级"}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

// --- 重要经历 ---
MERGE (r:Rule {rule_id: 'TV-04'})
SET r.rule_name = '街乡单位→街乡经历',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '街乡经历',
    r.target_dimension = '重要经历',
    r.condition_json = '{"field":"unit_category","operator":"eq","value":"街乡"}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'TV-17'})
SET r.rule_name = '非本区经历',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '非本区经历',
    r.target_dimension = '重要经历',
    r.condition_json = '{"field":"has_external_experience","operator":"eq","value":true}',
    r.priority = 8,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'TV-18'})
SET r.rule_name = '街乡基层副职领导经历',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '街乡基层副职领导经历',
    r.target_dimension = '重要经历',
    r.condition_json = '{"field":"grassroots_deputy_leader_exp","operator":"eq","value":true}',
    r.priority = 8,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'TV-19'})
SET r.rule_name = '中青班培训经历',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '中青班培训',
    r.target_dimension = '重要经历',
    r.condition_json = '{"field":"youth_cadre_training","operator":"eq","value":true}',
    r.priority = 8,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'TV-24'})
SET r.rule_name = '挂职经历',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '中央企业挂职',
    r.target_dimension = '重要经历',
    r.condition_json = '{"field":"secondment_experience","operator":"contains","value":"挂职"}',
    r.priority = 7,
    r.confidence_default = 0.9,
    r.enabled = true;

// --- 特殊情况 ---
MERGE (r:Rule {rule_id: 'TV-05'})
SET r.rule_name = '年轻干部标签',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '年轻干部',
    r.target_dimension = '特殊情况',
    r.condition_json = '{"field":"is_young_cadre","operator":"eq","value":true}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'TV-06'})
SET r.rule_name = '优秀年轻干部标签',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '优秀年轻干部',
    r.target_dimension = '特殊情况',
    r.condition_json = '{"field":"is_excellent_young_cadre","operator":"eq","value":true}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'TV-07'})
SET r.rule_name = '党外干部标签',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '党外干部',
    r.target_dimension = '特殊情况',
    r.condition_json = '{"field":"is_non_party_cadre","operator":"eq","value":true}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'TV-08'})
SET r.rule_name = '少数民族干部标签',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '少数民族干部',
    r.target_dimension = '特殊情况',
    r.condition_json = '{"field":"is_minority_cadre","operator":"eq","value":true}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

// --- 熟悉领域 ---
UNWIND [
  {id:'TV-09', field:'economic_cadre_tag', tag:'经济干部', dim:'熟悉领域', pr:10},
  {id:'TV-10', field:'party_affairs_cadre_tag', tag:'党务干部', dim:'熟悉领域', pr:10},
  {id:'TV-11', field:'political_legal_cadre_tag', tag:'政法干部', dim:'熟悉领域', pr:10},
  {id:'TV-12', field:'urban_construction_cadre_tag', tag:'城建干部', dim:'熟悉领域', pr:10},
  {id:'TV-13', field:'tech_cadre_tag', tag:'科技干部', dim:'熟悉领域', pr:10}
] AS row
MERGE (r:Rule {rule_id: row.id})
SET r.rule_name = row.field + '→' + row.tag,
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = row.tag,
    r.target_dimension = row.dim,
    r.condition_json = '{"field":"' + row.field + '","operator":"eq","value":true}',
    r.priority = row.pr,
    r.confidence_default = 1.0,
    r.enabled = true;

// --- 风险标签 ---
MERGE (r:Rule {rule_id: 'TV-20'})
SET r.rule_name = '任职超期提醒',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '任职超期提醒',
    r.target_dimension = '风险标签',
    r.condition_json = '{"field":"tenure_overdue_alert","operator":"eq","value":true}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

// --- 专业背景 ---
MERGE (r:Rule {rule_id: 'TV-21'})
SET r.rule_name = '双一流/985/211背景',
    r.rule_type = 'field_value',
    r.target_entity = 'Cadre',
    r.target_tag = '双一流高校',
    r.target_dimension = '专业背景',
    r.condition_json = '{"field":"fulltime_school","operator":"in","value":"双一流学校列表（运行时加载）"}',
    r.priority = 5,
    r.confidence_default = 0.95,
    r.enabled = true;

// ═══════════════════════════════════════════════════════════
// PART B: 履历规则 (10条) — rule_type: career_rule
// ═══════════════════════════════════════════════════════════

UNWIND [
  {id:'CR-01', tag:'援疆', keywords:'新疆|和田|阿克苏', pr:8, conf:0.85},
  {id:'CR-02', tag:'援藏', keywords:'西藏|拉萨|日喀则', pr:8, conf:0.85},
  {id:'CR-03', tag:'援青', keywords:'青海|西宁|玉树', pr:8, conf:0.85},
  {id:'CR-04', tag:'开发区/高新区/自贸区经历', keywords:'开发区|高新区|自贸区', pr:7, conf:0.80},
  {id:'CR-06', tag:'街乡经历', keywords:'街道|乡|镇|社区', pr:8, conf:0.85},
  {id:'CR-07', tag:'秘书经历', keywords:'秘书', pr:6, conf:0.75},
  {id:'CR-08', tag:'企业任职经历', keywords:'公司|集团|企业|厂', pr:5, conf:0.70},
  {id:'CR-09', tag:'挂职经历', keywords:'挂职|借调|抽调', pr:7, conf:0.80}
] AS row
MERGE (r:Rule {rule_id: row.id})
SET r.rule_name = row.tag + '（履历关键词: ' + row.keywords + '）',
    r.rule_type = 'career_rule',
    r.target_entity = 'Cadre',
    r.target_tag = row.tag,
    r.target_dimension = '重要经历',
    r.condition_json = '{"field":"career_unit","operator":"match_keywords","value":"' + row.keywords + '"}',
    r.priority = row.pr,
    r.confidence_default = row.conf,
    r.enabled = true;

// 履历规则: 破格提拔
MERGE (r:Rule {rule_id: 'CR-10'})
SET r.rule_name = '破格提拔（任免类别判定）',
    r.rule_type = 'career_rule',
    r.target_entity = 'Cadre',
    r.target_tag = '破格提拔',
    r.target_dimension = '特殊情况',
    r.condition_json = '{"field":"appointment_type","operator":"eq","value":"破格提拔"}',
    r.priority = 9,
    r.confidence_default = 1.0,
    r.enabled = true;

// ═══════════════════════════════════════════════════════════
// PART C: 关键词/语义规则 (15条) — rule_type: semantic
// ═══════════════════════════════════════════════════════════

UNWIND [
  {id:'KW-01', dim:'能力特点', tag:'组织协调能力强', kw:'统筹|协调|兼顾|全局', conf:0.75},
  {id:'KW-02', dim:'能力特点', tag:'开拓创新意识强', kw:'创新|突破|新思路|首创|改革攻坚', conf:0.75},
  {id:'KW-03', dim:'能力特点', tag:'调查研究能力强', kw:'调查研究|调研|走访|摸排', conf:0.75},
  {id:'KW-04', dim:'能力特点', tag:'应急处理能力强', kw:'应急|突发事件|危机|抢险|突发', conf:0.80},
  {id:'KW-05', dim:'能力特点', tag:'执行力强、善于抓落实', kw:'执行|落实|推动|狠抓|贯彻', conf:0.70},
  {id:'KW-06', dim:'能力特点', tag:'善于做群众工作', kw:'群众|走访|服务群众|民生', conf:0.75},
  {id:'KW-07', dim:'政治素养', tag:'对党忠诚', kw:'忠诚|四个意识|两个维护|政治立场', conf:0.80},
  {id:'KW-08', dim:'工作作风', tag:'敢于担当', kw:'担当|负责|主动|敢于|承担', conf:0.75},
  {id:'KW-09', dim:'工作作风', tag:'作风务实', kw:'务实|扎实|踏实|深入基层|一线', conf:0.75},
  {id:'KW-10', dim:'工作作风', tag:'作风民主、善于听取意见', kw:'民主|听取意见|集思广益|班子', conf:0.75},
  {id:'KW-11', dim:'个性特征', tag:'严谨细致', kw:'严谨|细致|精益求精|一丝不苟', conf:0.75},
  {id:'KW-12', dim:'个性特征', tag:'处事果断', kw:'果断|干练|雷厉风行|快速', conf:0.75},
  {id:'KW-13', dim:'个性特征', tag:'性格沉稳', kw:'沉稳|内敛|稳重|低调', conf:0.70},
  {id:'KW-15', dim:'能力特点', tag:'攻坚克难型干部', kw:'攻坚克难|解决历史遗留|急难险重|重点难点', conf:0.80}
] AS row
MERGE (r:Rule {rule_id: row.id})
SET r.rule_name = row.tag + '（关键词: ' + row.kw + '）',
    r.rule_type = 'semantic',
    r.target_entity = 'Cadre',
    r.target_tag = row.tag,
    r.target_dimension = row.dim,
    r.condition_json = '{"method":"keyword_match","keywords":"' + row.kw + '","doc_types":["annual_report","assessment_material","performance_material"]}',
    r.priority = 5,
    r.confidence_default = row.conf,
    r.enabled = true;

// 负向规则: 不足关键词 → 触发LLM分类
MERGE (r:Rule {rule_id: 'KW-14'})
SET r.rule_name = '不足关键词触发LLM分类',
    r.rule_type = 'semantic',
    r.target_entity = 'Cadre',
    r.target_tag = '主要不足（需LLM分类）',
    r.target_dimension = '主要不足',
    r.condition_json = '{"method":"keyword_trigger_llm","keywords":"不足|不够|有待|欠缺|差距","doc_types":["annual_report","assessment_material","performance_material"]}',
    r.priority = 3,
    r.confidence_default = 0.60,
    r.enabled = true;

// ═══════════════════════════════════════════════════════════
// PART D: 统计计算规则 (5条) — rule_type: stat_rule
// ═══════════════════════════════════════════════════════════

MERGE (r:Rule {rule_id: 'ST-01'})
SET r.rule_name = '正处级≤35岁→年轻干部',
    r.rule_type = 'stat_rule',
    r.target_entity = 'Cadre',
    r.target_tag = '年轻干部',
    r.target_dimension = '特殊情况',
    r.condition_json = '{"formula":"current_level==正处 && age<=35"}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'ST-02'})
SET r.rule_name = '副处级≤40岁→年轻干部（副处后备）',
    r.rule_type = 'stat_rule',
    r.target_entity = 'Cadre',
    r.target_tag = '年轻干部',
    r.target_dimension = '特殊情况',
    r.condition_json = '{"formula":"current_level==副处 && age<=40"}',
    r.priority = 10,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'ST-03'})
SET r.rule_name = '任现职≥8年→任职超期提醒',
    r.rule_type = 'stat_rule',
    r.target_entity = 'Cadre',
    r.target_tag = '任职超期提醒',
    r.target_dimension = '风险标签',
    r.condition_json = '{"formula":"current_tenure_years>=8 && position_type!=纪委岗位"}',
    r.priority = 9,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'ST-04'})
SET r.rule_name = '纪委岗位≥5年→任职超期提醒',
    r.rule_type = 'stat_rule',
    r.target_entity = 'Cadre',
    r.target_tag = '任职超期提醒',
    r.target_dimension = '风险标签',
    r.condition_json = '{"formula":"current_tenure_years>=5 && position_type==纪委岗位"}',
    r.priority = 9,
    r.confidence_default = 1.0,
    r.enabled = true;

MERGE (r:Rule {rule_id: 'ST-05'})
SET r.rule_name = '晋升速度"快"→越级提拔',
    r.rule_type = 'stat_rule',
    r.target_entity = 'Cadre',
    r.target_tag = '越级提拔',
    r.target_dimension = '特殊情况',
    r.condition_json = '{"formula":"promotion_speed==快"}',
    r.priority = 8,
    r.confidence_default = 0.90,
    r.enabled = true;

// ═══════════════════════════════════════════════════════════
// 关联规则到文档类型
// ═══════════════════════════════════════════════════════════

// 字段值规则 → 任免表
MATCH (r:Rule {rule_type: 'field_value'}), (dt:DocType {doc_type: 'cadre_appointment_form'})
MERGE (r)-[:APPLIES_TO_DOC_TYPE]->(dt);

// 字段值规则 → 分工备案表
MATCH (r:Rule {rule_type: 'field_value'}), (dt:DocType {doc_type: 'division_record'})
MERGE (r)-[:APPLIES_TO_DOC_TYPE]->(dt);

// 履历规则 → 任免表
MATCH (r:Rule {rule_type: 'career_rule'}), (dt:DocType {doc_type: 'cadre_appointment_form'})
MERGE (r)-[:APPLIES_TO_DOC_TYPE]->(dt);

// 语义规则 → 述职报告
MATCH (r:Rule {rule_type: 'semantic'}), (dt:DocType {doc_type: 'annual_report'})
MERGE (r)-[:APPLIES_TO_DOC_TYPE]->(dt);

// 语义规则 → 考察材料
MATCH (r:Rule {rule_type: 'semantic'}), (dt:DocType {doc_type: 'assessment_material'})
MERGE (r)-[:APPLIES_TO_DOC_TYPE]->(dt);

// 语义规则 → 现实表现材料
MATCH (r:Rule {rule_type: 'semantic'}), (dt:DocType {doc_type: 'performance_material'})
MERGE (r)-[:APPLIES_TO_DOC_TYPE]->(dt);

// 统计规则 → 所有doc_type（不依赖文档类型）
MATCH (r:Rule {rule_type: 'stat_rule'}), (dt:DocType)
MERGE (r)-[:APPLIES_TO_DOC_TYPE]->(dt);

// ═══════════════════════════════════════════════════════════
// 关联规则到产出标签
// ═══════════════════════════════════════════════════════════

MATCH (r:Rule), (t:Tag)
WHERE r.target_tag = t.tag_name AND r.target_dimension = t.tag_dimension
MERGE (r)-[:PRODUCES_TAG]->(t);

RETURN 'Rules created: ' +
       count { (r:Rule) } + ' rules' AS summary;

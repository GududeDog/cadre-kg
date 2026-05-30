// ============================================================
// seeds/04_profiles.cypher
// ExtractionProfile — 每种文档类型的抽取配置
// ============================================================

CREATE CONSTRAINT profile_id_unique IF NOT EXISTS FOR (n:ExtractionProfile) REQUIRE n.profile_id IS UNIQUE;

// ─── Profile 1: 任免表 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_cadre_form'})
SET p.display_name = '任免表抽取配置',
    p.structured_fields_json = '["name","gender","ethnicity","birth_date","political_status","party_join_date","work_start_date","native_place","health_status","current_position","current_position_level","current_position_rank","fulltime_education_level","fulltime_degree","fulltime_school","fulltime_major","in_service_education_level","in_service_school","in_service_major","career_history","family_members","annual_assessment","rewards_punishments","retirement_date"]',
    p.use_llm = false,
    p.use_structured = true,
    p.structured_method = 'table_coordinate';

MATCH (p:ExtractionProfile {profile_id: 'profile_cadre_form'})
MATCH (dt:DocType {doc_type: 'cadre_appointment_form'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 2: 述职报告 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_annual_report'})
SET p.display_name = '述职报告抽取配置',
    p.structured_fields_json = '["cadre_id","report_year","current_position_at_report"]',
    p.use_llm = true,
    p.use_structured = true,
    p.llm_extract_targets_json = '["ability_tags","work_performances","quantifiable_indicators","awards","main_shortcomings"]',
    p.structured_method = 'filename_regex';

MATCH (p:ExtractionProfile {profile_id: 'profile_annual_report'})
MATCH (dt:DocType {doc_type: 'annual_report'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 3: 考察材料 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_assessment'})
SET p.display_name = '考察材料抽取配置',
    p.structured_fields_json = '["cadre_id","inspection_type","democratic_evaluation","discipline_check","archive_check","personal_affairs_check","petition_check"]',
    p.use_llm = true,
    p.use_structured = true,
    p.llm_extract_targets_json = '["political_quality_eval","ability_evaluation","ability_tags_third_party","shortcomings_third_party"]',
    p.structured_method = 'keyword_section';

MATCH (p:ExtractionProfile {profile_id: 'profile_assessment'})
MATCH (dt:DocType {doc_type: 'assessment_material'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 4: 现实表现材料 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_performance'})
SET p.display_name = '现实表现材料抽取配置',
    p.structured_fields_json = '["cadre_id","report_date"]',
    p.use_llm = true,
    p.use_structured = true,
    p.llm_extract_targets_json = '["political_performance","work_ability_performance","work_style_performance","ability_tags_d2","shortcomings_d2","overall_evaluation"]',
    p.structured_method = 'filename_regex';

MATCH (p:ExtractionProfile {profile_id: 'profile_performance'})
MATCH (dt:DocType {doc_type: 'performance_material'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 5: 民主测评 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_democratic_eval'})
SET p.display_name = '民主测评抽取配置',
    p.structured_fields_json = '["cadre_id","excellent_rate","competent_rate","basic_competent_rate","incompetent_rate","overall_evaluation"]',
    p.use_llm = false,
    p.use_structured = true,
    p.structured_method = 'table_cell';

MATCH (p:ExtractionProfile {profile_id: 'profile_democratic_eval'})
MATCH (dt:DocType {doc_type: 'democratic_evaluation'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 6: 分工备案表 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_division'})
SET p.display_name = '分工备案表抽取配置',
    p.structured_fields_json = '["team_id","team_name","authorized_headcount","actual_headcount","vacancy_count","vacancy_positions","team_members","division_info"]',
    p.use_llm = false,
    p.use_structured = true,
    p.structured_method = 'table_cell';

MATCH (p:ExtractionProfile {profile_id: 'profile_division'})
MATCH (dt:DocType {doc_type: 'division_record'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 7: 三件典型事件 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_typical_events'})
SET p.display_name = '三件典型事件抽取配置',
    p.structured_fields_json = '["cadre_id"]',
    p.use_llm = true,
    p.use_structured = true,
    p.llm_extract_targets_json = '["typical_events","event_quantifiable_metrics","event_ability_mapping"]',
    p.structured_method = 'filename_regex';

MATCH (p:ExtractionProfile {profile_id: 'profile_typical_events'})
MATCH (dt:DocType {doc_type: 'typical_events'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 8: 考察情况登记表 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_inspection_register'})
SET p.display_name = '考察情况登记表抽取配置',
    p.structured_fields_json = '["cadre_id","inspection_date","position_at_inspection","main_advantages","talk_statistics","political_quality_score","theory_exam_score"]',
    p.use_llm = false,
    p.use_structured = true,
    p.structured_method = 'table_cell';

MATCH (p:ExtractionProfile {profile_id: 'profile_inspection_register'})
MATCH (dt:DocType {doc_type: 'inspection_register'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 9: 干部基本信息审核表 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_cadre_review'})
SET p.display_name = '干部基本信息审核表抽取配置',
    p.structured_fields_json = '["cadre_id","basic_info_verified","three_ages_two_cals_verified","basic_info_fields"]',
    p.use_llm = false,
    p.use_structured = true,
    p.structured_method = 'table_cell';

MATCH (p:ExtractionProfile {profile_id: 'profile_cadre_review'})
MATCH (dt:DocType {doc_type: 'cadre_review_form'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 10: 工作业绩事例 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_performance_case'})
SET p.display_name = '工作业绩事例抽取配置',
    p.structured_fields_json = '["cadre_id","work_period"]',
    p.use_llm = true,
    p.use_structured = true,
    p.llm_extract_targets_json = '["performance_cases","case_category","case_quantifiable","case_ability_mapping"]',
    p.structured_method = 'filename_regex';

MATCH (p:ExtractionProfile {profile_id: 'profile_performance_case'})
MATCH (dt:DocType {doc_type: 'performance_case'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 11: 考察工作方案（非数据源，仅记录） ───
MERGE (p:ExtractionProfile {profile_id: 'profile_inspection_plan'})
SET p.display_name = '考察工作方案（流程文件，不抽取数据字段）',
    p.structured_fields_json = '["inspection_batch_id","inspection_team","inspection_timeline"]',
    p.use_llm = false,
    p.use_structured = false,
    p.is_data_source = false;

MATCH (p:ExtractionProfile {profile_id: 'profile_inspection_plan'})
MATCH (dt:DocType {doc_type: 'inspection_plan'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

// ─── Profile 12: 干部名册 ───
MERGE (p:ExtractionProfile {profile_id: 'profile_cadre_roster'})
SET p.display_name = '干部名册/花名册抽取配置',
    p.structured_fields_json = '["name","gender","birth_date","ethnicity","political_status","current_unit","current_position","current_level"]',
    p.use_llm = false,
    p.use_structured = true,
    p.structured_method = 'excel_rows';

MATCH (p:ExtractionProfile {profile_id: 'profile_cadre_roster'})
MATCH (dt:DocType {doc_type: 'cadre_roster'})
MERGE (dt)-[:HAS_EXTRACTION_PROFILE]->(p);

RETURN 'Profiles created: ' +
       count { (n:ExtractionProfile) } + ' extraction profiles' AS summary;

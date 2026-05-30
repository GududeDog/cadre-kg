NODE_SCHEMA = {
    "Cadre": {
        "properties": [
            "cadre_id", "name", "gender", "ethnicity", "birth_date", "age",
            "political_status", "party_join_date", "work_start_date", "work_years",
            "native_place", "health_status",
            "highest_education", "highest_degree", "highest_major", "highest_school",
            "current_position", "current_unit", "current_level", "current_status",
            "current_start_date", "current_tenure_years", "current_division",
            "current_rank",
            "is_young_cadre_35", "is_young_cadre_40", "is_non_party", "is_minority",
            "is_reserve_cadre", "is_key_successor", "is_probation", "is_tenure_overdue",
            "has_discipline_record", "has_audit_issue", "has_petition",
            "has_economic_audit_issue", "has_inspection_issue",
            "thinking_planning_score", "coordination_score", "execution_score",
            "innovation_score", "mass_work_score", "overall_ability_score",
            "style_label", "personality_label",
            "performance_level", "promotion_speed", "growth_stage",
            "cultivation_direction",
            "data_sources", "last_updated", "confidence_level",
        ]
    },
    "Organization": {
        "properties": [
            "org_id", "org_name", "org_short_name", "org_type", "org_level",
            "parent_org_id", "functional_domain", "is_key_department",
            "is_street_town", "established_date", "status",
        ]
    },
    "Position": {
        "properties": [
            "position_id", "position_name", "position_level", "position_type",
            "org_id", "org_name", "functional_domain",
            "is_key_position", "is_party_secretary", "is_leading_position",
            "required_education", "required_major", "required_age_min", "required_age_max",
            "required_tenure_years", "required_abilities", "required_experience",
            "status", "current_holder_id", "vacancy_date", "is_reserved",
        ]
    },
    "Appointment": {
        "properties": [
            "appointment_id", "cadre_id", "position_id", "position_name",
            "org_id", "org_name",
            "appointment_type", "start_date", "end_date", "tenure_years", "is_current",
            "is_key_position", "is_leading_position", "is_street_town",
            "is_district_outside", "is_deputy_position", "is_section_chief",
            "is_below_section", "is_big_office_deputy",
            "is_economic_position", "is_tech_position", "is_planning_position",
            "functional_domain",
            "data_source", "document_ref",
        ]
    },
    "Assessment": {
        "properties": [
            "assessment_id", "cadre_id", "assessment_year", "assessment_type",
            "result", "result_level", "score", "assessment_org", "assessment_date",
            "key_achievements", "data_source",
        ]
    },
    "DemocraticAssessment": {
        "properties": [
            "da_id", "cadre_id", "assessment_date", "assessment_org",
            "excellent_rate", "competent_rate", "basic_competent_rate",
            "incompetent_rate", "abstention_rate",
            "overall_evaluation", "key_strengths", "key_weaknesses", "data_source",
        ]
    },
    "Event": {
        "properties": [
            "event_id", "event_type", "event_name", "event_date", "end_date",
            "description", "location", "cadre_id",
            "is_pandemic_related", "is_petition_related", "is_safety_related",
            "is_project_related", "is_aid_related", "is_innovation_related",
            "is_crisis_related",
            "ability_impact", "style_impact", "character_impact",
            "source_document", "source_type",
        ]
    },
    "Training": {
        "properties": [
            "training_id", "cadre_id", "training_name", "training_type",
            "training_org", "start_date", "end_date", "duration_days",
            "is_central_party_school", "is_youth_league",
            "certificate", "key_learnings",
        ]
    },
    "Award": {
        "properties": [
            "award_id", "cadre_id", "award_name", "award_level", "award_type",
            "award_date", "awarding_org", "is_provincial_ministerial",
            "related_work", "data_source",
        ]
    },
    "Discipline": {
        "properties": [
            "discipline_id", "cadre_id", "discipline_type", "discipline_measure",
            "discipline_date", "decision_org", "reason", "duration",
            "is_expired", "data_source",
        ]
    },
    "Audit": {
        "properties": [
            "audit_id", "cadre_id", "audit_type", "audit_date", "audit_org",
            "audit_result", "issues_found", "rectification_status", "data_source",
        ]
    },
    "Document": {
        "properties": [
            "doc_id", "doc_name", "doc_type", "doc_format",
            "cadre_id", "org_id", "doc_date", "doc_year",
            "content_summary", "key_entities", "key_sentiments",
            "storage_path", "chunk_ids",
        ]
    },
    "DocumentChunk": {
        "properties": [
            "chunk_id", "doc_id", "chunk_index", "chunk_text", "chunk_type",
            "extracted_entities", "extracted_relations",
        ]
    },
    "LeadershipTeam": {
        "properties": [
            "team_id", "org_id", "org_name", "team_name", "formation_date", "status",
            "combat_score", "execution_score", "coordination_score",
            "innovation_score", "stability_score", "structural_balance",
            "echelon_score", "rank_in_category", "total_in_category",
            "avg_age", "min_age", "max_age",
            "young_cadre_count", "female_count", "non_party_count", "minority_count",
            "major_coverage", "major_coverage_score",
            "risk_warnings", "risk_level",
        ]
    },
    "TeamConfig": {
        "properties": [
            "config_id", "team_id", "config_name", "config_type",
            "change_member_id", "change_member_name",
            "new_member_id", "new_member_name",
            "before_avg_age", "after_avg_age",
            "before_combat_score", "after_combat_score",
            "risk_alerts",
            "is_valid", "validation_rules", "validation_results",
            "created_at",
        ]
    },
    "Person": {
        "properties": [
            "person_id", "person_name", "person_type",
            "gender", "birth_date", "age",
            "occupation", "work_unit", "political_status", "education",
            "relation_to_cadre", "cadre_id",
        ]
    },
    "Education": {
        "properties": [
            "edu_id", "cadre_id", "school_name", "major",
            "education_level", "degree",
            "start_date", "end_date", "is_full_time",
            "school_type", "is_party_school",
        ]
    },
    "AbilityTag": {
        "properties": [
            "tag_id", "tag_name", "tag_category", "tag_weight",
            "related_positions", "related_domains",
        ]
    },
    "CultivationPath": {
        "properties": [
            "path_id", "cadre_id", "path_name",
            "current_stage", "target_stage",
            "path_steps", "recommended_trainings", "recommended_positions",
            "estimated_duration", "priority",
        ]
    },
}

REL_SCHEMA = {
    # 1. 干部-任职关系（时态核心）
    "HOLDS": {
        "source": "Cadre", "target": "Position",
        "properties": ["appointment_type", "start_date", "end_date", "is_current",
                        "division", "is_key_position", "is_leading_position"],
    },
    # 2. 岗位-单位关系
    "BELONGS_TO": {
        "source": "Position", "target": "Organization",
        "properties": ["is_primary", "effective_date"],
    },
    # 3. 干部-单位关系（当前所属）
    "CURRENTLY_IN": {
        "source": "Cadre", "target": "Organization",
        "properties": ["relation_type", "start_date"],
    },
    # 4. 干部-任职记录（历史追溯）
    "HAS_APPOINTMENT": {
        "source": "Cadre", "target": "Appointment",
        "properties": [],
    },
    "FOR_POSITION": {
        "source": "Appointment", "target": "Position",
        "properties": [],
    },
    "IN_ORGANIZATION": {
        "source": "Appointment", "target": "Organization",
        "properties": [],
    },
    # 5. 干部-考核
    "HAS_ASSESSMENT": {
        "source": "Cadre", "target": "Assessment",
        "properties": ["assessment_year", "assessment_type"],
    },
    # 6. 干部-民主测评
    "HAS_DEMOCRATIC_ASSESSMENT": {
        "source": "Cadre", "target": "DemocraticAssessment",
        "properties": ["assessment_date"],
    },
    # 7. 干部-事件（成长轨迹）
    "PARTICIPATED_IN": {
        "source": "Cadre", "target": "Event",
        "properties": ["role", "impact_level"],
    },
    # 8. 事件-能力影响
    "DEVELOPS_ABILITY": {
        "source": "Event", "target": "AbilityTag",
        "properties": ["ability_type", "impact_score"],
    },
    # 9. 干部-培训
    "ATTENDED": {
        "source": "Cadre", "target": "Training",
        "properties": ["completion_status", "performance"],
    },
    # 10. 干部-奖励
    "RECEIVED": {
        "source": "Cadre", "target": "Award",
        "properties": ["award_date", "is_primary_recipient"],
    },
    # 11. 干部-处分
    "RECEIVED_DISCIPLINE": {
        "source": "Cadre", "target": "Discipline",
        "properties": ["discipline_date", "is_active"],
    },
    # 12. 干部-审计
    "AUDITED": {
        "source": "Cadre", "target": "Audit",
        "properties": ["audit_date", "audit_type"],
    },
    # 13. 干部-文档
    "HAS_DOCUMENT": {
        "source": "Cadre", "target": "Document",
        "properties": ["doc_type", "doc_year", "is_primary_source"],
    },
    # 14. 文档-分块
    "HAS_CHUNK": {
        "source": "Document", "target": "DocumentChunk",
        "properties": ["chunk_index"],
    },
    # 15. 干部-教育经历
    "STUDIED_AT": {
        "source": "Cadre", "target": "Education",
        "properties": ["is_highest", "education_level"],
    },
    # 17. 干部-能力标签
    "HAS_ABILITY": {
        "source": "Cadre", "target": "AbilityTag",
        "properties": ["proficiency", "source", "confidence"],
    },
    # 18. 岗位-要求能力
    "REQUIRES_ABILITY": {
        "source": "Position", "target": "AbilityTag",
        "properties": ["importance", "weight"],
    },
    # 19. 干部-关系人
    "HAS_RELATION": {
        "source": "Cadre", "target": "Person",
        "properties": ["relation_type", "is_household_registered"],
    },
    # 21. 干部-同事关系
    "COLLEAGUE_WITH": {
        "source": "Cadre", "target": "Cadre",
        "properties": ["overlap_period", "same_org", "relation_strength"],
    },
    # 22. 干部-校友关系
    "SCHOOLMATE_WITH": {
        "source": "Cadre", "target": "Cadre",
        "properties": ["school_name", "major_relation", "overlap_period"],
    },
    # 23. 干部-同乡关系
    "FROM_SAME_PLACE": {
        "source": "Cadre", "target": "Cadre",
        "properties": ["place_type", "place_name"],
    },
    # 24. 领导班子-成员
    "HAS_MEMBER": {
        "source": "LeadershipTeam", "target": "Cadre",
        "properties": ["role_in_team", "join_date", "is_core_member", "division"],
    },
    # 25. 领导班子-所属单位
    "LEADS": {
        "source": "LeadershipTeam", "target": "Organization",
        "properties": [],
    },
    # 26. 班子配置方案-原班子
    "BASED_ON": {
        "source": "TeamConfig", "target": "LeadershipTeam",
        "properties": [],
    },
    # 27. 培养路径-干部
    "FOR_CADRE": {
        "source": "CultivationPath", "target": "Cadre",
        "properties": [],
    },
    # 29. 培养路径-推荐岗位
    "TARGETS_POSITION": {
        "source": "CultivationPath", "target": "Position",
        "properties": [],
    },
    # 30. 单位-上级单位
    "SUBORDINATE_TO": {
        "source": "Organization", "target": "Organization",
        "properties": ["relation_type"],
    },
    # 31. 文档-提取实体
    "MENTIONS": {
        "source": "DocumentChunk", "target": "Entity",
        "properties": ["entity_type", "mention_text", "confidence"],
    },
    # 32. 干部-熟悉领域
    "FAMILIAR_WITH": {
        "source": "Cadre", "target": "AbilityTag",
        "properties": ["proficiency_level", "proficiency_score", "evidence_source"],
    },
}

# ─── Vector Index Query ───
VECTOR_INDEX_QUERY = "CALL db.index.vector.queryNodes('entity_embedding', $k, $embedding) YIELD node, score RETURN node, score"

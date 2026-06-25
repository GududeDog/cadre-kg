NODE_SCHEMA = {
    "Cadre": {
        "properties": [
            "cadre_id", "name", "gender", "birth_date", "age", "ethnicity",
            "native_place", "birth_place", "party_join_date", "work_start_date",
            "retirement_date", "health_status", "tech_title", "specialty",
            "current_position_level", "current_rank",
        ]
    },
    "Position": {
        "properties": ["position_id", "position_name", "level"]
    },
    "Resume": {
        "properties": [
            "resume_id", "period", "unit", "department", "position",
            "region", "dept", "rank", "cadre_id",
            "position_level", "rank_level",
        ]
    },
    "Education": {
        "properties": [
            "edu_id", "edu_level", "degree", "school", "major",
            "cadre_id", "edu_type",
        ]
    },
    "Relation": {
        "properties": [
            "relation_id", "relation_type", "name", "age",
            "political_status", "work_unit_position", "cadre_id",
        ]
    },
    "RewardPunish": {
        "properties": [
            "reward_punish_id", "seq_no", "source", "source_doc",
            "content", "time", "source_2", "cadre_id",
        ]
    },
    "Performance": {
        "properties": [
            "performance_id", "content", "source", "source_doc",
            "work_experience", "work_performance", "source_doc_2",
            "source_fragment", "cadre_id",
        ]
    },
    "Evaluation": {
        "properties": [
            "evaluation_id", "content", "source", "source_doc", "cadre_id",
        ]
    },
    "Shortcoming": {
        "properties": [
            "shortcoming_id", "assessment_year", "content",
            "source_doc", "source_fragment", "cadre_id",
        ]
    },
    "Personality": {
        "properties": [
            "personality_id", "time", "trait", "source_doc", "source_fragment",
            "shortcoming", "positive_eval", "negative_eval",
            "issue_tag_1", "issue_tag_2",
            "time_2", "source_doc_2", "cadre_id",
        ]
    },
    "Ability": {
        "properties": [
            "ability_id", "time", "ability_trait", "source_doc",
            "source_fragment", "cadre_id",
        ]
    },
    "FamiliarField": {
        "properties": [
            "field_id", "assessment_year", "field_name",
            "source_doc", "cadre_id",
        ]
    },
    "Tag": {
        "properties": [
            "tag_id", "assessment_year", "style_tag", "special_tag",
            "source_doc", "issue_tag", "time", "source_doc_2", "cadre_id",
        ]
    },
    "WritingStyle": {
        "properties": [
            "writing_id", "time", "style_type", "source_fragment",
            "source_doc", "cadre_id",
        ]
    },
    "AnnualAssessment": {
        "properties": [
            "assessment_id", "result", "commendation", "cadre_id",
        ]
    },
    "Profile": {
        "properties": [
            "profile_id", "assessment_year", "core_traits",
            "trait_evidence", "main_shortcomings", "familiar_fields",
            "style_tag", "special_tag", "source_fragment",
            "source_doc", "cadre_id",
        ]
    },
    "PositionStatus": {
        "properties": [
            "position_status_id", "current_position", "proposed_position",
            "proposed_removal", "cadre_id",
        ]
    },
    "Division": {
        "properties": [
            "division_id", "division_content", "department",
            "source_doc", "source_fragment", "cadre_id",
        ]
    },
    "AbilityEvolution": {
        "properties": [
            "evolution_id", "time", "ability_structure", "source_doc_1",
            "work_effect", "source_doc_2", "performance_change",
            "source_doc_3", "source_fragment", "cadre_id",
        ]
    },
    "ExcellenceIndicator": {
        "properties": [
            "indicator_id", "excellence_rate", "excellence_rank", "cadre_id",
        ]
    },
}

REL_SCHEMA = {
    # 干部 → 各子实体 (1:N)
    "HAS_RESUME": {
        "source": "Cadre", "target": "Resume",
        "properties": [],
    },
    "HAS_EDUCATION": {
        "source": "Cadre", "target": "Education",
        "properties": [],
    },
    "HAS_RELATIVE": {
        "source": "Cadre", "target": "Relation",
        "properties": [],
    },
    "HAS_REWARD": {
        "source": "Cadre", "target": "RewardPunish",
        "properties": [],
    },
    "HAS_ACHIEVEMENT": {
        "source": "Cadre", "target": "Performance",
        "properties": [],
    },
    "HAS_EVALUATION": {
        "source": "Cadre", "target": "Evaluation",
        "properties": [],
    },
    "HAS_SHORTCOMING": {
        "source": "Cadre", "target": "Shortcoming",
        "properties": [],
    },
    "HAS_PERSONALITY": {
        "source": "Cadre", "target": "Personality",
        "properties": [],
    },
    "HAS_ABILITY": {
        "source": "Cadre", "target": "Ability",
        "properties": [],
    },
    "HAS_FAMILIAR_FIELD": {
        "source": "Cadre", "target": "FamiliarField",
        "properties": [],
    },
    "HAS_TAG": {
        "source": "Cadre", "target": "Tag",
        "properties": [],
    },
    "HAS_WRITING_STYLE": {
        "source": "Cadre", "target": "WritingStyle",
        "properties": [],
    },
    "HAS_ANNUAL_ASSESSMENT": {
        "source": "Cadre", "target": "AnnualAssessment",
        "properties": [],
    },
    "HAS_PROFILE": {
        "source": "Cadre", "target": "Profile",
        "properties": [],
    },
    "HAS_POSITION_STATUS": {
        "source": "Cadre", "target": "PositionStatus",
        "properties": [],
    },
    "HAS_DIVISION": {
        "source": "Cadre", "target": "Division",
        "properties": [],
    },
    "HAS_ABILITY_EVOLUTION": {
        "source": "Cadre", "target": "AbilityEvolution",
        "properties": [],
    },
    "HAS_EXCELLENCE": {
        "source": "Cadre", "target": "ExcellenceIndicator",
        "properties": [],
    },
    # 子实体 → 岗位 (N:1)
    "REFERENCES_POSITION": {
        "source": "PositionStatus", "target": "Position",
        "properties": [],
    },
    "RESUME_REFERENCES_POSITION": {
        "source": "Resume", "target": "Position",
        "properties": [],
    },
}

# ─── Vector Index Query ───
VECTOR_INDEX_QUERY = "CALL db.index.vector.queryNodes('entity_embedding', $k, $embedding) YIELD node, score RETURN node, score"

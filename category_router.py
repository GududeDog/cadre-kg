"""材料类目 → 处理路径路由表。"""

CATEGORY_LIST = [
    {
        "code": "basic_info",
        "name": "基础信息",
        "doc_type": "cadre_appointment_form",
        "use_llm": True,
        "primary_entity": "Cadre",
    },
    {
        "code": "annual_assessment",
        "name": "年度考核",
        "doc_type": "annual_report",
        "use_llm": True,
        "primary_entity": "AnnualAssessment",
    },
    {
        "code": "clean_gov",
        "name": "党风廉政情况",
        "doc_type": "discipline_decision",
        "use_llm": True,
        "primary_entity": "RewardPunish",
    },
    {
        "code": "inspection",
        "name": "巡察报告",
        "doc_type": "inspection_talk_summary",
        "use_llm": True,
        "primary_entity": "Cadre",
    },
    {
        "code": "election",
        "name": "换届材料",
        "doc_type": "assessment_analysis",
        "use_llm": True,
        "primary_entity": "Cadre",
    },
    {
        "code": "research",
        "name": "组织部大调研材料",
        "doc_type": "research_report",
        "use_llm": True,
        "primary_entity": "Cadre",
    },
    {
        "code": "org_evaluation",
        "name": "组织评价材料",
        "doc_type": "assessment_material",
        "use_llm": True,
        "primary_entity": "Cadre",
    },
    {
        "code": "democratic_life",
        "name": "民主生活会材料",
        "doc_type": "democratic_life_meeting",
        "use_llm": True,
        "primary_entity": "Cadre",
    },
    {
        "code": "secondment",
        "name": "实践锻炼",
        "doc_type": "secondment_record",
        "use_llm": True,
        "primary_entity": "Cadre",
    },
]


def get_category(code: str):
    """按 code 查询类目配置。"""
    for c in CATEGORY_LIST:
        if c["code"] == code:
            return c
    return None

import os
from pathlib import Path

# ─── Neo4j ───
NEO4J_URI = "neo4j://localhost"
NEO4J_AUTH = ("neo4j", "12345678")

# ─── Source Documents ───
# SOURCE_DIR = Path(r"E:\ZKSJ_project\CYRS_test\demo\材料 - 副本")
SOURCE_DIR = Path(r"E:\大模型工作内容\朝阳人事\朝阳人事数据\训练数据\街乡班子任免表\乡\1-南磨房乡-001等14人-任免表（2026-05-14）")

# ─── Embedding ───
EMBEDDING_MODEL = r"E:\ZKSJ_project\CYRS_test\demo\bge-base-zh-v1.5"
EMBEDDING_DIM = 768
EMBEDDING_DEVICE = "cuda"
EMBEDDING_CACHE_DIR = r"E:\ZKSJ_project\CYRS_test\demo\bge-base-zh-v1.5"

# ─── Chunking ───
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 100
CHUNK_HARD_MAX = 1800  # Force-split any single chunk longer than this at sentence boundaries

# ─── LLM (DeepSeek) ───
LLM_API_KEY = "sk-275f42912df249b29595b6ff4cc8ed89"
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "deepseek-v4-flash"

# ─── LLM (DeepSeek) ───
# LLM_API_KEY = "43F2FBB5055A7CDDCD082D740B0475E0"
# LLM_BASE_URL = "http://41.0.0.114:8088/lm/v2/chat/completions"
# LLM_MODEL = "ds-v4-flash"

# ─── Extraction ───
ENTITY_TYPES = [
    "Cadre", "Position", "Resume", "Education", "Relation",
    "RewardPunish", "Performance", "Evaluation", "Shortcoming",
    "Personality", "Ability", "FamiliarField", "Tag", "WritingStyle",
    "AnnualAssessment", "Profile", "PositionStatus", "Division",
    "AbilityEvolution", "ExcellenceIndicator",
]

RELATION_TYPES = [
    "HAS_RESUME", "HAS_EDUCATION", "HAS_RELATIVE", "HAS_REWARD",
    "HAS_ACHIEVEMENT", "HAS_EVALUATION", "HAS_SHORTCOMING",
    "HAS_PERSONALITY", "HAS_ABILITY", "HAS_FAMILIAR_FIELD",
    "HAS_TAG", "HAS_WRITING_STYLE", "HAS_ANNUAL_ASSESSMENT",
    "HAS_PROFILE", "HAS_POSITION_STATUS", "HAS_DIVISION",
    "HAS_ABILITY_EVOLUTION", "HAS_EXCELLENCE",
    "REFERENCES_POSITION", "RESUME_REFERENCES_POSITION",
]

TAG_CATEGORIES = ["专业技能", "管理能力", "通用能力", "工作作风", "负面"]

# ─── Tag Taxonomy (控词表, 对应 AbilityTag.tag_category) ───
TAG_TAXONOMY = {
    "专业技能": {
        "fixed_tags": ["经济工作", "规划建设", "科技创新", "党建工作",
                       "政法工作", "纪检监察", "社区建设", "城市管理",
                       "应急管理", "安全生产", "信访维稳", "招商引资"],
        "keywords": ["经济", "规划", "科技", "党建", "政法", "纪检",
                     "社区", "城市管理", "应急", "安全", "信访", "招商"],
        "sources": ["cadre_form", "investigation", "report"],
    },
    "管理能力": {
        "fixed_tags": ["统筹协调", "应急处突", "组织协调", "团队建设",
                       "决策能力", "执行落实", "指挥调度"],
        "keywords": ["统筹", "协调", "组织", "团队", "决策", "执行",
                     "指挥", "调度"],
        "sources": ["investigation", "report", "cadre_form"],
    },
    "通用能力": {
        "fixed_tags": ["群众工作", "依法办事", "文字综合", "沟通表达",
                       "学习能力", "创新突破", "基层治理"],
        "keywords": ["群众", "法律", "文字", "沟通", "学习", "创新",
                     "基层"],
        "sources": ["investigation", "report", "cadre_form"],
    },
    "工作作风": {
        "fixed_tags": ["担当精神", "务实作风", "法治思维", "规矩意识",
                       "廉洁自律", "团结同志", "作风正派", "严谨细致",
                       "事业心强", "责任感强"],
        "keywords": ["担当", "务实", "法治", "规矩", "廉洁", "自律",
                     "正派", "严谨", "细致", "责任心", "事业心"],
        "sources": ["investigation", "report", "cadre_form"],
    },
    "负面": {
        "fixed_tags": ["能力短板", "廉政风险", "学习不足",
                       "创新不足", "研究不深入", "工作方式需改进",
                       "灵活性不足"],
        "keywords": ["不足", "不够", "差距", "有待提高", "存在问题",
                     "注意改进", "欠缺", "薄弱"],
        "sources": ["investigation", "report"],
    },
}

# ─── Tag Synonym Map (标签同义归一化) ───
TAG_SYNONYM = {
    "统筹协调": ["统筹协调能力", "协调能力强", "善于统筹", "统筹兼顾"],
    "严谨细致": ["工作细致", "细致认真", "一丝不苟", "严谨"],
    "应急处突": ["应急处置", "处理复杂问题", "应急管理"],
    "群众工作": ["群众工作能力", "善于做群众工作", "服务群众"],
    "党建工作": ["党务工作", "党建创新", "基层组织建设"],
    "务实作风": ["求真务实", "讲实话办实事", "实干"],
    "创新不足": ["工作创新不够持久", "创新意识不足", "缺乏创新"],
    "学习不足": ["学习不够系统", "理论学习不够", "学习有待加强"],
}

# ─── Cadre ID Pattern ───
CADRE_ID_PATTERN = r'(?:审批表述职报告考察测评考察材料归档)?[_-]?(\d{3})(?:同志)?'

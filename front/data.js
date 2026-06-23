// ═══════════════════════════════════════════════════════════
// data.js — 干部画像 Mock 数据 (新实体结构)
// ═══════════════════════════════════════════════════════════

const MOCK_DATA = {
  cadre_id: "001",
  name: "张三",
  gender: "男",
  ethnicity: "汉族",
  birth_date: "1981.10",
  age: 44,
  native_place: "江苏盐城",
  birth_place: "江苏省东台市",
  party_join_date: "2006.06",
  work_start_date: "2003.07",
  retirement_date: "2041.10",
  health_status: "健康",
  tech_title: "高级经济师",
  specialty: "区域经济发展、产业规划",

  // 教育经历
  educations: [
    {
      edu_id: "edu_001_01",
      edu_level: "大学",
      degree: "法学学士",
      school: "中国政法大学",
      major: "法学专业",
      edu_type: "全日制",
    },
    {
      edu_id: "edu_001_02",
      edu_level: "研究生",
      degree: "管理学硕士",
      school: "中央党校研究生院",
      major: "马克思主义哲学专业",
      edu_type: "在职",
    },
  ],

  // 关系人
  relatives: [
    {
      relation_id: "rel_001_01",
      relation_type: "配偶",
      name: "001配偶",
      age: 42,
      political_status: "中共党员",
      work_unit_position: "朝阳区三间房乡经管站 八级职员",
    },
    {
      relation_id: "rel_001_02",
      relation_type: "父亲",
      name: "001父亲",
      age: 72,
      political_status: "群众",
      work_unit_position: "江苏省东台市退休",
    },
    {
      relation_id: "rel_001_03",
      relation_type: "母亲",
      name: "001母亲",
      age: 70,
      political_status: "群众",
      work_unit_position: "江苏省东台市退休",
    },
    {
      relation_id: "rel_001_04",
      relation_type: "子女",
      name: "001子女",
      age: 16,
      political_status: "群众",
      work_unit_position: "北京某中学 学生",
    },
  ],

  // 简历 / 任职记录
  resumes: [
    {
      resume_id: "resume_001_01",
      period: "2003.07-2006.04",
      unit: "朝阳区将台地区办事处（乡）",
      department: "办公室",
      position: "科员",
      region: "朝阳区",
      dept: "办公室",
      rank: "科员级",
    },
    {
      resume_id: "resume_001_02",
      period: "2006.04-2007.03",
      unit: "朝阳区将台地区办事处（乡）",
      department: "办公室",
      position: "办公室科员",
      region: "朝阳区",
      dept: "办公室",
      rank: "科员级",
    },
    {
      resume_id: "resume_001_03",
      period: "2007.03-2007.10",
      unit: "朝阳区将台地区工委（乡党委）",
      department: "组织科",
      position: "组织科科员",
      region: "朝阳区",
      dept: "组织科",
      rank: "科员级",
    },
    {
      resume_id: "resume_001_04",
      period: "2007.10-2010.01",
      unit: "朝阳区将台地区工委（乡党委）",
      department: "组织科",
      position: "组织科副科长",
      region: "朝阳区",
      dept: "组织科",
      rank: "副科级",
    },
    {
      resume_id: "resume_001_05",
      period: "2010.01-2014.02",
      unit: "朝阳区太阳宫地区办事处（乡）",
      department: "",
      position: "办事处副主任",
      region: "朝阳区",
      dept: "",
      rank: "副处级",
    },
    {
      resume_id: "resume_001_06",
      period: "2014.02-2016.07",
      unit: "朝阳区太阳宫地区工委",
      department: "",
      position: "副书记",
      region: "朝阳区",
      dept: "",
      rank: "副处级",
    },
    {
      resume_id: "resume_001_07",
      period: "2016.07-2019.03",
      unit: "朝阳区发改委",
      department: "",
      position: "副书记、副主任",
      region: "朝阳区",
      dept: "",
      rank: "副处级",
    },
    {
      resume_id: "resume_001_08",
      period: "2019.03-2022.09",
      unit: "朝阳区发改委",
      department: "",
      position: "副书记、副主任、纪检组组长",
      region: "朝阳区",
      dept: "",
      rank: "副处级",
    },
    {
      resume_id: "resume_001_09",
      period: "2022.09-2025.10",
      unit: "朝阳区南磨房地区工委（乡党委）",
      department: "",
      position: "书记、办事处主任",
      region: "朝阳区",
      dept: "",
      rank: "正处级",
    },
    {
      resume_id: "resume_001_10",
      period: "2025.10-至今",
      unit: "朝阳区发改委",
      department: "",
      position: "党组书记、主任",
      region: "朝阳区",
      dept: "",
      rank: "正处级",
    },
  ],

  // 职务情况
  position_statuses: [
    {
      position_status_id: "ps_001_01",
      current_position: "朝阳区发改委党组书记、主任",
      proposed_position: "",
      proposed_removal: "",
    },
  ],

  // 年度考核
  annual_assessments: [
    { assessment_id: "assess_001_2022", result: "称职", commendation: "" },
    { assessment_id: "assess_001_2023", result: "称职", commendation: "" },
    { assessment_id: "assess_001_2024", result: "优秀", commendation: "嘉奖" },
  ],

  // 能力特征
  abilities: [
    { ability_id: "ab_001_01", time: "2024", ability_trait: "组织协调能力强", source_doc: "换届考察材料" },
    { ability_id: "ab_001_02", time: "2024", ability_trait: "应急处理能力强", source_doc: "换届考察材料" },
    { ability_id: "ab_001_03", time: "2024", ability_trait: "执行力强、善于抓落实", source_doc: "换届考察材料" },
    { ability_id: "ab_001_04", time: "2024", ability_trait: "调查研究能力强", source_doc: "换届考察材料" },
    { ability_id: "ab_001_05", time: "2024", ability_trait: "善于做群众工作", source_doc: "换届考察材料" },
    { ability_id: "ab_001_06", time: "2024", ability_trait: "文字能力强", source_doc: "换届考察材料" },
    { ability_id: "ab_001_07", time: "2024", ability_trait: "领导管理能力强", source_doc: "换届考察材料" },
  ],

  // 标签
  tags: [
    { tag_id: "tag_001_01", style_tag: "政法干部", special_tag: "", issue_tag: "",
      assessment_year: 2024, source_doc: "换届考察材料" },
    { tag_id: "tag_001_02", style_tag: "规划干部", special_tag: "", issue_tag: "",
      assessment_year: 2024, source_doc: "换届考察材料" },
    { tag_id: "tag_001_03", style_tag: "经济干部", special_tag: "", issue_tag: "",
      assessment_year: 2024, source_doc: "换届考察材料" },
  ],

  // 性格特征
  personalities: [
    {
      personality_id: "per_001_01",
      time: "2024",
      trait: "严谨细致、处事果断、性格沉稳",
      source_doc: "大调研",
      shortcoming: "性格偏内敛",
      positive_eval: "作风务实、敢于担当、善于团结同志",
      negative_eval: "主动沟通交流意识需加强",
      issue_tag_1: "",
      issue_tag_2: "",
      time_2: "",
      source_doc_2: "",
    },
  ],

  // 主要不足
  shortcomings: [
    {
      shortcoming_id: "sc_001_01",
      assessment_year: 2024,
      content: "创新意识不够强，面对新经济形态研究不够深入",
      source_doc: "换届考察材料",
    },
    {
      shortcoming_id: "sc_001_02",
      assessment_year: 2024,
      content: "缺少科技、数字化领域工作经验",
      source_doc: "换届考察材料",
    },
  ],

  // 熟悉领域
  familiar_fields: [
    { field_id: "ff_001_01", assessment_year: 2024, field_name: "政法", source_doc: "换届考察材料" },
    { field_id: "ff_001_02", assessment_year: 2024, field_name: "规划建设", source_doc: "换届考察材料" },
    { field_id: "ff_001_03", assessment_year: 2024, field_name: "宏观经济", source_doc: "换届考察材料" },
  ],

  // 奖惩情况
  reward_punishes: [
    {
      reward_punish_id: "rp_001_01",
      seq_no: 1,
      source: "个人述职报告",
      source_doc: "个人述职报告",
      content: "北京市优秀共产党员",
      time: "2022",
      source_2: "",
    },
    {
      reward_punish_id: "rp_001_02",
      seq_no: 2,
      source: "个人述职报告",
      source_doc: "个人述职报告",
      content: "朝阳区优秀领导干部",
      time: "2024",
      source_2: "",
    },
  ],

  // 工作业绩
  performances: [
    {
      performance_id: "perf_001_01",
      content: '推动"两区"建设取得突破',
      source: "述职报告",
      source_doc: "个人述职报告",
      work_experience: "牵头推进国家服务业扩大开放综合示范区建设",
      work_performance: "推动政策落地见效，招商引资工作取得新突破",
      source_doc_2: "换届考察材料",
    },
    {
      performance_id: "perf_001_02",
      content: "谋划产业布局成效显著",
      source: "考察材料",
      source_doc: "换届考察材料",
      work_experience: "推动产业园区升级优化",
      work_performance: "引进多家龙头企业",
      source_doc_2: "换届考察材料",
    },
  ],

  // 能力演变
  ability_evolutions: [
    {
      evolution_id: "evo_001_01",
      time: "2024",
      ability_structure: "从执行型向统筹型转变",
      source_doc_1: "大调研报告原文",
      work_effect: "团队建设、跨部门协调能力显著提升",
      source_doc_2: "大调研报告原文",
      performance_change: "攻坚能力+9%、抓落实能力+14%",
      source_doc_3: "大调研",
    },
  ],
};

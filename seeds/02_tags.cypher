// ============================================================
// seeds/02_tags.cypher
// 标签字典 — 干部画像标签体系
// ============================================================

// ─── 标签维度: 能力特点 ───
UNWIND [
  '视野开阔',
  '开拓创新意识强',
  '决策果断有魄力',
  '战略思维能力强',
  '思路清晰',
  '善于应对复杂局面、解决实际问题',
  '应急处理能力强',
  '调查研究能力强',
  '执行力强、善于抓落实',
  '善于做群众工作',
  '组织协调能力强',
  '领导管理能力强',
  '文字能力强',
  '专家型干部、专业理论功底扎实',
  '专业管理能力强',
  '服务意识强',
  '善于抓班子带队伍',
  '学习能力强、接受新事物快',
  '综合素质好',
  '政策理论水平高',
  '注重思考谋划',
  '适应能力强',
  '虑事周全',
  '抗压能力强',
  '攻坚克难型干部'
] AS name
MERGE (t:TagDict {tag_name: name, tag_dimension: '能力特点'})
SET t.tag_category = '评价标签',
    t.enabled = true;

// ─── 标签维度: 政治素养 ───
UNWIND [
  '对党忠诚',
  '政治敏感性强',
  '严守政治纪律和政治规矩',
  '政治理论素养高',
  '宗旨意识强',
  '信念坚定',
  '大局意识强',
  '组织观念强'
] AS name
MERGE (t:TagDict {tag_name: name, tag_dimension: '政治素养'})
SET t.tag_category = '评价标签',
    t.enabled = true;

// ─── 标签维度: 工作作风 ───
UNWIND [
  '敢于担当',
  '工作有韧性',
  '工作干劲足',
  '作风务实',
  '作风扎实',
  '原则性强',
  '作风硬朗',
  '勤奋敬业',
  '作风民主、善于听取意见',
  '工作标准高'
] AS name
MERGE (t:TagDict {tag_name: name, tag_dimension: '工作作风'})
SET t.tag_category = '评价标签',
    t.enabled = true;

// ─── 标签维度: 个性特征 ───
UNWIND [
  '开朗外向',
  '处事果断',
  '严谨细致',
  '积极乐观',
  '公道正派',
  '待人诚恳',
  '谦虚低调',
  '待人热情',
  '包容大度',
  '待人谦和',
  '性格泼辣',
  '处事老练',
  '性格直率',
  '性格沉稳',
  '善于团结同志',
  '善于合作共事',
  '敢闯敢干',
  '甘于奉献'
] AS name
MERGE (t:TagDict {tag_name: name, tag_dimension: '个性特征'})
SET t.tag_category = '评价标签',
    t.enabled = true;

// ─── 标签维度: 熟悉领域 ───
UNWIND [
  '城市建设', '规划建设', '综合执法与市场监管', '金融',
  '科技创新', '网络安全和信息化', '政策研究', '外事港澳台侨',
  '高精尖产业发展', '水利', '农业农村', '教育',
  '交通运输', '体育', '卫生', '机构编制',
  '重大建设项目管理', '园区管理', '宏观经济', '工业经济',
  '企业经营管理', '商贸流通', '财政税收', '财务审计',
  '安全生产和应急管理', '行政管理', '群众工作', '组织人事',
  '党务', '群团', '纪检监察', '宣传思想意识形态',
  '统战', '自然资源管理', '生态环境保护', '文化旅游',
  '社会建设', '基层社会治理', '政法', '国防军事'
] AS name
MERGE (t:TagDict {tag_name: name, tag_dimension: '熟悉领域'})
SET t.tag_category = '熟悉领域',
    t.enabled = true;

// ─── 标签维度: 风险标签 ───
UNWIND [
  '任职超期提醒',
  '经历单一',
  '廉政风险',
  '审计问题'
] AS name
MERGE (t:TagDict {tag_name: name, tag_dimension: '风险标签'})
SET t.tag_category = '风险标签',
    t.enabled = true;

// ─── 同义标签关系 ───
UNWIND [
  {canonical:'组织协调能力强', variant:'统筹协调能力'},
  {canonical:'组织协调能力强', variant:'协调能力强'},
  {canonical:'组织协调能力强', variant:'善于统筹'},
  {canonical:'严谨细致', variant:'工作细致'},
  {canonical:'严谨细致', variant:'细致认真'},
  {canonical:'应急处理能力强', variant:'应急处置'},
  {canonical:'善于做群众工作', variant:'群众工作能力'},
  {canonical:'作风务实', variant:'求真务实'},
  {canonical:'开拓创新意识强', variant:'改革攻坚能力'},
  {canonical:'执行力强、善于抓落实', variant:'推动工作有力度'}
] AS row
MERGE (ct:TagDict {tag_name: row.canonical, tag_dimension: '能力特点'})
MERGE (vt:TagDict {tag_name: row.variant, tag_dimension: '能力特点'})
MERGE (ct)-[:HAS_SYNONYM]->(vt);

RETURN 'Tags created: ' + count { (t:TagDict) } AS summary;

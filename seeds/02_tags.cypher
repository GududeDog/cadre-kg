// ============================================================
// seeds/02_tags.cypher
// 标签字典 — 来自（参考市委）干部画像标签体系 + 朝阳区补充
// ============================================================

// Community Edition: use uniqueness constraint on single property
CREATE CONSTRAINT tag_name_unique IF NOT EXISTS FOR (n:Tag) REQUIRE (n.tag_name, n.tag_dimension) IS UNIQUE;
CREATE INDEX tag_dim_idx IF NOT EXISTS FOR (n:Tag) ON (n.tag_dimension);
CREATE INDEX tag_category_idx IF NOT EXISTS FOR (n:Tag) ON (n.tag_category);

// ═══════════════════════════════════════════════════════════
// 1. 评价标签 — 能力特点 (25个)
// ═══════════════════════════════════════════════════════════
UNWIND [
  {name:'视野开阔', alias:[]},
  {name:'开拓创新意识强', alias:['改革攻坚能力']},
  {name:'决策果断有魄力', alias:[]},
  {name:'战略思维能力强', alias:[]},
  {name:'思路清晰', alias:[]},
  {name:'善于应对复杂局面、解决实际问题', alias:[]},
  {name:'应急处理能力强', alias:[]},
  {name:'调查研究能力强', alias:[]},
  {name:'执行力强、善于抓落实', alias:['推动工作有力度']},
  {name:'善于做群众工作', alias:[]},
  {name:'组织协调能力强', alias:['统筹协调能力','协调能力强','善于统筹','统筹兼顾']},
  {name:'领导管理能力强', alias:['统筹驾驭能力']},
  {name:'文字能力强', alias:[]},
  {name:'专家型干部、专业理论功底扎实', alias:[]},
  {name:'专业管理能力强', alias:[]},
  {name:'服务意识强', alias:[]},
  {name:'善于抓班子带队伍', alias:[]},
  {name:'学习能力强、接受新事物快', alias:[]},
  {name:'综合素质好', alias:[]},
  {name:'政策理论水平高', alias:[]},
  {name:'注重思考谋划', alias:[]},
  {name:'适应能力强', alias:[]},
  {name:'虑事周全', alias:[]},
  {name:'抗压能力强', alias:[]},
  {name:'攻坚克难型干部', alias:[]}
] AS row
MERGE (t:Tag {tag_name: row.name, tag_dimension: '能力特点'})
SET t.tag_category = '评价标签',
    t.tag_domain = '干部标签',
    t.aliases = row.alias,
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 2. 评价标签 — 政治素养 (8个)
// ═══════════════════════════════════════════════════════════
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
MERGE (t:Tag {tag_name: name, tag_dimension: '政治素养'})
SET t.tag_category = '评价标签',
    t.tag_domain = '干部标签',
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 3. 评价标签 — 工作作风 (10个)
// ═══════════════════════════════════════════════════════════
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
MERGE (t:Tag {tag_name: name, tag_dimension: '工作作风'})
SET t.tag_category = '评价标签',
    t.tag_domain = '干部标签',
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 4. 评价标签 — 个性特征 (18个)
// ═══════════════════════════════════════════════════════════
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
MERGE (t:Tag {tag_name: name, tag_dimension: '个性特征'})
SET t.tag_category = '评价标签',
    t.tag_domain = '干部标签',
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 5. 熟悉领域 (~52个)
// ═══════════════════════════════════════════════════════════
UNWIND [
  {name:'城市建设', sub:['招商引资']},
  {name:'规划建设', sub:['党的建设','住房建筑','统计分析']},
  {name:'综合执法与市场监管', sub:[]},
  {name:'金融', sub:[]},
  {name:'科技创新', sub:['科技成果转化']},
  {name:'网络安全和信息化', sub:[]},
  {name:'政策研究', sub:[]},
  {name:'外事港澳台侨', sub:['国际交往']},
  {name:'高精尖产业发展', sub:[]},
  {name:'水利', sub:[]},
  {name:'农业农村', sub:[]},
  {name:'教育', sub:[]},
  {name:'交通运输', sub:[]},
  {name:'体育', sub:[]},
  {name:'卫生', sub:[]},
  {name:'机构编制', sub:[]},
  {name:'重大建设项目管理', sub:[]},
  {name:'园区管理', sub:[]},
  {name:'宏观经济', sub:['发改','财政']},
  {name:'工业经济', sub:[]},
  {name:'企业经营管理', sub:[]},
  {name:'商贸流通', sub:[]},
  {name:'财政税收', sub:[]},
  {name:'财务审计', sub:['国有资产监督管理','国企改革']},
  {name:'安全生产和应急管理', sub:[]},
  {name:'行政管理', sub:['公共服务','后勤管理']},
  {name:'群众工作', sub:['社会管理']},
  {name:'组织人事', sub:[]},
  {name:'党务', sub:[]},
  {name:'群团', sub:['工会','团委','妇联']},
  {name:'纪检监察', sub:[]},
  {name:'宣传思想意识形态', sub:['新闻出版']},
  {name:'统战', sub:['民族宗教']},
  {name:'自然资源管理', sub:[]},
  {name:'生态环境保护', sub:[]},
  {name:'文化旅游', sub:['文物保护']},
  {name:'社会建设', sub:[]},
  {name:'基层社会治理', sub:[]},
  {name:'政法', sub:['法检','公安']},
  {name:'国防军事', sub:['武装','人防']},
  {name:'企业生产运行', sub:[]},
  {name:'企业市场营销', sub:[]},
  {name:'企业财务管理', sub:[]},
  {name:'企业专业技术', sub:[]},
  {name:'企业国际业务', sub:[]}
] AS row
MERGE (t:Tag {tag_name: row.name, tag_dimension: '熟悉领域'})
SET t.tag_category = '熟悉领域',
    t.tag_domain = '干部标签',
    t.sub_domains = row.sub,
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 6. 重要经历 — 困难艰苦地区工作经历 (8个)
// ═══════════════════════════════════════════════════════════
UNWIND [
  {name:'援疆', subcat:'困难艰苦地区工作经历'},
  {name:'援藏', subcat:'困难艰苦地区工作经历'},
  {name:'援青', subcat:'困难艰苦地区工作经历'},
  {name:'援蒙', subcat:'困难艰苦地区工作经历'},
  {name:'贫困地区工作经历', subcat:'困难艰苦地区工作经历'},
  {name:'西部地区、老工业基地和革命老区', subcat:'困难艰苦地区工作经历'},
  {name:'赣南中央苏区', subcat:'困难艰苦地区工作经历'},
  {name:'其他困难艰苦地区工作经历', subcat:'困难艰苦地区工作经历'}
] AS row
MERGE (t:Tag {tag_name: row.name, tag_dimension: '重要经历'})
SET t.tag_category = '重要经历',
    t.tag_domain = '干部标签',
    t.sub_category = row.subcat,
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 7. 重要经历 — 两代表一委员 (5个)
// ═══════════════════════════════════════════════════════════
UNWIND [
  '党的全国代表大会代表',
  '全国人大代表',
  '全国人大专门委员会委员',
  '全国政协委员',
  '全国政协各专门委员会副主任'
] AS name
MERGE (t:Tag {tag_name: name, tag_dimension: '重要经历'})
SET t.tag_category = '重要经历',
    t.tag_domain = '干部标签',
    t.sub_category = '两代表一委员',
    t.enabled = false;  // 朝阳区适用性低，默认禁用

// ═══════════════════════════════════════════════════════════
// 8. 重要经历 — 法律/秘书/开发区/挂职/任职/重点工作 (40个)
// ═══════════════════════════════════════════════════════════
UNWIND [
  {name:'从事法律工作五年及以上', subcat:'法律工作经历', enabled:true},
  {name:'秘书', subcat:'秘书经历', enabled:true},
  {name:'国家级开发区、高新区、自贸区', subcat:'开发区经历', enabled:true},
  {name:'省级开发区、高新区、自贸区', subcat:'开发区经历', enabled:true},
  {name:'中央企业挂职', subcat:'挂职经历', enabled:true},
  {name:'中央单位挂职', subcat:'挂职经历', enabled:true},
  {name:'外省市挂职', subcat:'挂职经历', enabled:true},
  {name:'中央单位借调', subcat:'挂职经历', enabled:true},
  {name:'中央企业任职', subcat:'任职经历', enabled:true},
  {name:'中央单位任职', subcat:'任职经历', enabled:true},
  {name:'外省市任职', subcat:'任职经历', enabled:true},
  {name:'金融企业任职', subcat:'任职经历', enabled:true},
  {name:'中组部双向交流任职干部', subcat:'其他经历', enabled:true},
  {name:'中组部双向交流挂职干部', subcat:'其他经历', enabled:true},
  {name:'两年及以上基层工作经历', subcat:'其他经历', enabled:true},
  {name:'公开选拔', subcat:'其他经历', enabled:true},
  {name:'选调生', subcat:'其他经历', enabled:true},
  {name:'街乡经历', subcat:'朝阳补充', enabled:true},
  {name:'非本区经历', subcat:'朝阳补充', enabled:true},
  {name:'街乡基层副职领导经历', subcat:'朝阳补充', enabled:true}
] AS row
MERGE (t:Tag {tag_name: row.name, tag_dimension: '重要经历'})
SET t.tag_category = '重要经历',
    t.tag_domain = '干部标签',
    t.sub_category = row.subcat,
    t.enabled = row.enabled;

// ═══════════════════════════════════════════════════════════
// 9. 重要经历 — 重点工作（北京市特色）(14个)
// ═══════════════════════════════════════════════════════════
UNWIND [
  '奥运会',
  '一带一路高峰论坛',
  '中非合作论坛',
  'APEC会议',
  '世园会',
  '环球影城建设',
  '天安门阅兵',
  '主题教育',
  '征地拆迁',
  '疏整促',
  '回天行动',
  '12345热线',
  '北京城市建设总体规划',
  '副中心建设'
] AS name
MERGE (t:Tag {tag_name: name, tag_dimension: '重要经历'})
SET t.tag_category = '重要经历',
    t.tag_domain = '干部标签',
    t.sub_category = '重点工作',
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 10. 重要职务 — 朝阳区适用关键职务 (10个)
// ═══════════════════════════════════════════════════════════
UNWIND [
  {name:'街乡党政正职', subcat:'街乡职务', level:'正处级'},
  {name:'街乡党政副职', subcat:'街乡职务', level:'副处级'},
  {name:'委办局正职', subcat:'委办局职务', level:'正处级'},
  {name:'委办局副职', subcat:'委办局职务', level:'副处级'},
  {name:'街乡副书记', subcat:'关键岗位', level:'副处级'},
  {name:'大办副主任', subcat:'关键岗位', level:'正科级'},
  {name:'重点科室科长', subcat:'关键岗位', level:'正科级'},
  {name:'县处级正职领导职务', subcat:'职务层级', level:'正处级'},
  {name:'县处级党政副职', subcat:'职务层级', level:'副处级'},
  {name:'乡镇（街道）党政正职', subcat:'职务层级', level:'正处级'}
] AS row
MERGE (t:Tag {tag_name: row.name, tag_dimension: '重要职务'})
SET t.tag_category = '重要职务',
    t.tag_domain = '干部标签',
    t.sub_category = row.subcat,
    t.position_level = row.level,
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 11. 其他标签 — 特殊情况 (8个)
// ═══════════════════════════════════════════════════════════
UNWIND [
  '优秀年轻干部',
  '选调生',
  '越级提拔',
  '破格提拔',
  '归国侨眷',
  '本地成长的干部',
  '本单位成长的干部',
  '重大疾病'
] AS name
MERGE (t:Tag {tag_name: name, tag_dimension: '特殊情况'})
SET t.tag_category = '特殊标签',
    t.tag_domain = '干部标签',
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 12. 其他标签 — 专业背景 (4个)
// ═══════════════════════════════════════════════════════════
UNWIND [
  '双一流高校',
  '双一流学科',
  '985',
  '211'
] AS name
MERGE (t:Tag {tag_name: name, tag_dimension: '专业背景'})
SET t.tag_category = '特殊标签',
    t.tag_domain = '干部标签',
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 13. 其他标签 — 重大奖励
// ═══════════════════════════════════════════════════════════
MERGE (t:Tag {tag_name: '重大奖励', tag_dimension: '重大奖励'})
SET t.tag_category = '特殊标签',
    t.tag_domain = '干部标签',
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 14. 风险标签 (4个) — 朝阳区补充
// ═══════════════════════════════════════════════════════════
UNWIND [
  '任职超期提醒',
  '经历单一',
  '廉政风险',
  '审计问题'
] AS name
MERGE (t:Tag {tag_name: name, tag_dimension: '风险标签'})
SET t.tag_category = '风险标签',
    t.tag_domain = '干部标签',
    t.enabled = true;

// ═══════════════════════════════════════════════════════════
// 15. 同义标签关系
// ═══════════════════════════════════════════════════════════
UNWIND [
  {canonical:'组织协调能力强', variant:'统筹协调能力'},
  {canonical:'组织协调能力强', variant:'协调能力强'},
  {canonical:'组织协调能力强', variant:'善于统筹'},
  {canonical:'组织协调能力强', variant:'统筹兼顾'},
  {canonical:'严谨细致', variant:'工作细致'},
  {canonical:'严谨细致', variant:'细致认真'},
  {canonical:'严谨细致', variant:'一丝不苟'},
  {canonical:'应急处理能力强', variant:'应急处置'},
  {canonical:'应急处理能力强', variant:'处理复杂问题'},
  {canonical:'善于做群众工作', variant:'群众工作能力'},
  {canonical:'善于做群众工作', variant:'善于做群众工作'},
  {canonical:'善于做群众工作', variant:'服务群众'},
  {canonical:'作风务实', variant:'求真务实'},
  {canonical:'作风务实', variant:'讲实话办实事'},
  {canonical:'作风务实', variant:'实干'},
  {canonical:'开拓创新意识强', variant:'改革攻坚能力'},
  {canonical:'执行力强、善于抓落实', variant:'推动工作有力度'},
  {canonical:'领导管理能力强', variant:'统筹驾驭能力'}
] AS row
MERGE (ct:Tag {tag_name: row.canonical, tag_dimension: '能力特点'})
MERGE (vt:Tag {tag_name: row.variant, tag_dimension: '能力特点'})
MERGE (ct)-[:HAS_SYNONYM]->(vt);

RETURN 'Tags created: ' +
       count { (t:Tag {tag_domain:'干部标签'}) } + ' cadre tags' AS summary;

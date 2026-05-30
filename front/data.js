// ═══════════════════════════════════════════════════════════
// data.js — 干部画像 Mock 数据
// 后续对接 FastAPI 时替换为 API 调用即可
// ═══════════════════════════════════════════════════════════

const MOCK_DATA = {
  cadre_id: "001",
  name: "001",
  gender: "男",
  ethnicity: "汉族",
  birth_date: "1981.10",
  age: 44,
  political_status: "中共党员",
  party_join_date: "2006.06",
  work_start_date: "2003.07",
  native_place: "江苏盐城",
  health_status: "健康",
  highest_education: "研究生",
  highest_degree: "管理学硕士",
  highest_school: "中央党校",
  current_position: "朝阳区发改委党组书记、主任",
  current_level: "正处级",
  current_rank: "一级调研员",
  current_start_date: "2025.10",
  current_unit: "朝阳区发改委",
  current_division: "主持全面工作，分管办公室、综合科",
  division_departments: ["办公室", "综合科"],

  career_history: [
    {start:"2003.07",end:"2006.04",unit:"朝阳区将台地区办事处（乡）",position:"科员",level:"科员级",is_current:false},
    {start:"2006.04",end:"2007.03",unit:"朝阳区将台地区办事处（乡）",position:"办公室科员",level:"科员级",is_current:false},
    {start:"2007.03",end:"2007.10",unit:"朝阳区将台地区工委（乡党委）",position:"组织科科员",level:"科员级",is_current:false},
    {start:"2007.10",end:"2010.01",unit:"朝阳区将台地区工委（乡党委）",position:"组织科副科长",level:"副科级",is_current:false},
    {start:"2010.01",end:"2011.05",unit:"朝阳区太阳宫地区办事处（乡）",position:"办事处副主任",level:"副处级",is_current:false},
    {start:"2011.05",end:"2014.02",unit:"朝阳区太阳宫地区办事处（乡）",position:"办事处副主任",level:"副处级",is_current:false},
    {start:"2014.02",end:"2016.07",unit:"朝阳区太阳宫地区工委",position:"副书记",level:"副处级",is_current:false},
    {start:"2016.07",end:"2019.03",unit:"朝阳区发改委",position:"副书记、副主任",level:"副处级",is_current:false},
    {start:"2019.03",end:"2019.11",unit:"朝阳区发改委",position:"副书记、副主任",level:"副处级",is_current:false},
    {start:"2019.11",end:"2022.09",unit:"朝阳区发改委",position:"副书记、副主任、纪检组组长",level:"副处级",is_current:false},
    {start:"2022.09",end:"2025.10",unit:"朝阳区南磨房地区工委（乡党委）",position:"书记、办事处主任",level:"正处级",is_current:false},
    {start:"2025.10",end:"至今",unit:"朝阳区发改委",position:"党组书记、主任",level:"正处级",is_current:true},
  ],

  education_detail: [
    {type:"全日制",school:"中国政法大学",major:"法学专业",degree:"法学学士",level:"大学",period:"1999-2003"},
    {type:"在职",school:"中央党校研究生院",major:"马克思主义哲学专业",degree:"硕士",level:"研究生",period:"2012-2015"}
  ],

  family_members: [
    {relation:"配偶",name:"001配偶",work_unit:"朝阳区三间房乡经管站",political_status:"中共党员",position:"八级职员"},
    {relation:"父亲",name:"001父亲",work_unit:"江苏省东台市退休",political_status:"群众",position:"退休"},
    {relation:"母亲",name:"001母亲",work_unit:"江苏省东台市退休",political_status:"群众",position:"退休"},
    {relation:"子女",name:"001子女",work_unit:"北京某中学",political_status:"群众",position:"学生"},
  ],

  familiar_fields: ["政法","规划建设","经济"],
  professional_labels: ["政法干部","规划干部"],
  economic_cadre_tag: false,
  party_affairs_cadre_tag: false,
  political_legal_cadre_tag: true,
  urban_construction_cadre_tag: true,

  ability_tags: [
    {tag:"组织协调能力强",category:"能力特点",confidence:0.9,hot:true},
    {tag:"应急处理能力强",category:"能力特点",confidence:0.85,hot:true},
    {tag:"执行力强，善于抓落实",category:"能力特点",confidence:0.88,hot:true},
    {tag:"统筹驾驭能力强",category:"能力特点",confidence:0.82},
    {tag:"注重思考谋划",category:"能力特点",confidence:0.78},
    {tag:"调查研究能力强",category:"能力特点",confidence:0.8},
    {tag:"善于做群众工作",category:"能力特点",confidence:0.85},
    {tag:"文字能力强",category:"能力特点",confidence:0.75},
    {tag:"对党忠诚",category:"政治素养",confidence:0.95,hot:true},
    {tag:"政治敏感性强",category:"政治素养",confidence:0.9},
    {tag:"大局意识强",category:"政治素养",confidence:0.88},
    {tag:"严守政治纪律",category:"政治素养",confidence:0.92},
    {tag:"敢于担当",category:"工作作风",confidence:0.9,hot:true},
    {tag:"作风务实",category:"工作作风",confidence:0.92,hot:true},
    {tag:"工作有韧性",category:"工作作风",confidence:0.85},
    {tag:"原则性强",category:"工作作风",confidence:0.82},
    {tag:"勤奋敬业",category:"工作作风",confidence:0.88},
    {tag:"严谨细致",category:"个性特征",confidence:0.85},
    {tag:"处事果断",category:"个性特征",confidence:0.82},
    {tag:"性格沉稳",category:"个性特征",confidence:0.78},
    {tag:"善于团结同志",category:"个性特征",confidence:0.85},
    {tag:"公道正派",category:"个性特征",confidence:0.88},
  ],

  radar_scores: {
    "素质基础": 92,
    "胜任能力": 88,
    "工作绩效": 85,
    "自画像": 78,
    "负面信息": 95
  },

  main_shortcomings: [
    {type:"能力类",text:"创新意识不够强，面对新经济形态研究不够深入"},
    {type:"经验类",text:"缺少科技、数字化领域工作经验"},
    {type:"性格类",text:"性格偏内敛，主动沟通交流意识需加强"},
  ],

  work_performances: [
    {title:"推动"两区"建设取得突破",desc:"牵头推进国家服务业扩大开放综合示范区建设，推动政策落地见效",level:"突出",source:"述职报告"},
    {title:"谋划产业布局成效显著",desc:"推动产业园区升级优化，引进多家龙头企业，招商引资工作取得新突破",level:"良好",source:"考察材料"},
    {title:"深化基层治理创新",desc:"推进社区治理数字化转型，建设智慧社区平台，基层治理水平显著提升",level:"突出",source:"述职报告"},
  ],

  structural_tags: [
    {tag:"经济干部",icon:"📊"},
    {tag:"规划干部",icon:"📐"},
    {tag:"政法干部",icon:"⚖️"},
    {tag:"街乡书记经历",icon:"🏘️"},
    {tag:"正处级关键岗位",icon:"⭐"},
    {tag:"一把手",icon:"👔"},
    {tag:"副处级后备干部",icon:"📋"},
  ],

  supervision: [
    {label:"审计审计情况",status:"无",type:"ok"},
    {label:"纪检监察情况",status:"无",type:"ok"},
    {label:"信访举报情况",status:"无",type:"ok"},
    {label:"经济责任审计结果",status:"无",type:"ok"},
    {label:"越级提拔情况",status:"无",type:"ok"},
  ],

  career_trajectory: [
    {year:"2003",phase:"科级以下",label:"单点执行",desc:"街道科员，基层工作"},
    {year:"2007",phase:"副科级",label:"组织协调",desc:"组织科副科长"},
    {year:"2010",phase:"副处级",label:"街乡副职",desc:"太阳宫副主任"},
    {year:"2014",phase:"副处级",label:"街乡正职",desc:"太阳宫副书记"},
    {year:"2016",phase:"副处级",label:"委办局副职",desc:"发改委副主任"},
    {year:"2022",phase:"正处级",label:"街乡正职",desc:"南磨房书记"},
    {year:"2025",phase:"正处级",label:"委办局正职",desc:"发改委主任"},
  ],

  relations: [
    {name:"李建国",type:"同事",position:"朝阳区发改委副主任",distance:"center"},
    {name:"王芳",type:"配偶",work_unit:"三间房乡经管站"},
    {name:"张强",type:"校友",school:"中国政法大学"},
    {name:"刘洋",type:"同事",position:"太阳宫地区工委"},
    {name:"赵明",type:"上级",position:"区委组织部部长"},
  ],

  growth_traits: [
    {title:"从执行型向统筹型转变",desc:"经历基层→中层→主政三个关键跃升",tags:["执行力强→统筹协调→战略规划"]},
    {title:"作风演变",desc:"雷厉风行→务实稳健→创新突破，逐步形成复合型领导风格"},
  ],
  待突破瓶颈: "战略谋划和数字化转型能力仍需加强",
  风格变化趋势: "雷厉风行→务实稳健→创新突破",

  awards: [
    {year:2022,name:"北京市优秀共产党员",level:"省部级"},
    {year:2024,name:"朝阳区优秀领导干部",level:"区级"},
  ],

  annual_assessment: [
    {year:2022,result:"称职"},
    {year:2023,result:"称职"},
    {year:2024,result:"称职"},
  ],
};

const MOCK_EVENTS = [
  {year:"2018",desc:"朝阳区"疏整促"专项行动"},
  {year:"2020",desc:"疫情防控一线"},
  {year:"2022",desc:"南磨房乡社区治理创新"},
  {year:"2024",desc:"发改委两区建设推进"},
];

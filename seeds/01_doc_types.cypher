// ============================================================
// seeds/01_doc_types.cypher
// 文档类型定义 — 用于文档识别器的分类规则
// 用法: cypher-shell -u neo4j -p xxx -f 01_doc_types.cypher
// ============================================================

// ─── 索引 ───
CREATE CONSTRAINT doc_type_id IF NOT EXISTS FOR (n:DocType) REQUIRE n.doc_type IS UNIQUE;

// ─── 文档类型节点 ───
// 优先级: A=直接可用 B=需LLM辅助 C=流程文件 D=降级兜底

MERGE (dt1:DocType {doc_type: 'cadre_appointment_form'})
SET dt1.display_name = '干部任免表',
    dt1.priority = 'A',
    dt1.path_keywords = ['任免表', '干部任免'],
    dt1.title_keywords = ['干部任免审批表'],
    dt1.table_headers = ['姓名', '性别', '出生年月', '民族', '籍贯', '现任职务', '简历'],
    dt1.structure_rules = '{table_count_min:1, paragraph_count_max:20, cell_count_min:50}',
    dt1.ext = ['.doc', '.docx'];

MERGE (dt2:DocType {doc_type: 'annual_report'})
SET dt2.display_name = '述职报告',
    dt2.priority = 'A',
    dt2.path_keywords = ['述职报告', '述职述廉', '述德述廉', '述党建'],
    dt2.title_keywords = ['个人述职报告', '述职述廉报告'],
    dt2.body_keywords = ['履职情况', '党风廉政', '存在问题', '下一步工作'],
    dt2.structure_rules = '{paragraph_count_min:10, table_count_max:2, has_numbered_sections:true}',
    dt2.ext = ['.doc', '.docx'];

MERGE (dt3:DocType {doc_type: 'assessment_material'})
SET dt3.display_name = '考察材料',
    dt3.priority = 'A',
    dt3.path_keywords = ['考察材料', '考察'],
    dt3.title_keywords = ['同志考察材料', '考察材料'],
    dt3.body_keywords = ['政治素质', '民主测评', '纪检监察', '主要不足'],
    dt3.structure_rules = '{paragraph_count_min:5, table_count_max:1}',
    dt3.ext = ['.doc', '.docx'];

MERGE (dt4:DocType {doc_type: 'performance_material'})
SET dt4.display_name = '现实表现材料',
    dt4.priority = 'B',
    dt4.path_keywords = ['现实表现'],
    dt4.title_keywords = ['现实表现材料'],
    dt4.body_keywords = ['政治素质表现', '工作能力', '工作作风', '主要不足'],
    dt4.structure_rules = '{paragraph_count_min:5, table_count_max:1}',
    dt4.ext = ['.doc', '.docx'];

MERGE (dt5:DocType {doc_type: 'democratic_evaluation'})
SET dt5.display_name = '民主测评',
    dt5.priority = 'A',
    dt5.path_keywords = ['民主测评'],
    dt5.title_keywords = ['民主测评汇总表', '测评结果'],
    dt5.table_headers = ['优秀', '称职', '基本称职', '不称职'],
    dt5.structure_rules = '{table_count_min:1, has_evaluation_columns:true}',
    dt5.ext = ['.doc', '.docx', '.xls', '.xlsx'];

MERGE (dt6:DocType {doc_type: 'division_record'})
SET dt6.display_name = '领导班子分工备案表',
    dt6.priority = 'A',
    dt6.path_keywords = ['分工备案', '班子分工'],
    dt6.title_keywords = ['领导班子分工', '备案报告'],
    dt6.body_keywords = ['调整原因', '班子成员', '分管工作'],
    dt6.structure_rules = '{table_count_min:1, has_attachment_xlsx:true}',
    dt6.ext = ['.doc', '.docx'];

MERGE (dt7:DocType {doc_type: 'typical_events'})
SET dt7.display_name = '三件典型事件',
    dt7.priority = 'A',
    dt7.path_keywords = ['典型事件', '典型事例'],
    dt7.title_keywords = ['三件典型事件', '典型事例'],
    dt7.body_keywords = ['一、', '二、', '三、', '名词解释'],
    dt7.structure_rules = '{paragraph_count_min:5, has_numbered_sections:true}',
    dt7.ext = ['.doc', '.docx'];

MERGE (dt8:DocType {doc_type: 'inspection_register'})
SET dt8.display_name = '考察情况登记表',
    dt8.priority = 'A',
    dt8.path_keywords = ['考察情况登记表'],
    dt8.title_keywords = ['考察情况登记表'],
    dt8.table_headers = ['考察日期', '考察单位', '主要优点', '主要不足'],
    dt8.structure_rules = '{table_count_min:1}',
    dt8.ext = ['.doc', '.docx'];

MERGE (dt9:DocType {doc_type: 'cadre_review_form'})
SET dt9.display_name = '干部基本信息审核表',
    dt9.priority = 'B',
    dt9.path_keywords = ['基本信息审核表'],
    dt9.title_keywords = ['干部基本信息审核表'],
    dt9.table_headers = ['三龄两历一身份'],
    dt9.structure_rules = '{table_count_min:1}',
    dt9.ext = ['.doc', '.docx'];

MERGE (dt10:DocType {doc_type: 'public_notice'})
SET dt10.display_name = '任前公示',
    dt10.priority = 'B',
    dt10.path_keywords = ['任前公示', '公示'],
    dt10.title_keywords = ['任前公示'],
    dt10.structure_rules = '{paragraph_count_max:10}',
    dt10.ext = ['.doc', '.docx'];

MERGE (dt11:DocType {doc_type: 'performance_case'})
SET dt11.display_name = '工作业绩事例',
    dt11.priority = 'B',
    dt11.path_keywords = ['工作业绩', '业绩事例'],
    dt11.title_keywords = ['近三年工作业绩'],
    dt11.body_keywords = ['背景', '做法', '成效'],
    dt11.structure_rules = '{paragraph_count_min:5}',
    dt11.ext = ['.doc', '.docx'];

MERGE (dt12:DocType {doc_type: 'inspection_plan'})
SET dt12.display_name = '考察工作方案',
    dt12.priority = 'C',
    dt12.path_keywords = ['考察工作方案', '工作方案'],
    dt12.title_keywords = ['考察工作方案'],
    dt12.structure_rules = '{}',
    dt12.ext = ['.doc', '.docx'];

MERGE (dt13:DocType {doc_type: 'evaluation_team'})
SET dt13.display_name = '领导班子民主测评',
    dt13.priority = 'A',
    dt13.path_keywords = ['领导班子民主测评'],
    dt13.title_keywords = ['领导班子民主测评'],
    dt13.table_headers = ['班子评价'],
    dt13.structure_rules = '{table_count_min:1}',
    dt13.ext = ['.doc', '.docx', '.xls', '.xlsx'];

MERGE (dt14:DocType {doc_type: 'evaluation_summary'})
SET dt14.display_name = '民主测评汇总表',
    dt14.priority = 'B',
    dt14.path_keywords = ['民主测评汇总'],
    dt14.title_keywords = ['民主测评汇总表'],
    dt14.table_headers = ['姓名', '优秀', '称职'],
    dt14.structure_rules = '{table_count_min:1, row_count_min:5}',
    dt14.ext = ['.xls', '.xlsx'];

MERGE (dt15:DocType {doc_type: 'cadre_roster'})
SET dt15.display_name = '干部名册/花名册',
    dt15.priority = 'B',
    dt15.path_keywords = ['干部名册', '花名册', '干部信息'],
    dt15.table_headers = ['姓名', '性别', '出生年月', '单位', '职务'],
    dt15.structure_rules = '{row_count_min:20}',
    dt15.ext = ['.xls', '.xlsx'];

MERGE (dt16:DocType {doc_type: 'unknown'})
SET dt16.display_name = '未知类型',
    dt16.priority = 'D',
    dt16.structure_rules = '{}',
    dt16.ext = [];

RETURN count { (n:DocType) } AS doc_type_count;

// ============================================================
// seeds/01_schema.cypher
// 图数据库约束和索引定义
// ============================================================

// ─── Cadre 约束 ───
CREATE CONSTRAINT cadre_cadre_id IF NOT EXISTS FOR (n:Cadre) REQUIRE n.cadre_id IS UNIQUE;
CREATE INDEX idx_cadre_name IF NOT EXISTS FOR (n:Cadre) ON (n.name);

// ─── Position 约束 ───
CREATE CONSTRAINT position_id IF NOT EXISTS FOR (n:Position) REQUIRE n.position_id IS UNIQUE;

// ─── Resume 约束 ───
CREATE CONSTRAINT resume_id IF NOT EXISTS FOR (n:Resume) REQUIRE n.resume_id IS UNIQUE;

// ─── Education 约束 ───
CREATE CONSTRAINT edu_id IF NOT EXISTS FOR (n:Education) REQUIRE n.edu_id IS UNIQUE;

// ─── Relation 约束 ───
CREATE CONSTRAINT relation_id IF NOT EXISTS FOR (n:Relation) REQUIRE n.relation_id IS UNIQUE;

// ─── RewardPunish 约束 ───
CREATE CONSTRAINT reward_punish_id IF NOT EXISTS FOR (n:RewardPunish) REQUIRE n.reward_punish_id IS UNIQUE;

// ─── Performance 约束 ───
CREATE CONSTRAINT performance_id IF NOT EXISTS FOR (n:Performance) REQUIRE n.performance_id IS UNIQUE;

// ─── Evaluation 约束 ───
CREATE CONSTRAINT evaluation_id IF NOT EXISTS FOR (n:Evaluation) REQUIRE n.evaluation_id IS UNIQUE;

// ─── Shortcoming 约束 ───
CREATE CONSTRAINT shortcoming_id IF NOT EXISTS FOR (n:Shortcoming) REQUIRE n.shortcoming_id IS UNIQUE;

// ─── Personality 约束 ───
CREATE CONSTRAINT personality_id IF NOT EXISTS FOR (n:Personality) REQUIRE n.personality_id IS UNIQUE;

// ─── Ability 约束 ───
CREATE CONSTRAINT ability_id IF NOT EXISTS FOR (n:Ability) REQUIRE n.ability_id IS UNIQUE;

// ─── FamiliarField 约束 ───
CREATE CONSTRAINT field_id IF NOT EXISTS FOR (n:FamiliarField) REQUIRE n.field_id IS UNIQUE;

// ─── Tag 约束 ───
CREATE CONSTRAINT tag_id IF NOT EXISTS FOR (n:Tag) REQUIRE n.tag_id IS UNIQUE;

// ─── WritingStyle 约束 ───
CREATE CONSTRAINT writing_id IF NOT EXISTS FOR (n:WritingStyle) REQUIRE n.writing_id IS UNIQUE;

// ─── AnnualAssessment 约束 ───
CREATE CONSTRAINT annual_assessment_id IF NOT EXISTS FOR (n:AnnualAssessment) REQUIRE n.assessment_id IS UNIQUE;

// ─── Profile 约束 ───
CREATE CONSTRAINT profile_id IF NOT EXISTS FOR (n:Profile) REQUIRE n.profile_id IS UNIQUE;

// ─── PositionStatus 约束 ───
CREATE CONSTRAINT position_status_id IF NOT EXISTS FOR (n:PositionStatus) REQUIRE n.position_status_id IS UNIQUE;

// ─── Division 约束 ───
CREATE CONSTRAINT division_id IF NOT EXISTS FOR (n:Division) REQUIRE n.division_id IS UNIQUE;

// ─── AbilityEvolution 约束 ───
CREATE CONSTRAINT evolution_id IF NOT EXISTS FOR (n:AbilityEvolution) REQUIRE n.evolution_id IS UNIQUE;

// ─── ExcellenceIndicator 约束 ───
CREATE CONSTRAINT indicator_id IF NOT EXISTS FOR (n:ExcellenceIndicator) REQUIRE n.indicator_id IS UNIQUE;

RETURN 'Schema constraints created successfully' AS status;

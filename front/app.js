// ═══════════════════════════════════════════════════════════
// app.js — 干部画像前端主逻辑
// 对接 FastAPI 时将 MOCK_DATA 替换为 fetch 调用即可
// ═══════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("updateDate").textContent =
    "数据更新时间: " + new Date().toLocaleDateString("zh-CN");
  renderCadre(MOCK_DATA);
});

function searchCadre() {
  const v = document.getElementById("searchInput").value.trim();
  if (v) renderCadre(MOCK_DATA); // 后续替换为 fetch(`/api/cadre/${v}`)
}

function renderCadre(d) {
  const app = document.getElementById("app");
  app.innerHTML = `
    ${heroSection(d)}
    ${aiSection(d)}
    ${basicInfoSection(d)}
    ${careerSection(d)}
    ${abilitySection(d)}
    ${achievementSection(d)}
    ${structuralSection(d)}
    ${supervisionSection(d)}
    ${relationSection(d)}
    ${growthSection(d)}
    ${directionSection(d)}
  `;
  // 渲染图表
  setTimeout(() => {
    ChartUtils.drawRadar(document.getElementById("radarCanvas"), d.radar_scores);
    ChartUtils.drawRelationGraph(
      document.getElementById("relationCanvas"),
      d.name,
      d.relations
    );
  }, 100);
}

// ─── 各区块渲染函数 ───

function heroSection(d) {
  return `
  <div class="hero">
    <div class="hero-avatar">${d.name}</div>
    <div class="hero-info">
      <div class="hero-name">${d.name} <span class="hero-badge">${d.current_level}</span></div>
      <div class="hero-subtitle">${d.current_position}</div>
      <div class="hero-tags">
        <span class="hero-tag">👤 ${d.gender}</span>
        <span class="hero-tag">📅 ${d.birth_date}（${d.age}岁）</span>
        <span class="hero-tag">🏛️ ${d.current_unit}</span>
        <span class="hero-tag">⭐ ${d.current_level}（${d.career_history.length}段经历）</span>
      </div>
      <div class="hero-stats">
        <div class="hero-stat"><div class="hero-stat-val">6年</div><div class="hero-stat-label">正处级</div></div>
        <div class="hero-stat"><div class="hero-stat-val">${d.career_history.length}个</div><div class="hero-stat-label">历任岗位</div></div>
        <div class="hero-stat"><div class="hero-stat-val">7年</div><div class="hero-stat-label">街乡经历</div></div>
      </div>
    </div>
  </div>`;
}

function aiSection(d) {
  return `
  <div class="section">
    <div class="section-title">🤖 AI 智能研判</div>
    <div style="background:var(--primary-bg);padding:16px;border-radius:8px;font-size:13px;line-height:1.8;color:var(--text)">
      <strong>综合研判：</strong>具备基层治理与产业统筹复合经历，政法背景深厚，规划视野清晰，执行力与应急处突能力突出。建议安排到科技、数字化部门轮岗锻炼，补齐数字经济短板。作风务实稳健，群众工作能力强，适合综合协调类岗位。
    </div>
  </div>`;
}

function basicInfoSection(d) {
  const info = [
    ["干部编号", d.cadre_id], ["性别", d.gender], ["民族", d.ethnicity],
    ["出生年月", `${d.birth_date}（${d.age}岁）`], ["政治面貌", d.political_status],
    ["入党时间", d.party_join_date], ["参加工作时间", d.work_start_date],
    ["学历学位", `${d.highest_education}·${d.highest_degree}`],
    ["现任职务", d.current_position], ["任现职时间", d.current_start_date],
    ["职级", `${d.current_level}·${d.current_rank}`],
    ["分工信息", d.current_division],
  ];
  return `
  <div class="section">
    <div class="section-title">干部基本信息明细</div>
    <div class="info-grid">
      ${info.map(([l, v]) => `
        <div class="info-item">
          <span class="info-label">${l}</span>
          <span class="info-value">${v}</span>
        </div>`).join("")}
    </div>
  </div>`;
}

function careerSection(d) {
  return `
  <div class="section">
    <div class="section-title">任职经历与履历分析</div>
    <div class="exp-row">
      <div class="exp-label">经历标签</div>
      <div class="exp-tags">
        ${d.structural_tags.map(t => `<span class="tag tag-blue">${t.icon} ${t.tag}</span>`).join("")}
      </div>
    </div>
    <div class="exp-row">
      <div class="exp-label">熟悉领域</div>
      <div class="exp-tags">
        ${d.familiar_fields.map(f => `<span class="tag tag-green">${f}</span>`).join("")}
        ${d.professional_labels.map(f => `<span class="tag tag-orange">${f}</span>`).join("")}
      </div>
    </div>
    <div style="margin-top:20px">
      <h4 style="font-size:14px;margin-bottom:12px;color:var(--text-light)">经历时间线</h4>
      <div class="timeline">
        ${d.career_history.slice().reverse().map(c => `
          <div class="tl-item ${c.is_current ? "current" : ""}">
            <div class="tl-period">${c.start} - ${c.end}</div>
            <div class="tl-position">${c.position}</div>
            <div class="tl-unit">${c.unit}</div>
          </div>`).join("")}
      </div>
    </div>
  </div>`;
}

function abilitySection(d) {
  return `
  <div class="section">
    <div class="section-title">能力素质与评价</div>
    <div class="dual-col">
      <div>
        <h4 style="font-size:14px;margin-bottom:12px;color:var(--text-light)">五维能力评估</h4>
        <div class="radar-wrap">
          <canvas id="radarCanvas" class="radar-canvas"></canvas>
        </div>
      </div>
      <div>
        <h4 style="font-size:14px;margin-bottom:12px;color:var(--text-light)">能力标签云</h4>
        <div style="margin-bottom:16px">
          ${d.ability_tags.filter(t => t.hot).map(t => `<span class="ability-tag hot">${t.tag}</span>`).join("")}
        </div>
        <div style="margin-bottom:16px">
          ${d.ability_tags.filter(t => !t.hot && t.confidence > 0.8).map(t => `<span class="ability-tag warm">${t.tag}</span>`).join("")}
        </div>
        <div>
          ${d.ability_tags.filter(t => !t.hot && t.confidence <= 0.8).map(t => `<span class="ability-tag cool">${t.tag}</span>`).join("")}
        </div>
      </div>
    </div>
    <div style="margin-top:24px">
      <h4 style="font-size:14px;margin-bottom:12px;color:var(--text-light)">主要短板</h4>
      ${d.main_shortcomings.map(s => `
        <div class="shortcoming">
          <span class="shortcoming-badge ${s.type === "能力类" ? "ability" : s.type === "经验类" ? "experience" : "personality"}">${s.type}</span>
          <span class="shortcoming-text">${s.text}</span>
        </div>`).join("")}
    </div>
  </div>`;
}

function achievementSection(d) {
  return `
  <div class="section">
    <div class="section-title">工作实绩与成效</div>
    ${d.work_performances.map(p => `
      <div class="achievement">
        <div class="achievement-header">
          <span class="achievement-title">${p.title}</span>
          <span class="achievement-level ${p.level === "突出" ? "good" : "mid"}">${p.level}</span>
        </div>
        <div class="achievement-desc">${p.desc}</div>
        <div class="achievement-source">来源: ${p.source}</div>
      </div>`).join("")}
  </div>`;
}

function structuralSection(d) {
  return `
  <div class="section">
    <div class="section-title">结构性人选标签</div>
    <div class="selection-grid">
      <div class="selection-card"><div class="icon">📊</div><div class="count">3</div><div class="label">经历标签</div></div>
      <div class="selection-card"><div class="icon">⚙️</div><div class="count">3</div><div class="label">能力特点</div></div>
      <div class="selection-card"><div class="icon">🎯</div><div class="count">2</div><div class="label">培养方向</div></div>
      <div class="selection-card"><div class="icon">📋</div><div class="count">2</div><div class="label">熟悉领域</div></div>
      <div class="selection-card"><div class="icon">🏆</div><div class="count">${d.awards ? d.awards.length : 0}</div><div class="label">重大奖励</div></div>
      <div class="selection-card"><div class="icon">⭐</div><div class="count">3</div><div class="label">关键岗位</div></div>
    </div>
  </div>`;
}

function supervisionSection(d) {
  return `
  <div class="section">
    <div class="section-title">监督与负面信息</div>
    <div class="alert-grid">
      ${d.supervision.map(s => `
        <div class="alert-item ${s.type}">
          <span class="alert-icon">${s.type === "ok" ? "✅" : s.type === "warn" ? "⚠️" : "🚨"}</span>
          <div class="alert-text">
            <div class="label">${s.label}</div>
            <div class="value">${s.status}</div>
          </div>
        </div>`).join("")}
    </div>
  </div>`;
}

function relationSection(d) {
  return `
  <div class="section">
    <div class="section-title">关系图谱</div>
    <div class="relation-container">
      <div class="relation-graph">
        <canvas id="relationCanvas" class="network-canvas"></canvas>
      </div>
      <div class="relation-sidebar">
        <h4 style="font-size:14px;margin-bottom:12px">关系图例</h4>
        <ul class="relation-list">
          ${d.relations.map(r => `
            <li>
              <span class="relation-dot" style="background:${getRelColor(r.type)}"></span>
              <span class="relation-name">${r.name}</span>
              <span class="relation-type">${r.type}</span>
            </li>`).join("")}
        </ul>
      </div>
    </div>
  </div>`;
}

function growthSection(d) {
  return `
  <div class="section">
    <div class="section-title">成长轨迹分析</div>
    <div class="timeline">
      ${d.career_trajectory.map(c => `
        <div class="tl-item">
          <div class="tl-period">${c.year}</div>
          <div class="tl-position">${c.phase} — ${c.label}</div>
          <div class="tl-unit">${c.desc}</div>
        </div>`).join("")}
    </div>
    <div style="margin-top:16px;background:#f9f9f9;padding:16px;border-radius:8px">
      <strong style="font-size:13px">成长特征总结：</strong>
      <div style="font-size:13px;color:var(--text-light);margin-top:8px;line-height:1.8">
        ${d.growth_traits.map(t => `<div>• <strong>${t.title}</strong>：${t.desc}</div>`).join("")}
        <div>• 待突破瓶颈：${d.待突破瓶颈}</div>
        <div>• 风格变化趋势：${d.风格变化趋势}</div>
      </div>
    </div>
  </div>`;
}

function directionSection(d) {
  return `
  <div class="section">
    <div class="section-title">培养使用方向</div>
    <div class="direction-grid">
      <div class="direction-card">
        <h4>🎯 培养建议</h4>
        <ul>
          <li>政治素质过硬，组织协调能力突出，建议继续在区级部门一把手岗位历练</li>
          <li>建议安排到科技、数字化部门轮岗锻炼，补齐数字经济短板</li>
          <li>建议加强战略谋划和宏观决策能力培养</li>
        </ul>
      </div>
      <div class="direction-card">
        <h4>💼 拟任方向</h4>
        <ul>
          <li><strong>区发改委主任</strong>（留任）— 经历匹配，专业对口</li>
          <li><strong>区商务局局长</strong> — 经济工作方向</li>
          <li><strong>区科信局局长</strong> — 补齐科技短板</li>
        </ul>
      </div>
    </div>
  </div>`;
}

function getRelColor(type) {
  const map = {"配偶":"#e8a0a0","同事":"#7ec8e3","校友":"#7ec87e","上级":"#e8b060","亲属":"#d0a0e8"};
  return map[type] || "#ccc";
}

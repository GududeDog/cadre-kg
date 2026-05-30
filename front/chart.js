// ═══════════════════════════════════════════════════════════
// chart.js — Canvas 图表绘制
// ═══════════════════════════════════════════════════════════

const ChartUtils = {
  // ─── 五维雷达图 ───
  drawRadar(canvas, scores) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width = canvas.clientWidth * 2;
    const H = canvas.height = canvas.clientHeight * 2;
    ctx.scale(2, 2);
    const w = W / 2, h = H / 2;
    const cx = w / 2, cy = h / 2;
    const R = Math.min(cx, cy) - 30;

    const dims = Object.keys(scores);
    const n = dims.length;
    const step = (Math.PI * 2) / n;
    const start = -Math.PI / 2;

    // 清空
    ctx.clearRect(0, 0, w, h);

    // 同心多边形
    [0.2, 0.4, 0.6, 0.8, 1.0].forEach(r => {
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const a = start + (i % n) * step;
        const x = cx + R * r * Math.cos(a);
        const y = cy + R * r * Math.sin(a);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = "#e0e0e0";
      ctx.lineWidth = 0.5;
      ctx.stroke();
    });

    // 轴线
    for (let i = 0; i < n; i++) {
      const a = start + i * step;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + R * Math.cos(a), cy + R * Math.sin(a));
      ctx.strokeStyle = "#ddd";
      ctx.lineWidth = 0.5;
      ctx.stroke();
    }

    // 数据多边形
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const idx = i % n;
      const a = start + idx * step;
      const val = (scores[dims[idx]] || 0) / 100;
      const x = cx + R * val * Math.cos(a);
      const y = cy + R * val * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = "rgba(196, 30, 44, 0.15)";
    ctx.fill();
    ctx.strokeStyle = "rgba(196, 30, 44, 0.8)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // 数据点 + 值
    for (let i = 0; i < n; i++) {
      const a = start + i * step;
      const val = (scores[dims[i]] || 0) / 100;
      const x = cx + R * val * Math.cos(a);
      const y = cy + R * val * Math.sin(a);
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = "#c41e2c";
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fill();
    }

    // 标签
    ctx.fillStyle = "#333";
    ctx.font = "12px PingFang SC, sans-serif";
    ctx.textAlign = "center";
    for (let i = 0; i < n; i++) {
      const a = start + i * step;
      const lx = cx + (R + 24) * Math.cos(a);
      const ly = cy + (R + 24) * Math.sin(a);
      ctx.fillText(dims[i], lx, ly + 4);
      // 值
      ctx.fillStyle = "#c41e2c";
      ctx.font = "bold 11px sans-serif";
      ctx.fillText(scores[dims[i]], lx, ly + 18);
      ctx.fillStyle = "#333";
      ctx.font = "12px PingFang SC, sans-serif";
    }
  },

  // ─── 关系网络图 ───
  drawRelationGraph(canvas, centerName, relations) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width = canvas.clientWidth * 2;
    const H = canvas.height = canvas.clientHeight * 2;
    ctx.scale(2, 2);
    const w = W / 2, h = H / 2;
    const cx = w / 2, cy = h / 2;
    const R = Math.min(cx, cy) - 50;

    ctx.clearRect(0, 0, w, h);

    // 中心节点
    ctx.beginPath();
    ctx.arc(cx, cy, 28, 0, Math.PI * 2);
    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 28);
    grad.addColorStop(0, "#e74c3c");
    grad.addColorStop(1, "#c0392b");
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.font = "bold 14px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(centerName, cx, cy);

    const n = relations.length;
    const typeColors = {
      "配偶": "#e8a0a0",
      "同事": "#7ec8e3",
      "校友": "#7ec87e",
      "上级": "#e8b060",
      "亲属": "#d0a0e8",
    };

    for (let i = 0; i < n; i++) {
      const angle = -Math.PI / 2 + (i / n) * Math.PI * 2;
      const x = cx + R * Math.cos(angle);
      const y = cy + R * Math.sin(angle);
      const color = typeColors[relations[i].type] || "#ccc";

      // 连线（虚线）
      ctx.beginPath();
      ctx.setLineDash([4, 4]);
      ctx.moveTo(cx, cy);
      ctx.lineTo(x, y);
      ctx.strokeStyle = "#ddd";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.setLineDash([]);

      // 圆点
      ctx.beginPath();
      ctx.arc(x, y, 22, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();

      // 名字
      ctx.fillStyle = "#fff";
      ctx.font = "bold 11px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const displayName = relations[i].name.length > 3 
        ? relations[i].name.slice(-2) 
        : relations[i].name;
      ctx.fillText(displayName, x, y);

      // 类型标签
      ctx.fillStyle = "#666";
      ctx.font = "10px sans-serif";
      ctx.fillText(relations[i].type, x, y + 32);
    }
  }
};

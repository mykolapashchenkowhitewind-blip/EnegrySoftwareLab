const api = (path) => fetch(path).then((response) => {
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
});

const fmt = (value, digits = 2) => Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: digits });

function drawLineChart(canvas, rows, xKey, series, colors) {
  const ctx = canvas.getContext("2d");
  const width = canvas.width = canvas.clientWidth * devicePixelRatio;
  const height = canvas.height = canvas.clientHeight * devicePixelRatio;
  ctx.scale(devicePixelRatio, devicePixelRatio);
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = "#d8dee5";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(42, 12);
  ctx.lineTo(42, h - 28);
  ctx.lineTo(w - 12, h - 28);
  ctx.stroke();
  const values = rows.flatMap(row => series.map(s => Number(row[s.key] || 0)));
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  series.forEach((s, idx) => {
    ctx.strokeStyle = colors[idx];
    ctx.lineWidth = 2;
    ctx.beginPath();
    rows.forEach((row, i) => {
      const x = 42 + (i / Math.max(rows.length - 1, 1)) * (w - 58);
      const y = h - 28 - ((Number(row[s.key] || 0) - min) / (max - min || 1)) * (h - 44);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });
  ctx.fillStyle = "#697586";
  ctx.font = "12px Arial";
  ctx.fillText(fmt(max), 6, 18);
  ctx.fillText(fmt(min), 8, h - 30);
}

function drawBarChart(canvas, rows, labelKey, bars) {
  const ctx = canvas.getContext("2d");
  const width = canvas.width = canvas.clientWidth * devicePixelRatio;
  const height = canvas.height = canvas.clientHeight * devicePixelRatio;
  ctx.scale(devicePixelRatio, devicePixelRatio);
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  ctx.clearRect(0, 0, w, h);
  const max = Math.max(...rows.flatMap(row => bars.map(b => Number(row[b.key] || 0))), 1);
  const groupW = (w - 50) / rows.length;
  rows.forEach((row, i) => {
    bars.forEach((bar, j) => {
      const val = Number(row[bar.key] || 0);
      const barW = groupW / (bars.length + 1);
      const x = 40 + i * groupW + j * barW;
      const y = h - 24 - (val / max) * (h - 42);
      ctx.fillStyle = bar.color;
      ctx.fillRect(x, y, barW - 2, h - 24 - y);
    });
  });
}

function kpi(label, value, unit = "") {
  return `<article class="kpi"><div class="label">${label}</div><div class="value">${value}${unit}</div></article>`;
}

async function loadDashboard() {
  const summary = await api("/api/dashboard/summary");
  document.getElementById("kpiGrid").innerHTML = [
    kpi("Latest kWh", fmt(summary.latest?.consumption_kwh), ""),
    kpi("Year kWh", fmt(summary.year_consumption_kwh), ""),
    kpi("Forecast kWh", fmt(summary.forecast_next_month_kwh), ""),
    kpi("Weekly Savings", fmt(summary.weekly_savings_uah), " UAH"),
    kpi("PV Week", fmt(summary.pv_generation_week_kwh), " kWh"),
    kpi("Avg SOC", fmt(summary.avg_battery_soc_percent), "%"),
  ].join("");
}

async function loadConsumption() {
  const period = document.getElementById("periodSelect").value;
  const rows = await api(`/api/consumption/aggregate?period=${period}`);
  drawLineChart(document.getElementById("consumptionChart"), rows.slice(-120), "period", [{ key: "consumption_kwh" }], ["#2f6fbd"]);
  const baseline = await api("/api/baseline");
  drawBarChart(document.getElementById("baselineChart"), baseline, "month", [
    { key: "baseline_kwh", color: "#c58a1c" },
    { key: "actual_kwh", color: "#2f6fbd" },
  ]);
  renderHeatmap(await api("/api/consumption/history?start=2025-04-07&end=2025-04-14&level=1"));
}

function renderHeatmap(rows) {
  const heatmap = document.getElementById("heatmap");
  const buckets = new Map();
  rows.forEach(row => {
    const d = new Date(row.measured_at);
    const key = `${d.getDay()}-${d.getHours()}`;
    buckets.set(key, (buckets.get(key) || 0) + Number(row.consumption_kwh || 0));
  });
  const max = Math.max(...buckets.values(), 1);
  let html = "";
  for (let hour = 0; hour < 24; hour++) {
    for (let day = 0; day < 7; day++) {
      const val = buckets.get(`${day}-${hour}`) || 0;
      const intensity = Math.round(235 - (val / max) * 150);
      html += `<div class="heat-cell" title="${hour}:00 day ${day}: ${fmt(val)} kWh" style="background: rgb(${intensity}, ${245 - intensity / 8}, 210)"></div>`;
    }
  }
  heatmap.innerHTML = html;
}

async function loadForecast() {
  const forecast = await api("/api/forecast");
  drawLineChart(document.getElementById("forecastChart"), forecast.slice(0, 240), "measured_at", [{ key: "forecast_kwh" }], ["#229b72"]);
  const models = await api("/api/models/comparison");
  document.getElementById("modelTable").innerHTML = `<thead><tr><th>Model</th><th>R2</th><th>RMSE</th><th>MAE</th><th>MAPE</th></tr></thead><tbody>` +
    models.map(row => `<tr><td>${row.model}</td><td>${fmt(row.r2, 4)}</td><td>${fmt(row.rmse)}</td><td>${fmt(row.mae)}</td><td>${fmt(row.mape)}%</td></tr>`).join("") +
    `</tbody>`;
}

async function loadEMS() {
  const rows = await api("/api/ems/results");
  const metrics = await api("/api/ems/metrics");
  drawLineChart(document.getElementById("emsChart"), rows, "timestamp", [
    { key: "load_kwh" },
    { key: "pv_generation_kwh" },
    { key: "grid_import_kwh" },
  ], ["#102a43", "#229b72", "#b94b4b"]);
  const last = rows[rows.length - 1] || {};
  document.getElementById("emsStatus").innerHTML = [
    ["Mode", "Tariff-aware"],
    ["SOC", `${fmt(last.battery_soc_percent)}%`],
    ["PV", `${fmt(last.pv_generation_kwh)} kWh`],
    ["Load", `${fmt(last.load_kwh)} kWh`],
    ["Tariff", last.tariff_zone || "-"],
    ["Alert", Number(last.battery_soc_percent || 0) < 25 ? "Low SOC" : "Normal"],
  ].map(([label, value]) => `<div class="status-item">${label}<strong>${value}</strong></div>`).join("");
  renderFlows(metrics.energy);
}

function renderFlows(energy) {
  const get = (name) => Number((energy.find(row => row.metric === name) || {}).value || 0);
  const flows = [
    ["PV generation", get("total_pv_generation_kwh"), "#229b72"],
    ["Battery discharge", get("battery_discharged_kwh"), "#c58a1c"],
    ["Grid import", get("grid_import_kwh"), "#2f6fbd"],
  ];
  const max = Math.max(...flows.map(f => f[1]), 1);
  document.getElementById("flowChart").innerHTML = flows.map(([label, value, color]) =>
    `<div class="flow-row"><span>${label}</span><div class="flow-bar" style="width:${Math.max(4, value / max * 100)}%;background:${color}"></div><strong>${fmt(value)}</strong></div>`
  ).join("");
}

async function loadReport() {
  const report = await api("/api/reports/summary");
  document.getElementById("reportPreview").textContent = JSON.stringify(report.dashboard, null, 2);
}

async function boot() {
  await Promise.all([loadDashboard(), loadConsumption(), loadForecast(), loadEMS(), loadReport()]);
}

document.getElementById("refresh").addEventListener("click", boot);
document.getElementById("periodSelect").addEventListener("change", loadConsumption);
document.getElementById("exportReport").addEventListener("click", async () => {
  const result = await api("/api/reports/export");
  alert(`Exported: ${result.path}`);
});

boot().catch(error => {
  document.body.insertAdjacentHTML("afterbegin", `<div style="background:#b94b4b;color:white;padding:12px">${error.message}</div>`);
});

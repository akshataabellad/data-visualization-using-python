/**
 * Sovereign Health & Capital Analytics - Mission-Critical Dashboard Engine
 * v3.0 — Full reactive binding: every control change immediately re-fetches
 * and redraws the relevant chart(s), metrics, distress diagnostics, and table.
 */

// ─── Application State ───────────────────────────────────────────────────────
const state = {
  currentCountry: 'ALL',
  currentRegion: 'ALL',
  currentIncome: 'ALL',
  currentYear: 2024,
  currency: 'USD',
  activeChartTab: 'timeseries',

  // Per-chart reactive metric bindings
  timeseriesIndicator: 'life_expectancy_years',   // driven by #chart-metric-select
  benchmarkIndicator: 'health_resilience_score',   // driven by #benchmark-indicator-select
  correlationX: 'health_expenditure_pct_gdp',      // driven by #corr-x-select
  correlationY: 'life_expectancy_years',           // driven by #corr-y-select

  // Table state
  gridSortBy: 'health_resilience_score',
  gridSortDir: 'DESC',
  gridPage: 1,
  gridPageSize: 15,
  gridSearch: '',

  // Playback
  isPlaying: false,
  playTimer: null,

  // Data cache
  countries: [],
  metadata: null,
};

// ─── API Base URL (works both from FastAPI and direct file:// open) ──────────
const API_BASE = window.location.protocol === 'file:'
  ? 'http://127.0.0.1:8000/api'
  : '/api';

// ─── Palette ─────────────────────────────────────────────────────────────────
const COLORS = ['#1d4ed8', '#ea580c', '#4338ca', '#dc2626', '#16a34a', '#0891b2', '#9333ea', '#ca8a04'];

// ─── Indicator display labels ─────────────────────────────────────────────────
const INDICATOR_LABELS = {
  life_expectancy_years: 'Life Expectancy (Years)',
  health_expenditure_pct_gdp: 'Health Exp. (% GDP)',
  health_expenditure_per_capita_usd: 'Per Capita Outlay (USD)',
  out_of_pocket_expenditure_pct: 'Out-of-Pocket Exp. (% OOPE)',
  health_resilience_score: 'Health Resilience Score (0–100)',
  uhc_service_coverage_index: 'UHC Coverage Index',
  physicians_per_1000: 'Physicians per 1,000',
  hospital_beds_per_1000: 'Hospital Beds per 1,000',
  infant_mortality_per_1000: 'Infant Mortality per 1,000',
  clean_water_access_pct: 'Clean Water Access (%)',
  ncd_mortality_pct_30_70: 'NCD Mortality Risk (%)',
  tb_incidence_per_100k: 'TB Incidence per 100k',
  hiv_prevalence_pct: 'HIV Prevalence (%)',
  maternal_mortality_per_100k: 'Maternal Mortality per 100k',
  under5_mortality_per_1000: 'Under-5 Mortality per 1,000',
  dpt_immunization_pct: 'DPT Immunization (%)',
  birth_rate_per_1000: 'Birth Rate per 1,000',
  death_rate_per_1000: 'Death Rate per 1,000',
  sanitation_access_pct: 'Sanitation Access (%)',
  obesity_prevalence_pct: 'Obesity Prevalence (%)',
  diabetes_prevalence_pct: 'Diabetes Prevalence (%)',
  tobacco_use_pct: 'Tobacco Use (%)',
  alcohol_consumption_liters_pc: 'Alcohol Consumption (L/capita)',
};

// ─── Initialization ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await fetchMetadata();
  await fetchCountries();
  buildChartControls();     // inject per-tab controls into the toolbar
  initEventListeners();
  await refreshDashboard();
});

// ─── Metadata & Country Population ────────────────────────────────────────────
async function fetchMetadata() {
  try {
    const data = await apiFetch('/metadata');
    state.metadata = data;

    const regionSelect = document.getElementById('region-select');
    const tableRegionSelect = document.getElementById('table-region-filter');
    data.regions.forEach(reg => {
      regionSelect.add(new Option(reg, reg));
      tableRegionSelect.add(new Option(reg, reg));
    });

    const incomeSelect = document.getElementById('table-income-filter');
    data.income_groups.forEach(inc => incomeSelect.add(new Option(inc, inc)));

    setText('total-countries-badge', `${data.total_countries} SOVEREIGN NATIONS`);
    setText('total-records-badge', `${data.total_records.toLocaleString()} RECORDS`);
  } catch (err) { console.error('fetchMetadata:', err); }
}

async function fetchCountries() {
  try {
    state.countries = await apiFetch('/countries');
    const sel = document.getElementById('country-select');
    state.countries.forEach(c => sel.add(new Option(`${c.country} (${c.iso_code})`, c.iso_code)));
  } catch (err) { console.error('fetchCountries:', err); }
}

// ─── Build per-tab control panels injected below the tabs row ─────────────────
function buildChartControls() {
  const toolbar = document.getElementById('chart-controls-panel');
  if (!toolbar) return;

  // All indicators as <option> list
  const allOpts = Object.entries(INDICATOR_LABELS)
    .map(([v, l]) => `<option value="${v}">${l}</option>`).join('');

  toolbar.innerHTML = `
    <!-- TIMESERIES controls (default visible) -->
    <div class="ctrl-panel" id="ctrl-timeseries">
      <span class="control-label">METRIC:</span>
      <select class="select-input" id="ts-indicator-select" style="min-width:200px;">
        ${allOpts}
      </select>
      <span class="control-label" style="margin-left:12px;">COUNTRIES:</span>
      <select class="select-input" id="ts-countries-select" multiple size="1" style="min-width:160px;"
        title="Hold Ctrl/Cmd to select multiple">
        <option value="DEFAULT" selected>Auto (from filter)</option>
        <option value="IND">India</option>
        <option value="USA">United States</option>
        <option value="CHN">China</option>
        <option value="DEU">Germany</option>
        <option value="JPN">Japan</option>
        <option value="GBR">United Kingdom</option>
        <option value="BRA">Brazil</option>
        <option value="ZAF">South Africa</option>
        <option value="NGA">Nigeria</option>
        <option value="FRA">France</option>
        <option value="AUS">Australia</option>
        <option value="THA">Thailand</option>
        <option value="KOR">South Korea</option>
        <option value="RWA">Rwanda</option>
        <option value="ETH">Ethiopia</option>
      </select>
    </div>

    <!-- BENCHMARKING controls -->
    <div class="ctrl-panel hidden" id="ctrl-benchmarking">
      <span class="control-label">RANK BY:</span>
      <select class="select-input" id="bench-indicator-select" style="min-width:220px;">
        ${allOpts}
      </select>
      <span class="control-label" style="margin-left:12px;">TOP:</span>
      <select class="select-input" id="bench-limit-select">
        <option value="10">10</option>
        <option value="20" selected>20</option>
        <option value="30">30</option>
        <option value="50">50</option>
      </select>
    </div>

    <!-- CORRELATION controls -->
    <div class="ctrl-panel hidden" id="ctrl-correlation">
      <span class="control-label">X-AXIS:</span>
      <select class="select-input" id="corr-x-select" style="min-width:200px;">
        ${allOpts}
      </select>
      <span class="control-label" style="margin-left:10px;">Y-AXIS:</span>
      <select class="select-input" id="corr-y-select" style="min-width:200px;">
        ${allOpts}
      </select>
    </div>

    <!-- RADAR controls -->
    <div class="ctrl-panel hidden" id="ctrl-radar">
      <span class="control-label">COMPARE NATIONS:</span>
      <select class="select-input" id="radar-countries-select" multiple size="1" style="min-width:180px;"
        title="Hold Ctrl/Cmd to select up to 5">
        <option value="IND" selected>India</option>
        <option value="USA" selected>United States</option>
        <option value="DEU" selected>Germany</option>
        <option value="JPN" selected>Japan</option>
        <option value="CHN">China</option>
        <option value="BRA">Brazil</option>
        <option value="ZAF">South Africa</option>
        <option value="GBR">United Kingdom</option>
        <option value="NGA">Nigeria</option>
        <option value="THA">Thailand</option>
        <option value="KOR">South Korea</option>
        <option value="RWA">Rwanda</option>
      </select>
      <span class="control-label" style="font-size:9.5px;color:var(--text-tertiary);">Hold Ctrl/Cmd to multi-select (max 5)</span>
    </div>
  `;

  // Set default selections
  document.getElementById('ts-indicator-select').value = state.timeseriesIndicator;
  document.getElementById('bench-indicator-select').value = state.benchmarkIndicator;
  document.getElementById('corr-x-select').value = state.correlationX;
  document.getElementById('corr-y-select').value = state.correlationY;
}

// ─── Show the correct control panel for the active tab ───────────────────────
function showTabControls(tab) {
  ['timeseries', 'benchmarking', 'correlation', 'radar'].forEach(t => {
    const el = document.getElementById(`ctrl-${t}`);
    if (el) el.classList.toggle('hidden', t !== tab);
  });
}

// ─── Global Full Refresh ──────────────────────────────────────────────────────
async function refreshDashboard() {
  await Promise.all([
    renderMacroMetrics(),
    renderActiveChart(),
    renderDistressDiagnostics(),
    renderGridTable(),
  ]);
}

// ─── Partial refresh (only chart + metrics, not table) ───────────────────────
async function refreshChartAndMetrics() {
  await Promise.all([
    renderMacroMetrics(),
    renderActiveChart(),
    renderDistressDiagnostics(),
  ]);
}

// ─── API Helper ──────────────────────────────────────────────────────────────
async function apiFetch(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json();
}

function setText(id, txt) {
  const el = document.getElementById(id);
  if (el) el.innerText = txt;
}

// ─── Macro Metric Cards ───────────────────────────────────────────────────────
async function renderMacroMetrics() {
  try {
    const p = new URLSearchParams({
      iso_code: state.currentCountry,
      region: state.currentRegion,
      year: state.currentYear,
      currency: state.currency,
    });
    const data = await apiFetch(`/macro-metrics?${p}`);

    const container = document.getElementById('macro-metrics-row');
    container.innerHTML = '';

    data.cards.forEach(card => {
      const pos = card.delta >= 0;
      const deltaClass = pos ? 'delta-positive' : 'delta-negative';
      const deltaIcon = pos ? '▲' : '▼';
      const badgeClass = card.semantic === 'deficit' ? 'badge-deficit'
        : card.semantic === 'gdp' ? 'badge-gdp' : 'badge-resilience';

      const el = document.createElement('div');
      el.className = 'metric-card';
      el.innerHTML = `
        <div class="metric-card-header">
          <span class="metric-card-title">${card.label}</span>
          <span class="badge ${badgeClass}">${card.taxonomy}</span>
        </div>
        <div class="metric-val-row">
          <span class="metric-display">${card.value.toLocaleString()}</span>
          <span class="metric-sub">${card.unit}</span>
        </div>
        <div class="metric-card-footer">
          <span class="delta-tag ${deltaClass}">${deltaIcon} ${Math.abs(card.delta)}%</span>
          <span class="delta-label">${card.delta_label}</span>
        </div>
        <canvas class="sparkline-lane" id="spark-${card.id}"></canvas>
      `;
      container.appendChild(el);

      setTimeout(() => {
        const spColor = card.semantic === 'deficit' ? '#dc2626' : '#1d4ed8';
        drawSparkline(`spark-${card.id}`, card.sparkline, spColor);
      }, 0);
    });
  } catch (err) { console.error('renderMacroMetrics:', err); }
}

// ─── Sparkline Mini-Chart ─────────────────────────────────────────────────────
function drawSparkline(canvasId, values, strokeColor) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !values || values.length < 2) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth || 160;
  const h = canvas.clientHeight || 22;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.scale(dpr, dpr);

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  ctx.clearRect(0, 0, w, h);
  ctx.beginPath();
  const step = w / (values.length - 1);
  values.forEach((v, i) => {
    const x = i * step;
    const y = h - ((v - min) / range) * (h - 5) - 2;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 1.6;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke();

  // Gradient fill
  ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath();
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, hexToRgba(strokeColor, 0.2));
  grad.addColorStop(1, hexToRgba(strokeColor, 0));
  ctx.fillStyle = grad;
  ctx.fill();
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ─── Chart Router ─────────────────────────────────────────────────────────────
async function renderActiveChart() {
  const canvas = document.getElementById('main-chart-canvas');
  if (!canvas) return;

  // Ensure canvas fills its container properly
  const container = canvas.parentElement;
  const w = container.clientWidth;
  const h = container.clientHeight;
  if (w > 0) canvas.style.width = '100%';
  if (h > 0) canvas.style.height = '100%';

  try {
    switch (state.activeChartTab) {
      case 'timeseries':   await renderTimeseriesChart(canvas); break;
      case 'benchmarking': await renderBenchmarkingChart(canvas); break;
      case 'correlation':  await renderCorrelationChart(canvas); break;
      case 'radar':        await renderRadarChart(canvas); break;
    }
  } catch (err) { console.error('renderActiveChart:', err); }
}

// ─── Chart Drawing Utilities ──────────────────────────────────────────────────
function setupCanvas(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  return { ctx, w, h };
}

function getThemeColor(role) {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const map = {
    gridLine: isDark ? 'rgba(60,74,66,0.55)' : 'rgba(148,163,184,0.4)',
    axisText: isDark ? '#767680' : '#475569',
    labelText: isDark ? '#d4e4fa' : '#0f172a',
    dotBorder: isDark ? '#051424' : '#ffffff',
    pointLabel: isDark ? '#d4e4fa' : '#1e293b',
  };
  return map[role] || '#000';
}

function drawGrid(ctx, padding, w, h, yMin, yMax, xLabels) {
  const pw = w - padding.left - padding.right;
  const ph = h - padding.top - padding.bottom;
  const gc = getThemeColor('gridLine');
  const tc = getThemeColor('axisText');

  ctx.save();
  ctx.setLineDash([4, 4]);
  ctx.strokeStyle = gc;
  ctx.lineWidth = 1;
  ctx.font = '10px "JetBrains Mono"';
  ctx.fillStyle = tc;

  // Y gridlines
  const yTicks = 5;
  for (let i = 0; i <= yTicks; i++) {
    const yVal = yMin + (yMax - yMin) * (i / yTicks);
    const yPos = padding.top + ph - (i / yTicks) * ph;
    ctx.beginPath();
    ctx.moveTo(padding.left, yPos);
    ctx.lineTo(w - padding.right, yPos);
    ctx.stroke();
    ctx.textAlign = 'right';
    ctx.fillText(yVal.toFixed(1), padding.left - 6, yPos + 3);
  }

  // X labels
  if (xLabels && xLabels.length) {
    ctx.textAlign = 'center';
    const step = Math.ceil(xLabels.length / 9);
    xLabels.forEach((lbl, idx) => {
      if (idx % step === 0 || idx === xLabels.length - 1) {
        const xPos = padding.left + (idx / (xLabels.length - 1)) * pw;
        ctx.beginPath();
        ctx.moveTo(xPos, padding.top);
        ctx.lineTo(xPos, padding.top + ph);
        ctx.stroke();
        ctx.fillText(lbl, xPos, h - padding.bottom + 14);
      }
    });
  }
  ctx.setLineDash([]);
  ctx.restore();
}

// ─── 1. Timeseries Line Chart ─────────────────────────────────────────────────
async function renderTimeseriesChart(canvas) {
  // Determine which countries to show
  const selEl = document.getElementById('ts-countries-select');
  let isoList;
  if (selEl) {
    const chosen = Array.from(selEl.selectedOptions).map(o => o.value).filter(v => v !== 'DEFAULT');
    if (chosen.length > 0) {
      isoList = chosen;
    } else {
      isoList = state.currentCountry !== 'ALL'
        ? [state.currentCountry]
        : ['IND', 'USA', 'DEU', 'CHN', 'JPN'];
    }
  } else {
    isoList = state.currentCountry !== 'ALL'
      ? [state.currentCountry]
      : ['IND', 'USA', 'DEU', 'CHN', 'JPN'];
  }

  const indicator = state.timeseriesIndicator;
  const p = new URLSearchParams({
    iso_codes: isoList.join(','),
    indicators: indicator,
    start_year: 1980,
    end_year: 2024,
  });

  const result = await apiFetch(`/timeseries?${p}`);
  const { ctx, w, h } = setupCanvas(canvas);
  const pad = { top: 28, right: 24, bottom: 38, left: 52 };
  const pw = w - pad.left - pad.right;
  const ph = h - pad.top - pad.bottom;

  if (!result.series || result.series.length === 0) {
    drawNoData(ctx, w, h);
    return;
  }

  const years = result.series[0].years || [];
  let allVals = [];
  result.series.forEach(s => { allVals = allVals.concat(s.data[indicator] || []); });
  const minVal = Math.floor(Math.min(...allVals) * 0.94);
  const maxVal = Math.ceil(Math.max(...allVals) * 1.04);

  drawGrid(ctx, pad, w, h, minVal, maxVal, years);

  // Legend
  const legendRow = document.getElementById('chart-legend-row');
  legendRow.innerHTML = '';

  result.series.forEach((s, idx) => {
    const color = COLORS[idx % COLORS.length];
    const item = document.createElement('div');
    item.className = 'legend-item';
    item.innerHTML = `<span class="legend-swatch" style="background:${color}"></span><span>${s.country} (${s.iso_code})</span>`;
    legendRow.appendChild(item);

    const pts = s.data[indicator] || [];
    if (pts.length === 0) return;

    // Area fill
    ctx.beginPath();
    pts.forEach((v, i) => {
      const x = pad.left + (i / (years.length - 1)) * pw;
      const y = pad.top + ph - ((v - minVal) / (maxVal - minVal)) * ph;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.lineTo(pad.left + pw, pad.top + ph);
    ctx.lineTo(pad.left, pad.top + ph);
    ctx.closePath();
    ctx.fillStyle = hexToRgba(color, 0.07);
    ctx.fill();

    // Line
    ctx.beginPath();
    pts.forEach((v, i) => {
      const x = pad.left + (i / (years.length - 1)) * pw;
      const y = pad.top + ph - ((v - minVal) / (maxVal - minVal)) * ph;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.stroke();

    // Current-year dot
    const curIdx = years.indexOf(state.currentYear);
    if (curIdx !== -1) {
      const hx = pad.left + (curIdx / (years.length - 1)) * pw;
      const hy = pad.top + ph - ((pts[curIdx] - minVal) / (maxVal - minVal)) * ph;
      ctx.beginPath();
      ctx.arc(hx, hy, 5, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = getThemeColor('dotBorder');
      ctx.lineWidth = 2;
      ctx.stroke();

      // Value label near dot
      ctx.font = 'bold 10px "JetBrains Mono"';
      ctx.fillStyle = color;
      ctx.textAlign = 'center';
      ctx.fillText(pts[curIdx].toFixed(1), hx, hy - 10);
    }
  });

  // Current year vertical line
  const yearIdx = years.indexOf(state.currentYear);
  if (yearIdx !== -1) {
    const xPos = pad.left + (yearIdx / (years.length - 1)) * pw;
    ctx.save();
    ctx.strokeStyle = '#ea580c';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(xPos, pad.top);
    ctx.lineTo(xPos, pad.top + ph);
    ctx.stroke();

    // Year badge at top
    ctx.fillStyle = '#ea580c';
    ctx.font = 'bold 10px "JetBrains Mono"';
    ctx.textAlign = 'center';
    ctx.fillText(state.currentYear, xPos, pad.top - 6);
    ctx.setLineDash([]);
    ctx.restore();
  }

  // Chart title
  updateChartHeading(`${INDICATOR_LABELS[indicator] || indicator} — Longitudinal Trajectory (1980–2024)`);

  // Store for tooltip
  window._ts = { series: result.series, years, indicator, pad, minVal, maxVal };
}

// ─── 2. Benchmarking Bar Chart ────────────────────────────────────────────────
async function renderBenchmarkingChart(canvas) {
  const indicator = state.benchmarkIndicator;
  const limitEl = document.getElementById('bench-limit-select');
  const limit = limitEl ? parseInt(limitEl.value) : 20;

  const p = new URLSearchParams({
    indicator,
    year: state.currentYear,
    region: state.currentRegion,
    limit,
  });

  const data = await apiFetch(`/cross-country?${p}`);
  const { ctx, w, h } = setupCanvas(canvas);
  const pad = { top: 20, right: 70, bottom: 28, left: 130 };
  const pw = w - pad.left - pad.right;
  const ph = h - pad.top - pad.bottom;

  if (!data || data.length === 0) { drawNoData(ctx, w, h); return; }

  const maxVal = Math.max(...data.map(d => d.val || 0)) * 1.08 || 10;
  const barSlot = ph / data.length;
  const barH = Math.min(18, barSlot - 4);

  const tc = getThemeColor('axisText');
  const lc = getThemeColor('labelText');

  // X gridlines
  ctx.save();
  ctx.setLineDash([4, 4]);
  ctx.strokeStyle = getThemeColor('gridLine');
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const xv = (maxVal / 5) * i;
    const xp = pad.left + (i / 5) * pw;
    ctx.beginPath();
    ctx.moveTo(xp, pad.top);
    ctx.lineTo(xp, pad.top + ph);
    ctx.stroke();
    ctx.fillStyle = tc;
    ctx.font = '9px "JetBrains Mono"';
    ctx.textAlign = 'center';
    ctx.fillText(xv.toFixed(1), xp, h - pad.bottom + 14);
  }
  ctx.setLineDash([]);

  data.forEach((d, idx) => {
    const yCenter = pad.top + idx * barSlot + barSlot / 2;
    const yTop = yCenter - barH / 2;
    const bw = Math.max(2, ((d.val || 0) / maxVal) * pw);
    const isSelected = d.iso_code === state.currentCountry;
    const color = isSelected ? '#1d4ed8' : (d.oope > 35 ? '#ea580c' : '#4338ca');

    // Country label
    ctx.fillStyle = isSelected ? '#1d4ed8' : lc;
    ctx.font = isSelected ? 'bold 11px "Inter"' : '11px "Inter"';
    ctx.textAlign = 'right';
    ctx.fillText(`${d.country.substring(0, 16)} (${d.iso_code})`, pad.left - 8, yCenter + 4);

    // Bar
    ctx.fillStyle = color;
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(pad.left, yTop, bw, barH, [2, 2, 2, 2]);
    } else {
      ctx.rect(pad.left, yTop, bw, barH);
    }
    ctx.fill();

    // Value label
    ctx.fillStyle = tc;
    ctx.font = '10px "JetBrains Mono"';
    ctx.textAlign = 'left';
    ctx.fillText((d.val || 0).toFixed(1), pad.left + bw + 5, yCenter + 4);
  });
  ctx.restore();

  // Legend
  const legendRow = document.getElementById('chart-legend-row');
  legendRow.innerHTML = `
    <div class="legend-item"><span class="legend-swatch" style="background:#1d4ed8"></span><span>Selected Nation</span></div>
    <div class="legend-item"><span class="legend-swatch" style="background:#4338ca"></span><span>Resilient / Low OOPE</span></div>
    <div class="legend-item"><span class="legend-swatch" style="background:#ea580c"></span><span>Elevated OOPE (>35%)</span></div>
    <div class="legend-item" style="margin-left:auto;font-family:var(--font-mono);font-size:10.5px;color:var(--text-secondary);">Year: ${state.currentYear} | Metric: ${INDICATOR_LABELS[indicator] || indicator}</div>
  `;

  updateChartHeading(`${INDICATOR_LABELS[indicator] || indicator} — Top ${limit} Sovereign Nations (${state.currentYear})`);
}

// ─── 3. Correlation Scatter ───────────────────────────────────────────────────
async function renderCorrelationChart(canvas) {
  const p = new URLSearchParams({
    x_indicator: state.correlationX,
    y_indicator: state.correlationY,
    year: state.currentYear,
    region: state.currentRegion,
  });

  const result = await apiFetch(`/correlation?${p}`);
  const { ctx, w, h } = setupCanvas(canvas);
  const pad = { top: 28, right: 28, bottom: 44, left: 58 };
  const pw = w - pad.left - pad.right;
  const ph = h - pad.top - pad.bottom;

  const points = (result.points || []).filter(p => p.x != null && p.y != null);
  if (points.length === 0) { drawNoData(ctx, w, h); return; }

  const minX = Math.floor(Math.min(...points.map(p => p.x)) * 0.92);
  const maxX = Math.ceil(Math.max(...points.map(p => p.x)) * 1.08) || 10;
  const minY = Math.floor(Math.min(...points.map(p => p.y)) * 0.92);
  const maxY = Math.ceil(Math.max(...points.map(p => p.y)) * 1.06) || 100;

  const tc = getThemeColor('axisText');
  // Axis labels
  ctx.save();
  ctx.setLineDash([4, 4]);
  ctx.strokeStyle = getThemeColor('gridLine');
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    // Y
    const yv = minY + (maxY - minY) * (i / 5);
    const yp = pad.top + ph - (i / 5) * ph;
    ctx.beginPath(); ctx.moveTo(pad.left, yp); ctx.lineTo(w - pad.right, yp); ctx.stroke();
    ctx.fillStyle = tc;
    ctx.font = '10px "JetBrains Mono"';
    ctx.textAlign = 'right';
    ctx.fillText(yv.toFixed(1), pad.left - 6, yp + 3);

    // X
    const xv = minX + (maxX - minX) * (i / 5);
    const xp = pad.left + (i / 5) * pw;
    ctx.beginPath(); ctx.moveTo(xp, pad.top); ctx.lineTo(xp, pad.top + ph); ctx.stroke();
    ctx.textAlign = 'center';
    ctx.fillText(xv.toFixed(1), xp, h - pad.bottom + 14);
  }
  ctx.setLineDash([]);

  // Regression line
  const n = points.length;
  const meanX = points.reduce((s, p) => s + p.x, 0) / n;
  const meanY = points.reduce((s, p) => s + p.y, 0) / n;
  const slope = points.reduce((s, p) => s + (p.x - meanX) * (p.y - meanY), 0) /
    points.reduce((s, p) => s + (p.x - meanX) ** 2, 0);
  const intercept = meanY - slope * meanX;
  const regY1 = slope * minX + intercept;
  const regY2 = slope * maxX + intercept;

  const toCanvasX = v => pad.left + ((v - minX) / (maxX - minX)) * pw;
  const toCanvasY = v => pad.top + ph - ((v - minY) / (maxY - minY)) * ph;

  ctx.save();
  ctx.strokeStyle = '#ea580c';
  ctx.lineWidth = 1.5;
  ctx.setLineDash([5, 4]);
  ctx.beginPath();
  ctx.moveTo(toCanvasX(minX), toCanvasY(regY1));
  ctx.lineTo(toCanvasX(maxX), toCanvasY(regY2));
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();

  // Points
  points.forEach(p => {
    const px = toCanvasX(p.x);
    const py = toCanvasY(p.y);
    const isTarget = p.iso_code === state.currentCountry;
    const r = isTarget ? 7 : 4;
    const color = isTarget ? '#1d4ed8' : (p.oope > 35 ? '#ea580c' : '#4338ca');

    ctx.beginPath();
    ctx.arc(px, py, r, 0, Math.PI * 2);
    ctx.fillStyle = hexToRgba(color, 0.75);
    ctx.fill();
    ctx.strokeStyle = getThemeColor('dotBorder');
    ctx.lineWidth = 1.5;
    ctx.stroke();

    if (isTarget || ['IND', 'USA', 'CHN', 'DEU', 'NGA', 'JPN', 'BRA', 'GBR'].includes(p.iso_code)) {
      ctx.font = isTarget ? 'bold 10px "JetBrains Mono"' : '9px "JetBrains Mono"';
      ctx.fillStyle = getThemeColor('pointLabel');
      ctx.textAlign = 'left';
      ctx.fillText(p.iso_code, px + 6, py - 3);
    }
  });
  ctx.restore();

  // Legend + Stats
  const xl = INDICATOR_LABELS[state.correlationX] || state.correlationX;
  const yl = INDICATOR_LABELS[state.correlationY] || state.correlationY;
  const legendRow = document.getElementById('chart-legend-row');
  legendRow.innerHTML = `
    <div class="legend-item"><span class="badge badge-resilience">PEARSON r: ${result.pearson_r}</span></div>
    <div class="legend-item"><span class="badge badge-gdp">R²: ${result.r_squared}</span></div>
    <div class="legend-item" style="color:var(--text-secondary);">${points.length} nations | Year: ${state.currentYear}</div>
    <div class="legend-item" style="color:var(--text-tertiary);font-family:var(--font-mono);font-size:9.5px;margin-left:auto;">X: ${xl} &nbsp;|&nbsp; Y: ${yl}</div>
  `;

  updateChartHeading(`${yl} vs ${xl} — Correlation Scatter (${state.currentYear})`);
}

// ─── 4. Radar Chart ───────────────────────────────────────────────────────────
async function renderRadarChart(canvas) {
  const radarEl = document.getElementById('radar-countries-select');
  let isoList = radarEl
    ? Array.from(radarEl.selectedOptions).map(o => o.value).slice(0, 5)
    : ['IND', 'USA', 'JPN', 'DEU'];

  if (state.currentCountry !== 'ALL' && !isoList.includes(state.currentCountry)) {
    isoList = [state.currentCountry, ...isoList].slice(0, 5);
  }
  if (isoList.length === 0) isoList = ['IND', 'USA', 'DEU'];

  const p = new URLSearchParams({ iso_codes: isoList.join(','), year: state.currentYear });
  const result = await apiFetch(`/radar?${p}`);
  const { ctx, w, h } = setupCanvas(canvas);

  const cx = w / 2;
  const cy = h / 2;
  const radius = Math.min(cx, cy) - 52;
  const numAxes = result.labels.length;
  const angleStep = (Math.PI * 2) / numAxes;

  const gc = getThemeColor('gridLine');
  const tc = getThemeColor('axisText');

  // Concentric grids
  ctx.save();
  ctx.setLineDash([4, 4]);
  for (let lev = 1; lev <= 4; lev++) {
    const r = (radius / 4) * lev;
    ctx.beginPath();
    for (let a = 0; a < numAxes; a++) {
      const ang = a * angleStep - Math.PI / 2;
      const x = cx + Math.cos(ang) * r;
      const y = cy + Math.sin(ang) * r;
      a === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = gc;
    ctx.lineWidth = 1;
    ctx.stroke();

    // Level label (25%, 50%, 75%, 100%)
    ctx.fillStyle = tc;
    ctx.font = '9px "JetBrains Mono"';
    ctx.textAlign = 'left';
    ctx.fillText(`${lev * 25}%`, cx + 4, cy - r + 3);
  }
  ctx.setLineDash([]);

  // Axes + Labels
  for (let a = 0; a < numAxes; a++) {
    const ang = a * angleStep - Math.PI / 2;
    const x = cx + Math.cos(ang) * radius;
    const y = cy + Math.sin(ang) * radius;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(x, y);
    ctx.strokeStyle = gc; ctx.lineWidth = 1; ctx.stroke();

    const lx = cx + Math.cos(ang) * (radius + 18);
    const ly = cy + Math.sin(ang) * (radius + 18);
    ctx.fillStyle = tc;
    ctx.font = '10px "JetBrains Mono"';
    ctx.textAlign = 'center';
    // Word-wrap long labels
    const words = result.labels[a].split(' ');
    if (words.length > 2) {
      ctx.fillText(words.slice(0, 2).join(' '), lx, ly);
      ctx.fillText(words.slice(2).join(' '), lx, ly + 11);
    } else {
      ctx.fillText(result.labels[a], lx, ly);
    }
  }

  // Series Polygons
  const legendRow = document.getElementById('chart-legend-row');
  legendRow.innerHTML = '';

  result.series.forEach((s, idx) => {
    const color = COLORS[idx % COLORS.length];
    const item = document.createElement('div');
    item.className = 'legend-item';
    item.innerHTML = `<span class="legend-swatch" style="background:${color}"></span><span>${s.country} (${s.iso_code})</span>`;
    legendRow.appendChild(item);

    ctx.beginPath();
    s.scores.forEach((sc, si) => {
      const norm = Math.min(100, Math.max(0, sc || 0)) / 100;
      const ang = si * angleStep - Math.PI / 2;
      const x = cx + Math.cos(ang) * radius * norm;
      const y = cy + Math.sin(ang) * radius * norm;
      si === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.fillStyle = hexToRgba(color, 0.15);
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
  });
  ctx.restore();

  updateChartHeading(`Multi-Dimensional Health Resilience Profile (${state.currentYear})`);
}

// ─── OOPE Distress Diagnostics ────────────────────────────────────────────────
async function renderDistressDiagnostics() {
  const container = document.getElementById('distress-telemetry-body');
  if (!container) return;

  const p = new URLSearchParams({
    indicator: 'out_of_pocket_expenditure_pct',
    year: state.currentYear,
    region: state.currentRegion,
    limit: 226,
  });

  const data = await apiFetch(`/cross-country?${p}`);
  let low = 0, mod = 0, elev = 0, crit = 0;
  data.forEach(d => {
    if (d.val < 20) low++;
    else if (d.val < 35) mod++;
    else if (d.val < 50) elev++;
    else crit++;
  });
  const total = data.length || 1;

  container.innerHTML = `
    <div class="distress-meter-container">
      <div style="display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:10.5px;margin-bottom:4px;">
        <span style="color:var(--text-secondary)">GLOBAL OOPE DISTRESS SPECTRUM — ${state.currentYear}</span>
        <span style="color:var(--accent-deficit)">${crit} CRITICAL DEFICIT</span>
      </div>
      <div class="meter-track">
        <div class="meter-segment" style="width:${(low/total)*100}%;background:#1d4ed8;"></div>
        <div class="meter-segment" style="width:${(mod/total)*100}%;background:#4338ca;"></div>
        <div class="meter-segment" style="width:${(elev/total)*100}%;background:#ea580c;"></div>
        <div class="meter-segment" style="width:${(crit/total)*100}%;background:#dc2626;"></div>
      </div>
      <div class="distress-legend-grid">
        <div class="distress-box">
          <span class="distress-box-title" style="color:#1d4ed8;">Universal Shield (&lt;20%)</span>
          <span class="distress-box-val">${low} <span style="font-size:9px;color:var(--text-tertiary);">Nations</span></span>
        </div>
        <div class="distress-box">
          <span class="distress-box-title" style="color:#4338ca;">Moderate (20-35%)</span>
          <span class="distress-box-val">${mod} <span style="font-size:9px;color:var(--text-tertiary);">Nations</span></span>
        </div>
        <div class="distress-box">
          <span class="distress-box-title" style="color:#ea580c;">Elevated Strain (35-50%)</span>
          <span class="distress-box-val">${elev} <span style="font-size:9px;color:var(--text-tertiary);">Nations</span></span>
        </div>
        <div class="distress-box">
          <span class="distress-box-title" style="color:#dc2626;">Severe Deficit (&gt;50%)</span>
          <span class="distress-box-val">${crit} <span style="font-size:9px;color:var(--text-tertiary);">Nations</span></span>
        </div>
      </div>
    </div>
  `;
}

// ─── Data Grid Table ─────────────────────────────────────────────────────────
async function renderGridTable() {
  const p = new URLSearchParams({
    search: state.gridSearch,
    iso_code: state.currentCountry,
    region: state.currentRegion,
    income_group: state.currentIncome,
    year: state.currentYear,
    sort_by: state.gridSortBy,
    sort_dir: state.gridSortDir,
    page: state.gridPage,
    page_size: state.gridPageSize,
  });

  const data = await apiFetch(`/grid?${p}`);
  const tbody = document.getElementById('table-records-body');
  tbody.innerHTML = '';

  const mult = state.currency === 'INR' ? 84.25 : 1;
  const sym = state.currency === 'INR' ? '₹' : '$';

  data.records.forEach(r => {
    const badgeCls = r.health_resilience_score >= 80 ? 'badge-resilience'
      : r.health_resilience_score >= 60 ? 'badge-gdp' : 'badge-deficit';
    const oopeCls = r.out_of_pocket_expenditure_pct >= 50 ? 'badge-deficit'
      : r.out_of_pocket_expenditure_pct >= 35 ? 'badge-liquidity' : 'badge-resilience';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${r.country}</strong></td>
      <td style="font-family:var(--font-mono);">${r.iso_code}</td>
      <td>${r.region}</td>
      <td>${r.income_group}</td>
      <td class="numeric-col"><span class="badge ${badgeCls}">${r.health_resilience_score}</span></td>
      <td class="numeric-col">${r.life_expectancy_years} y</td>
      <td class="numeric-col">${r.health_expenditure_pct_gdp}%</td>
      <td class="numeric-col">${sym} ${(r.health_expenditure_per_capita_usd * mult).toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
      <td class="numeric-col"><span class="badge ${oopeCls}">${r.out_of_pocket_expenditure_pct}%</span></td>
      <td class="numeric-col">${r.physicians_per_1000}</td>
      <td class="numeric-col">${r.hospital_beds_per_1000}</td>
      <td class="numeric-col">${r.infant_mortality_per_1000}</td>
      <td class="numeric-col">${r.uhc_service_coverage_index}</td>
    `;
    tbody.appendChild(tr);
  });

  setText('table-page-info', `Page ${data.page} of ${Math.max(1, data.total_pages)} (${data.total} records)`);
  document.getElementById('btn-prev-page').disabled = data.page <= 1;
  document.getElementById('btn-next-page').disabled = data.page >= data.total_pages;
}

// ─── No-data Placeholder ─────────────────────────────────────────────────────
function drawNoData(ctx, w, h) {
  ctx.fillStyle = getThemeColor('axisText');
  ctx.font = '13px "Inter"';
  ctx.textAlign = 'center';
  ctx.fillText('No data available for the selected filters.', w / 2, h / 2);
}

// ─── Heading Update ──────────────────────────────────────────────────────────
function updateChartHeading(text) {
  const el = document.getElementById('chart-heading-text');
  if (el) el.innerText = text;
}

// ─── Event Listeners — Every Control Triggers Reactive Chart Updates ──────────
function initEventListeners() {

  // ── Country Selector
  document.getElementById('country-select').addEventListener('change', e => {
    state.currentCountry = e.target.value;
    state.gridPage = 1;
    updateQuickPills();
    refreshDashboard();
  });

  // ── Region Selector (ribbon)
  document.getElementById('region-select').addEventListener('change', e => {
    state.currentRegion = e.target.value;
    state.gridPage = 1;
    syncRegionSelects('region-select', e.target.value);
    refreshDashboard();
  });

  // ── Table Region Filter
  document.getElementById('table-region-filter').addEventListener('change', e => {
    state.currentRegion = e.target.value;
    state.gridPage = 1;
    syncRegionSelects('table-region-filter', e.target.value);
    refreshDashboard();
  });

  // ── Table Income Filter
  document.getElementById('table-income-filter').addEventListener('change', e => {
    state.currentIncome = e.target.value;
    state.gridPage = 1;
    renderGridTable();
  });

  document.getElementById('btn-clear-filters').addEventListener('click', () => {
    state.currentCountry = 'ALL';
    state.currentRegion = 'ALL';
    state.currentIncome = 'ALL';
    state.gridSearch = '';
    state.gridPage = 1;

    document.getElementById('country-select').value = 'ALL';
    document.getElementById('region-select').value = 'ALL';
    document.getElementById('table-region-filter').value = 'ALL';
    document.getElementById('table-income-filter').value = 'ALL';
    document.getElementById('table-search-input').value = '';
    updateQuickPills();
    refreshDashboard();
  });

  // ── Table Search (debounced 250ms)
  let debounce;
  document.getElementById('table-search-input').addEventListener('input', e => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      state.gridSearch = e.target.value;
      state.gridPage = 1;
      renderGridTable();
    }, 250);
  });

  // ── Table Header Sort
  document.querySelectorAll('.data-table th[data-col]').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.getAttribute('data-col');
      state.gridSortBy === col
        ? (state.gridSortDir = state.gridSortDir === 'ASC' ? 'DESC' : 'ASC')
        : (state.gridSortBy = col, state.gridSortDir = 'DESC');
      renderGridTable();
    });
  });

  // ── Pagination
  document.getElementById('btn-prev-page').addEventListener('click', () => {
    if (state.gridPage > 1) { state.gridPage--; renderGridTable(); }
  });
  document.getElementById('btn-next-page').addEventListener('click', () => {
    state.gridPage++; renderGridTable();
  });

  // ── Currency
  document.querySelectorAll('.currency-toggle-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      document.querySelectorAll('.currency-toggle-btn').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      state.currency = e.target.getAttribute('data-curr');
      refreshDashboard();
    });
  });

  // ── Year Slider
  const yearSlider = document.getElementById('year-slider');
  const yearDisplay = document.getElementById('year-display');
  yearSlider.addEventListener('input', e => {
    state.currentYear = parseInt(e.target.value);
    yearDisplay.innerText = state.currentYear;
    refreshDashboard();
  });

  // ── Timeline Play/Pause
  document.getElementById('play-btn').addEventListener('click', () => {
    if (state.isPlaying) {
      clearInterval(state.playTimer);
      state.isPlaying = false;
      document.getElementById('play-btn').innerHTML = '▶';
    } else {
      state.isPlaying = true;
      document.getElementById('play-btn').innerHTML = '❚❚';
      state.playTimer = setInterval(() => {
        state.currentYear = state.currentYear >= 2024 ? 1980 : state.currentYear + 1;
        yearSlider.value = state.currentYear;
        yearDisplay.innerText = state.currentYear;
        refreshDashboard();
      }, 700);
    }
  });

  // ── Quick Sovereign Pills
  document.querySelectorAll('.sovereign-pill').forEach(pill => {
    pill.addEventListener('click', e => {
      const iso = e.target.getAttribute('data-iso');
      state.currentCountry = iso;
      document.getElementById('country-select').value = iso;
      updateQuickPills();
      refreshDashboard();
    });
  });

  // ── Chart Tab Buttons
  document.querySelectorAll('.chart-tab-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      document.querySelectorAll('.chart-tab-btn').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      state.activeChartTab = e.target.getAttribute('data-tab');
      showTabControls(state.activeChartTab);
      renderActiveChart();
    });
  });

  // ── Timeseries: Metric Select → re-draw chart
  document.addEventListener('change', e => {
    const id = e.target.id;

    if (id === 'ts-indicator-select') {
      state.timeseriesIndicator = e.target.value;
      renderActiveChart();
      return;
    }
    if (id === 'ts-countries-select') {
      renderActiveChart();
      return;
    }
    if (id === 'bench-indicator-select') {
      state.benchmarkIndicator = e.target.value;
      renderActiveChart();
      return;
    }
    if (id === 'bench-limit-select') {
      renderActiveChart();
      return;
    }
    if (id === 'corr-x-select') {
      state.correlationX = e.target.value;
      renderActiveChart();
      return;
    }
    if (id === 'corr-y-select') {
      state.correlationY = e.target.value;
      renderActiveChart();
      return;
    }
    if (id === 'radar-countries-select') {
      renderActiveChart();
      return;
    }
  });

  // ── Legacy: chart-metric-select (for backward compat if HTML still has it)
  const legacySel = document.getElementById('chart-metric-select');
  if (legacySel) {
    legacySel.addEventListener('change', e => {
      state.timeseriesIndicator = e.target.value;
      state.benchmarkIndicator = e.target.value;
      renderActiveChart();
    });
  }

  // ── Theme Toggle
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const html = document.documentElement;
      const isDark = html.getAttribute('data-theme') === 'dark';
      html.setAttribute('data-theme', isDark ? 'light' : 'dark');
      document.getElementById('theme-icon').textContent = isDark ? '☀️' : '🌙';
      document.getElementById('theme-text').textContent = isDark ? 'LIGHT' : 'DARK';
      renderActiveChart(); // redraw with new theme colors
    });
  }

  // ── Exports
  const exportFilteredCsv = () => {
    const p = new URLSearchParams({
      year: state.currentYear,
      region: state.currentRegion,
      income_group: state.currentIncome,
      iso_code: state.currentCountry,
      search: state.gridSearch,
    });
    window.open(`${API_BASE}/export/csv?${p}`, '_blank');
  };
  document.getElementById('btn-export-csv').addEventListener('click', exportFilteredCsv);
  document.getElementById('btn-table-export').addEventListener('click', exportFilteredCsv);

  // ── Responsive Resize
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => renderActiveChart(), 120);
  });

  // ── Hover Tooltip on Timeseries
  const canvas = document.getElementById('main-chart-canvas');
  const tooltip = document.getElementById('chart-tooltip');
  if (canvas && tooltip) {
    canvas.addEventListener('mousemove', e => {
      if (state.activeChartTab !== 'timeseries' || !window._ts) {
        tooltip.style.display = 'none';
        return;
      }
      const { series, years, indicator, pad, minVal, maxVal } = window._ts;
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const pw = canvas.clientWidth - pad.left - pad.right;

      if (mx < pad.left || mx > canvas.clientWidth - pad.right) {
        tooltip.style.display = 'none'; return;
      }

      const t = (mx - pad.left) / pw;
      const idx = Math.round(t * (years.length - 1));
      const year = years[idx];
      if (!year) { tooltip.style.display = 'none'; return; }

      let html = `<div style="font-weight:700;margin-bottom:4px;border-bottom:1px solid var(--rim-subtle);padding-bottom:2px;">YEAR: ${year}</div>`;
      series.forEach((s, si) => {
        const val = (s.data[indicator] || [])[idx];
        const col = COLORS[si % COLORS.length];
        html += `<div style="display:flex;justify-content:space-between;gap:10px;margin:2px 0;">
          <span style="color:${col}">■ ${s.country} (${s.iso_code})</span>
          <span style="font-weight:600;">${val !== undefined ? val.toFixed(1) : '—'}</span>
        </div>`;
      });

      tooltip.innerHTML = html;
      tooltip.style.left = `${Math.min(canvas.clientWidth - 190, mx + 14)}px`;
      tooltip.style.top = `${Math.max(10, e.clientY - rect.top - 36)}px`;
      tooltip.style.display = 'block';
    });

    canvas.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
  }
}

// ─── Helper: sync both region selects ────────────────────────────────────────
function syncRegionSelects(sourceId, value) {
  ['region-select', 'table-region-filter'].forEach(id => {
    if (id !== sourceId) {
      const el = document.getElementById(id);
      if (el) el.value = value;
    }
  });
}

// ─── Helper: update active pill ──────────────────────────────────────────────
function updateQuickPills() {
  document.querySelectorAll('.sovereign-pill').forEach(p => {
    p.classList.toggle('active', p.getAttribute('data-iso') === state.currentCountry);
  });
}

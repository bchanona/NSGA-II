const API = '';

// ── Estado global ──────────────────────────────────────────────────
let topSolutions = [];
let evoChart     = null;
let paretoChart  = null;
let paretoChart2 = null;

// ── Validar DOM al cargar ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  console.log('🔍 Validando elementos del DOM...');
  
  const requiredElements = [
    'n_posts', 'pop_size', 'generations', 'mutation_rate', 
    'hours_available', 'platform', 'btn-run', 'status-bar'
  ];
  
  let missing = [];
  requiredElements.forEach(id => {
    if (!document.getElementById(id)) {
      console.error(`❌ Elemento faltante: ${id}`);
      missing.push(id);
    } else {
      console.log(`✅ ${id}`);
    }
  });
  
  if (missing.length > 0) {
    console.error('⚠️ Elementos faltantes:', missing);
    document.getElementById('status-bar').textContent = `❌ Error: Elementos faltantes en la página: ${missing.join(', ')}`;
  } else {
    console.log('✅ Todos los elementos encontrados');
  }
});

const TYPE_COLORS = {
  reel:     '#8A5200',
  image:    '#0D6640',
  carousel: '#1A3FAA',
  short:    '#A31840',
  video:    '#5B18A8',
  story:    '#C24A12',
};
const TYPE_BG = {
  reel:     '#FFF4D6',
  image:    '#E6FAF0',
  carousel: '#E8F0FF',
  short:    '#FFE8EF',
  video:    '#F0EAFF',
  story:    '#FFF0E8',
};

// ── Optimizar ──────────────────────────────────────────────────────
async function runOptimize() {
  const btn = document.getElementById('btn-run');
  const sb  = document.getElementById('status-bar');

  btn.disabled = true;
  btn.classList.add('loading');
  sb.textContent = '⚙ Ejecutando algoritmo NSGA-II...';

  // Validación de elementos del DOM
  const getElementValue = (id, defaultValue) => {
    const el = document.getElementById(id);
    if (!el) {
      console.warn(`⚠️ Elemento no encontrado: ${id}`);
      return defaultValue;
    }
    return el.value;
  };

  const body = {
    n_posts:       +getElementValue('n_posts', 7),
    pop_size:      +getElementValue('pop_size', 60),
    generations:   +getElementValue('generations', 80),
    mutation_rate: +getElementValue('mutation_rate', 0.3),
    hours_available: +getElementValue('hours_available', 10),
    platform:      getElementValue('platform', 'instagram'),
  };

  console.log('📤 Enviando request con parámetros:', body);

  try {
    const r = await fetch(`${API}/api/optimize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(await r.text());
    const d = await r.json();
    sb.textContent = `✓ ${d.message}`;
    await loadAll();
  } catch (e) {
    sb.textContent = `✗ Error: ${e.message}`;
  } finally {
    btn.disabled = false;
    btn.classList.remove('loading');
  }
}

// ── Cargar todas las secciones ─────────────────────────────────────
async function loadAll() {
  await Promise.all([
    loadEvolution(),
    loadPareto(),
    loadTopSolutions(3),
    loadComparison(),
  ]);
  buildCalTabs();
  await loadCalendar(1);
}

// ── 1. Evolución ───────────────────────────────────────────────────
async function loadEvolution() {
  const wrap = document.getElementById('evo-wrap');
  const r = await fetch(`${API}/api/evolution`);
  if (!r.ok) return;
  const d = await r.json();

  wrap.innerHTML = '<canvas id="evo-canvas"></canvas>';
  const ctx = document.getElementById('evo-canvas').getContext('2d');
  if (evoChart) evoChart.destroy();

  evoChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: d.labels,
      datasets: [
        {
          label: 'Engagement',
          data: d.series.engagement,
          borderColor: '#FF6B35',
          backgroundColor: 'rgba(255,107,53,.08)',
          tension: .35, pointRadius: 0, borderWidth: 2.5,
        },
        {
          label: 'Alcance',
          data: d.series.reach,
          borderColor: '#4FACFE',
          backgroundColor: 'rgba(79,172,254,.08)',
          tension: .35, pointRadius: 0, borderWidth: 2.5,
        },
        {
          label: 'Retención',
          data: d.series.retention,
          borderColor: '#43E8A0',
          backgroundColor: 'rgba(67,232,160,.08)',
          tension: .35, pointRadius: 0, borderWidth: 2.5,
        },
        {
          label: 'Saturación',
          data: d.series.saturation,
          borderColor: '#F5C842',
          backgroundColor: 'rgba(245,200,66,.06)',
          tension: .35, pointRadius: 0, borderWidth: 1.5,
          borderDash: [5, 4],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { boxWidth: 12, font: { size: 11, family: "'DM Sans', sans-serif" }, color: '#3B4A6B' },
        },
        tooltip: {
          backgroundColor: '#0D1B3E',
          titleColor: '#F5C842',
          bodyColor: '#E8EEF8',
          borderColor: 'rgba(255,255,255,.1)',
          borderWidth: 1,
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(4)}`,
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: 'Generación', font: { size: 11 }, color: '#8B9BBF' },
          grid: { color: 'rgba(13,27,62,.06)' },
          ticks: { color: '#8B9BBF', font: { size: 10 } },
        },
        y: {
          title: { display: true, text: 'Valor promedio (normalizado)', font: { size: 11 }, color: '#8B9BBF' },
          grid: { color: 'rgba(13,27,62,.06)' },
          ticks: { color: '#8B9BBF', font: { size: 10 } },
          min: 0,
        },
      },
    },
  });
}

// ── 2. Pareto ──────────────────────────────────────────────────────
async function loadPareto() {
  const r = await fetch(`${API}/api/pareto`);
  if (!r.ok) return;
  const d = await r.json();
  const pts = d.points;

  const tooltipBase = {
    backgroundColor: '#0D1B3E',
    titleColor: '#F5C842',
    bodyColor: '#E8EEF8',
    borderColor: 'rgba(255,255,255,.1)',
    borderWidth: 1,
  };
  const scaleBase = {
    grid: { color: 'rgba(13,27,62,.06)' },
    ticks: { color: '#8B9BBF', font: { size: 10 } },
  };

  // Gráfico 1: Engagement vs Alcance
  document.getElementById('pareto-sk').style.display = 'none';
  const c1 = document.getElementById('pareto-chart');
  c1.style.display = 'block';
  if (paretoChart) paretoChart.destroy();

  paretoChart = new Chart(c1.getContext('2d'), {
    type: 'scatter',
    data: {
      datasets: [{
        label: 'Solución Pareto',
        data: pts.map(p => ({ x: p.engagement, y: p.reach })),
        backgroundColor: pts.map(p => `rgba(79,172,254,${0.25 + p.retention * 0.75})`),
        borderColor: pts.map(p => `rgba(79,172,254,${0.5 + p.retention * 0.5})`),
        pointRadius: 6,
        pointHoverRadius: 10,
        borderWidth: 1.5,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          ...tooltipBase,
          callbacks: {
            label: ctx => {
              const p = pts[ctx.dataIndex];
              return [`Eng: ${p.engagement.toFixed(3)}`, `Reach: ${p.reach.toFixed(3)}`, `Ret: ${p.retention.toFixed(3)}`];
            },
          },
        },
      },
      scales: {
        x: { ...scaleBase, title: { display: true, text: 'Engagement', font: { size: 11 }, color: '#8B9BBF' } },
        y: { ...scaleBase, title: { display: true, text: 'Alcance',    font: { size: 11 }, color: '#8B9BBF' } },
      },
    },
  });

  // Gráfico 2: Engagement vs Saturación
  document.getElementById('pareto-sk2').style.display = 'none';
  const c2 = document.getElementById('pareto-chart2');
  c2.style.display = 'block';
  if (paretoChart2) paretoChart2.destroy();

  paretoChart2 = new Chart(c2.getContext('2d'), {
    type: 'scatter',
    data: {
      datasets: [{
        label: 'Solución Pareto',
        data: pts.map(p => ({ x: p.engagement, y: p.saturation })),
        backgroundColor: pts.map(p => `rgba(255,107,53,${0.25 + p.prod_time * 0.75})`),
        borderColor: 'rgba(255,107,53,.55)',
        pointRadius: 6,
        pointHoverRadius: 10,
        borderWidth: 1.5,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          ...tooltipBase,
          callbacks: {
            label: ctx => {
              const p = pts[ctx.dataIndex];
              return [`Eng: ${p.engagement.toFixed(3)}`, `Sat: ${p.saturation.toFixed(3)}`, `Prod: ${p.prod_time.toFixed(3)}`];
            },
          },
        },
      },
      scales: {
        x: { ...scaleBase, title: { display: true, text: 'Engagement',  font: { size: 11 }, color: '#8B9BBF' } },
        y: { ...scaleBase, title: { display: true, text: 'Saturación',  font: { size: 11 }, color: '#8B9BBF' } },
      },
    },
  });
}

// ── 3. Top Solutions ───────────────────────────────────────────────
async function loadTopSolutions(n = 3) {
  const r = await fetch(`${API}/api/top-solutions?n=${n}`);
  if (!r.ok) return;
  const d = await r.json();
  topSolutions = d.solutions;

  const tabsEl = document.getElementById('sol-tabs');
  tabsEl.innerHTML = '';
  topSolutions.forEach((sol, i) => {
    const btn = document.createElement('button');
    btn.className = `sol-tab${i === 0 ? ' active' : ''}`;
    btn.textContent = `Solución #${sol.rank}`;
    btn.onclick = () => renderSolution(i);
    tabsEl.appendChild(btn);
  });

  renderSolution(0);
}

function renderSolution(idx) {
  document.querySelectorAll('.sol-tab').forEach((t, i) => t.classList.toggle('active', i === idx));
  const sol = topSolutions[idx];
  const m   = sol.metrics;

  document.getElementById('sol-metrics').innerHTML = `
    <span class="stat eng"><span class="stat-dot"></span>Eng: ${m.engagement.toFixed(4)}</span>
    <span class="stat rch"><span class="stat-dot"></span>Reach: ${m.reach.toFixed(4)}</span>
    <span class="stat ret"><span class="stat-dot"></span>Ret: ${m.retention.toFixed(4)}</span>
    <span class="stat sat"><span class="stat-dot"></span>Sat: ${m.saturation.toFixed(4)}</span>
    <span class="stat prd"><span class="stat-dot"></span>Prod: ${m.prod_hours.toFixed(1)}h</span>
  `;

  document.getElementById('sol-body').innerHTML = sol.posts.map(p => `
    <tr>
      <td>${p.day_name}</td>
      <td><span style="font-family:var(--font-mono);font-size:.85rem">${p.hour_fmt}</span></td>
      <td><span class="type-badge type-${p.type}">${typeIcon(p.type)} ${p.type}</span></td>
      <td style="font-family:var(--font-mono);font-size:.83rem">${m.engagement.toFixed(4)}</td>
      <td style="font-family:var(--font-mono);font-size:.83rem">${m.reach.toFixed(4)}</td>
      <td style="font-family:var(--font-mono);font-size:.83rem">${m.retention.toFixed(4)}</td>
      <td style="font-family:var(--font-mono);font-size:.83rem">${m.saturation.toFixed(4)}</td>
      <td style="font-family:var(--font-mono);font-size:.83rem">${p.prod_cost.toFixed(1)}h</td>
    </tr>
  `).join('');
}

// ── 4. Calendario ──────────────────────────────────────────────────
function buildCalTabs() {
  const el = document.getElementById('cal-tabs');
  el.innerHTML = '';
  [1, 2, 3].forEach(rank => {
    const btn = document.createElement('button');
    btn.className = `cal-tab${rank === 1 ? ' active' : ''}`;
    btn.textContent = `Solución #${rank}`;
    btn.onclick = () => loadCalendar(rank);
    el.appendChild(btn);
  });
}

async function loadCalendar(rank) {
  document.querySelectorAll('.cal-tab').forEach((t, i) => t.classList.toggle('active', i === rank - 1));
  const r = await fetch(`${API}/api/calendar/${rank}`);
  if (!r.ok) return;
  const d = await r.json();

  document.getElementById('week-grid').innerHTML = d.calendar.map(day => `
    <div class="day-col">
      <div class="day-header">${day.name.slice(0, 3).toUpperCase()}</div>
      <div class="day-posts">
        ${day.posts.length
          ? day.posts.map(p => `
              <div class="post-pill"
                style="background:${TYPE_BG[p.type] || '#F0EDE6'};border-left-color:${TYPE_COLORS[p.type] || '#8B9BBF'}">
                <div class="ph">${p.hour_fmt}</div>
                <div class="pt">${typeIcon(p.type)} ${p.type}</div>
              </div>`)
            .join('')
          : '<div class="day-empty">— libre —</div>'
        }
      </div>
    </div>
  `).join('');
}

// ── 5. Comparación ─────────────────────────────────────────────────
async function loadComparison() {
  const r = await fetch(`${API}/api/comparison`);
  if (!r.ok) return;
  const d = await r.json();

  const metrics = [
    { k: 'engagement', label: 'Engagement',      higher: true,  color: '#FF6B35' },
    { k: 'reach',      label: 'Alcance',          higher: true,  color: '#4FACFE' },
    { k: 'retention',  label: 'Retención',        higher: true,  color: '#43E8A0' },
    { k: 'saturation', label: 'Saturación',       higher: false, color: '#F5C842' },
    { k: 'prod_time',  label: 'T. Producción',    higher: false, color: '#FF6B8A' },
  ];

  const maxVals = {};
  metrics.forEach(m => { maxVals[m.k] = Math.max(d.initial[m.k], d.optimized[m.k], 0.01); });

  const barRow = (m, val, opacity = '88') => `
    <div class="cmp-metric">
      <div class="cmp-label">${m.label}</div>
      <div class="cmp-bar-wrap">
        <div class="cmp-bar-bg">
          <div class="cmp-bar" style="width:${(val / maxVals[m.k] * 100).toFixed(1)}%;background:${m.color}${opacity}"></div>
        </div>
        <div class="cmp-val">${val.toFixed(3)}</div>
      </div>
    </div>`;

  const deltaEl = (m) => {
    const delta = d.deltas[m.k];
    const improved = m.higher ? delta > 0 : delta < 0;
    const cls = Math.abs(delta) < 1 ? 'neu' : (improved ? 'pos' : 'neg');
    return `<div class="delta ${cls}">${delta > 0 ? '+' : ''}${delta.toFixed(1)}%</div>`;
  };

  document.getElementById('cmp-card').innerHTML = `
    <div class="cmp-grid">
      <div>
        <div class="cmp-col-title">
          <span style="color:var(--muted)">⬡</span>
          Estrategia aleatoria <em style="font-weight:300;font-style:normal">(n=${d.initial_size})</em>
        </div>
        ${metrics.map(m => barRow(m, d.initial[m.k], '66')).join('')}
      </div>
      <div class="cmp-arrow">
        ${metrics.map(deltaEl).join('')}
      </div>
      <div>
        <div class="cmp-col-title">
          <span style="color:var(--coral)">◆</span>
          Estrategia optimizada <em style="font-weight:300;font-style:normal">(n=${d.optimized_size})</em>
        </div>
        ${metrics.map(m => barRow(m, d.optimized[m.k], 'FF')).join('')}
      </div>
    </div>`;
}

// ── Utilidades ─────────────────────────────────────────────────────
function typeIcon(t) {
  return { reel: '🎬', image: '📷', carousel: '🎠', short: '⚡', video: '📹', story: '✨' }[t] || '📌';
}

// ── Init ───────────────────────────────────────────────────────────
(async () => {
  const r = await fetch(`${API}/api/status`).catch(() => null);
  if (!r) return;
  const d = await r.json();
  if (d.ready) {
    document.getElementById('status-bar').textContent = '✓ Datos previos disponibles. Cargando...';
    await loadAll();
  }
})();
/* =================================================================
   Comparación 3D de población por condado · Arkansas vs Texas
   Datos: U.S. Census Bureau (TIGERweb + Population Estimates)
   Render: MapLibre GL JS (fill-extrusion 3D, sin API key)
   ================================================================= */

const YEARS = [2000, 2010, 2020];
const state = { metric: 'pop', year: 2020, playing: false, timer: null, sync: true };

// rampa de color monocromática (pocos = oscuro -> muchos = claro)
const RAMP = ['#1c1c1c', '#3a3a3a', '#585858', '#787878', '#9e9e9e', '#c8c8c8', '#ffffff'];

// escalas de extrusión: metros de altura por unidad
const EXTRUDE = {
  pop: 0.09,       // ~ pop * 0.09  (Harris 4.7M -> ~425 km de alto escalado)
  growth: 2200,    // ~ growth% * 2200
};

let geo = null, stats = null, maps = {}, hovered = { AR: null, TX: null };

/* estilo base oscuro sin API key (raster CARTO dark via demotiles alternativo) */
function baseStyle() {
  return {
    version: 8,
    glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
    sources: {
      carto: {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        attribution: 'Esri · U.S. Census Bureau',
      },
    },
    layers: [
      { id: 'bg', type: 'background', paint: { 'background-color': '#000000' } },
      { id: 'carto', type: 'raster', source: 'carto', paint: { 'raster-opacity': 0.5 } },
    ],
  };
}

const fmt = n => n == null ? '—' : Math.round(n).toLocaleString('en-US');
const fmtK = n => n == null ? '—' : n >= 1e6 ? (n/1e6).toFixed(2)+'M' : n >= 1e3 ? (n/1e3).toFixed(0)+'k' : fmt(n);

function metricVal(p, year) {
  return state.metric === 'pop' ? p['pop' + year] : p.growth;
}

/* expresiones MapLibre para color y altura */
function colorExpr() {
  const field = state.metric === 'pop' ? 'pop' + state.year : 'growth';
  // dominios aproximados por métrica
  const stops = state.metric === 'pop'
    ? [0, 5000, 15000, 40000, 120000, 500000, 2000000, 4800000]
    : [-30, -10, 0, 20, 50, 100, 200];
  const expr = ['interpolate', ['linear'], ['coalesce', ['get', field], 0]];
  const n = stops.length;
  stops.forEach((s, i) => {
    expr.push(s);
    expr.push(RAMP[Math.min(i, RAMP.length - 1)]);
  });
  return expr;
}

function heightExpr() {
  const field = state.metric === 'pop' ? 'pop' + state.year : 'growth';
  const k = EXTRUDE[state.metric];
  // altura = max(0, valor) * k   (crecimiento negativo => altura 0)
  return ['*', ['max', 0, ['coalesce', ['get', field], 0]], k];
}

function makeMap(container, stateFips, center, zoom) {
  const m = new maplibregl.Map({
    container,
    style: baseStyle(),
    center,
    zoom,
    pitch: 55,
    bearing: -18,
    maxPitch: 75,
    attributionControl: false,
  });
  m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'bottom-right');

  m.on('load', () => {
    const feats = { type: 'FeatureCollection',
      features: geo.features.filter(f => f.properties.state === stateFips) };
    m.addSource('counties', { type: 'geojson', data: feats });

    m.addLayer({
      id: 'extrusion', type: 'fill-extrusion', source: 'counties',
      paint: {
        'fill-extrusion-color': colorExpr(),
        'fill-extrusion-height': heightExpr(),
        'fill-extrusion-base': 0,
        'fill-extrusion-opacity': 0.9,
        'fill-extrusion-vertical-gradient': true,
      },
    });
    m.addLayer({
      id: 'edges', type: 'line', source: 'counties',
      paint: { 'line-color': '#000000', 'line-width': 0.4, 'line-opacity': 0.6 },
    });

    const code = stateFips === '05' ? 'AR' : 'TX';
    m.on('mousemove', 'extrusion', e => {
      m.getCanvas().style.cursor = 'pointer';
      showHover(e.features[0].properties, e.originalEvent, code);
    });
    m.on('mouseleave', 'extrusion', () => {
      m.getCanvas().style.cursor = '';
      document.getElementById('hoverCard').classList.add('hidden');
    });
  });

  return m;
}

/* sincronización de cámaras */
let syncing = false;
function linkMaps(a, b) {
  function sync(src, dst) {
    src.on('move', () => {
      if (!state.sync || syncing) return;
      syncing = true;
      dst.jumpTo({
        center: src.getCenter(), zoom: src.getZoom(),
        bearing: src.getBearing(), pitch: src.getPitch(),
      });
      syncing = false;
    });
  }
  sync(a, b);
  sync(b, a);
}

/* actualizar paint de ambos mapas */
function refresh() {
  ['AR', 'TX'].forEach(k => {
    const m = maps[k];
    if (!m || !m.getLayer || !m.getLayer('extrusion')) return;
    m.setPaintProperty('extrusion', 'fill-extrusion-color', colorExpr());
    m.setPaintProperty('extrusion', 'fill-extrusion-height', heightExpr());
  });
  updateHeads();
  updateLegend();
  updateInsights();
}

/* paneles de estadísticas por estado */
function updateHeads() {
  [['AR', '05'], ['TX', '48']].forEach(([code, fips]) => {
    const s = stats.states[fips];
    const pop = s.pop[state.year];
    const prev = state.year === 2000 ? null : s.pop[YEARS[YEARS.indexOf(state.year) - 1]];
    const chg = prev ? ((pop - prev) / prev * 100).toFixed(1) : null;
    document.getElementById('stats' + code).innerHTML = `
      <div class="mh-big">${fmtK(pop)}</div>
      <div class="mh-row"><span>Población ${state.year}</span><b>${fmt(pop)}</b></div>
      <div class="mh-row"><span>Condados</span><b>${s.counties}</b></div>
      <div class="mh-row"><span>Crec. 2000–2020</span><b>${s.growth_2000_2020}%</b></div>
      ${chg ? `<div class="mh-row"><span>Δ vs década ant.</span><b>${chg>0?'+':''}${chg}%</b></div>` : ''}`;
  });
}

function updateLegend() {
  const el = document.getElementById('legend');
  const isPop = state.metric === 'pop';
  const lo = isPop ? '0' : '−30%';
  const hi = isPop ? (state.year === 2020 ? '4.7M' : '4.1M') : '+200%';
  el.innerHTML = `
    <span class="lg-title">${isPop ? 'Población '+state.year : 'Crecimiento 2000→2020'}</span>
    <div>
      <div class="ramp">${RAMP.map(c=>`<i style="background:${c}"></i>`).join('')}</div>
      <div class="lg-ends"><span>${lo}</span><span>${hi}</span></div>
    </div>
    <span class="lg-title">altura ∝ ${isPop ? 'población' : 'crecimiento'}</span>`;
}

function updateInsights() {
  const ar = stats.states['05'], tx = stats.states['48'];
  const ratio = (tx.pop[state.year] / ar.pop[state.year]).toFixed(1);
  const topAR = ar.top_pop[0], topTX = tx.top_pop[0];
  const fastTX = tx.fastest[0];
  document.getElementById('insights').innerHTML = [
    `<div class="insight"><span class="lab">Texas es</span> <b class="tx-c">${ratio}×</b> <span class="lab">más poblado que Arkansas (${state.year})</span></div>`,
    `<div class="insight"><span class="lab">Condado mayor AR</span> <b class="ar-c">${topAR.name}</b> <b>${fmtK(topAR.pop)}</b></div>`,
    `<div class="insight"><span class="lab">Condado mayor TX</span> <b class="tx-c">${topTX.name}</b> <b>${fmtK(topTX.pop)}</b></div>`,
    `<div class="insight"><span class="lab">TX creció</span> <b class="tx-c">+${tx.growth_2000_2020}%</b> <span class="lab">vs AR</span> <b class="ar-c">+${ar.growth_2000_2020}%</b> <span class="lab">(2000–2020)</span></div>`,
    `<div class="insight"><span class="lab">Más rápido TX</span> <b class="tx-c">${fastTX.name}</b> <b>+${fastTX.growth}%</b></div>`,
  ].join('');
}

function showHover(p, ev, code) {
  const card = document.getElementById('hoverCard');
  const col = code === 'AR' ? 'var(--ar)' : 'var(--tx)';
  card.style.borderColor = col;
  const g = p.growth;
  card.innerHTML = `
    <span class="hc-state" style="background:${col}22;color:${col}">${p.state_name}</span>
    <h3>${p.name} County</h3>
    <div class="hc-row">Pob. ${state.year} <b>${fmt(p['pop'+state.year])}</b></div>
    <div class="hc-row">2000 → 2020 <b>${fmt(p.pop2000)} → ${fmt(p.pop2020)}</b></div>
    <div class="hc-row">Crecimiento <b style="color:${g>=0?'#ffffff':'#8a8a8a'}">${g>=0?'+':''}${g}%</b></div>`;
  card.classList.remove('hidden');
  card.style.left = (ev.clientX + 16) + 'px';
  card.style.top = (ev.clientY + 16) + 'px';
}

/* controles */
function bind() {
  document.querySelectorAll('.seg-btn').forEach(b => b.onclick = () => {
    document.querySelectorAll('.seg-btn').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    state.metric = b.dataset.metric;
    // crecimiento es fijo 2000->2020; desactivar años
    document.querySelectorAll('.yr-btn').forEach(y => y.style.opacity = state.metric === 'growth' ? .4 : 1);
    refresh();
  });

  document.querySelectorAll('.yr-btn').forEach(b => b.onclick = () => {
    if (state.metric === 'growth') return;
    document.querySelectorAll('.yr-btn').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    state.year = +b.dataset.year;
    refresh();
  });

  document.getElementById('playBtn').onclick = togglePlay;
  document.getElementById('syncBtn').onclick = () => {
    state.sync = !state.sync;
    const btn = document.getElementById('syncBtn');
    btn.classList.toggle('active', state.sync);
    btn.textContent = state.sync ? 'Sincronizado' : 'Independiente';
  };
}

function togglePlay() {
  const btn = document.getElementById('playBtn');
  if (state.playing) {
    clearInterval(state.timer); state.playing = false; btn.textContent = 'Animar 2000–2020'; return;
  }
  if (state.metric === 'growth') {
    document.querySelector('.seg-btn[data-metric="pop"]').click();
  }
  state.playing = true; btn.textContent = 'Pausar';
  let i = YEARS.indexOf(state.year);
  state.timer = setInterval(() => {
    i = (i + 1) % YEARS.length;
    document.querySelector(`.yr-btn[data-year="${YEARS[i]}"]`).click();
  }, 1500);
}

/* init */
async function init() {
  [geo, stats] = await Promise.all([
    fetch('data/compare.geojson').then(r => r.json()),
    fetch('data/compare_stats.json').then(r => r.json()),
  ]);

  maps.AR = makeMap('mapAR', '05', [-92.4, 34.8], 5.9);
  maps.TX = makeMap('mapTX', '48', [-99.3, 31.3], 4.7);

  let loaded = 0;
  ['AR', 'TX'].forEach(k => maps[k].on('load', () => {
    if (++loaded === 2) { linkMaps(maps.AR, maps.TX); refresh(); }
  }));

  bind();
  updateHeads(); updateLegend(); updateInsights();
}

init();

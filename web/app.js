/* ============================================================
   Observatorio de Gobernanza de Datos Geoespaciales · Arkansas
   Fuente: Arkansas GIS Office (geodata.gis.arkansas.gov)
   ============================================================ */

const DECADES = [1900,1910,1920,1930,1940,1950,1960,1970,1980,1990,2000,2010,2020];

// Escala de color secuencial (oscuro -> claro-calido)
const RAMP = ['#0d2b3e','#11465c','#1f7a7a','#36a89a','#5fd0a8','#9ee6a0','#f2e394','#f6a94a','#e8622a'];

const LAYER_LABELS = { counties: 'Condados', municipalities: 'Municipios', congress: 'Distritos Congresionales' };

const state = {
  layer: 'counties',
  metric: 'pop',
  year: 2020,
  playing: false,
  playTimer: null,
  bubbles: false,
};

let map, geoLayer, bubbleLayer, data = {}, stats = {}, dictionary = {}, quality = {};
let currentScale = null;

/* ---------------- utilidades ---------------- */
const fmt = n => (n == null || isNaN(n)) ? '—' : Math.round(n).toLocaleString('en-US');
const fmtK = n => n == null ? '—' : n >= 1e6 ? (n/1e6).toFixed(2)+'M' : n >= 1e3 ? (n/1e3).toFixed(0)+'k' : fmt(n);

function metricValue(props) {
  if (state.layer === 'congress') return 1;
  const pop = props['pop' + state.year];
  if (state.metric === 'pop') return pop;
  if (state.metric === 'density') {
    const sm = props.sq_miles;
    return (pop != null && sm) ? pop / sm : null;
  }
  if (state.metric === 'growth') {
    const base = state.layer === 'counties' ? props.pop1900 : props.pop2000;
    const cur = state.layer === 'counties' ? props['pop'+state.year] : props.pop2020;
    if (!base || cur == null) return null;
    return ((cur - base) / base) * 100;
  }
  return pop;
}

function metricLabel() {
  return state.metric === 'pop' ? 'Población' : state.metric === 'density' ? 'Densidad' : 'Crecimiento';
}

function colorScale(features) {
  const vals = features.map(f => metricValue(f.properties)).filter(v => v != null && !isNaN(v)).sort((a,b)=>a-b);
  if (!vals.length) return { fn: () => RAMP[0], breaks: [] };
  const breaks = [];
  for (let i = 1; i < RAMP.length; i++) breaks.push(vals[Math.floor((i / RAMP.length) * vals.length)]);
  const fn = v => {
    if (v == null || isNaN(v)) return '#2a3150';
    for (let i = 0; i < breaks.length; i++) if (v <= breaks[i]) return RAMP[i];
    return RAMP[RAMP.length - 1];
  };
  return { fn, breaks };
}

/* ---------------- estilos ---------------- */
function styleFor(feature) {
  if (state.layer === 'congress') {
    const palette = ['#b388ff','#8c9eff','#80d8ff','#a0f0c0'];
    const d = parseInt(feature.properties.district) || 1;
    return { color: '#0b1020', weight: 1.4, fillColor: palette[(d-1)%palette.length], fillOpacity: .6 };
  }
  const v = metricValue(feature.properties);
  return { color: '#0b1020', weight: .8, fillColor: currentScale.fn(v), fillOpacity: state.bubbles ? .35 : .85 };
}

/* ---------------- interacciones ---------------- */
function onEachFeature(feature, lyr) {
  lyr.on('mouseover', e => {
    e.target.setStyle({ weight: 2.4, color: '#ffffff' });
    e.target.bringToFront();
    showInfo(feature.properties, e.originalEvent);
  });
  lyr.on('mousemove', e => positionInfo(e.originalEvent));
  lyr.on('mouseout', e => {
    geoLayer.resetStyle(e.target);
    document.getElementById('infoCard').classList.add('hidden');
  });
  lyr.on('click', () => {
    if (state.layer === 'counties') drawCountyTrend(feature.properties);
    map.fitBounds(lyr.getBounds(), { maxZoom: 9, padding: [40,40] });
  });
}

function showInfo(p, ev) {
  const card = document.getElementById('infoCard');
  let html = '';
  if (state.layer === 'counties') {
    html = `<h3>${p.name} County</h3>
      <div class="ic-row">Pob. ${state.year} <b>${fmt(p['pop'+state.year])}</b></div>
      <div class="ic-row">Superficie <b>${fmt(p.sq_miles)} mi²</b></div>
      <div class="ic-row">Densidad <b>${p.sq_miles ? (p['pop'+state.year]/p.sq_miles).toFixed(1) : '—'}/mi²</b></div>
      <div class="ic-row">FIPS <b>05${p.fips}</b></div>
      <span class="tag">clic → serie histórica</span>`;
  } else if (state.layer === 'municipalities') {
    html = `<h3>${p.name}</h3>
      <div class="ic-row">Pob. 2020 <b>${fmt(p.pop2020)}</b></div>
      <div class="ic-row">Pob. 2010 <b>${fmt(p.pop2010)}</b></div>
      <div class="ic-row">Superficie <b>${(p.sq_miles||0).toFixed(2)} mi²</b></div>
      <span class="tag">${p.classification || 'N/D'}</span>`;
  } else {
    html = `<h3>Distrito Congresional ${p.district}</h3>
      <div class="ic-row">Cámara de Representantes de EE. UU.</div>`;
  }
  card.innerHTML = html;
  card.classList.remove('hidden');
  positionInfo(ev);
}

function positionInfo(ev) {
  const card = document.getElementById('infoCard');
  const wrap = document.getElementById('map-wrap').getBoundingClientRect();
  let x = ev.clientX - wrap.left + 16;
  let y = ev.clientY - wrap.top + 16;
  if (x + 200 > wrap.width) x = ev.clientX - wrap.left - 200;
  if (y + 160 > wrap.height) y = ev.clientY - wrap.top - 160;
  card.style.left = x + 'px';
  card.style.top = y + 'px';
}

/* ---------------- burbujas proporcionales ---------------- */
function renderBubbles() {
  if (bubbleLayer) { map.removeLayer(bubbleLayer); bubbleLayer = null; }
  if (!state.bubbles || state.layer === 'congress') return;
  const fc = data[state.layer].features;
  const vals = fc.map(f => f.properties['pop'+state.year] || f.properties.pop2020 || 0);
  const maxV = Math.max(...vals, 1);
  bubbleLayer = L.layerGroup();
  fc.forEach(f => {
    const p = f.properties;
    const lat = p._lat, lon = p._lon;
    if (lat == null || lon == null) return;
    const v = (state.layer === 'counties' ? p['pop'+state.year] : p.pop2020) || 0;
    const r = 3 + Math.sqrt(v / maxV) * 26;
    L.circleMarker([lat, lon], {
      radius: r, color: '#fff', weight: .8, fillColor: '#f6a94a', fillOpacity: .55,
    }).bindTooltip(`${p.name}: ${fmt(v)}`, { direction: 'top' }).addTo(bubbleLayer);
  });
  bubbleLayer.addTo(map);
}

/* ---------------- render principal ---------------- */
function render() {
  if (geoLayer) map.removeLayer(geoLayer);
  const fc = data[state.layer];
  if (!fc) return;
  if (state.layer !== 'congress') currentScale = colorScale(fc.features);
  geoLayer = L.geoJSON(fc, { style: styleFor, onEachFeature }).addTo(map);
  renderBubbles();
  buildLegend();
  updateKPIs();
  togglePanels();
  buildRanking();
  updateExportNote();
}

function togglePanels() {
  const isCounty = state.layer === 'counties';
  const isCongress = state.layer === 'congress';
  document.getElementById('choroplethPanel').style.display = isCongress ? 'none' : 'block';
  document.getElementById('timePanel').style.display = isCounty ? 'block' : 'none';
  document.getElementById('rankPanel').style.display = isCongress ? 'none' : 'block';
  document.querySelector('[data-metric="growth"]').style.display = isCounty ? 'block' : 'none';
  document.getElementById('metricHint').textContent =
    state.metric === 'pop' ? 'población' : state.metric === 'density' ? 'densidad' : 'crecimiento';
  document.getElementById('rankMetricLabel').textContent = metricLabel();
}

function buildLegend() {
  const el = document.getElementById('legend');
  if (state.layer === 'congress') { el.innerHTML = '<div class="row">4 distritos federales de EE. UU.</div>'; return; }
  const b = currentScale.breaks;
  const unit = state.metric === 'density' ? '/mi²' : state.metric === 'growth' ? '%' : '';
  let rows = '';
  for (let i = 0; i < RAMP.length; i++) {
    const lo = i === 0 ? 0 : b[i-1];
    const hi = b[i] != null ? b[i] : '+';
    const label = state.metric === 'growth'
      ? `${Math.round(lo)}${unit} – ${hi==='+'?'+':Math.round(hi)+unit}`
      : `${fmtK(lo)} – ${hi==='+'?'+':fmtK(hi)}${unit}`;
    rows += `<div class="row"><span class="sw" style="background:${RAMP[i]}"></span>${label}</div>`;
  }
  el.innerHTML = rows;
}

function updateKPIs() {
  const strip = document.getElementById('kpiStrip');
  let kpis = [];
  if (state.layer === 'counties') {
    const fc = data.counties.features;
    const totPop = fc.reduce((s,f)=> s + (f.properties['pop'+state.year]||0), 0);
    const totArea = fc.reduce((s,f)=> s + (f.properties.sq_miles||0), 0);
    kpis = [
      { v: fmtK(totPop), l: `Población ${state.year}`, a: true },
      { v: '75', l: 'Condados' },
      { v: (totPop/totArea).toFixed(1), l: 'Densidad /mi²' },
      { v: fmtK(totArea)+' mi²', l: 'Superficie' },
    ];
  } else if (state.layer === 'municipalities') {
    kpis = [
      { v: '200', l: 'Municipios', a: true },
      { v: fmtK(stats.municipalities.total_pop2020), l: 'Pob. urbana 2020' },
      { v: (stats.municipalities.by_class['First Class']||0), l: 'Primera clase' },
      { v: (stats.municipalities.by_class['Second Class']||0), l: 'Segunda clase' },
    ];
  } else {
    kpis = [
      { v: '4', l: 'Distritos fed.', a: true },
      { v: fmtK(stats.counties.total_pop2020), l: 'Pob. estatal 2020' },
    ];
  }
  strip.innerHTML = kpis.map(k =>
    `<div class="kpi"><div class="k-val ${k.a?'accent':''}">${k.v}</div><div class="k-lab">${k.l}</div></div>`
  ).join('');
}

/* ---------------- ranking ---------------- */
function buildRanking() {
  const el = document.getElementById('rankList');
  if (!el || state.layer === 'congress') { if (el) el.innerHTML=''; return; }
  const fc = data[state.layer].features.slice();
  const scored = fc.map(f => ({ f, v: metricValue(f.properties) }))
    .filter(x => x.v != null && !isNaN(x.v))
    .sort((a,b) => b.v - a.v).slice(0, 10);
  const unit = state.metric === 'density' ? '/mi²' : state.metric === 'growth' ? '%' : '';
  const maxV = scored.length ? scored[0].v : 1;
  el.innerHTML = scored.map((x, i) => {
    const p = x.f.properties;
    const val = state.metric === 'growth' ? x.v.toFixed(0)+unit
      : state.metric === 'density' ? x.v.toFixed(0)+unit : fmtK(x.v);
    const w = Math.max(4, (x.v / maxV) * 100);
    return `<button class="rank-row" data-name="${p.name}">
      <span class="rk-i">${i+1}</span>
      <span class="rk-name">${p.name}</span>
      <span class="rk-bar"><span style="width:${w}%"></span></span>
      <span class="rk-val">${val}</span>
    </button>`;
  }).join('');
  el.querySelectorAll('.rank-row').forEach(btn => {
    btn.onclick = () => focusByName(btn.dataset.name);
  });
}

/* ---------------- búsqueda ---------------- */
function bindSearch() {
  const box = document.getElementById('searchBox');
  const results = document.getElementById('searchResults');
  box.oninput = () => {
    const q = box.value.trim().toLowerCase();
    if (q.length < 2) { results.innerHTML = ''; results.classList.remove('open'); return; }
    const pool = [];
    ['counties','municipalities'].forEach(layer => {
      data[layer].features.forEach(f => {
        if (f.properties.name && f.properties.name.toLowerCase().includes(q))
          pool.push({ layer, name: f.properties.name });
      });
    });
    const items = pool.slice(0, 8);
    results.innerHTML = items.map(it =>
      `<button class="sr-item" data-layer="${it.layer}" data-name="${it.name}">
        <span class="sr-dot ${it.layer==='counties'?'c-county':'c-muni'}"></span>
        ${it.name}<small>${it.layer==='counties'?'Condado':'Municipio'}</small>
      </button>`).join('') || '<div class="sr-empty">Sin resultados</div>';
    results.classList.add('open');
    results.querySelectorAll('.sr-item').forEach(btn => {
      btn.onclick = () => {
        if (btn.dataset.layer !== state.layer) switchLayer(btn.dataset.layer);
        focusByName(btn.dataset.name);
        results.classList.remove('open');
        box.value = btn.dataset.name;
      };
    });
  };
  document.addEventListener('click', e => {
    if (!e.target.closest('.search-wrap')) results.classList.remove('open');
  });
}

function focusByName(name) {
  let target = null;
  geoLayer.eachLayer(l => {
    if (l.feature && l.feature.properties.name === name) target = l;
  });
  if (!target) return;
  map.fitBounds(target.getBounds(), { maxZoom: 9, padding: [60,60] });
  const orig = target.options;
  target.setStyle({ weight: 3.5, color: '#fff' });
  setTimeout(() => geoLayer.resetStyle(target), 1800);
  if (state.layer === 'counties') drawCountyTrend(target.feature.properties);
}

/* ---------------- gráficos SVG ---------------- */
function lineChart(points, labels, title, sub) {
  const svg = document.getElementById('trendChart');
  document.getElementById('cpTitle').textContent = title;
  document.getElementById('cpSub').textContent = sub || '';
  document.getElementById('chartPanel').style.display = 'block';
  const W = 320, H = 150, pad = { l: 34, r: 10, t: 12, b: 20 };
  const max = Math.max(...points), min = Math.min(...points, 0);
  const x = i => pad.l + (i/(points.length-1)) * (W - pad.l - pad.r);
  const y = v => H - pad.b - ((v - min)/(max - min || 1)) * (H - pad.t - pad.b);
  const path = points.map((v,i)=> (i===0?'M':'L') + x(i).toFixed(1) + ' ' + y(v).toFixed(1)).join(' ');
  const area = path + ` L ${x(points.length-1)} ${H-pad.b} L ${x(0)} ${H-pad.b} Z`;
  const dots = points.map((v,i)=>`<circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="2.6" fill="#4ad7d4"/>`).join('');
  const xlabels = labels.map((l,i)=> (i%3===0||i===labels.length-1)
    ? `<text class="axis-label" x="${x(i)}" y="${H-6}" text-anchor="middle">${l}</text>` : '').join('');
  const ylabels = [max, (max+min)/2, min].map(v =>
    `<text class="axis-label" x="4" y="${(y(v)+3).toFixed(1)}">${fmtK(v)}</text>`).join('');
  svg.innerHTML = `
    <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#4ad7d4" stop-opacity=".45"/>
      <stop offset="100%" stop-color="#4ad7d4" stop-opacity="0"/>
    </linearGradient></defs>
    <path d="${area}" fill="url(#g)"/>
    <path d="${path}" fill="none" stroke="#4ad7d4" stroke-width="2"/>
    ${dots}${xlabels}${ylabels}`;
}

function drawStateTrend() {
  const s = stats.state_pop_series;
  lineChart(s.map(d=>d.pop), s.map(d=>String(d.year).slice(2)),
    'Población del estado · 1900–2020',
    'Serie decadal agregada de los 75 condados. Clic en un condado para su propia curva.');
}

function drawCountyTrend(p) {
  const pts = DECADES.map(y => p['pop'+y] || 0);
  lineChart(pts, DECADES.map(y=>String(y).slice(2)),
    `${p.name} County · 1900–2020`,
    `Pico histórico: ${fmt(Math.max(...pts))} hab. · Clic en otro condado para comparar.`);
}

/* ---------------- pestañas ---------------- */
function bindTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.onclick = () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const name = tab.dataset.tab;
      document.querySelectorAll('.tab-body').forEach(b =>
        b.classList.toggle('hidden', b.dataset.body !== name));
      if (name === 'dictionary') renderDictionary();
      if (name === 'quality') renderQuality();
    };
  });
}

/* ---------------- diccionario de datos ---------------- */
function renderDictionary() {
  const el = document.getElementById('dictContent');
  const d = dictionary[state.layer];
  if (!d) { el.innerHTML = '<p class="muted-p">Sin metadatos.</p>'; return; }
  el.innerHTML = `<div class="dict-layer">Capa activa: <b>${d.label}</b></div>` +
    d.fields.map(f => `
      <div class="dict-field">
        <div class="df-head"><code>${f.field}</code><span class="df-type">${f.type}</span></div>
        <div class="df-desc">${f.desc}${f.unit ? ` <em>(${f.unit})</em>` : ''}</div>
      </div>`).join('');
}

/* ---------------- calidad de datos ---------------- */
function renderQuality() {
  const head = document.getElementById('qualityHead');
  const el = document.getElementById('qualityContent');
  const q = quality[state.layer];
  if (!q) { el.innerHTML = '<p class="muted-p">Sin reporte.</p>'; return; }
  // completitud promedio
  const fields = Object.entries(q.fields);
  const avg = fields.reduce((s,[,v]) => s + v.completeness, 0) / (fields.length || 1);
  head.innerHTML = `
    <div class="q-score">
      <div class="q-ring" style="--p:${avg}">${avg.toFixed(0)}%</div>
      <div><strong>${q.records}</strong> registros · ${fields.length} campos<br>
      <small>Completitud media · clave: <code>${q.key_field}</code> (${q.unique_keys} únicas)</small></div>
    </div>
    <div class="q-issues">${q.issues.map(i =>
      `<span class="q-issue ${/Sin anomalias/i.test(i)?'ok':'warn'}">${/Sin anomalias/i.test(i)?'✓':'⚠'} ${i}</span>`).join('')}</div>`;
  el.innerHTML = fields.map(([name, v]) => `
    <div class="q-field">
      <div class="qf-top"><code>${name}</code><span>${v.completeness}%</span></div>
      <div class="qf-bar"><span style="width:${v.completeness}%; background:${v.completeness>=99?'#5fd0a8':v.completeness>=90?'#f2e394':'#e8622a'}"></span></div>
      <div class="qf-meta">${v.nulls>0?`<span class="warn">${v.nulls} nulos</span> · `:''}${
        v.min!=null ? `min ${fmtK(v.min)} · máx ${fmtK(v.max)} · media ${fmtK(v.mean)}` : 'categórico'}</div>
    </div>`).join('');
}

/* ---------------- exportación ---------------- */
function currentFeatureCollection() {
  return { type: 'FeatureCollection',
    properties: {
      source: 'Arkansas GIS Office (geodata.gis.arkansas.gov)',
      layer: LAYER_LABELS[state.layer], crs: 'EPSG:4326', exported: new Date().toISOString(),
    },
    features: data[state.layer].features };
}

function download(filename, text, type) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function exportGeoJSON() {
  download(`arkansas_${state.layer}.geojson`,
    JSON.stringify(currentFeatureCollection()), 'application/geo+json');
}

function exportCSV() {
  const feats = data[state.layer].features;
  const cols = Object.keys(feats[0].properties).filter(k => !k.startsWith('_'));
  const rows = [cols.join(',')];
  feats.forEach(f => {
    rows.push(cols.map(c => {
      const v = f.properties[c];
      const s = v == null ? '' : String(v);
      return /[",\n]/.test(s) ? `"${s.replace(/"/g,'""')}"` : s;
    }).join(','));
  });
  download(`arkansas_${state.layer}.csv`, rows.join('\n'), 'text/csv');
}

function exportCitation() {
  const year = new Date().getFullYear();
  const cite = `Arkansas GIS Office. "${LAYER_LABELS[state.layer]}". `
    + `Arkansas Geospatial Data Portal, geodata.gis.arkansas.gov. `
    + `Servicio ArcGIS REST (FEATURESERVICES/Boundaries/FeatureServer). `
    + `CRS EPSG:4326. Consultado ${new Date().toLocaleDateString('es')}. Dominio público (${year}).`;
  navigator.clipboard?.writeText(cite).then(
    () => flashNote('🔖 Cita copiada al portapapeles'),
    () => download('cita.txt', cite, 'text/plain'));
}

function flashNote(msg) {
  const n = document.getElementById('exportNote');
  n.textContent = msg; n.classList.add('flash');
  setTimeout(() => n.classList.remove('flash'), 2200);
}

function updateExportNote() {
  const n = document.getElementById('exportNote');
  const count = data[state.layer] ? data[state.layer].features.length : 0;
  n.textContent = `Exporta ${count} entidades de «${LAYER_LABELS[state.layer]}».`;
}

/* ---------------- controles ---------------- */
function switchLayer(layer) {
  state.layer = layer;
  document.querySelectorAll('.layer-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.layer === layer));
  if (layer !== 'counties' && state.metric === 'growth') {
    state.metric = 'pop';
    document.querySelectorAll('.metric-btn').forEach(b => b.classList.toggle('active', b.dataset.metric==='pop'));
  }
  render();
  if (layer === 'counties') drawStateTrend();
}

function bindControls() {
  document.querySelectorAll('.layer-btn').forEach(btn =>
    btn.onclick = () => switchLayer(btn.dataset.layer));

  document.querySelectorAll('.metric-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.metric-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      state.metric = btn.dataset.metric;
      render();
    };
  });

  const slider = document.getElementById('yearSlider');
  slider.oninput = () => {
    state.year = +slider.value;
    document.getElementById('yearLabel').textContent = state.year;
    if (state.layer !== 'congress') currentScale = colorScale(data[state.layer].features);
    if (geoLayer) geoLayer.setStyle(styleFor);
    renderBubbles();
    buildLegend();
    updateKPIs();
    buildRanking();
  };

  document.getElementById('bubbleToggle').onchange = e => {
    state.bubbles = e.target.checked;
    render();
  };

  document.getElementById('playBtn').onclick = togglePlay;
  document.getElementById('cpClose').onclick = () => document.getElementById('chartPanel').style.display='none';

  document.getElementById('exportGeo').onclick = exportGeoJSON;
  document.getElementById('exportCsv').onclick = exportCSV;
  document.getElementById('exportCite').onclick = exportCitation;
}

function togglePlay() {
  const btn = document.getElementById('playBtn');
  if (state.playing) {
    clearInterval(state.playTimer); state.playing = false; btn.textContent = '▶ Animar un siglo'; return;
  }
  state.playing = true; btn.textContent = '⏸ Pausar';
  let idx = DECADES.indexOf(state.year);
  state.playTimer = setInterval(() => {
    idx = (idx + 1) % DECADES.length;
    const y = DECADES[idx];
    document.getElementById('yearSlider').value = y;
    document.getElementById('yearSlider').dispatchEvent(new Event('input'));
  }, 900);
}

/* ---------------- init ---------------- */
async function init() {
  map = L.map('map', { zoomControl: true, attributionControl: false, minZoom: 6, maxZoom: 12 })
    .setView([34.8, -92.3], 7);

  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', { maxZoom: 16 }).addTo(map);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', { maxZoom: 16, opacity: .9 }).addTo(map);

  const [c, m, cg, st, dict, q] = await Promise.all([
    fetch('data/counties.geojson').then(r=>r.json()),
    fetch('data/municipalities.geojson').then(r=>r.json()),
    fetch('data/congress.geojson').then(r=>r.json()),
    fetch('data/stats.json').then(r=>r.json()),
    fetch('data/dictionary.json').then(r=>r.json()).catch(()=>({})),
    fetch('data/quality.json').then(r=>r.json()).catch(()=>({})),
  ]);
  data = { counties: c, municipalities: m, congress: cg };
  stats = st; dictionary = dict; quality = q;

  bindTabs();
  bindControls();
  bindSearch();
  render();
  drawStateTrend();
}

init();

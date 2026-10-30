ML.topbar('charts.html', { dark: true });
ML.footer(true);

const UNITS = ['All', 'Unit 1', 'Unit 2', 'Unit 3', 'Unit 4', 'Unit 5', 'Case Study'];
const NAMES = { 'All': 'All 26 charts', 'Unit 1': 'Unit 1 · Introduction', 'Unit 2': 'Unit 2 · Pre-processing & aesthetics', 'Unit 3': 'Unit 3 · Visualization design', 'Unit 4': 'Unit 4 · Advanced design', 'Unit 5': 'Unit 5 · Time series & geospatial', 'Case Study': 'Case study · Supply chain' };
const NOTES = { 'All': 'Every topic of the syllabus, in menu order', 'Unit 1': 'Design principles and the three kinds of data graphic', 'Unit 2': 'Pairplots, heatmaps, interaction, perception, grammar of graphics', 'Unit 3': 'Bars, dots, grouped and stacked bars, distributions, ECDF and Q-Q', 'Unit 4': 'Many distributions, proportions, nested parts, associations, paired data', 'Unit 5': 'Smoothing, decomposition, projections, layers, choropleth, cartogram', 'Case Study': 'Share delivery: investor to demat account on T+1' };
const UCOL = { 'Unit 1': ['#4338CA', '#EEF0FF'], 'Unit 2': ['#0E7490', '#E0F5FA'], 'Unit 3': ['#7E22CE', '#F5ECFE'], 'Unit 4': ['#C2410C', '#FFF0E6'], 'Unit 5': ['#047857', '#E7F6EF'], 'Case Study': ['#B91C1C', '#FDECEE'] };
const hashUnit = decodeURIComponent(location.hash.slice(1));
const st = { unit: UNITS.includes(hashUnit) ? hashUnit : 'All', spot: 20 };
let C = [];
const $ = (id) => document.getElementById(id);

function renderSpot() {
  const c = C.find((x) => x.id === st.spot); if (!c) return;
  $('sp-num').textContent = '#' + String(c.id).padStart(2, '0');
  $('sp-unit').textContent = c.unit.toUpperCase() + ' · SPOTLIGHT';
  $('sp-title').textContent = c.title;
  $('sp-desc').textContent = c.desc;
  $('sp-ins').innerHTML = '<strong>Takeaway · </strong>' + ML.esc(c.insight);
  $('sp-pos').textContent = c.id + ' / ' + C.length;
  $('sp-plot').innerHTML = ML.chartSVG(c);
}

function renderGrid() {
  const { esc } = ML;
  $('tabs').innerHTML = UNITS.map((u) => '<button type="button" role="tab" aria-selected="' + (st.unit === u) + '" class="chip' + (st.unit === u ? ' on' : '') + '" data-unit="' + u + '">' + u + '<span class="n">' + (u === 'All' ? C.length : C.filter((c) => c.unit === u).length) + '</span></button>').join('');
  $('tab-title').textContent = NAMES[st.unit];
  $('tab-note').textContent = NOTES[st.unit];
  const list = C.filter((c) => st.unit === 'All' || c.unit === st.unit);
  $('grid').innerHTML = list.map((c, i) => { const u = UCOL[c.unit];
    return '<article class="ccard" style="animation-delay:' + Math.min(i * 0.05, 0.6).toFixed(2) + 's">' +
      '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px"><div style="display:flex;align-items:center;gap:8px"><span class="num mono">' + String(c.id).padStart(2, '0') + '</span>' +
      '<span class="tag" style="letter-spacing:.08em;color:' + u[0] + ';background:' + u[1] + '">' + c.unit.toUpperCase() + '</span></div>' +
      '<button type="button" class="btn ghost small" data-open="' + c.id + '" aria-label="Open chart ' + c.id + ' large"><svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="M8.5 1.5h4v4M5.5 12.5h-4v-4M12.5 1.5 8 6M1.5 12.5 6 8" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"></path></svg>Open</button></div>' +
      '<h3>' + esc(c.title) + '</h3><div class="plot">' + ML.chartSVG(c) + '</div>' +
      '<p style="margin:0;font-size:13.5px;line-height:1.55;color:#4A5266">' + esc(c.desc) + '</p>' +
      '<div class="note"><svg width="16" height="16" viewBox="0 0 16 16" style="flex:none;margin-top:1px" aria-hidden="true"><circle cx="8" cy="8" r="6.5" stroke="#4F46E5" stroke-width="1.5" fill="none"></circle><path d="M8 7v4M8 4.6v.4" stroke="#4F46E5" stroke-width="1.6" stroke-linecap="round"></path></svg><span>' + esc(c.insight) + '</span></div></article>'; }).join('');
}

document.addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b || !C.length) return;
  if (b.dataset.unit) { st.unit = b.dataset.unit; history.replaceState(null, '', '#' + encodeURIComponent(st.unit)); renderGrid(); }
  else if (b.dataset.open) { st.spot = +b.dataset.open; renderSpot(); $('spot').scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  else if (b.id === 'prev') { st.spot = ((st.spot - 2 + C.length) % C.length) + 1; renderSpot(); }
  else if (b.id === 'next') { st.spot = (st.spot % C.length) + 1; renderSpot(); }
  else if (b.id === 'replay') renderSpot();
});

ML.charts().then((charts) => { C = charts; renderSpot(); renderGrid(); }).catch((e) => ML.fail($('sp-plot'), e));

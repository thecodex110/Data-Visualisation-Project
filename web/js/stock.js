/* Search & Analyse (Option 4): searchable stock list, candlestick / line chart with DMAs, volume, RSI and the signal. */
ML.topbar('stock.html');
ML.footer();

const st = { sel: new URLSearchParams(location.search).get('s') || 'IOC', q: '', range: 120, type: 'candle', hi: null };
let D = null, G = null;
const $ = (id) => document.getElementById(id);

function sma(a, n) { const out = []; let s = 0; for (let i = 0; i < a.length; i++) { s += a[i]; if (i >= n) s -= a[i - n]; out.push(s / Math.min(i + 1, n)); } return out; }
/* RSI(14) the same way preprocessing.analyse_stock does it: average gain / average loss of the last 14 days */
function rsi(c) {
  const out = [50];
  for (let i = 1; i < c.length; i++) {
    let g = 0, l = 0, n = 0;
    for (let j = Math.max(1, i - 13); j <= i; j++) { const ch = c[j] - c[j - 1]; if (ch > 0) g += ch; else l -= ch; n++; }
    out.push(l === 0 ? (g === 0 ? 50 : 100) : 100 - 100 / (1 + (g / n) / (l / n)));
  }
  return out;
}

function renderList() {
  const { esc, pct, num } = ML;
  const q = st.q.trim().toLowerCase();
  const m = D.stocks.filter((s) => !q || s.sym.toLowerCase().includes(q) || s.name.toLowerCase().includes(q) || s.sec.toLowerCase().includes(q));
  $('match').textContent = m.length + ' of ' + D.stocks.length + ' stocks' + (q ? ' match “' + st.q + '”' : '');
  $('list').innerHTML = m.map((s) => { const on = s.sym === st.sel; const c = on ? (s.d1 >= 0 ? '#34D399' : '#FB7185') : ML.col(s.d1);
    return '<button type="button" class="pick' + (on ? ' on' : '') + '" data-sym="' + esc(s.sym) + '" aria-pressed="' + on + '"><span style="font-weight:750;font-size:13.5px">' + esc(s.sym) + '</span>' +
      '<span class="mono" style="font-size:13px;font-weight:600;text-align:right">' + num(s.px) + '</span><span class="nm">' + esc(s.name) + ' · ' + s.sec + '</span>' +
      '<span class="mono" style="font-size:11.5px;font-weight:700;text-align:right;color:' + c + '">' + pct(s.d1) + '</span></button>'; }).join('') || '<div class="small" style="padding:10px">No stock matches. Try a sector name like “Auto”.</div>';
}

function renderStock() {
  const { UP, DN, esc, pct, num, money, col } = ML;
  const s = D.stocks.find((x) => x.sym === st.sel) || D.stocks[0];
  st.sel = s.sym;
  const N = s.c.length, ma20 = sma(s.c, 20), ma50 = sma(s.c, 50), rs = rsi(s.c);
  $('head').innerHTML = '<div><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><span class="eyebrow">OPTION 4 · SEARCH &amp; ANALYSE</span>' +
    '<span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:650;background:#F4F5F9;padding:4px 10px;border-radius:999px"><span style="width:8px;height:8px;border-radius:3px;background:' + D.secColors[s.sec] + '"></span>' + s.sec + ' · HQ ' + esc(s.hq) + '</span></div>' +
    '<h1 style="font-size:40px;margin-top:8px;font-weight:760">' + esc(s.sym) + ' <span style="font-weight:500;color:#5B6478;font-size:22px;letter-spacing:-.01em">' + esc(s.name) + '</span></h1></div>' +
    '<div style="text-align:right"><div class="mono" style="font-size:38px;font-weight:700;letter-spacing:-.03em">₹' + num(s.px) + '</div><div class="mono" style="font-size:15px;font-weight:700;color:' + col(s.d1) + '">' + pct(s.d1) + ' today · ' + pct(s.y1, 1) + ' 1Y</div></div>';

  const sig = s.sig.charAt(0) + s.sig.slice(1).toLowerCase(), last = s.c[N - 1], d20 = ma20[N - 1], d50 = ma50[N - 1];
  const why = sig === 'Bullish' ? 'Price ₹' + num(last) + ' is above its 50-day average (₹' + num(d50) + ') and the 20-DMA is above the 50-DMA: the trend is up.'
    : sig === 'Bearish' ? 'Price ₹' + num(last) + ' is below its 50-day average (₹' + num(d50) + ') and the 20-DMA is below the 50-DMA: the trend is down.'
    : 'The moving averages disagree (20-DMA ₹' + num(d20) + ', 50-DMA ₹' + num(d50) + '), so there is no clear trend.';
  const sc = { Bullish: ['#08714F', '#F0FAF5', '#BDE9D4'], Bearish: ['#B42235', '#FEF3F4', '#F8C9D0'], Neutral: ['#92400E', '#FFFBEB', '#FCE7B2'] }[sig];
  const sigEl = $('signal'); sigEl.style.background = sc[1]; sigEl.style.borderColor = sc[2];
  sigEl.innerHTML = '<div style="font-size:12px;font-weight:700;letter-spacing:.08em;color:' + sc[0] + '">SIGNAL</div><div style="font-family:var(--display);font-size:34px;font-weight:780;letter-spacing:-.02em;color:' + sc[0] + ';margin-top:6px">' + sig + '</div>' +
    '<div style="font-size:13.5px;line-height:1.55;color:#3B4255;margin-top:8px">' + why + '</div><div class="small" style="margin-top:12px;font-size:11.5px">Educational analysis on simulated data — not investment advice.</div>';

  const box = (l, v) => '<div style="background:' + (v >= 0 ? '#E7F6EF' : '#FDECEE') + ';border-radius:12px;padding:10px 8px;text-align:center"><div style="font-size:11px;font-weight:700;color:#5B6478">' + l + '</div><div class="mono" style="font-size:14px;font-weight:700;color:' + (v >= 0 ? '#08714F' : '#B42235') + ';margin-top:4px">' + pct(v, 1) + '</div></div>';
  const pos = ((s.px - s.l52) / ((s.h52 - s.l52) || 1) * 100).toFixed(1);
  $('returns').innerHTML = '<div style="font-size:13px;font-weight:700">Returns</div><div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:14px">' + box('1D', s.d1) + box('1M', s.m1) + box('3M', s.m3) + box('1Y', s.y1) + '</div>' +
    '<div style="font-size:13px;font-weight:700;margin-top:20px">52-week range</div><div style="position:relative;height:10px;background:linear-gradient(90deg,#FAD4DA,#FCE7B2,#C9F0DE);border-radius:6px;margin-top:12px"><div style="position:absolute;top:-5px;left:' + pos + '%;width:4px;height:20px;background:#0E1324;border-radius:2px;transform:translateX(-2px);transition:left .6s"></div></div>' +
    '<div class="mono" style="display:flex;justify-content:space-between;font-size:12px;color:#3B4255;margin-top:8px"><span>₹' + num(s.l52) + '</span><span>₹' + num(s.h52) + '</span></div>';

  const rows = [
    ['Volatility', s.vol.toFixed(1) + '%', 'a year', '#0E1324'], ['Max drawdown', s.dd.toFixed(1) + '%', 'worst fall from a peak', DN],
    ['Beta vs market', s.beta.toFixed(2), s.beta > 1 ? 'moves more than market' : 'moves less than market', '#0E1324'],
    ['RSI (14)', s.rsi.toFixed(1), s.rsi > 70 ? 'overbought' : s.rsi < 30 ? 'oversold' : 'normal zone', s.rsi > 70 ? DN : s.rsi < 30 ? UP : '#0E1324'],
    ['20 / 50-DMA', '₹' + Math.round(d20).toLocaleString('en-IN') + ' / ₹' + Math.round(d50).toLocaleString('en-IN'), '', '#0E1324'],
    ['Avg volume (20d)', (s.avgv / 1e5).toFixed(1) + ' L', 'shares', '#0E1324']
  ];
  $('stats').innerHTML = '<div style="font-size:13px;font-weight:700">Risk &amp; technicals</div>' + rows.map(([l, v, n, c]) => '<div style="display:flex;justify-content:space-between;align-items:baseline;padding:9px 0;border-bottom:1px solid #F1F2F7;gap:10px"><span style="font-size:13px;color:#4A5266">' + l + '</span><span style="text-align:right"><span class="mono" style="font-size:13.5px;font-weight:700;color:' + c + '">' + v + '</span> <span class="small" style="font-size:11px">' + n + '</span></span></div>').join('');

  /* chart geometry for the selected range */
  const n = Math.min(st.range, N), off = N - n, sl = (a) => a.slice(off);
  const o = sl(s.o), h = sl(s.h), l = sl(s.l), c = sl(s.c), v = sl(s.v), m20 = sl(ma20), m50 = sl(ma50), r = sl(rs), dates = D.dates.slice(off);
  let lo = Math.min(...l, ...m20, ...m50), hi = Math.max(...h, ...m20, ...m50); const pad = (hi - lo) * 0.06; lo -= pad; hi += pad;
  const W = 840, step = W / n, cw = Math.max(1.5, step * 0.62);
  const X = (i) => i * step + step / 2, Y = (p) => 12 + (1 - (p - lo) / (hi - lo)) * 278, RY = (x) => 388 + (1 - x / 100) * 56, vmax = Math.max(...v);
  const path = (arr, f) => 'M' + arr.map((a, i) => X(i).toFixed(1) + ',' + f(a).toFixed(1)).join(' L');
  let svg = '<defs><linearGradient id="lnF" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4F46E5" stop-opacity="0.22"></stop><stop offset="1" stop-color="#4F46E5" stop-opacity="0"></stop></linearGradient></defs>';
  for (let k = 0; k <= 4; k++) { const p = lo + (hi - lo) * k / 4, y = Y(p); svg += '<rect x="0" y="' + y.toFixed(1) + '" width="840" height="1" fill="#EEF0F5"></rect><text x="848" y="' + (y + 4).toFixed(1) + '" font-size="11" fill="#5B6478" font-family="JetBrains Mono">' + (p >= 1000 ? Math.round(p).toLocaleString('en-IN') : p.toFixed(1)) + '</text>'; }
  svg += '<rect x="0" y="388" width="840" height="56" fill="#F7F8FC"></rect><rect x="0" y="388" width="840" height="11.2" fill="#FDECEE"></rect><rect x="0" y="432.8" width="840" height="11.2" fill="#E7F6EF"></rect>' +
    '<text x="848" y="398" font-size="10" fill="#B42235" font-family="JetBrains Mono">70</text><text x="848" y="442" font-size="10" fill="#08714F" font-family="JetBrains Mono">30</text>' +
    '<text x="6" y="384" font-size="10.5" fill="#5B6478" font-family="Inter" font-weight="600">RSI (14)</text><text x="6" y="312" font-size="10.5" fill="#5B6478" font-family="Inter" font-weight="600">Volume</text>';
  v.forEach((vv, i) => { const hh = vv / vmax * 60; svg += '<rect class="g" x="' + (X(i) - cw / 2).toFixed(1) + '" y="' + (378 - hh).toFixed(1) + '" width="' + cw.toFixed(1) + '" height="' + hh.toFixed(1) + '" fill="' + (c[i] >= o[i] ? UP : DN) + '" opacity="0.55" rx="1"></rect>'; });
  if (st.type === 'line') {
    const lp = path(c, Y);
    svg += '<path class="f" d="' + lp + ' L' + X(n - 1).toFixed(1) + ',290 L' + X(0).toFixed(1) + ',290 Z" fill="url(#lnF)"></path><path d="' + lp + '" pathLength="1" class="d" stroke="#4F46E5" stroke-width="2.2" fill="none"></path>';
  } else {
    c.forEach((cl, i) => { const up = cl >= o[i], y1 = Y(Math.max(o[i], cl)), y2 = Y(Math.min(o[i], cl)), k = up ? UP : DN;
      svg += '<rect x="' + (X(i) - 0.7).toFixed(1) + '" y="' + Y(h[i]).toFixed(1) + '" width="1.4" height="' + Math.max(1, Y(l[i]) - Y(h[i])).toFixed(1) + '" fill="' + k + '"></rect>' +
        '<rect class="g" x="' + (X(i) - cw / 2).toFixed(1) + '" y="' + y1.toFixed(1) + '" width="' + cw.toFixed(1) + '" height="' + Math.max(1, y2 - y1).toFixed(1) + '" fill="' + k + '" rx="1"></rect>'; });
  }
  svg += '<path d="' + path(m20, Y) + '" pathLength="1" class="d" stroke="#4F46E5" stroke-width="1.8" fill="none" opacity="0.9"></path><path d="' + path(m50, Y) + '" pathLength="1" class="d" stroke="#EA580C" stroke-width="1.8" fill="none" opacity="0.9"></path>' +
    '<path d="' + path(r, RY) + '" pathLength="1" class="d" stroke="#9333EA" stroke-width="1.7" fill="none"></path>';
  const every = Math.ceil(n / 6);
  for (let i = 0; i < n; i += every) svg += '<text x="' + X(i).toFixed(1) + '" y="464" font-size="11" text-anchor="middle" fill="#5B6478" font-family="Inter">' + ML.fmtDate(dates[i], { day: 'numeric', month: 'short' }) + '</text>';
  svg += '<g id="cross" style="display:none"><rect id="cx-line" x="0" y="0" width="1" height="444" fill="#0E1324" opacity="0.35"></rect><circle id="cx-dot" r="4.5" fill="#FFFFFF" stroke="#0E1324" stroke-width="2"></circle><rect id="cx-lab" x="842" width="56" height="20" rx="5" fill="#0E1324"></rect><text id="cx-txt" x="870" font-size="11" text-anchor="middle" fill="#FFFFFF" font-family="JetBrains Mono" font-weight="700"></text></g>';
  $('chart').innerHTML = svg;
  G = { n, step, X, Y, o, h, l, c, v, r, dates };
  showTip(null);

  $('ranges').innerHTML = [['1M', 21], ['3M', 63], ['6M', 120], ['1Y', 250]].map(([lb, k]) => '<button type="button" class="seg' + (st.range === k ? ' on' : '') + '" data-range="' + k + '" aria-pressed="' + (st.range === k) + '">' + lb + '</button>').join('');
  $('types').innerHTML = [['Candles', 'candle'], ['Line', 'line']].map(([lb, k]) => '<button type="button" class="seg' + (st.type === k ? ' on' : '') + '" data-type="' + k + '" aria-pressed="' + (st.type === k) + '">' + lb + '</button>').join('');
  history.replaceState(null, '', '?s=' + encodeURIComponent(s.sym));
}

/* crosshair + OHLC readout without re-drawing the chart */
function showTip(i) {
  if (!G) return;
  const { num, col } = ML, k = i == null ? G.n - 1 : i;
  $('tip').innerHTML = '<span style="font-weight:700;color:#0E1324">' + ML.fmtDate(G.dates[k]) + '</span><span>O ' + num(G.o[k]) + '</span><span>H ' + num(G.h[k]) + '</span><span>L ' + num(G.l[k]) + '</span>' +
    '<span style="font-weight:700;color:' + col(G.c[k] - G.o[k]) + '">C ' + num(G.c[k]) + '</span><span>Vol ' + (G.v[k] / 1e5).toFixed(1) + ' L</span><span>RSI ' + G.r[k].toFixed(1) + '</span>';
  const g = $('cross'); if (!g) return;
  if (i == null) { g.style.display = 'none'; return; }
  const x = G.X(k), y = G.Y(G.c[k]);
  g.style.display = '';
  $('cx-line').setAttribute('x', x.toFixed(1)); $('cx-dot').setAttribute('cx', x.toFixed(1)); $('cx-dot').setAttribute('cy', y.toFixed(1));
  $('cx-lab').setAttribute('y', (y - 10).toFixed(1)); $('cx-txt').setAttribute('y', (y + 4).toFixed(1));
  $('cx-txt').textContent = G.c[k] >= 1000 ? Math.round(G.c[k]) : G.c[k].toFixed(1);
}

$('chart').addEventListener('pointermove', (e) => {
  if (!G) return; const r = e.currentTarget.getBoundingClientRect();
  const i = Math.max(0, Math.min(G.n - 1, Math.floor(((e.clientX - r.left) / r.width * 900) / G.step)));
  if (i !== st.hi) { st.hi = i; showTip(i); }
});
$('chart').addEventListener('pointerleave', () => { st.hi = null; showTip(null); });
$('q').addEventListener('input', (e) => { st.q = e.target.value; renderList(); });
document.addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b || !D) return;
  if (b.dataset.sym) { st.sel = b.dataset.sym; renderList(); renderStock(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
  else if (b.dataset.range) { st.range = +b.dataset.range; renderStock(); }
  else if (b.dataset.type) { st.type = b.dataset.type; renderStock(); }
});

ML.data().then((d) => { D = d; renderList(); renderStock(); }).catch((e) => ML.fail($('head'), e));

/* Home: hero ridge of sector indices, index strip, market today, big stats. */
ML.topbar('index.html', { ticker: true });
ML.footer();
ML.reveal();

ML.data().then((d) => {
  const { UP, DN, esc, inr, pct, col } = ML;
  const $ = (id) => document.getElementById(id);
  const k = d.kpis['All|0'];
  const secs = Object.keys(d.sectors);
  const lv = d.index.lv;
  const ichg = (lv[lv.length - 1] / lv[0] - 1) * 100;

  $('h-pill').textContent = d.stocks.length + ' stocks · ' + secs.length + ' sectors · 1 year of daily prices';
  $('h-stats').innerHTML = [
    [lv[lv.length - 1].toFixed(1), 'Market index (base 1000)', '#0E1324'],
    [pct(ichg, 1), 'Index, 1 year', col(ichg)],
    [k.breadth_pct.toFixed(1) + '%', 'Stocks above 50-DMA', '#0E1324']
  ].map(([v, l, c]) => '<div><div class="mono" style="font-size:26px;font-weight:700;color:' + c + '">' + v + '</div><div class="small" style="margin-top:2px">' + l + '</div></div>').join('');

  /* 3D ridge: each sector index drawn on its own layer, shifted back and up like a terrain */
  const all = secs.flatMap((s) => d.sectors[s]);
  const lo = Math.min(...all), hi = Math.max(...all);
  let svg = '<defs><linearGradient id="ridgeF" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8B85FF" stop-opacity="0.42"></stop><stop offset="1" stop-color="#EEF0FF" stop-opacity="0.05"></stop></linearGradient>' +
    '<linearGradient id="floorF" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF"></stop><stop offset="1" stop-color="#E9EBFF"></stop></linearGradient></defs>' +
    '<path d="M40 360 L470 360 L600 250 L170 250 Z" fill="url(#floorF)" stroke="#D5D9F5"></path><path d="M40 360 L40 388 L470 388 L470 360 Z" fill="#E4E6FA"></path><path d="M470 360 L600 250 L600 278 L470 388 Z" fill="#D4D7F6"></path>';
  for (let i = 1; i < 8; i++) { const x = 40 + i * 430 / 8; svg += '<path d="M' + x + ',360 L' + (x + 130) + ',250" stroke="#D9DCF5" stroke-width="0.8"></path>'; }
  for (let i = 1; i < 5; i++) { const f = i / 5; svg += '<path d="M' + (40 + 130 * f) + ',' + (360 - 110 * f) + ' L' + (470 + 130 * f) + ',' + (360 - 110 * f) + '" stroke="#D9DCF5" stroke-width="0.8"></path>'; }
  const layers = secs.map((s, i) => {
    const vals = d.sectors[s], back = secs.length - 1 - i;
    const ox = 40 + back * 24, oy = 360 - back * 20;
    const pts = []; for (let j = 0; j < vals.length; j += 2) pts.push([ox + (j / (vals.length - 1)) * 430, oy - 18 - ((vals[j] - lo) / (hi - lo)) * 190]);
    const line = 'M' + pts.map((p) => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' L');
    let ribs = ''; for (let j = 0; j < pts.length; j += 5) ribs += 'M' + pts[j][0].toFixed(1) + ',' + pts[j][1].toFixed(1) + ' L' + pts[j][0].toFixed(1) + ',' + oy + ' ';
    const last = pts[pts.length - 1], c = d.secColors[s], dl = (i * 0.18).toFixed(2) + 's';
    return '<g class="f" style="animation-delay:' + dl + '"><path d="' + line + ' L' + (ox + 430) + ',' + oy + ' L' + ox + ',' + oy + ' Z" fill="url(#ridgeF)"></path>' +
      '<path d="' + ribs + '" stroke="#A7A2FF" stroke-width="0.6" stroke-opacity="0.55" fill="none"></path>' +
      '<path d="' + line + '" pathLength="1" class="d" style="animation-delay:' + dl + '" stroke="' + c + '" stroke-width="2" fill="none" stroke-linejoin="round"></path>' +
      '<text x="' + (last[0] + 6) + '" y="' + (last[1] + 4) + '" font-size="11" font-weight="700" fill="' + c + '" font-family="Inter, sans-serif">' + esc(s) + '</text></g>';
  });
  $('ridge').innerHTML = svg + layers.reverse().join('');

  const sr = secs.map((s) => ({ s, v: d.secRet[s] })).sort((a, b) => b.v - a.v);
  $('h-best').innerHTML = '<span style="font-weight:750;font-size:15px">' + esc(sr[0].s) + '</span><span class="mono" style="color:' + UP + ';font-weight:700;font-size:14px">' + pct(sr[0].v, 1) + '</span>';
  const w = sr[sr.length - 1];
  $('h-worst').innerHTML = '<span style="font-weight:750;font-size:15px">' + esc(w.s) + '</span><span class="mono" style="color:' + col(w.v) + ';font-weight:700;font-size:14px">' + pct(w.v, 1) + '</span>';

  /* index strip */
  const card = (name, vals, c, href) => {
    const sp = ML.spark(vals, 140, 36, 3), ch = (vals[vals.length - 1] / vals[0] - 1) * 100;
    return '<a class="lift" href="' + href + '"><div style="display:flex;align-items:center;gap:7px;font-size:11.5px;font-weight:700;letter-spacing:.05em;color:#5B6478"><span style="width:8px;height:8px;border-radius:3px;background:' + c + '"></span>' + esc(name) + '</div>' +
      '<div style="display:flex;align-items:baseline;justify-content:space-between;gap:8px;margin-top:8px"><span class="mono" style="font-size:18px;font-weight:700">' + vals[vals.length - 1].toFixed(1) + '</span><span class="mono" style="font-size:12px;font-weight:700;color:' + col(ch) + '">' + pct(ch, 1) + '</span></div>' +
      '<svg viewBox="0 0 140 36" preserveAspectRatio="none" style="width:100%;height:36px;margin-top:6px;display:block" aria-hidden="true"><path d="' + sp.area + '" fill="' + c + '" fill-opacity="0.1"></path><path d="' + sp.line + '" pathLength="1" class="d" stroke="' + c + '" stroke-width="1.8" fill="none" vector-effect="non-scaling-stroke"></path></svg></a>';
  };
  $('idx-strip').innerHTML = card('MARKET', lv, '#0E1324', 'dashboard.html') + secs.map((s) => card(s.toUpperCase(), d.sectors[s], d.secColors[s], 'dashboard.html?sector=' + encodeURIComponent(s))).join('');

  /* market today */
  const mood = k.breadth_pct >= 60 ? 'Bullish' : k.breadth_pct >= 40 ? 'Neutral' : 'Bearish';
  const rising = Math.round(k.breadth_pct / 100 * k.stocks);
  $('mood-title').innerHTML = 'The mood is <span style="color:' + (mood === 'Bullish' ? UP : mood === 'Bearish' ? DN : '#CA8A04') + '">' + mood + '</span>.';
  $('mood-text').textContent = rising + ' of ' + k.stocks + ' stocks are trading above their 50-day average price. Investors hold ' + k.open_positions + ' open positions worth ' + inr(k.open_value) + '.';
  $('gauge').innerHTML = '<path d="M20 110 A90 90 0 0 1 200 110" stroke="#262C46" stroke-width="18" fill="none" stroke-linecap="round"></path>' +
    '<path d="M20 110 A90 90 0 0 1 200 110" pathLength="100" stroke="#8B85FF" stroke-width="18" fill="none" stroke-linecap="round" stroke-dasharray="' + k.breadth_pct.toFixed(1) + ' 100" class="f"></path>' +
    '<g class="needle" style="transform: rotate(' + (-90 + k.breadth_pct / 100 * 180).toFixed(1) + 'deg)"><path d="M110 110 L110 34" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"></path></g><circle cx="110" cy="110" r="7" fill="#FFFFFF"></circle>';
  $('g-val').textContent = k.breadth_pct.toFixed(1) + '%';
  $('g-note').textContent = rising + ' of ' + k.stocks + ' stocks above 50-DMA · bullish at 60%+';

  const kc = [
    ['Unrealised P&L', inr(k.unrealised_pnl, true), col(k.unrealised_pnl), 'Paper profit on shares not sold'],
    ['Realised P&L', inr(k.realised_pnl, true), col(k.realised_pnl), 'Locked in by selling'],
    ['Win rate', k.win_rate_pct.toFixed(1) + '%', k.win_rate_pct >= 55 ? UP : '#B45309', 'Target 55% · ' + (k.win_rate_pct >= 55 ? 'on target' : 'below target')],
    ['Stop-loss alerts', String(k.stop_loss_hits), DN, 'Open positions down 8%+']
  ];
  $('kpis').innerHTML = kc.map(([l, v, c, n]) => '<div class="card lift" style="padding:18px;display:flex;flex-direction:column;justify-content:space-between;min-height:132px"><div style="font-size:12.5px;font-weight:650;color:#5B6478">' + l + '</div><div class="mono" style="font-size:24px;font-weight:700;color:' + c + ';letter-spacing:-.02em">' + v + '</div><div class="small" style="font-size:11.5px">' + n + '</div></div>').join('');

  const sorted = d.stocks.slice().sort((a, b) => b.d1 - a.d1);
  const mv = sorted.slice(0, 4).concat(sorted.slice(-4).reverse());
  const mAbs = Math.max(...mv.map((m) => Math.abs(m.d1)));
  $('movers').innerHTML = mv.map((m, i) => '<a href="stock.html?s=' + encodeURIComponent(m.sym) + '" style="display:grid;grid-template-columns:96px minmax(0,1fr) 64px;align-items:center;gap:10px;color:#0E1324;min-height:28px"><span style="font-weight:700;font-size:12.5px">' + esc(m.sym) + '</span>' +
    '<div class="bar-track"><div class="bar-fill gx" style="animation-delay:' + (i * 0.05) + 's;width:' + Math.max(4, Math.abs(m.d1) / mAbs * 100).toFixed(0) + '%;background:' + col(m.d1) + '"></div></div>' +
    '<span class="mono" style="font-size:12.5px;font-weight:700;color:' + col(m.d1) + ';text-align:right">' + pct(m.d1) + '</span></a>').join('');

  const maxSec = Math.max(...sr.map((x) => Math.abs(x.v)));
  $('secbars').innerHTML = sr.map((x, i) => '<a href="dashboard.html?sector=' + encodeURIComponent(x.s) + '" style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;gap:8px;color:#0E1324">' +
    '<span class="mono" style="font-size:13px;font-weight:700;color:' + (x.v >= 0 ? '#0E1324' : DN) + '">' + pct(x.v, 1) + '</span>' +
    '<div class="g" style="width:100%;max-width:92px;height:' + Math.max(6, Math.abs(x.v) / maxSec * 150).toFixed(0) + 'px;background:' + (x.v >= 0 ? d.secColors[x.s] : '#F5B5BE') + ';border-radius:10px 10px 4px 4px;animation-delay:' + (i * 0.08) + 's"></div>' +
    '<span style="font-size:12.5px;font-weight:650">' + esc(x.s) + '</span></a>').join('');

  $('bigstats').innerHTML = [[d.stocks.length, 'NSE stocks tracked'], [(d.stocks.length * d.dates.length).toLocaleString('en-IN'), 'Daily price rows'], [d.trades.length, 'Buy / sell trades'], [26, 'Syllabus charts']]
    .map(([v, l]) => '<div style="border-left:1px solid #2B3150;padding-left:18px"><div class="mono" style="color:#FFF;font-size:40px;font-weight:700;letter-spacing:-.03em">' + v + '</div><div style="color:#A9AFC2;font-size:13px;margin-top:4px">' + l + '</div></div>').join('');
}).catch((e) => ML.fail(document.getElementById('idx-strip'), e));

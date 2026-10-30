ML.topbar('dashboard.html');
ML.footer();

const SECS = ['IT', 'Banking', 'Pharma', 'Auto', 'FMCG', 'Energy'];
const RISKS = ['All', 'Conservative', 'Moderate', 'Growth', 'Aggressive'];
const qs = new URLSearchParams(location.search);
const state = { sector: SECS.includes(qs.get('sector')) ? qs.get('sector') : null, risk: 0, drill: null };
state.drill = state.sector;
let D = null;
const $ = (id) => document.getElementById(id);

function chips() {
  $('sec-chips').innerHTML = [null].concat(SECS).map((s) => '<button type="button" class="chip' + (state.sector === s ? ' on' : '') + '" aria-pressed="' + (state.sector === s) + '" data-sec="' + (s || '') + '">' + (s || 'All') + '</button>').join('');
  $('risk-chips').innerHTML = RISKS.map((r, i) => '<button type="button" class="chip' + (state.risk === i ? ' on' : '') + '" aria-pressed="' + (state.risk === i) + '" data-risk="' + i + '">' + r + '</button>').join('');
}

function render() {
  const { UP, DN, esc, inr, pct, col } = ML;
  const d = D;
  chips();
  $('filters').innerHTML = 'Sector: <strong>' + (state.sector || 'All') + '</strong> · Investor type: <strong>' + RISKS[state.risk] + '</strong>';
  const k = d.kpis[(state.sector || 'All') + '|' + state.risk];
  const mood = k.breadth_pct >= 60 ? 'Bullish' : k.breadth_pct >= 40 ? 'Neutral' : 'Bearish';
  const rising = Math.round(k.breadth_pct / 100 * k.stocks);
  $('mood-box').innerHTML = '<div style="font-size:12px;color:#A9AFC2">Market mood</div><div style="font-family:var(--display);font-size:24px;font-weight:750;margin-top:2px;color:' +
    (mood === 'Bullish' ? '#34D399' : mood === 'Bearish' ? '#FB7185' : '#FCD34D') + '">' + mood + '</div><div style="font-size:12px;color:#C3C8D8;margin-top:4px">' + rising + ' of ' + k.stocks + ' stocks above 50-DMA</div>';

  const change = k.trades_this_month - k.trades_last_month;
  const pnlCard = (label, v, note) => ({ label, val: inr(v, true), c: col(v), tag: v >= 0 ? 'PROFIT' : 'LOSS', tc: v >= 0 ? 'up' : 'dn', bar: Math.min(100, Math.abs(v) / Math.max(1, k.open_invested) * 400), bc: col(v), note });
  const cards = [
    { label: 'Value of shares held', val: inr(k.open_value), c: '#0E1324', tag: k.open_positions + ' OPEN', tc: 'acc', bar: 100, bc: '#4F46E5', note: 'Bought for ' + inr(k.open_invested) },
    pnlCard('Unrealised P&L', k.unrealised_pnl, 'Paper profit — can still change'),
    pnlCard('Realised P&L', k.realised_pnl, 'Already locked in by selling'),
    { label: 'Win rate vs target', val: k.win_rate_pct.toFixed(1) + '%', c: k.win_rate_pct >= 55 ? UP : '#B45309', tag: k.win_rate_pct >= 55 ? 'ON TARGET' : 'BELOW 55%', tc: k.win_rate_pct >= 55 ? 'up' : 'warn', bar: k.win_rate_pct, bc: k.win_rate_pct >= 55 ? UP : '#D97706', note: 'Of every 100 sells, ' + Math.round(k.win_rate_pct) + ' made money' },
    { label: 'Orders this month', val: String(k.trades_this_month), c: '#0E1324', tag: (change > 0 ? '▲ +' : change < 0 ? '▼ ' : '■ ') + change, tc: change >= 0 ? 'up' : 'dn', bar: Math.min(100, k.trades_this_month / Math.max(1, k.trades_last_month) * 100), bc: '#4F46E5', note: 'vs ' + k.trades_last_month + ' last month · ' + k.investors + ' investors' },
    { label: 'Stop-loss alerts', val: String(k.stop_loss_hits), c: DN, tag: 'ACT', tc: 'dn', bar: Math.min(100, k.stop_loss_hits / Math.max(1, k.open_positions) * 100), bc: DN, note: 'Open positions down more than 8%', href: 'portfolio.html#alerts' }
  ];
  $('cards').innerHTML = cards.map((c, i) => '<' + (c.href ? 'a href="' + c.href + '"' : 'div') + ' class="card anim-up lift" style="animation-delay:' + (i * 0.05) + 's;padding:18px;display:flex;flex-direction:column;gap:8px;min-height:128px;color:#0E1324">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><span style="font-size:12.5px;font-weight:650;color:#5B6478">' + c.label + '</span><span class="tag ' + c.tc + '">' + c.tag + '</span></div>' +
    '<div class="mono" style="font-size:25px;font-weight:700;letter-spacing:-.02em;color:' + c.c + '">' + c.val + '</div>' +
    '<div style="height:6px;background:#F1F2F7;border-radius:4px;overflow:hidden"><div class="gx" style="height:100%;width:' + c.bar.toFixed(0) + '%;background:' + c.bc + ';border-radius:4px"></div></div>' +
    '<div style="font-size:11.5px;color:#5B6478">' + c.note + '</div></' + (c.href ? 'a' : 'div') + '>').join('');

  $('gauge').innerHTML = '<path d="M20 110 A90 90 0 0 1 74 27.6" stroke="#FAD4DA" stroke-width="18" fill="none"></path><path d="M74 27.6 A90 90 0 0 1 165.6 39.3" stroke="#FCE7B2" stroke-width="18" fill="none"></path><path d="M165.6 39.3 A90 90 0 0 1 200 110" stroke="#C9F0DE" stroke-width="18" fill="none"></path>' +
    '<g class="needle" style="transform: rotate(' + (-90 + k.breadth_pct / 100 * 180).toFixed(1) + 'deg)"><path d="M110 110 L110 30" stroke="#0E1324" stroke-width="3.5" stroke-linecap="round"></path></g><circle cx="110" cy="110" r="8" fill="#0E1324"></circle>';
  $('g-val').textContent = k.breadth_pct.toFixed(1) + '%';
  $('g-note').textContent = rising + ' of ' + k.stocks + ' stocks trade above their 50-day average, so the mood is ' + mood.toLowerCase() + '.';

  const pool = d.stocks.filter((s) => !state.sector || s.sec === state.sector).sort((a, b) => b.d1 - a.d1);
  const g5 = pool.filter((s) => s.d1 >= 0).slice(0, 5), l5 = pool.filter((s) => s.d1 < 0).slice(-5).reverse();
  const mAbs = Math.max(0.01, ...g5.concat(l5).map((s) => Math.abs(s.d1)));
  const mv = (s, side) => '<a href="stock.html?s=' + encodeURIComponent(s.sym) + '" style="display:grid;grid-template-columns:90px minmax(0,1fr) 62px;gap:8px;align-items:center;color:#0E1324"><span style="font-size:12.5px;font-weight:700">' + esc(s.sym) + '</span>' +
    '<div style="height:22px;display:flex;' + (side === 'l' ? 'justify-content:flex-end' : '') + '"><div class="' + (side === 'l' ? 'gxn' : 'gx') + '" style="width:' + Math.max(3, Math.abs(s.d1) / mAbs * 100).toFixed(0) + '%;background:' + col(s.d1) + ';border-radius:' + (side === 'l' ? '6px 3px 3px 6px' : '3px 6px 6px 3px') + '"></div></div>' +
    '<span class="mono" style="font-size:12.5px;font-weight:700;color:' + col(s.d1) + ';text-align:right">' + pct(s.d1) + '</span></a>';
  const none = (t) => '<div class="small" style="font-size:12.5px;padding:4px 0">' + t + '</div>';
  $('gainers').innerHTML = g5.map((s) => mv(s, 'g')).join('') || none('No stock rose today.');
  $('losers').innerHTML = l5.map((s) => mv(s, 'l')).join('') || none('No stock fell today.');
  $('mv-note').textContent = state.sector || 'All sectors';

  const rowsOf = (items, key, name, colorOf, click) => {
    const m = Math.max(...items.map((r) => Math.abs(r[key])));
    return items.map((r) => { const v = r[key], w = Math.abs(v) / m * 50; return '<button type="button" class="drill"' + (click ? ' data-drill="' + esc(r[name]) + '"' : ' tabindex="-1"') + '><span style="font-size:13px;font-weight:650">' + esc(r[name]) + '</span>' +
      '<div class="track"><div class="zero"></div><div class="fill ' + (v >= 0 ? 'gx' : 'gxn') + '" style="left:' + (v >= 0 ? 50 : 50 - w).toFixed(1) + '%;width:' + w.toFixed(1) + '%;background:' + (v >= 0 ? colorOf(r) : DN) + '"></div></div>' +
      '<span class="mono" style="font-size:12.5px;font-weight:700;text-align:right;color:' + (v >= 0 ? '#0E1324' : DN) + '">' + pct(v, 1) + '</span></button>'; }).join('');
  };
  if (!state.drill) {
    $('drill-title').textContent = 'Drill-down · Level 1 · sectors';
    $('drill-hint').textContent = 'Average 1-year return. Click a sector to see its stocks.';
    $('drill').innerHTML = rowsOf(SECS.map((s) => ({ s, v: d.secRet[s] })).sort((a, b) => b.v - a.v), 'v', 's', (r) => d.secColors[r.s], true);
    $('drill-up').hidden = true;
  } else {
    $('drill-title').textContent = 'Drill-down · Level 2 · stocks in ' + state.drill;
    $('drill-hint').textContent = '1-year return of each stock inside ' + state.drill + '.';
    $('drill').innerHTML = rowsOf(d.stocks.filter((s) => s.sec === state.drill).sort((a, b) => b.y1 - a.y1), 'y1', 'sym', () => d.secColors[state.drill], false);
    $('drill-up').hidden = false;
  }

  const mo = d.monthlyOrders, mmax = Math.max(...mo.map((m) => m.n));
  $('months').innerHTML = mo.map((m, i) => { const h = m.n / mmax * 160, x = 8 + i * 32.5, c = i === mo.length - 1 ? '#4F46E5' : i === mo.length - 2 ? '#A5A0FF' : '#D9DCEA';
    return '<rect class="g" style="animation-delay:' + (i * 0.05) + 's" x="' + x + '" y="' + (184 - h) + '" width="24" height="' + h + '" rx="5" fill="' + c + '"><title>' + m.m + ': ' + m.n + ' orders</title></rect>' +
      '<text x="' + (x + 12) + '" y="' + (178 - h) + '" font-size="10" text-anchor="middle" fill="#3B4255" font-family="JetBrains Mono" font-weight="600">' + m.n + '</text><text x="' + (x + 12) + '" y="204" font-size="10" text-anchor="middle" fill="#5B6478" font-family="Inter">' + m.label + '</text>'; }).join('');
  $('ord-delta').textContent = (change > 0 ? '▲ +' : change < 0 ? '▼ ' : '■ ') + change + ' vs last month';
  $('ord-delta').style.color = col(change);

  const pr = d.pnlRisk, vals = pr.flatMap((r) => [r.real, r.unreal]);
  const hi = Math.max(0, ...vals), lo = Math.min(0, ...vals), sc = 160 / ((hi - lo) || 1), zero = 10 + hi * sc;
  $('risk').innerHTML = '<rect x="0" y="' + zero + '" width="400" height="1.5" fill="#9AA1B2"></rect>' + pr.map((r, i) => { const cx = 50 + i * 100;
    const bar = (v, x, c) => '<rect class="' + (v >= 0 ? 'g' : 'gn') + '" x="' + x + '" y="' + (v >= 0 ? zero - v * sc : zero) + '" width="30" height="' + Math.max(1, Math.abs(v) * sc) + '" rx="4" fill="' + c + '"><title>' + r.risk + ': ₹' + v + ' L</title></rect>';
    return bar(r.real, cx - 31, '#4F46E5') + bar(r.unreal, cx + 1, '#A5A0FF') + '<text x="' + cx + '" y="196" font-size="11" text-anchor="middle" fill="#3B4255" font-family="Inter" font-weight="600">' + r.risk + '</text>'; }).join('');

  const watch = d.stocks.filter((s) => !state.sector || s.sec === state.sector).sort((a, b) => a.sec.localeCompare(b.sec) || a.sym.localeCompare(b.sym));
  const upN = watch.filter((s) => s.d1 >= 0).length;
  $('watch-note').textContent = 'Option 1 · ' + watch.length + ' stocks · ' + upN + ' up · ' + (watch.length - upN) + ' down today';
  $('watch').innerHTML = watch.map((s) => { const sp = ML.spark(s.c.slice(-60), 110, 28);
    return '<tr><td><a href="stock.html?s=' + encodeURIComponent(s.sym) + '" style="font-weight:750;color:#0E1324">' + esc(s.sym) + '</a></td><td style="color:#3B4255">' + esc(s.name) + '</td>' +
      '<td><span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600"><span style="width:8px;height:8px;border-radius:3px;background:' + d.secColors[s.sec] + '"></span>' + s.sec + '</span></td>' +
      '<td class="mono r" style="font-weight:600">' + ML.num(s.px) + '</td><td class="mono r" style="font-weight:700;color:' + col(s.d1) + '">' + pct(s.d1) + '</td><td class="mono r" style="font-weight:700;color:' + col(s.y1) + '">' + pct(s.y1, 1) + '</td>' +
      '<td style="padding-top:4px;padding-bottom:4px"><svg viewBox="0 0 110 28" width="110" height="28" aria-hidden="true"><path d="' + sp.line + '" pathLength="1" class="d" stroke="' + col(s.y1) + '" stroke-width="1.6" fill="none"></path></svg></td><td style="color:#5B6478">' + esc(s.hq) + '</td></tr>'; }).join('');
}

document.addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b || !D) return;
  if (b.dataset.sec !== undefined) { state.sector = b.dataset.sec || null; state.drill = state.sector; render(); }
  else if (b.dataset.risk !== undefined) { state.risk = +b.dataset.risk; render(); }
  else if (b.dataset.drill) { state.drill = b.dataset.drill; render(); }
  else if (b.id === 'drill-up') { state.drill = null; state.sector = null; render(); }
});

ML.data().then((d) => { D = d; render(); }).catch((e) => ML.fail(document.getElementById('cards'), e));

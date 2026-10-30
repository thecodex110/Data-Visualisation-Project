ML.topbar('portfolio.html');
ML.footer();

const RISKS = ['All', 'Conservative', 'Moderate', 'Growth', 'Aggressive'];
const RC = { Conservative: ['#E0F5FA', '#0E7490'], Moderate: ['#EEF0FF', '#4338CA'], Growth: ['#FFF0E6', '#C2410C'], Aggressive: ['#FDECEE', '#B42235'] };
const st = { sel: null, q: '', risk: 'All', mode: 'buy', busy: false };
let D = null;
const $ = (id) => document.getElementById(id);
const ini = (n) => n.split(' ').map((w) => w[0]).slice(0, 2).join('');

function renderDirectory() {
  const { esc, inr, col } = ML;
  $('risk-chips').innerHTML = RISKS.map((r) => '<button type="button" class="chip' + (st.risk === r ? ' on' : '') + '" data-risk="' + r + '" aria-pressed="' + (st.risk === r) + '" style="min-height:36px;font-size:12.5px">' + r + '</button>').join('');
  const q = st.q.toLowerCase();
  const list = D.investors.filter((i) => (st.risk === 'All' || i.risk === st.risk) && (!q || (i.name + ' ' + i.state + ' ' + i.broker).toLowerCase().includes(q))).sort((a, b) => b.pnl - a.pnl);
  $('inv-count').textContent = list.length + ' shown';
  $('inv-list').innerHTML = list.map((i) => '<button type="button" class="inv' + (st.sel === i.id ? ' on' : '') + '" data-inv="' + i.id + '" aria-pressed="' + (st.sel === i.id) + '">' +
    '<span class="av" style="background:' + RC[i.risk][0] + ';color:' + RC[i.risk][1] + '">' + esc(ini(i.name)) + '</span>' +
    '<span style="min-width:0"><span class="nm">' + esc(i.name) + '</span><span class="small" style="display:block;font-size:11.5px">' + i.risk + ' · ' + esc(i.state) + ' · ' + i.trades + ' trades</span></span>' +
    '<span class="mono" style="font-size:12.5px;font-weight:700;color:' + col(i.pnl) + '">' + inr(i.pnl, true) + '</span></button>').join('') || '<div class="small" style="padding:10px">No investor matches.</div>';
}

function renderInvestor() {
  const { UP, DN, esc, inr, pct, num, col } = ML;
  const inv = D.investors.find((i) => i.id === st.sel) || D.investors[0];
  st.sel = inv.id;
  const tr = D.trades.filter((t) => t.inv === inv.id).sort((a, b) => a.bd.localeCompare(b.bd) || a.id - b.id);
  const open = tr.filter((t) => t.st === 'Open'), closed = tr.filter((t) => t.st !== 'Open');
  const sum = (a) => a.reduce((s, t) => s + t.pnl, 0);
  const win = closed.length ? closed.filter((t) => t.pnl > 0).length / closed.length * 100 : 0;
  const stats = [
    ['Open · invested', open.length + ' · ' + inr(open.reduce((s, t) => s + t.bp * t.q, 0)), '#0E1324'],
    ['Unrealised P&L', inr(sum(open), true), col(sum(open))], ['Realised P&L', inr(sum(closed), true), col(sum(closed))],
    ['Win rate (' + closed.length + ' closed)', win.toFixed(0) + '%', win >= 55 ? UP : '#B45309']
  ];
  $('profile').innerHTML = '<span style="width:64px;height:64px;border-radius:20px;background:#0E1324;color:#FFF;display:flex;align-items:center;justify-content:center;font-family:var(--display);font-weight:750;font-size:24px">' + esc(ini(inv.name)) + '</span>' +
    '<div style="flex:1 1 220px"><div style="font-family:var(--display);font-size:26px;font-weight:720;letter-spacing:-.02em">' + esc(inv.name) + '</div><div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">' +
    '<span class="tag acc" style="font-size:12px;padding:4px 10px;border-radius:999px">' + inv.risk + '</span><span class="tag" style="font-size:12px;padding:4px 10px;border-radius:999px;background:#F4F5F9">' + esc(inv.state) + '</span>' +
    '<span class="tag" style="font-size:12px;padding:4px 10px;border-radius:999px;background:#F4F5F9">Broker · ' + esc(inv.broker) + '</span><span class="tag mono" style="font-size:12px;padding:4px 10px;border-radius:999px;background:#F4F5F9">ID ' + inv.id + '</span></div></div>' +
    '<div style="display:grid;grid-template-columns:repeat(2,minmax(120px,1fr));gap:10px;flex:1 1 300px">' + stats.map(([l, v, c]) => '<div style="background:#F7F8FC;border-radius:14px;padding:10px 12px"><div class="small" style="font-size:11.5px">' + l + '</div><div class="mono" style="font-size:17px;font-weight:700;color:' + c + ';margin-top:2px">' + v + '</div></div>').join('') + '</div>';

  const mx = Math.max(1, ...tr.map((t) => Math.abs(t.pnl))), zero = 80, slot = 760 / Math.max(1, tr.length), bw = Math.min(46, slot - 8);
  $('pnl').innerHTML = '<rect x="0" y="' + zero + '" width="800" height="1.5" fill="#9AA1B2"></rect>' + (tr.length ? tr.map((t, i) => { const h = Math.max(2, Math.abs(t.pnl) / mx * 70), x = 20 + i * slot, c = col(t.pnl);
    return '<rect class="' + (t.pnl >= 0 ? 'g' : 'gn') + '" style="animation-delay:' + Math.min(i * 0.04, 0.6) + 's" x="' + x.toFixed(1) + '" y="' + (t.pnl >= 0 ? zero - h : zero).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + h.toFixed(1) + '" rx="3" fill="' + (t.st === 'Open' ? '#FFFFFF' : c) + '" stroke="' + c + '" stroke-width="1.5"><title>#' + t.id + ' ' + t.sym + ': ' + inr(t.pnl, true) + '</title></rect>' +
      (tr.length <= 16 ? '<text x="' + (x + bw / 2).toFixed(1) + '" y="166" font-size="10" text-anchor="middle" fill="#3B4255" font-family="Inter" font-weight="600">' + esc(t.sym) + '</text>' : ''); }).join('')
    : '<text x="400" y="70" text-anchor="middle" font-size="13" fill="#5B6478" font-family="Inter">No trades yet. Place a buy order with the ticket below.</text>');

  const SB = { 'Profit Booked': 'up', 'Loss Booked': 'dn', 'Open': 'acc' };
  $('hist').innerHTML = tr.map((t) => '<tr><td class="mono" style="color:#5B6478">#' + t.id + '</td><td><a href="stock.html?s=' + encodeURIComponent(t.sym) + '" style="font-weight:750;color:#0E1324">' + esc(t.sym) + '</a></td><td class="mono r">' + t.q + '</td><td class="mono" style="color:#3B4255">' + t.bd + '</td>' +
    '<td class="mono r">' + num(t.bp) + '</td><td class="mono r">' + num(t.xp) + '</td><td class="mono r" style="font-weight:700;color:' + col(t.pnl) + '">' + pct(t.ret, 1) + '</td><td class="mono r" style="font-weight:700;color:' + col(t.pnl) + '">' + (t.pnl >= 0 ? '+' : '−') + Math.abs(t.pnl).toLocaleString('en-IN') + '</td>' +
    '<td><span class="tag ' + (t.hit ? 'solid-dn' : SB[t.st]) + '" style="font-size:11.5px;padding:4px 9px">' + (t.hit ? 'Stop-loss hit' : t.st) + '</span></td></tr>').join('') || '<tr><td colspan="9" class="small">No trades yet.</td></tr>';

  $('s-id').innerHTML = open.length ? open.map((t) => '<option value="' + t.id + '">#' + t.id + ' · ' + t.q + ' × ' + esc(t.sym) + ' @ ₹' + num(t.bp) + '</option>').join('') : '<option value="">No open positions</option>';
  renderTicket();
}

function renderTicket() {
  const { money, inr, pct, col, esc } = ML;
  const inv = D.investors.find((i) => i.id === st.sel);
  const s = D.stocks.find((x) => x.sym === $('b-sym').value) || D.stocks[0];
  const qty = Math.max(1, parseInt($('b-qty').value, 10) || 1);
  $('buy-box').innerHTML = '<div class="line"><span>Last price</span><span class="mono" style="font-weight:700">' + money(s.px) + '</span></div>' +
    '<div class="line"><span>Investment</span><span class="mono" style="font-weight:700">' + money(s.px * qty) + '</span></div>' +
    '<div class="line"><span>Auto stop-loss (8% below)</span><span class="mono" style="font-weight:700;color:#D12B42">' + money(s.px * 0.92) + '</span></div>' +
    '<div class="line"><span>Shares reach demat via ' + esc(inv.broker) + '</span><span class="mono" style="font-weight:700;color:#08805A">T+1</span></div>';
  $('buy-btn').textContent = 'Buy ' + qty + ' × ' + s.sym + ' for ' + inv.name.split(' ')[0];
  const t = D.trades.find((x) => String(x.id) === $('s-id').value);
  if (t) {
    const px = (D.stocks.find((x) => x.sym === t.sym) || {}).px, pnl = (px - t.bp) * t.q;
    $('sell-box').innerHTML = '<div class="line"><span>Bought at</span><span class="mono" style="font-weight:700">' + money(t.bp) + '</span></div>' +
      '<div class="line"><span>Sell at today\'s price</span><span class="mono" style="font-weight:700">' + money(px) + '</span></div>' +
      '<div class="line"><span>Profit / loss</span><span class="mono" style="font-weight:750;color:' + col(pnl) + '">' + inr(pnl, true) + ' (' + pct((px / t.bp - 1) * 100) + ')</span></div>';
    $('sell-btn').textContent = 'Sell ' + t.q + ' × ' + t.sym; $('sell-btn').disabled = false;
  } else { $('sell-box').innerHTML = '<div class="small">This investor has no open position to sell.</div>'; $('sell-btn').textContent = 'Nothing to sell'; $('sell-btn').disabled = true; }
}

function renderAlerts() {
  const { esc, pct, inr } = ML;
  const alerts = D.trades.filter((t) => t.hit).sort((a, b) => a.ret - b.ret);
  const worst = Math.max(1, ...alerts.map((a) => Math.abs(a.ret)));
  $('alert-note').textContent = alerts.length + ' open positions trade below their stop-loss · combined unrealised loss ' + inr(alerts.reduce((s, t) => s + t.pnl, 0), true);
  $('alert-list').innerHTML = alerts.map((a, i) => '<button type="button" class="inv" data-alert="' + a.id + '" data-owner="' + a.inv + '" style="grid-template-columns:52px minmax(0,1fr) minmax(70px,1fr) 70px;border-radius:0;border-top:1px solid #F1F2F7;padding:9px 20px">' +
    '<span class="mono small">#' + a.id + '</span><span style="min-width:0"><span class="nm" style="font-weight:750;font-size:13px">' + esc(a.sym) + '</span><span class="small" style="display:block;font-size:11.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(a.who) + ' · stop ₹' + a.sl.toLocaleString('en-IN') + '</span></span>' +
    '<div style="height:8px;background:#FDECEE;border-radius:4px;overflow:hidden"><div class="gx" style="animation-delay:' + Math.min(i * 0.03, 0.6) + 's;height:100%;width:' + (Math.abs(a.ret) / worst * 100).toFixed(0) + '%;background:#D12B42;border-radius:4px"></div></div>' +
    '<span class="mono" style="font-size:12.5px;font-weight:700;color:#D12B42;text-align:right">' + pct(a.ret, 1) + '</span></button>').join('') || '<div class="small" style="padding:0 20px 20px">No stop-loss alerts. All open positions are above their stop-loss.</div>';
}

function renderAll() {
  const open = D.trades.filter((t) => t.st === 'Open').length, hits = D.trades.filter((t) => t.hit).length;
  $('pills').innerHTML = [[D.investors.length, 'investors', '#0E1324'], [D.trades.length, 'trades', '#0E1324'], [open, 'open positions', '#4338CA'], [hits, 'stop-loss alerts', '#D12B42']]
    .map(([v, l, c]) => '<div class="card" style="padding:10px 16px;border-radius:14px"><div class="mono" style="font-size:20px;font-weight:700;color:' + c + '">' + v + '</div><div class="small" style="font-size:11.5px">' + l + '</div></div>').join('');
  renderDirectory(); renderInvestor(); renderAlerts();
}

function setMode(m) {
  st.mode = m;
  $('m-buy').classList.toggle('on', m === 'buy'); $('m-sell').classList.toggle('on', m === 'sell');
  $('m-buy').setAttribute('aria-pressed', m === 'buy'); $('m-sell').setAttribute('aria-pressed', m === 'sell');
  $('buy-form').hidden = m !== 'buy'; $('sell-form').hidden = m !== 'sell';
}

function submit(url, body, ok) {
  if (st.busy) return; st.busy = true;
  document.querySelectorAll('form button[type=submit]').forEach((b) => { b.disabled = true; });
  ML.post(url, body).then((r) => { ML.toast(ok(r)); return ML.data(true).then((d) => { D = d; renderAll(); }); })
    .catch((e) => ML.toast(e.message, true))
    .finally(() => { st.busy = false; document.querySelectorAll('form button[type=submit]').forEach((b) => { b.disabled = false; }); renderTicket(); });
}

$('iq').addEventListener('input', (e) => { st.q = e.target.value; renderDirectory(); });
$('b-sym').addEventListener('change', renderTicket); $('b-qty').addEventListener('input', renderTicket); $('s-id').addEventListener('change', renderTicket);
$('m-buy').addEventListener('click', () => setMode('buy')); $('m-sell').addEventListener('click', () => setMode('sell'));
document.addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b || !D) return;
  if (b.dataset.risk) { st.risk = b.dataset.risk; renderDirectory(); }
  else if (b.dataset.inv) { st.sel = +b.dataset.inv; renderDirectory(); renderInvestor(); }
  else if (b.dataset.alert) { st.sel = +b.dataset.owner; renderDirectory(); renderInvestor(); setMode('sell'); $('s-id').value = b.dataset.alert; renderTicket(); $('profile').scrollIntoView({ behavior: 'smooth' }); }
});
$('buy-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const s = D.stocks.find((x) => x.sym === $('b-sym').value), qty = parseInt($('b-qty').value, 10);
  submit('/api/buy', { investor_id: st.sel, stock_id: s.id, quantity: qty }, (r) => 'Trade #' + r.trade_id + ': ' + r.investor + ' bought ' + r.quantity + ' × ' + r.symbol + ' @ ' + ML.money(r.price) + '. Stop-loss ' + ML.money(r.stop_loss) + '. Delivery via ' + r.broker + ' on ' + r.due + ' (T+1).');
});
$('sell-form').addEventListener('submit', (e) => {
  e.preventDefault(); if (!$('s-id').value) return;
  submit('/api/sell', { trade_id: +$('s-id').value }, (r) => (r.pnl > 0 ? 'Profit booked: ' : r.pnl < 0 ? 'Loss booked: ' : 'Break-even: ') + ML.inr(r.pnl, true) + ' on ' + r.quantity + ' × ' + r.symbol + ' (' + ML.pct(r.return_pct) + ', held ' + r.held_days + ' days).');
});
$('add-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const body = { name: $('a-name').value, risk: +$('a-risk').value, home_state: $('a-state').value, broker: $('a-broker').value };
  if (st.busy) return; st.busy = true;
  ML.post('/api/investors', body).then((r) => { ML.toast('Registered ' + r.name + ' (ID ' + r.investor_id + ', ' + r.risk + ', broker ' + r.broker + ').'); $('a-name').value = '';
    return ML.data(true).then((d) => { D = d; st.sel = r.investor_id; st.risk = 'All'; st.q = ''; $('iq').value = ''; renderAll(); }); })
    .catch((er) => ML.toast(er.message, true)).finally(() => { st.busy = false; });
});

Promise.all([ML.data(), fetch('/api/meta').then((r) => r.json())]).then(([d, meta]) => {
  D = d;
  const esc = ML.esc;
  $('b-sym').innerHTML = d.stocks.slice().sort((a, b) => a.sym.localeCompare(b.sym)).map((s) => '<option value="' + esc(s.sym) + '">' + esc(s.sym) + ' · ₹' + s.px.toLocaleString('en-IN') + '</option>').join('');
  $('b-sym').value = 'TCS';
  $('a-risk').innerHTML = Object.entries(meta.risks).map(([k, v]) => '<option value="' + k + '">' + v + '</option>').join('');
  $('a-state').innerHTML = meta.states.map((s) => '<option>' + esc(s) + '</option>').join('');
  $('a-broker').innerHTML = meta.brokers.map((s) => '<option>' + esc(s) + '</option>').join('');
  st.sel = d.investors.slice().sort((a, b) => b.trades - a.trades)[0].id;
  renderAll();
  if (location.hash === '#alerts') $('alerts').scrollIntoView();
}).catch((e) => ML.fail($('profile'), e));

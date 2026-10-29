/* Share Delivery Tracker (Option 15, case study): animated chain, region slicer, KPIs, route map, brokers, delays, monthly trend. */
ML.topbar('delivery.html', { dark: true });
ML.footer();

const REG = ['All', 'North', 'West', 'South', 'East'];
const st = { region: REG.includes(location.hash.slice(1)) ? location.hash.slice(1) : 'All' };
let D = null;
const $ = (id) => document.getElementById(id);
const grade = (ot) => (ot >= 95 ? '#08805A' : ot >= 88 ? '#A16207' : '#D12B42');

(function chain() {
  const S = [['Investor', 'places order', 'shipment'], ['Broker', 'Zerodha, Groww…', 'courier'], ['NSE Mumbai', 'matches buyer + seller', 'warehouse'], ['Clearing Corp', 'settles money & shares', 'sorting hub'], ['Depository', 'CDSL / NSDL moves them', 'last mile'], ['Demat account', 'shares arrive · T+1', 'delivered']];
  let s = '<path d="M60 60 H940" stroke="#2B3150" stroke-width="3"></path><path class="flow" d="M60 60 H940" stroke="#8B85FF" stroke-width="3" fill="none"></path>' +
    ['t1', 't2', 't3'].map((t) => '<g class="' + t + '"><circle cx="60" cy="60" r="6" fill="#34D399"></circle></g>').join('');
  S.forEach((x, i) => { const cx = 60 + i * 176, c = i === 5 ? '#34D399' : '#8B85FF';
    s += '<circle class="ring" cx="' + cx + '" cy="60" r="7" fill="none" stroke="' + c + '" stroke-width="2"></circle><circle cx="' + cx + '" cy="60" r="15" fill="#0B0F1E" stroke="' + c + '" stroke-width="3"></circle>' +
      '<text x="' + cx + '" y="65" font-size="12" text-anchor="middle" fill="#FFF" font-family="JetBrains Mono" font-weight="700">' + (i + 1) + '</text>' +
      '<text x="' + cx + '" y="104" font-size="14" text-anchor="middle" fill="#FFF" font-family="Inter" font-weight="700">' + x[0] + '</text>' +
      '<text x="' + cx + '" y="124" font-size="11.5" text-anchor="middle" fill="#8A91B5" font-family="Inter">' + x[1] + '</text>' +
      '<text x="' + cx + '" y="24" font-size="10.5" text-anchor="middle" fill="#A5A0FF" font-family="Inter" font-weight="600">' + x[2] + '</text>'; });
  $('chain').innerHTML = s;
})();

function render() {
  const { esc, inr } = ML;
  $('regions').innerHTML = REG.map((r) => '<button type="button" class="chip' + (st.region === r ? ' on' : '') + '" data-region="' + r + '" aria-pressed="' + (st.region === r) + '">' + (r === 'All' ? 'All regions' : r) + '</button>').join('');
  const v = D.delivery[st.region], all = D.delivery.All, oc = grade(v.ontime);

  $('ring').innerHTML = '<circle cx="60" cy="60" r="48" fill="none" stroke="#EEF0F5" stroke-width="12"></circle>' +
    '<circle cx="60" cy="60" r="48" fill="none" stroke="' + oc + '" stroke-width="12" stroke-linecap="round" pathLength="100" stroke-dasharray="' + v.ontime.toFixed(1) + ' 100" transform="rotate(-90 60 60)" class="f"></circle>' +
    '<path d="M60 6 V18" stroke="#0E1324" stroke-width="2" transform="rotate(342 60 60)"><title>95% target</title></path>' +
    '<text x="60" y="64" font-size="22" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" fill="#0E1324">' + Math.round(v.ontime) + '%</text><text x="60" y="80" font-size="9" text-anchor="middle" font-family="Inter" fill="#5B6478">on time</text>';
  $('ot-note').textContent = 'About ' + Math.round(v.ontime) + ' of every 100 investors got their shares on the next trading day.';
  $('ot-verdict').textContent = v.ontime >= 95 ? '✓ Meets the 95% target' : '✗ Below the 95% target';
  $('ot-verdict').style.color = oc;
  $('kpis').innerHTML = [['Buy orders (shipments)', String(v.orders), 'worth ' + inr(v.value), '#0E1324'], ['Shares delivered', v.shares.toLocaleString('en-IN'), 'reached a demat account', '#0E1324'],
    ['Late · pending', v.late + ' · ' + v.pending, 'late deliveries · still in settlement', v.late ? '#D12B42' : '#08805A'], ['Average time to demat', 'T+' + v.avgdays.toFixed(2), 'trading days (target T+1.00)', '#0E1324']]
    .map(([l, val, n, c], i) => '<div class="card anim-up" style="padding:18px;animation-delay:' + (i * 0.05) + 's"><div style="font-size:12.5px;font-weight:650;color:#5B6478">' + l + '</div><div class="mono" style="font-size:26px;font-weight:700;letter-spacing:-.02em;margin-top:8px;color:' + c + '">' + val + '</div><div class="small" style="margin-top:4px">' + n + '</div></div>').join('');

  /* route map: simple lon/lat projection of the 10 investor cities, arcs to NSE Mumbai */
  const W = 520, H = 400, lon0 = 68, lon1 = 92, lat0 = 7, lat1 = 31;
  const X = (lo) => 30 + (lo - lon0) / (lon1 - lon0) * (W - 60), Y = (la) => 20 + (1 - (la - lat0) / (lat1 - lat0)) * (H - 40);
  let m = '<rect width="520" height="460" rx="16" fill="#F7F8FC"></rect>';
  for (let lo = 70; lo <= 90; lo += 5) m += '<path d="M' + X(lo) + ',' + Y(lat1) + ' L' + X(lo) + ',' + Y(lat0) + '" stroke="#E3E6EF"></path><text x="' + X(lo) + '" y="396" font-size="9" text-anchor="middle" fill="#5B6478" font-family="JetBrains Mono">' + lo + '°E</text>';
  for (let la = 10; la <= 30; la += 5) m += '<path d="M' + X(lon0) + ',' + Y(la) + ' L' + X(lon1) + ',' + Y(la) + '" stroke="#E3E6EF"></path><text x="34" y="' + (Y(la) - 3) + '" font-size="9" fill="#5B6478" font-family="JetBrains Mono">' + la + '°N</text>';
  const nx = X(D.nse.lon), ny = Y(D.nse.lat), byCity = {}, regC = {};
  all.routes.forEach((r) => { byCity[r.city] = r; }); v.routes.forEach((r) => { regC[r.city] = r; });
  const maxN = Math.max(...all.routes.map((r) => r.n));
  // cities that sit close to a neighbour get their label on the other side
  const LABEL_SIDE = { 'Jaipur': 'left', 'Bengaluru': 'left', 'Ahmedabad': 'left', 'Pune': 'right' };
  let arcs = '', dots = '';
  D.cities.forEach((c, i) => {
    const r = regC[c.city] || byCity[c.city] || { n: 0, ot: 0 }, active = st.region === 'All' || c.region === st.region, op = active ? 1 : 0.18;
    const x = X(c.lon), y = Y(c.lat), mx = (x + nx) / 2, my = Math.min(y, ny) - 40 - Math.abs(x - nx) * 0.15, col = grade(r.ot);
    const left = LABEL_SIDE[c.city] ? LABEL_SIDE[c.city] === 'left' : x < nx - 10;
    arcs += '<path d="M' + x.toFixed(1) + ',' + y.toFixed(1) + ' Q' + mx.toFixed(1) + ',' + my.toFixed(1) + ' ' + nx.toFixed(1) + ',' + ny.toFixed(1) + '" pathLength="1" class="d" style="animation-delay:' + (i * 0.08) + 's" stroke="' + col + '" stroke-width="' + (active ? 1.5 + r.n / maxN * 3 : 1).toFixed(1) + '" fill="none" opacity="' + op + '" stroke-linecap="round"></path>';
    dots += '<circle class="pop" style="animation-delay:' + (0.4 + i * 0.06) + 's" cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="' + (4 + Math.sqrt(r.n / maxN) * 9).toFixed(1) + '" fill="' + col + '" opacity="' + op + '" stroke="#FFF" stroke-width="2"><title>' + esc(c.city) + ': ' + r.n + ' orders, ' + Math.round(r.ot) + '% on time</title></circle>' +
      '<text x="' + (left ? x - 16 : x + 16).toFixed(1) + '" y="' + (y - 2).toFixed(1) + '" font-size="12" text-anchor="' + (left ? 'end' : 'start') + '" fill="#0E1324" opacity="' + op + '" font-family="Inter" font-weight="700">' + esc(c.city) + '</text>' +
      '<text x="' + (left ? x - 16 : x + 16).toFixed(1) + '" y="' + (y + 12).toFixed(1) + '" font-size="10.5" text-anchor="' + (left ? 'end' : 'start') + '" fill="#5B6478" opacity="' + op + '" font-family="JetBrains Mono">' + r.n + ' orders · ' + Math.round(r.ot) + '%</text>';
  });
  m += arcs + dots + '<circle class="ring" cx="' + nx + '" cy="' + ny + '" r="7" fill="none" stroke="#0E1324" stroke-width="2"></circle><rect x="' + (nx - 9) + '" y="' + (ny - 9) + '" width="18" height="18" rx="5" fill="#0E1324" transform="rotate(45 ' + nx + ' ' + ny + ')"></rect>' +
    '<text x="' + (nx - 18) + '" y="' + (ny + 28) + '" font-size="12.5" text-anchor="end" fill="#0E1324" font-family="Inter" font-weight="800">NSE Mumbai</text>' +
    '<rect x="16" y="414" width="12" height="12" rx="3" fill="#08805A"></rect><text x="34" y="424" font-size="11" fill="#3B4255" font-family="Inter">95%+ on time</text><rect x="120" y="414" width="12" height="12" rx="3" fill="#A16207"></rect><text x="138" y="424" font-size="11" fill="#3B4255" font-family="Inter">88–95%</text><rect x="204" y="414" width="12" height="12" rx="3" fill="#D12B42"></rect><text x="222" y="424" font-size="11" fill="#3B4255" font-family="Inter">below 88%</text>' +
    '<text x="16" y="448" font-size="11" fill="#5B6478" font-family="Inter">Distance does not slow a digital share: delay comes from brokers and paperwork.</text>';
  $('map').innerHTML = m;

  $('brokers').innerHTML = v.brokers.map((b, i) => { const g = { A: ['#E7F6EF', '#08805A'], B: ['#FEF3C7', '#A16207'], C: ['#FDECEE', '#D12B42'] }[b.g];
    return '<div style="display:grid;grid-template-columns:40px minmax(0,1fr);gap:12px;align-items:center"><span style="width:40px;height:40px;border-radius:12px;background:' + g[0] + ';color:' + g[1] + ';display:flex;align-items:center;justify-content:center;font-family:var(--display);font-weight:800;font-size:19px">' + b.g + '</span>' +
      '<div><div style="display:flex;justify-content:space-between;font-size:13px"><span style="font-weight:700">' + esc(b.b) + '</span><span class="mono" style="font-weight:700">' + b.ot.toFixed(0) + '%</span></div>' +
      '<div class="bar-track" style="height:8px;margin-top:6px"><div class="bar-fill gx" style="animation-delay:' + (i * 0.06) + 's;width:' + Math.max(4, (b.ot - 50) / 50 * 100).toFixed(0) + '%;background:' + g[1] + '"></div></div>' +
      '<div class="mono small" style="font-size:11px;margin-top:4px">' + b.n + ' orders · ' + b.late + ' late · avg T+' + b.days.toFixed(2) + '</div></div></div>'; }).join('');

  const rmax = Math.max(1, ...v.reasons.map((r) => r.n));
  $('reasons').innerHTML = v.reasons.map((r, i) => '<div><div style="display:flex;justify-content:space-between;font-size:13px;gap:10px"><span>' + esc(r.r) + '</span><span class="mono" style="font-weight:700">' + r.n + '</span></div><div class="bar-track" style="margin-top:6px"><div class="bar-fill gx" style="animation-delay:' + (i * 0.06) + 's;width:' + (r.n / rmax * 100).toFixed(0) + '%;background:#EA580C"></div></div></div>').join('') || '<div class="small" style="font-size:13px">No late deliveries in this region.</div>';

  const mo = v.monthly, lo = Math.min(70, ...mo.map((x) => x.v)) - 2;
  const MX = (i) => 46 + i * (456 / Math.max(1, mo.length - 1)), MY = (val) => 14 + (1 - (val - lo) / (100 - lo)) * 172;
  let s = '<defs><linearGradient id="mF" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#08805A" stop-opacity="0.22"></stop><stop offset="1" stop-color="#08805A" stop-opacity="0"></stop></linearGradient></defs>';
  for (let k = 0; k <= 3; k++) { const val = lo + (100 - lo) * k / 3; s += '<rect x="34" y="' + MY(val).toFixed(1) + '" width="480" height="1" fill="#EEF0F5"></rect><text x="28" y="' + (MY(val) + 3).toFixed(1) + '" font-size="10" text-anchor="end" fill="#5B6478" font-family="JetBrains Mono">' + Math.round(val) + '%</text>'; }
  const line = 'M' + mo.map((x, i) => MX(i).toFixed(1) + ',' + MY(x.v).toFixed(1)).join(' L');
  s += '<path d="M34 ' + MY(95).toFixed(1) + ' H514" stroke="#0E1324" stroke-width="1.4" stroke-dasharray="5 4"></path>' +
    '<path class="f" d="' + line + ' L' + MX(mo.length - 1).toFixed(1) + ',186 L' + MX(0).toFixed(1) + ',186 Z" fill="url(#mF)"></path><path d="' + line + '" pathLength="1" class="d" stroke="#08805A" stroke-width="2.4" fill="none" stroke-linejoin="round"></path>' +
    mo.map((x, i) => '<circle class="pop" style="animation-delay:' + (0.3 + i * 0.05) + 's" cx="' + MX(i).toFixed(1) + '" cy="' + MY(x.v).toFixed(1) + '" r="4" fill="' + grade(x.v) + '" stroke="#FFF" stroke-width="1.5"><title>' + x.m + ': ' + x.v + '%</title></circle><text x="' + MX(i).toFixed(1) + '" y="212" font-size="10" text-anchor="middle" fill="#5B6478" font-family="Inter">' + x.m + '</text>').join('');
  $('monthly').innerHTML = s;

  $('routes').innerHTML = v.routes.map((r) => '<tr><td style="font-weight:700">' + esc(r.city) + '</td><td style="color:#4A5266">' + r.region + '</td><td class="mono r">' + r.km.toLocaleString('en-IN') + '</td><td class="mono r">' + r.n + '</td><td class="mono r" style="font-weight:700;color:' + grade(r.ot) + '">' + Math.round(r.ot) + '%</td><td class="mono r">' + r.late + '</td></tr>').join('');

  const A = v.brokers.filter((b) => b.g === 'A').map((b) => b.b), best = v.brokers[0], worst = v.brokers[v.brokers.length - 1];
  $('reg-name').textContent = st.region === 'All' ? 'All regions' : st.region + ' region';
  $('takeaways').innerHTML = [
    Math.round(v.ontime) + '% of shares reached the demat account on time (T+1): ' + (v.ontime >= 95 ? 'this meets the 95% target.' : 'below the 95% target.'),
    A.length ? 'Choose a Grade A broker (' + A.join(', ') + ') for the fastest delivery. ' + worst.b + ' is late most often.' : 'No broker reaches Grade A here; ' + best.b + ' is the most reliable, ' + worst.b + ' the least.',
    v.reasons.length ? 'Most common delay: “' + v.reasons[0].r + '”. Pay funds on time and keep KYC / demat details correct.' : 'No late deliveries were recorded in this region.'
  ].map((t) => '<div style="display:flex;gap:10px;font-size:14.5px;line-height:1.55;color:#E3E6F2"><svg width="18" height="18" viewBox="0 0 18 18" style="flex:none;margin-top:2px" aria-hidden="true"><circle cx="9" cy="9" r="8" fill="#1F2547"></circle><path d="M5.5 9.2 8 11.5l4.5-5" stroke="#34D399" stroke-width="1.8" fill="none" stroke-linecap="round"></path></svg><span>' + esc(t) + '</span></div>').join('');
}

document.addEventListener('click', (e) => { const b = e.target.closest('button[data-region]'); if (!b || !D) return; st.region = b.dataset.region; history.replaceState(null, '', '#' + st.region); render(); });
ML.data().then((d) => { D = d; render(); }).catch((e) => ML.fail($('kpis'), e));

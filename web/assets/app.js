(function () {
  const UP = '#08805A', DN = '#D12B42';
  const PAGES = [
    ['index.html', 'Home'], ['dashboard.html', 'Dashboard'], ['stock.html', 'Stocks'],
    ['charts.html', 'Charts Lab'], ['portfolio.html', 'Investors & Trade'], ['delivery.html', 'Delivery']
  ];
  const LOGO = '<svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true"><rect width="30" height="30" rx="9" fill="currentColor"></rect>' +
    '<path d="M7 20 L12 14 L16 17 L23 9" stroke="#8B85FF" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"></path>' +
    '<circle cx="23" cy="9" r="2.4" fill="#34D399"></circle></svg>';

  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function inr(v, sign) {
    const s = sign ? (v > 0 ? '+' : v < 0 ? '−' : '') : (v < 0 ? '−' : '');
    const a = Math.abs(v);
    if (a >= 1e7) return s + '₹' + (a / 1e7).toFixed(2) + ' Cr';
    if (a >= 1e5) return s + '₹' + (a / 1e5).toFixed(1) + ' L';
    return s + '₹' + Math.round(a).toLocaleString('en-IN');
  }
  const pct = (v, dp) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(dp == null ? 2 : dp) + '%';
  const num = (v, dp) => Number(v).toLocaleString('en-IN', { minimumFractionDigits: dp == null ? 2 : dp, maximumFractionDigits: dp == null ? 2 : dp });
  const money = (v) => '₹' + num(v);
  const col = (v) => (v >= 0 ? UP : DN);
  const fmtDate = (d, opt) => new Date(d).toLocaleDateString('en-IN', opt || { day: 'numeric', month: 'short', year: 'numeric' });

  let dataPromise = null, chartsPromise = null;
  function getJSON(url) {
    return fetch(url, { cache: 'no-store' }).then((r) => {
      if (!r.ok) throw new Error('Server answered ' + r.status);
      return r.json();
    });
  }
  const data = (fresh) => { if (!dataPromise || fresh) dataPromise = getJSON('/api/data'); return dataPromise; };
  const charts = () => { if (!chartsPromise) chartsPromise = getJSON('/api/charts'); return chartsPromise; };
  function post(url, body) {
    return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then((r) => r.json().then((j) => { if (!r.ok) throw new Error(j.error || 'Request failed'); return j.result; }));
  }

  function topbar(active, opts) {
    opts = opts || {};
    const links = PAGES.map(([href, label]) => '<a href="' + href + '"' + (href === active ? ' class="on" aria-current="page"' : '') + '>' + esc(label) + '</a>').join('');
    const el = document.createElement('header');
    el.className = 'topbar' + (opts.dark ? ' dark' : '');
    el.innerHTML = '<div class="row"><a class="brand" href="index.html" style="color:' + (opts.dark ? '#FFFFFF' : '#0E1324') + '">' + LOGO +
      '<span style="color:inherit">Market<span>Lens</span></span></a><nav class="nav" aria-label="Main">' + links + '</nav>' +
      '<div class="status"><span class="live"></span><span id="ml-asof">NSE close</span></div></div>' + (opts.ticker ? '<div class="ticker" aria-label="Stock ticker"><div class="track" id="ml-ticker"></div></div>' : '');
    document.body.prepend(el);
    const host = document.createElement('div'); host.className = 'toast-host'; host.setAttribute('role', 'status'); host.id = 'ml-toasts';
    document.body.append(host);
    data().then((d) => {
      document.getElementById('ml-asof').innerHTML = 'NSE close · <b class="mono" style="color:' + (opts.dark ? '#FFFFFF' : '#0E1324') + '">' + fmtDate(d.asOf) + '</b>';
      const tk = document.getElementById('ml-ticker');
      if (tk) {
        const items = d.stocks.map((s) => '<a href="stock.html?s=' + encodeURIComponent(s.sym) + '"><b>' + esc(s.sym) + '</b><span class="mono" style="color:#3B4255">' + num(s.px) +
          '</span><span class="mono" style="font-weight:700;color:' + col(s.d1) + '">' + (s.d1 >= 0 ? '▲ ' : '▼ ') + Math.abs(s.d1).toFixed(2) + '%</span></a>').join('');
        tk.innerHTML = items + items;
      }
    }).catch(() => {});
  }

  function footer(dark) {
    const f = document.createElement('footer'); f.className = 'foot';
    f.innerHTML = '<span><strong style="color:' + (dark ? '#FFFFFF' : '#0E1324') + '">MarketLens</strong> · Stock Market Analysis System · Data Visualization project</span><span>Prices are simulated sample data. Nothing here is investment advice.</span>';
    document.body.append(f);
  }

  function toast(msg, isErr) {
    const host = document.getElementById('ml-toasts'); if (!host) return;
    const t = document.createElement('div'); t.className = 'toast' + (isErr ? ' err' : '');
    t.innerHTML = '<svg width="18" height="18" viewBox="0 0 18 18" style="flex:none" aria-hidden="true"><circle cx="9" cy="9" r="8" fill="' + (isErr ? '#FB7185' : '#08805A') + '"></circle>' +
      (isErr ? '<path d="M9 5v5M9 12.5v.5" stroke="#FFF" stroke-width="1.8" stroke-linecap="round"></path>' : '<path d="M5.5 9.2 8 11.5l4.5-5" stroke="#FFF" stroke-width="1.8" fill="none" stroke-linecap="round"></path>') +
      '</svg><span>' + esc(msg) + '</span>';
    host.append(t);
    setTimeout(() => { t.style.transition = 'opacity .4s'; t.style.opacity = '0'; setTimeout(() => t.remove(), 450); }, 6000);
  }

  function spark(vals, w, h, step) {
    const xs = []; for (let i = 0; i < vals.length; i += step || 1) xs.push(vals[i]);
    if (xs[xs.length - 1] !== vals[vals.length - 1]) xs.push(vals[vals.length - 1]);
    const lo = Math.min(...xs), hi = Math.max(...xs), sp = hi - lo || 1;
    const pts = xs.map((v, i) => [(i / (xs.length - 1)) * w, h - 3 - ((v - lo) / sp) * (h - 6)]);
    const line = 'M' + pts.map((p) => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' L');
    return { line, area: line + ' L' + w + ',' + h + ' L0,' + h + ' Z' };
  }

    // draws one chart from /api/charts as svg
  function chartSVG(c, label) {
    const a = (cls) => (cls ? ' class="' + cls + '"' : '');
    let s = '<svg viewBox="0 0 480 300" style="width:100%;height:auto;display:block" role="img" aria-label="' + esc(label || c.title) + '">' +
      '<defs><linearGradient id="gA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4F46E5" stop-opacity="0.28"></stop><stop offset="1" stop-color="#4F46E5" stop-opacity="0"></stop></linearGradient></defs>';
    c.rs.forEach((r) => { s += '<rect x="' + r.x + '" y="' + r.y + '" width="' + r.w + '" height="' + r.h + '" rx="' + r.rx + '" fill="' + r.f + '" opacity="' + r.o + '" stroke="' + r.sk + '"' + a(r.a) + '></rect>'; });
    c.ps.forEach((p) => {
      const dash = p.da && p.a.indexOf('d') !== 0 ? ' stroke-dasharray="' + p.da + '"' : '';
      const len = p.a.indexOf('d') === 0 ? ' pathLength="1"' : '';
      s += '<path d="' + p.d + '" stroke="' + p.s + '" fill="' + p.f + '" stroke-width="' + p.w + '" opacity="' + p.o + '"' + dash + len + ' stroke-linejoin="round" stroke-linecap="round"' + a(p.a) + '></path>';
    });
    c.cs.forEach((o) => { s += '<circle cx="' + o.x + '" cy="' + o.y + '" r="' + o.r + '" fill="' + o.f + '" opacity="' + o.o + '"' + a(o.a) + '></circle>'; });
    c.ts.forEach((t) => { s += '<text x="' + t.x + '" y="' + t.y + '" font-size="' + t.z + '" fill="' + t.f + '" text-anchor="' + t.an + '" font-weight="' + t.wt + '" font-family="Inter, sans-serif">' + esc(t.v) + '</text>'; });
    return s + '</svg>';
  }

  function reveal(root) {
    const els = (root || document).querySelectorAll('.reveal:not(.in)');
    if (!('IntersectionObserver' in window)) { els.forEach((e) => e.classList.add('in')); return; }
    const io = new IntersectionObserver((ents) => ents.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.12 });
    els.forEach((e) => io.observe(e));
  }

  function fail(el, err) {
    el.innerHTML = '<div class="err-box">Could not load data from the server (' + esc(err.message) + '). Is <span class="mono">python3 web_app.py</span> running?</div>';
  }

  window.ML = { UP, DN, esc, inr, pct, num, money, col, fmtDate, data, charts, post, topbar, footer, toast, spark, chartSVG, reveal, fail };
})();

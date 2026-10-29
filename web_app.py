"""
MarketLens website: the same Stock Market Analysis System, in the browser.

Run:  python3 web_app.py          (or Option 17 in the main menu / python3 main.py --web)
Open: http://localhost:8000

Uses only Python's built-in web server, so no extra package is needed.
  - web/            HTML, CSS and JavaScript of the six pages
  - /api/data       watchlist, OHLC prices, KPIs for every slicer, investors, trades, deliveries
  - /api/charts     the 26 syllabus charts as SVG shapes (built by web_data.py)
  - /api/buy, /api/sell, /api/investors   write to stock_market.db like Options 7, 8 and 6
  - /api/export     downloads stock_market_export.xlsx (Option 16)
"""
import os
import sys
import json
import gzip
import sqlite3
import threading
import warnings
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

warnings.filterwarnings("ignore")
import main as app
import db_setup
import web_data

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(ROOT, "web")

_cache = {}
_lock = threading.Lock()

def get_payload(name):
    """Builds charts + data once and keeps them in memory until the database changes."""
    with _lock:
        if not _cache:
            charts, data = web_data.build_all()
            _cache['charts'] = json.dumps(charts, separators=(",", ":")).encode()
            _cache['data'] = json.dumps(data, separators=(",", ":")).encode()
        return _cache[name]

def invalidate():
    with _lock:
        _cache.clear()

def add_investor(name, risk, home_state, broker):
    if not name.strip():
        raise ValueError("Name cannot be empty.")
    if risk not in db_setup.RISK_PROFILES:
        raise ValueError("Risk profile must be 1, 2, 3 or 4.")
    if home_state not in db_setup.INVESTOR_CITIES:
        raise ValueError("Pick one of the listed home states.")
    if broker not in db_setup.BROKERS:
        raise ValueError("Pick one of the listed brokers.")
    conn = app.get_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO investors (name, risk_profile, home_state, broker) VALUES (?, ?, ?, ?);",
                    (name.strip(), risk, home_state, broker))
        conn.commit()
        return {'investor_id': cur.lastrowid, 'name': name.strip(), 'risk': db_setup.RISK_PROFILES[risk], 'broker': broker}
    finally:
        conn.close()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, fmt, *args):
        # args[0] is the request line for normal logs but an HTTPStatus for error logs (e.g. a 404)
        if "/api/" in str(args[0] if args else ""):
            sys.stderr.write(" [web] " + (fmt % args) + "\n")

    def _send(self, body, ctype="application/json", status=200, extra=None):
        if "gzip" in self.headers.get("Accept-Encoding", "") and len(body) > 2048:
            body = gzip.compress(body, 5)
            extra = dict(extra or {}, **{"Content-Encoding": "gzip"})
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status=200):
        self._send(json.dumps(obj).encode(), status=status)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/data":
            return self._send(get_payload('data'))
        if path == "/api/charts":
            return self._send(get_payload('charts'))
        if path == "/api/meta":
            return self._json({'states': list(db_setup.INVESTOR_CITIES), 'brokers': db_setup.BROKERS, 'risks': db_setup.RISK_PROFILES})
        if path == "/api/export":
            app.export_for_power_bi()
            with open(os.path.join(ROOT, "stock_market_export.xlsx"), "rb") as f:
                body = f.read()
            return self._send(body, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              extra={"Content-Disposition": 'attachment; filename="stock_market_export.xlsx"'})
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            size = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(size) or b"{}")
            if path == "/api/buy":
                result = app.place_buy(int(body['investor_id']), int(body['stock_id']), int(body['quantity']))
            elif path == "/api/sell":
                result = app.place_sell(int(body['trade_id']))
            elif path == "/api/investors":
                result = add_investor(str(body.get('name', '')), int(body.get('risk', 0)), str(body.get('home_state', '')), str(body.get('broker', '')))
            else:
                return self._json({'error': 'Unknown action'}, 404)
        except (ValueError, KeyError, TypeError) as e:
            return self._json({'error': str(e) or 'Invalid request'}, 400)
        except sqlite3.Error as e:
            return self._json({'error': 'Database error: %s' % e}, 500)
        invalidate()
        return self._json({'ok': True, 'result': result})

def run(port=8000, open_browser=True):
    os.chdir(ROOT)
    app.check_db()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://localhost:%d" % port
    print("\n [Web] Building charts and data from stock_market.db ...")
    get_payload('data')
    print(f" [✓] MarketLens website running at {url}")
    print("     Pages: Home | Dashboard | Stocks | Charts Lab (26 charts) | Investors & Trade | Delivery")
    print("     Press Ctrl+C to stop the website and go back.\n")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n [i] Website stopped.")
    finally:
        server.server_close()

if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8000
    run(port, open_browser="--no-browser" not in sys.argv)

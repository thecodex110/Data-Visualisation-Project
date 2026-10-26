import sqlite3
import random
import math
import numpy as np
import pandas as pd
from datetime import datetime
from faker import Faker

DB_NAME = "stock_market.db"
TRADING_DAYS = 250          # about one year of NSE trading sessions
STOP_LOSS_PCT = 0.08        # stop-loss is placed 8% below the buy price

SECTORS = ["IT", "Banking", "Pharma", "Auto", "FMCG", "Energy"]
RISK_PROFILES = {1: "Conservative", 2: "Moderate", 3: "Growth", 4: "Aggressive"}

# Sector behaviour used by the price simulator: (annual drift, daily sector volatility, daily stock volatility)
SECTOR_PROFILE = {
    "IT":      (0.08, 0.006, 0.012),
    "Banking": (0.14, 0.007, 0.011),
    "Pharma":  (0.18, 0.006, 0.012),
    "Auto":    (0.22, 0.008, 0.015),
    "FMCG":    (0.06, 0.004, 0.008),
    "Energy":  (0.10, 0.007, 0.013),
}

# 36 NSE-listed companies (6 per sector): symbol, company, sector, HQ state, starting price (Rs)
# Prices are SIMULATED sample data, not real market prices.
STOCK_LIST = [
    ("TCS", "Tata Consultancy Services", "IT", "Maharashtra", 3850),
    ("INFY", "Infosys", "IT", "Karnataka", 1520),
    ("WIPRO", "Wipro", "IT", "Karnataka", 470),
    ("HCLTECH", "HCL Technologies", "IT", "Uttar Pradesh", 1380),
    ("TECHM", "Tech Mahindra", "IT", "Maharashtra", 1250),
    ("LTIM", "LTIMindtree", "IT", "Maharashtra", 5200),
    ("HDFCBANK", "HDFC Bank", "Banking", "Maharashtra", 1560),
    ("ICICIBANK", "ICICI Bank", "Banking", "Gujarat", 990),
    ("SBIN", "State Bank of India", "Banking", "Maharashtra", 610),
    ("KOTAKBANK", "Kotak Mahindra Bank", "Banking", "Maharashtra", 1780),
    ("AXISBANK", "Axis Bank", "Banking", "Gujarat", 1040),
    ("INDUSINDBK", "IndusInd Bank", "Banking", "Maharashtra", 1450),
    ("SUNPHARMA", "Sun Pharmaceutical", "Pharma", "Gujarat", 1150),
    ("DRREDDY", "Dr. Reddy's Laboratories", "Pharma", "Telangana", 5400),
    ("CIPLA", "Cipla", "Pharma", "Maharashtra", 1240),
    ("DIVISLAB", "Divi's Laboratories", "Pharma", "Telangana", 3600),
    ("LUPIN", "Lupin", "Pharma", "Maharashtra", 1100),
    ("AUROPHARMA", "Aurobindo Pharma", "Pharma", "Telangana", 920),
    ("MARUTI", "Maruti Suzuki", "Auto", "Delhi", 10100),
    ("TATAMOTORS", "Tata Motors", "Auto", "Maharashtra", 640),
    ("M&M", "Mahindra & Mahindra", "Auto", "Maharashtra", 1550),
    ("BAJAJ-AUTO", "Bajaj Auto", "Auto", "Maharashtra", 5000),
    ("HEROMOTOCO", "Hero MotoCorp", "Auto", "Delhi", 3100),
    ("EICHERMOT", "Eicher Motors", "Auto", "Delhi", 3400),
    ("HINDUNILVR", "Hindustan Unilever", "FMCG", "Maharashtra", 2550),
    ("ITC", "ITC", "FMCG", "West Bengal", 440),
    ("NESTLEIND", "Nestle India", "FMCG", "Delhi", 2400),
    ("BRITANNIA", "Britannia Industries", "FMCG", "West Bengal", 4700),
    ("DABUR", "Dabur India", "FMCG", "Delhi", 560),
    ("MARICO", "Marico", "FMCG", "Maharashtra", 540),
    ("RELIANCE", "Reliance Industries", "Energy", "Maharashtra", 2450),
    ("ONGC", "Oil & Natural Gas Corp", "Energy", "Delhi", 190),
    ("NTPC", "NTPC", "Energy", "Delhi", 240),
    ("POWERGRID", "Power Grid Corp", "Energy", "Delhi", 230),
    ("BPCL", "Bharat Petroleum", "Energy", "Maharashtra", 380),
    ("IOC", "Indian Oil Corp", "Energy", "Delhi", 120),
]

# ------------------------------------------------------------------------------
# Case study: the stock market's own supply chain = SHARE DELIVERY (T+1 settlement)
# Investor -> Broker -> NSE Mumbai -> Clearing Corporation -> Depository -> Demat account
# ------------------------------------------------------------------------------
# Investor home state -> (city, region, latitude, longitude): where each order starts from
INVESTOR_CITIES = {
    "Delhi": ("New Delhi", "North", 28.6139, 77.2090),
    "Uttar Pradesh": ("Lucknow", "North", 26.8467, 80.9462),
    "Rajasthan": ("Jaipur", "North", 26.9124, 75.7873),
    "Maharashtra": ("Pune", "West", 18.5204, 73.8567),
    "Gujarat": ("Ahmedabad", "West", 23.0225, 72.5714),
    "Karnataka": ("Bengaluru", "South", 12.9716, 77.5946),
    "Tamil Nadu": ("Chennai", "South", 13.0827, 80.2707),
    "Kerala": ("Kochi", "South", 9.9312, 76.2673),
    "Telangana": ("Hyderabad", "South", 17.3850, 78.4867),
    "West Bengal": ("Kolkata", "East", 22.5726, 88.3639),
}
EXCHANGE = ("NSE, Mumbai", 19.0662, 72.8657)
BROKERS = ["Zerodha", "Groww", "Upstox", "Angel One", "ICICI Direct"]
# Chance that a broker's order is NOT credited to the demat account on T+1
BROKER_DELAY_RATE = {"Zerodha": 0.05, "Groww": 0.07, "Upstox": 0.09, "Angel One": 0.12, "ICICI Direct": 0.15}
# Why a delivery can be late, with how many extra trading days it adds
DELAY_REASONS = {
    "Funds paid late by investor": (1, 1),
    "Seller short delivery -> auction": (2, 3),
    "Bank / settlement holiday": (1, 1),
    "Demat / KYC details mismatch": (2, 4),
}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Drop existing tables to ensure clean seed
    for table in ["deliveries", "shipments", "trades", "price_history", "stocks", "investors", "sectors"]:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")

    # Create tables
    cursor.execute("""
    CREATE TABLE sectors (
        sector_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sector_name TEXT NOT NULL UNIQUE
    );
    """)

    cursor.execute("""
    CREATE TABLE investors (
        investor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        risk_profile INTEGER NOT NULL,
        home_state TEXT NOT NULL,
        broker TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE stocks (
        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        company_name TEXT NOT NULL,
        sector_id INTEGER NOT NULL,
        hq_state TEXT NOT NULL,
        FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE price_history (
        price_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id INTEGER NOT NULL,
        trade_date TEXT NOT NULL,
        open REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        close REAL,
        volume INTEGER NOT NULL,
        FOREIGN KEY (stock_id) REFERENCES stocks(stock_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE trades (
        trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id INTEGER NOT NULL,
        investor_id INTEGER NOT NULL,
        buy_date TEXT NOT NULL,
        buy_price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        stop_loss REAL NOT NULL,
        sell_date TEXT,
        sell_price REAL,
        FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
        FOREIGN KEY (investor_id) REFERENCES investors(investor_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE deliveries (
        delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER NOT NULL,
        broker TEXT NOT NULL,
        from_city TEXT NOT NULL,
        region TEXT NOT NULL,
        distance_km REAL NOT NULL,
        order_date TEXT NOT NULL,
        expected_date TEXT NOT NULL,
        delivery_date TEXT,
        delay_reason TEXT,
        FOREIGN KEY (trade_id) REFERENCES trades(trade_id)
    );
    """)
    conn.commit()
    conn.close()

def trading_dates(n=TRADING_DAYS):
    """Last n weekday sessions ending today (or the last weekday)."""
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range(end=datetime.now().date(), periods=n)]

def next_trading_day(date_str, days=1):
    """Date `days` trading sessions (weekdays) after date_str - used for T+1 settlement."""
    return (pd.Timestamp(date_str) + pd.offsets.BDay(days)).strftime("%Y-%m-%d")

def build_ohlcv(rng, returns, start_price, base_volume):
    """Turns a series of daily returns into Open/High/Low/Close/Volume rows."""
    closes = start_price * np.cumprod(1 + returns)
    prev = np.concatenate([[start_price], closes[:-1]])
    opens = prev * (1 + rng.normal(0, 0.003, len(returns)))
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, 0.006, len(returns))))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, 0.006, len(returns))))
    volumes = (base_volume * np.exp(rng.normal(0, 0.35, len(returns))) * (1 + 8 * np.abs(returns))).astype(int)
    return opens, highs, lows, closes, volumes

def simulate_new_stock_history(conn, stock_id, sector_name, end_price, seed=None):
    """Creates one year of simulated prices for a newly added stock, ending at the given price."""
    rng = np.random.default_rng(seed)
    mu, s_sec, s_stock = SECTOR_PROFILE.get(sector_name, (0.10, 0.006, 0.012))
    sigma = math.sqrt(0.008 ** 2 + s_sec ** 2 + s_stock ** 2)
    returns = mu / 252 + sigma * rng.standard_t(4, TRADING_DAYS) / math.sqrt(2)
    opens, highs, lows, closes, volumes = build_ohlcv(rng, returns, 1.0, rng.uniform(5e5, 4e6))
    scale = end_price / closes[-1]
    rows = [(stock_id, d, round(o * scale, 2), round(h * scale, 2), round(l * scale, 2), round(c * scale, 2), int(v))
            for d, o, h, l, c, v in zip(trading_dates(), opens, highs, lows, closes, volumes)]
    conn.executemany("""
    INSERT INTO price_history (stock_id, trade_date, open, high, low, close, volume)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, rows)

def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def order_route(home_state):
    """Where an investor's order starts (city, region) and how far it is from NSE Mumbai."""
    city, region, lat, lon = INVESTOR_CITIES.get(home_state, (home_state, "Other", EXCHANGE[1], EXCHANGE[2]))
    return city, region, round(haversine_km(lat, lon, EXCHANGE[1], EXCHANGE[2]), 1)

def create_delivery(conn, trade_id, broker, home_state, order_date):
    """Delivery record for a NEW buy order: shares are expected in the demat account on T+1 (still pending)."""
    city, region, km = order_route(home_state)
    conn.execute("""
    INSERT INTO deliveries (trade_id, broker, from_city, region, distance_km, order_date, expected_date, delivery_date, delay_reason)
    VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL);
    """, (trade_id, broker, city, region, km, order_date, next_trading_day(order_date)))
    return next_trading_day(order_date)

def seed_deliveries(conn):
    """One share-delivery record per buy trade: T+1 on time, or late with a reason, or still pending."""
    rng = random.Random(7)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.trade_id, t.buy_date, i.broker, i.home_state
        FROM trades t JOIN investors i ON t.investor_id = i.investor_id;
    """)
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for trade_id, buy_date, broker, home_state in cursor.fetchall():
        city, region, km = order_route(home_state)
        expected = next_trading_day(buy_date)
        reason = None
        delivered = expected
        if rng.random() < BROKER_DELAY_RATE[broker]:
            reason = rng.choice(list(DELAY_REASONS))
            delivered = next_trading_day(expected, rng.randint(*DELAY_REASONS[reason]))
        if delivered > today:
            delivered = None          # still inside the settlement cycle
        rows.append((trade_id, broker, city, region, km, buy_date, expected, delivered, reason))
    cursor.executemany("""
    INSERT INTO deliveries (trade_id, broker, from_city, region, distance_km, order_date, expected_date, delivery_date, delay_reason)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, rows)
    conn.commit()

def seed_db():
    fake = Faker('en_IN')
    Faker.seed(42)
    random.seed(42)
    rng = np.random.default_rng(42)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Seed Sectors
    for sector in SECTORS:
        cursor.execute("INSERT INTO sectors (sector_name) VALUES (?);", (sector,))
    conn.commit()
    cursor.execute("SELECT sector_name, sector_id FROM sectors;")
    sector_map = dict(cursor.fetchall())

    # 2. Seed Investors (90 investors from 10 states, risk profile 1-4, each with one broker account)
    indian_states = list(INVESTOR_CITIES)
    investors_data = [(fake.name(), random.choice([1, 2, 2, 3, 3, 4]), random.choice(indian_states),
                       random.choices(BROKERS, weights=[30, 25, 20, 15, 10])[0]) for _ in range(90)]
    cursor.executemany("INSERT INTO investors (name, risk_profile, home_state, broker) VALUES (?, ?, ?, ?);", investors_data)

    # 3. Seed Stocks (36 companies, 6 per sector)
    cursor.executemany("""
    INSERT INTO stocks (symbol, company_name, sector_id, hq_state)
    VALUES (?, ?, ?, ?);
    """, [(s, c, sector_map[sec], st) for s, c, sec, st, _ in STOCK_LIST])
    conn.commit()
    cursor.execute("SELECT stock_id, symbol FROM stocks;")
    stock_ids = {sym: sid for sid, sym in cursor.fetchall()}

    # 4. Seed Price History: daily return = market move x beta + sector move + company move
    dates = trading_dates()
    n = len(dates)
    market = 0.0004 + 0.008 * rng.standard_t(4, n) / math.sqrt(2)
    sector_moves = {sec: SECTOR_PROFILE[sec][1] * rng.standard_t(4, n) / math.sqrt(2) for sec in SECTORS}
    closes_by_stock = {}
    price_rows = []
    for symbol, _, sector, _, start_price in STOCK_LIST:
        sid = stock_ids[symbol]
        mu, _, s_stock = SECTOR_PROFILE[sector]
        beta = rng.uniform(0.7, 1.3)
        drift = (mu + rng.normal(0, 0.12)) / 252 - 0.0004 * beta
        returns = drift + beta * market + sector_moves[sector] + s_stock * rng.standard_t(4, n) / math.sqrt(2)
        opens, highs, lows, closes, volumes = build_ohlcv(rng, returns, start_price, rng.uniform(5e5, 8e6))
        closes_by_stock[sid] = closes
        price_rows += [(sid, d, round(o, 2), round(h, 2), round(l, 2), round(c, 2), int(v))
                       for d, o, h, l, c, v in zip(dates, opens, highs, lows, closes, volumes)]

    # Data-feed gaps: about 1% of closing prices are missing (cleaned later with forward fill)
    gap_rows = set(rng.choice(len(price_rows), size=len(price_rows) // 100, replace=False))
    price_rows = [r[:5] + (None,) + r[6:] if i in gap_rows and r[1] not in (dates[0], dates[-1]) else r
                  for i, r in enumerate(price_rows)]
    cursor.executemany("""
    INSERT INTO price_history (stock_id, trade_date, open, high, low, close, volume)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, price_rows)
    conn.commit()

    # 5. Seed Trades (300 buy orders; most are sold later, some are still open positions)
    # Conservative investors prefer defensive sectors and hold longer; aggressive ones trade cyclicals quickly
    preferred = {1: ["FMCG", "Banking", "Pharma"], 2: ["Banking", "IT", "FMCG"],
                 3: ["IT", "Auto", "Pharma"], 4: ["Auto", "Energy", "IT"]}
    hold_range = {1: (30, 200), 2: (20, 150), 3: (10, 100), 4: (2, 45)}
    sector_stocks = {sec: [stock_ids[s] for s, _, sc, _, _ in STOCK_LIST if sc == sec] for sec in SECTORS}
    cursor.execute("SELECT investor_id, risk_profile FROM investors;")
    investors = cursor.fetchall()

    trades_data = []
    for _ in range(300):
        inv_id, risk = random.choice(investors)
        sector = random.choice(preferred[risk]) if random.random() < 0.7 else random.choice(SECTORS)
        sid = random.choice(sector_stocks[sector])
        buy_i = random.randint(0, n - 2)
        buy_price = round(float(closes_by_stock[sid][buy_i]), 2)
        # Trade sizes are log-normal: many small orders and a few very large ones (right-skewed)
        quantity = max(1, int(random.lognormvariate(math.log(50000), 0.9) * (0.6 + 0.4 * risk) / buy_price))
        stop_loss = round(buy_price * (1 - STOP_LOSS_PCT), 2)

        sell_i = buy_i + random.randint(*hold_range[risk])
        if random.random() < 0.8 and sell_i < n:
            sell_date, sell_price = dates[sell_i], round(float(closes_by_stock[sid][sell_i]), 2)
        else:
            sell_date, sell_price = None, None
        trades_data.append((sid, inv_id, dates[buy_i], buy_price, quantity, stop_loss, sell_date, sell_price))

    cursor.executemany("""
    INSERT INTO trades (stock_id, investor_id, buy_date, buy_price, quantity, stop_loss, sell_date, sell_price)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, trades_data)
    conn.commit()

    # 6. Seed Share Deliveries (Supply Chain case study: one T+1 delivery per buy order)
    seed_deliveries(conn)
    conn.close()

if __name__ == "__main__":
    print("Initializing database schema...")
    init_db()
    print("Seeding synthetic market data...")
    seed_db()
    print(f"Database setup complete! '{DB_NAME}' created successfully.")

import os
import sys
import argparse
import sqlite3
import pandas as pd
from datetime import datetime

import db_setup
import preprocessing
import visualizations

DB_NAME = "stock_market.db"

def check_db():
    if not os.path.exists(DB_NAME):
        print("\n [Setup] Initializing SQLite database 'stock_market.db' with one year of simulated NSE market data...")
        db_setup.init_db()
        db_setup.seed_db()
        print(" [Setup] Database ready!\n")

def get_conn():
    return sqlite3.connect(DB_NAME)

def _latest_price(cursor, stock_id):
    cursor.execute("""
        SELECT close, trade_date FROM price_history
        WHERE stock_id = ? AND close IS NOT NULL
        ORDER BY trade_date DESC LIMIT 1;
    """, (stock_id,))
    return cursor.fetchone()

def _pick_sector(conn):
    sectors = pd.read_sql_query("SELECT * FROM sectors;", conn)
    print("\nSelect Sector:")
    for _, s in sectors.iterrows():
        print(f"  {s['sector_id']}. {s['sector_name']}")
    sector_id = int(input("\nSelect Sector ID: "))
    match = sectors[sectors['sector_id'] == sector_id]
    if match.empty:
        raise ValueError("Sector ID not found")
    return sector_id, match['sector_name'].iloc[0]

# ==============================================================================
# CORE MARKET OPERATIONS (ADD, REMOVE, SEARCH & ANALYSE, BUY, SELL, STOP-LOSS)
# ==============================================================================

def view_stocks():
    summary = preprocessing.get_stock_summary()
    conn = get_conn()
    hq = pd.read_sql_query("SELECT stock_id, hq_state FROM stocks;", conn)
    conn.close()
    summary = summary.merge(hq, on='stock_id').sort_values(['sector_name', 'symbol'])

    print("\n" + "="*96)
    print("                                   MARKET WATCHLIST (NSE)")
    print("="*96)
    print(f"{'ID':<4} | {'Symbol':<11} | {'Company':<27} | {'Sector':<8} | {'Price (Rs)':>10} | {'1D %':>6} | {'1Y %':>7} | {'HQ State'}")
    print("-"*96)
    for _, r in summary.iterrows():
        print(f"{r['stock_id']:<4} | {r['symbol']:<11} | {r['company_name'][:27]:<27} | {r['sector_name']:<8} | "
              f"{r['last_close']:>10,.2f} | {r['change_1d']:>+6.2f} | {r['return_1y']:>+7.1f} | {r['hq_state']}")
    print("="*96)
    up = (summary['change_1d'] > 0).sum()
    print(f" Market breadth today: {up} stocks up, {len(summary) - up} down | (prices are simulated sample data)\n")

def add_stock():
    print("\n" + "-"*40)
    print("          ADD NEW STOCK (+)")
    print("-"*40)
    symbol = input("Enter NSE Symbol (e.g. ZOMATO): ").strip().upper()
    company = input("Enter Company Name: ").strip()
    if not symbol or not company:
        print(" [!] Symbol and Company Name cannot be empty.")
        return

    conn = get_conn()
    try:
        sector_id, sector_name = _pick_sector(conn)
        price = float(input("Enter Current Share Price (Rs): "))
        if price <= 0:
            print(" [!] Price must be greater than 0.")
            return

        hq_state = input("Enter Head-Office State (e.g., Maharashtra, Karnataka): ").strip()
        if not hq_state:
            hq_state = "Maharashtra"

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stocks (symbol, company_name, sector_id, hq_state, plant_city)
            VALUES (?, ?, ?, ?, NULL);
        """, (symbol, company, sector_id, hq_state))
        # A new listing needs history for the charts: simulate one year that ends at today's price
        db_setup.simulate_new_stock_history(conn, cursor.lastrowid, sector_name, price)
        conn.commit()
        print(f"\n [✓] Success: Added {symbol} - {company} ({sector_name}) at Rs {price:,.2f}.")
        print(f"     {db_setup.TRADING_DAYS} days of simulated price history created so it appears in every chart.")
    except sqlite3.IntegrityError:
        print(f" [!] Symbol '{symbol}' already exists in the watchlist.")
    except Exception as e:
        print(f" [!] Error adding stock: {e}")
    finally:
        conn.close()

def remove_stock():
    """Removes (delists) a stock from the watchlist, only if no investor still holds it."""
    print("\n" + "-"*40)
    print("        REMOVE / DELIST STOCK (-)")
    print("-"*40)
    try:
        stock_id = int(input("Enter Stock ID to remove: "))
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT symbol, company_name FROM stocks WHERE stock_id = ?;", (stock_id,))
        row = cursor.fetchone()
        if not row:
            print(" [!] Error: Stock ID not found in watchlist.")
            conn.close()
            return

        symbol, company = row
        cursor.execute("SELECT COUNT(*), COUNT(sell_date) FROM trades WHERE stock_id = ?;", (stock_id,))
        total_trades, sold = cursor.fetchone()
        open_positions = total_trades - sold
        print(f"\nFound: {symbol} - {company}")
        print(f"Trades in history: {total_trades} | Still open (held by investors): {open_positions}")

        if open_positions > 0:
            print(f" [!] Cannot remove: {open_positions} investor position(s) are still open in {symbol}.")
            print("     Sell those positions first (Option 8).")
        else:
            confirm = input(f"Permanently remove {symbol} with its price history and trades? (y/n): ").strip().lower()
            if confirm == 'y':
                for table in ["trades", "price_history", "shipments"]:
                    cursor.execute(f"DELETE FROM {table} WHERE stock_id = ?;", (stock_id,))
                cursor.execute("DELETE FROM stocks WHERE stock_id = ?;", (stock_id,))
                conn.commit()
                print(f"\n [✓] Successfully removed {symbol} from the watchlist.")
            else:
                print(" Operation cancelled.")
        conn.close()
    except Exception as e:
        print(f" [!] Error removing stock: {e}")

def search_and_analyse():
    query_str = input("\nEnter symbol / company / sector keyword: ").strip()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.stock_id, s.symbol, s.company_name, sec.sector_name, s.hq_state
        FROM stocks s
        JOIN sectors sec ON s.sector_id = sec.sector_id
        WHERE s.symbol LIKE ? OR s.company_name LIKE ? OR sec.sector_name LIKE ?;
    """, (f"%{query_str}%", f"%{query_str}%", f"%{query_str}%"))
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        print(" [!] No matching stocks found.")
        return

    print(f"\nFound {len(rows)} matching stock(s):")
    print("-" * 80)
    for r in rows:
        price, _ = _latest_price(cursor, r[0])
        print(f" [ID {r[0]}] {r[1]:<11} {r[2]} ({r[3]}) | Last: Rs {price:,.2f} | HQ: {r[4]}")
    print("-" * 80)
    conn.close()

    pick = input("Enter a Stock ID to ANALYSE (Enter to skip): ").strip()
    if not pick.isdigit():
        return
    report, _ = preprocessing.analyse_stock(int(pick))
    if report is None:
        print(" [!] Stock ID not found.")
        return

    rsi_note = "overbought" if report['rsi'] > 70 else ("oversold" if report['rsi'] < 30 else "normal zone")
    print("\n" + "=" * 70)
    print(f"  STOCK ANALYSIS: {report['symbol']} - {report['company']} ({report['sector']})")
    print("=" * 70)
    print(f"  Last close     : Rs {report['last_close']:,.2f}  (on {report['last_date']})")
    print(f"  Returns        : 1D {report['ret_1d']:+.2f}% | 1M {report['ret_1m']:+.2f}% | 3M {report['ret_3m']:+.2f}% | 1Y {report['ret_1y']:+.2f}%")
    print(f"  52-week range  : Rs {report['low_52w']:,.2f}  -  Rs {report['high_52w']:,.2f}")
    print(f"  Risk           : volatility {report['volatility']:.1f}% a year | max drawdown {report['max_drawdown']:.1f}%")
    print(f"  Moving averages: 20-DMA Rs {report['dma_20']:,.2f} | 50-DMA Rs {report['dma_50']:,.2f}")
    print(f"  RSI (14)       : {report['rsi']:.1f}  ({rsi_note})")
    print(f"  Avg volume (20d): {report['avg_volume']:,.0f} shares")
    print(f"  SIGNAL         : {report['signal']}")
    print("=" * 70)
    print("  (Educational analysis on simulated data - not investment advice.)")
    visualizations.plot_stock_analysis(int(pick))

def view_investors():
    summary = preprocessing.get_investor_summary().sort_values('investor_id')

    print("\n" + "="*88)
    print("                               INVESTOR DIRECTORY")
    print("="*88)
    print(f"{'ID':<5} | {'Investor Name':<25} | {'Risk Profile':<13} | {'Home State':<14} | {'Trades':>6} | {'Total P&L (Rs)':>14}")
    print("-"*88)
    for _, r in summary.iterrows():
        print(f"{r['investor_id']:<5} | {r['name'][:25]:<25} | {r['risk_label']:<13} | {r['home_state']:<14} | "
              f"{int(r['total_trades']):>6} | {r['total_pnl']:>+14,.0f}")
    print("="*88 + "\n")

def add_investor():
    print("\n" + "-"*40)
    print("          ADD NEW INVESTOR")
    print("-"*40)
    name = input("Enter Investor Full Name: ").strip()
    if not name:
        print(" [!] Name cannot be empty.")
        return

    print("\nRisk Profile:")
    for k, v in db_setup.RISK_PROFILES.items():
        print(f"  {k}. {v}")
    conn = get_conn()
    try:
        risk = int(input("\nSelect Risk Profile (1-4): "))
        if risk not in db_setup.RISK_PROFILES:
            print(" [!] Risk profile must be 1, 2, 3 or 4.")
            return
        home_state = input("Enter Home State (e.g. Maharashtra, Karnataka): ").strip()
        if not home_state:
            home_state = "Maharashtra"

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investors (name, risk_profile, home_state)
            VALUES (?, ?, ?);
        """, (name, risk, home_state))
        conn.commit()
        print(f"\n [✓] Successfully registered investor '{name}' (ID {cursor.lastrowid}, {db_setup.RISK_PROFILES[risk]}).")
    except Exception as e:
        print(f" [!] Error adding investor: {e}")
    finally:
        conn.close()

def buy_stock():
    print("\n" + "-"*40)
    print("          BUY A STOCK")
    print("-"*40)
    try:
        investor_id = int(input("Enter Investor ID: "))
        stock_id = int(input("Enter Stock ID to buy: "))
        quantity = int(input("Enter Quantity (number of shares): "))
        if quantity <= 0:
            print(" [!] Quantity must be at least 1.")
            return

        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM investors WHERE investor_id = ?;", (investor_id,))
        i_row = cursor.fetchone()
        if not i_row:
            print(" [!] Error: Investor ID not found.")
            conn.close()
            return

        cursor.execute("SELECT symbol FROM stocks WHERE stock_id = ?;", (stock_id,))
        s_row = cursor.fetchone()
        if not s_row:
            print(" [!] Error: Stock ID not found.")
            conn.close()
            return

        price, _ = _latest_price(cursor, stock_id)
        stop_loss = round(price * (1 - db_setup.STOP_LOSS_PCT), 2)
        buy_str = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO trades (stock_id, investor_id, buy_date, buy_price, quantity, stop_loss, sell_date, sell_price)
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL);
        """, (stock_id, investor_id, buy_str, price, quantity, stop_loss))
        conn.commit()
        trade_id = cursor.lastrowid
        conn.close()

        print(f"\n [✓] Trade #{trade_id}: {i_row[0]} bought {quantity} x {s_row[0]} @ Rs {price:,.2f}.")
        print(f"     Investment: Rs {price * quantity:,.2f} | Auto stop-loss: Rs {stop_loss:,.2f} "
              f"({db_setup.STOP_LOSS_PCT * 100:.0f}% below buy price)")
    except Exception as e:
        print(f" [!] Error buying stock: {e}")

def sell_stock():
    print("\n" + "-"*40)
    print("      SELL STOCK & CALCULATE PROFIT/LOSS")
    print("-"*40)
    try:
        trade_id = int(input("Enter Trade ID to sell: "))
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.stock_id, s.symbol, t.buy_date, t.buy_price, t.quantity, t.sell_date, i.name
            FROM trades t
            JOIN stocks s ON t.stock_id = s.stock_id
            JOIN investors i ON t.investor_id = i.investor_id
            WHERE t.trade_id = ?;
        """, (trade_id,))
        row = cursor.fetchone()

        if not row:
            print(" [!] Error: Trade ID not found.")
            conn.close()
            return

        stock_id, symbol, buy_str, buy_price, qty, sell_date, investor = row
        if sell_date is not None:
            print(f" [i] Notice: This position was already sold on {sell_date}.")
            conn.close()
            return

        sell_price, _ = _latest_price(cursor, stock_id)
        sell_str = datetime.now().strftime("%Y-%m-%d")
        held_days = max(1, (datetime.now().date() - datetime.strptime(buy_str, "%Y-%m-%d").date()).days)
        pnl = (sell_price - buy_price) * qty
        ret = (sell_price / buy_price - 1) * 100

        cursor.execute("""
            UPDATE trades
            SET sell_date = ?, sell_price = ?
            WHERE trade_id = ?;
        """, (sell_str, sell_price, trade_id))
        conn.commit()
        conn.close()

        print(f"\n [✓] Sold {qty} x {symbol} @ Rs {sell_price:,.2f} for {investor} (bought @ Rs {buy_price:,.2f}, held {held_days} days).")
        if pnl > 0:
            print(f" [✓] PROFIT BOOKED: Rs {pnl:,.2f}  ({ret:+.2f}%)")
        elif pnl == 0:
            print(" [i] BREAK-EVEN: sold at the buy price, no profit and no loss.")
        else:
            print(f" [!] LOSS BOOKED: Rs {pnl:,.2f}  ({ret:+.2f}%)")
    except Exception as e:
        print(f" [!] Error selling stock: {e}")

def view_stop_loss_alerts():
    print("\n" + "="*96)
    print("                 STOP-LOSS ALERTS (open positions trading below their stop-loss)")
    print("="*96)
    df = preprocessing.get_cleaned_trades()
    alerts = df[df['stop_loss_hit']].sort_values('return_pct')

    if alerts.empty:
        print(" No stop-loss alerts at present. All open positions are above their stop-loss.")
        return

    print(f"{'Trade':<6} | {'Investor':<20} | {'Stock':<11} | {'Buy (Rs)':>9} | {'Stop (Rs)':>9} | {'Now (Rs)':>9} | {'Return':>7} | {'Loss (Rs)':>10}")
    print("-"*96)
    for _, r in alerts.iterrows():
        print(f"{r['trade_id']:<6} | {r['investor_name'][:20]:<20} | {r['symbol']:<11} | {r['buy_price']:>9,.2f} | "
              f"{r['stop_loss']:>9,.2f} | {r['current_price']:>9,.2f} | {r['return_pct']:>+6.1f}% | {r['pnl']:>10,.0f}")
    print("="*96)
    print(f" {len(alerts)} position(s) hit stop-loss | combined unrealised loss: Rs {alerts['pnl'].sum():,.0f}")
    print(" Tip: use Option 8 with the Trade ID to sell and limit the loss.\n")

def investor_portfolio():
    try:
        i_id = int(input("\nEnter Investor ID: "))
        df = preprocessing.get_cleaned_trades()
        trades = df[df['investor_id'] == i_id].sort_values('buy_date')

        if trades.empty:
            print(" [!] No trade history found for this investor.")
            return

        print(f"\nPortfolio & Trade History: Investor {i_id} - {trades['investor_name'].iloc[0]} ({trades['risk_label'].iloc[0]}):")
        print("="*100)
        print(f"{'Trade':<6} | {'Stock':<11} | {'Qty':>5} | {'Buy Date':<10} | {'Buy (Rs)':>9} | {'Sell Date':<10} | {'Exit (Rs)':>9} | {'Return':>7} | {'P&L (Rs)':>10}")
        print("-"*100)
        for _, r in trades.iterrows():
            print(f"{r['trade_id']:<6} | {r['symbol']:<11} | {r['quantity']:>5} | {r['buy_date']:<10} | {r['buy_price']:>9,.2f} | "
                  f"{r['sell_date_display']:<10} | {r['exit_price']:>9,.2f} | {r['return_pct']:>+6.1f}% | {r['pnl']:>10,.0f}")
        print("="*100)
        open_t = trades[trades['simple_status'] == 'Open']
        closed = trades[trades['simple_status'] != 'Open']
        print(f"  Open positions: {len(open_t)} | invested Rs {open_t['invested'].sum():,.0f} | unrealised P&L Rs {open_t['pnl'].sum():+,.0f}")
        win = (closed['pnl'] > 0).mean() * 100 if len(closed) else 0
        print(f"  Closed trades : {len(closed)} | realised P&L Rs {closed['pnl'].sum():+,.0f} | win rate {win:.0f}%\n")
    except Exception as e:
        print(f" [!] Error fetching portfolio: {e}")

def export_for_power_bi():
    """Exports database tables into stock_market_export.xlsx for Power BI modeling."""
    print("\n" + "-"*40)
    print("      EXPORTING DATA FOR POWER BI")
    print("-"*40)
    try:
        conn = get_conn()
        excel_path = "stock_market_export.xlsx"
        tables = ["sectors", "stocks", "investors", "price_history", "trades", "shipments"]
        frames = {t: pd.read_sql_query(f"SELECT * FROM {t};", conn) for t in tables}
        conn.close()

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for name, frame in frames.items():
                frame.to_excel(writer, sheet_name=name, index=False)

        print(f" [✓] SUCCESS: Dataset exported to '{excel_path}' with {len(tables)} tables:")
        print("     - " + ", ".join(tables))
        print(" [i] Open POWERBI_GUIDE.md for step-by-step instructions on building the Power BI dashboard.")
    except Exception as e:
        print(f" [!] Error exporting to Excel: {e}")

# ==============================================================================
# POWER BI STYLE KPI CARDS (Cards, KPI vs target, Gauge, Slicers, Drill-down) IN THE TERMINAL
# ==============================================================================

def _text_gauge(pct, width=30):
    filled = int(round(max(0, min(100, pct)) / 100 * width))
    return "[" + "#" * filled + "-" * (width - filled) + f"] {pct:.1f}%"

def kpi_dashboard():
    sectors = db_setup.SECTORS

    # Slicers
    print("\nSlicer 1 - Sector:  0. All")
    for i, s in enumerate(sectors, 1):
        print(f"                    {i}. {s}")
    s_choice = input("Select sector (0 = All): ").strip()
    sector = sectors[int(s_choice) - 1] if s_choice.isdigit() and 1 <= int(s_choice) <= len(sectors) else None
    r_choice = input("Slicer 2 - Investor Risk Profile (1 Conservative ... 4 Aggressive, 0 = All): ").strip()
    risk = int(r_choice) if r_choice in ('1', '2', '3', '4') else None

    k = preprocessing.get_market_kpis(sector, risk)
    change = k['trades_this_month'] - k['trades_last_month']
    arrow = "▲" if change > 0 else ("▼" if change < 0 else "■")

    print("\n" + "=" * 74)
    print(f"  MARKET KPI DASHBOARD | Sector: {sector or 'All'} | Risk: {db_setup.RISK_PROFILES.get(risk, 'All')}")
    print("=" * 74)
    print("  CARDS")
    print(f"    Stocks: {k['stocks']:<5} Investors: {k['investors']:<5} Trades: {k['total_trades']:<5} Open Positions: {k['open_positions']}")
    print(f"    Invested (open): Rs {k['open_invested']:,.0f}   Current value: Rs {k['open_value']:,.0f}")
    print(f"    Unrealised P&L: Rs {k['unrealised_pnl']:+,.0f}   Realised P&L: Rs {k['realised_pnl']:+,.0f}")
    print("  KPI (vs target)")
    print(f"    Trades this month: {k['trades_this_month']}  vs last month: {k['trades_last_month']}  {arrow} {change:+d}")
    print(f"    Win rate: {k['win_rate_pct']:.1f}%  (target >= 55%: {'OK' if k['win_rate_pct'] >= 55 else 'BELOW TARGET'})")
    print(f"    Stop-loss alerts: {k['stop_loss_hits']}")
    print("  GAUGE - Market breadth (stocks trading above their 50-day average)")
    print(f"    {_text_gauge(k['breadth_pct'])}")
    print("=" * 74)

    # Drill-down: sector -> stocks
    stocks = preprocessing.get_stock_summary()
    if sector is None:
        print("\n  DRILL-DOWN LEVEL 1: Average 1-Year Return by Sector")
        for name, v in stocks.groupby('sector_name')['return_1y'].mean().sort_values(ascending=False).items():
            bar = ('█' if v >= 0 else '░') * int(abs(v) // 2)
            print(f"    {name:<10} {v:>+7.1f}%  {bar}")
        pick = input("\n  Type a sector name to drill down (Enter to skip): ").strip()
        sector = next((s for s in sectors if s.lower() == pick.lower()), None)
    if sector:
        print(f"\n  DRILL-DOWN LEVEL 2: Stocks in {sector} (1-Year Return)")
        for _, r in stocks[stocks['sector_name'] == sector].sort_values('return_1y', ascending=False).iterrows():
            v = r['return_1y']
            print(f"    {r['symbol']:<11} Rs {r['last_close']:>10,.2f} {v:>+7.1f}%  {('█' if v >= 0 else '░') * int(abs(v) // 3)}")
    print()

# ==============================================================================
# SELF-STUDY CASE STUDY: SUPPLY CHAIN & LOGISTICS (Route mapping, delivery KPIs, region filter)
# Export shipments of listed manufacturers -> does good logistics show up in the share price?
# ==============================================================================

def supply_chain_case_study():
    regions = ['North', 'West', 'South', 'East']
    print("\nFilter by Region:  0. All Regions")
    for i, r in enumerate(regions, 1):
        print(f"                   {i}. {r}")
    choice = input("Select region (0-4): ").strip()
    region = regions[int(choice) - 1] if choice in ('1', '2', '3', '4') else None

    ship = preprocessing.get_cleaned_shipments(region)
    if ship.empty:
        print(" [!] No shipments found for this region.")
        return
    delivered = ship[ship['status'].str.startswith('Delivered')]
    on_time = (delivered['status'] == 'Delivered On-Time').mean() * 100 if len(delivered) else 0.0

    print("\n" + "=" * 80)
    print(f"  SUPPLY CHAIN & LOGISTICS - EXPORT SHIPMENTS TO JNPT PORT | Region: {region or 'All'}")
    print("=" * 80)
    print(f"  Shipments: {len(ship)} | Containers: {ship['quantity'].sum()} | Freight: Rs {ship['freight_cost'].sum():,.0f}")
    print(f"  On-time delivery: {_text_gauge(on_time)} (target 90%)")
    print(f"  Avg transit days (delivered): {delivered['transit_days'].mean():.1f}")

    print("\n  DELIVERY STATUS KPIs")
    for status, n in ship['status'].value_counts().items():
        print(f"    {status:<20} {n:>4}  ({n / len(ship) * 100:.1f}%)")

    print("\n  ROUTES (factory hub -> JNPT port, Navi Mumbai)")
    print(f"    {'Origin':<12} {'Region':<7} {'Km':>6} {'Shipments':>10} {'Avg Days':>9} {'Late/Delayed':>13}")
    routes = ship.groupby(['origin_city', 'region']).agg(
        km=('distance_km', 'first'), n=('shipment_id', 'count'), days=('transit_days', 'mean'),
        late=('status', lambda s: s.isin(['Delivered Late', 'Delayed In Transit']).sum())
    ).reset_index().sort_values('n', ascending=False)
    for _, r in routes.iterrows():
        print(f"    {r['origin_city']:<12} {r['region']:<7} {r['km']:>6.0f} {r['n']:>10} {r['days']:>9.1f} {r['late']:>13}")

    print("\n  COMPANY SCORECARD (logistics vs share price)")
    print(f"    {'Stock':<11} {'Sector':<7} {'Shipments':>10} {'On-time %':>10} {'Avg Delay':>10} {'1Y Return':>10}")
    score = preprocessing.get_company_logistics_scorecard(region)
    for _, r in score.iterrows():
        print(f"    {r['symbol']:<11} {r['sector_name']:<7} {r['shipments']:>10} {r['on_time_pct']:>9.0f}% {r['avg_delay']:>9.1f}d {r['return_1y']:>+9.1f}%")
    if len(score) > 2:
        corr = score['on_time_pct'].corr(score['return_1y'])
        print(f"\n  Correlation (on-time % vs 1Y return): r = {corr:.2f}  -> "
              f"{'companies that deliver on time have done better on the stock market' if corr > 0.2 else 'no clear link in this region'}")
    print("=" * 80)

    visualizations.plot_supply_chain_dashboard(region)

# ==============================================================================
# DATA VISUALIZATION MENU (SYLLABUS UNIT-WISE)
# ==============================================================================

def print_chart_list():
    current_unit = None
    for i, (unit, title, _) in enumerate(visualizations.CHART_MENU, 1):
        if unit != current_unit:
            print(f"  --- {unit} ---")
            current_unit = unit
        print(f"  {i:>2}. {title}")

def run_chart(number):
    if 1 <= number <= len(visualizations.CHART_MENU):
        visualizations.CHART_MENU[number - 1][2]()
        return True
    print(f" [!] Invalid chart number. Use 1 to {len(visualizations.CHART_MENU)}.")
    return False

def visualization_menu():
    while True:
        print("\n" + "=" * 72)
        print("        DATA VISUALIZATION MENU (arranged by syllabus unit)")
        print("=" * 72)
        print_chart_list()
        print("   A. Generate ALL charts (saved to charts/, no windows)")
        print("   0. Back to Main Menu")
        print("=" * 72)

        choice = input(f"Select chart (1-{len(visualizations.CHART_MENU)}, A, 0): ").strip()
        if choice == '0':
            break
        elif choice.lower() == 'a':
            visualizations.generate_all_visualizations()
        elif choice.isdigit():
            run_chart(int(choice))
        else:
            print(" [!] Invalid option.")

# ==============================================================================
# MAIN APPLICATION MENU
# ==============================================================================

def main_menu():
    check_db()

    while True:
        print("\n" + "="*66)
        print("          STOCK MARKET ANALYSIS SYSTEM (NSE, INDIA)")
        print("           DATA VISUALIZATION & ANALYTICS PLATFORM")
        print("="*66)
        print("  1. View Market Watchlist (all stocks, price, 1D / 1Y change)")
        print("  2. Add New Stock")
        print("  3. Remove / Delist Stock")
        print("  4. Search & Analyse a Stock (signal + candlestick chart)")
        print("  5. View Investor Directory")
        print("  6. Add New Investor")
        print("  7. Buy a Stock (Auto 8% stop-loss)")
        print("  8. Sell a Stock (Auto profit / loss calculation)")
        print("  9. View Stop-Loss Alerts")
        print(" 10. Investor Portfolio & Trade History")
        print(" 11. Data Cleaning & Aggregation Report")
        print(" 12. Data Visualization Menu (Unit 1 - Unit 5)")
        print(" 13. Generate All Charts (One-Click)")
        print(" 14. KPI Dashboard (Cards, KPI, Gauge, Slicers, Drill-down)")
        print(" 15. Supply Chain & Logistics Case Study (Region filter)")
        print(" 16. Export Dataset for Power BI (stock_market_export.xlsx)")
        print("  0. Exit")
        print("="*66)

        choice = input("Enter choice (0-16): ").strip()

        actions = {
            '1': view_stocks, '2': add_stock, '3': remove_stock, '4': search_and_analyse,
            '5': view_investors, '6': add_investor, '7': buy_stock, '8': sell_stock,
            '9': view_stop_loss_alerts, '10': investor_portfolio,
            '11': preprocessing.print_cleaning_report, '12': visualization_menu,
            '13': visualizations.generate_all_visualizations, '14': kpi_dashboard,
            '15': supply_chain_case_study, '16': export_for_power_bi,
        }
        if choice == '0':
            print("\n [✓] Thank you for using the Stock Market Analysis System. Goodbye!\n")
            sys.exit(0)
        elif choice in actions:
            actions[choice]()
        else:
            print(" [!] Invalid selection. Please enter a valid menu number (0-16).")

def parse_args():
    parser = argparse.ArgumentParser(description="Stock Market Analysis System - Data Visualization project (terminal).")
    parser.add_argument('--all', action='store_true', help="generate every chart into charts/ and exit")
    parser.add_argument('--list', action='store_true', help="list all chart numbers and exit")
    parser.add_argument('--chart', type=int, metavar='N', help="open/save chart number N and exit")
    parser.add_argument('--report', action='store_true', help="print the data cleaning & aggregation report and exit")
    parser.add_argument('--export', action='store_true', help="export stock_market_export.xlsx for Power BI and exit")
    parser.add_argument('--reset-db', action='store_true', help="delete and re-create stock_market.db with fresh sample data")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.reset_db and os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    check_db()
    if args.list:
        print_chart_list()
    elif args.chart:
        run_chart(args.chart)
    elif args.all:
        visualizations.generate_all_visualizations()
    elif args.report:
        preprocessing.print_cleaning_report()
    elif args.export:
        export_for_power_bi()
    elif not args.reset_db:
        main_menu()

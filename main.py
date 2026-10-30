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
            INSERT INTO stocks (symbol, company_name, sector_id, hq_state)
            VALUES (?, ?, ?, ?);
        """, (symbol, company, sector_id, hq_state))

        db_setup.simulate_new_stock_history(conn, cursor.lastrowid, sector_name, price)
        conn.commit()
        print(f"\n [OK] Success: Added {symbol} - {company} ({sector_name}) at Rs {price:,.2f}.")
        print(f"     {db_setup.TRADING_DAYS} days of simulated price history created so it appears in every chart.")
    except sqlite3.IntegrityError:
        print(f" [!] Symbol '{symbol}' already exists in the watchlist.")
    except Exception as e:
        print(f" [!] Error adding stock: {e}")
    finally:
        conn.close()

def remove_stock():
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
                cursor.execute("DELETE FROM deliveries WHERE trade_id IN (SELECT trade_id FROM trades WHERE stock_id = ?);", (stock_id,))
                for table in ["trades", "price_history"]:
                    cursor.execute(f"DELETE FROM {table} WHERE stock_id = ?;", (stock_id,))
                cursor.execute("DELETE FROM stocks WHERE stock_id = ?;", (stock_id,))
                conn.commit()
                print(f"\n [OK] Successfully removed {symbol} from the watchlist.")
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

    print("\n" + "="*102)
    print("                                      INVESTOR DIRECTORY")
    print("="*102)
    print(f"{'ID':<5} | {'Investor Name':<25} | {'Risk Profile':<13} | {'Home State':<14} | {'Broker':<12} | {'Trades':>6} | {'Total P&L (Rs)':>14}")
    print("-"*102)
    for _, r in summary.iterrows():
        print(f"{r['investor_id']:<5} | {r['name'][:25]:<25} | {r['risk_label']:<13} | {r['home_state']:<14} | {r['broker']:<12} | "
              f"{int(r['total_trades']):>6} | {r['total_pnl']:>+14,.0f}")
    print("="*102 + "\n")

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
        print("\nBroker (where the investor has a demat/trading account):")
        for i, b in enumerate(db_setup.BROKERS, 1):
            print(f"  {i}. {b}")
        b_choice = input("Select Broker (1-5, Enter = Zerodha): ").strip()
        broker = db_setup.BROKERS[int(b_choice) - 1] if b_choice in ('1', '2', '3', '4', '5') else "Zerodha"

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investors (name, risk_profile, home_state, broker)
            VALUES (?, ?, ?, ?);
        """, (name, risk, home_state, broker))
        conn.commit()
        print(f"\n [OK] Successfully registered investor '{name}' (ID {cursor.lastrowid}, {db_setup.RISK_PROFILES[risk]}, broker {broker}).")
    except Exception as e:
        print(f" [!] Error adding investor: {e}")
    finally:
        conn.close()

def place_buy(investor_id, stock_id, quantity):
    if quantity <= 0:
        raise ValueError("Quantity must be at least 1.")
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, home_state, broker FROM investors WHERE investor_id = ?;", (investor_id,))
        i_row = cursor.fetchone()
        if not i_row:
            raise ValueError("Investor ID not found.")
        cursor.execute("SELECT symbol FROM stocks WHERE stock_id = ?;", (stock_id,))
        s_row = cursor.fetchone()
        if not s_row:
            raise ValueError("Stock ID not found.")

        price, _ = _latest_price(cursor, stock_id)
        # stop-loss is 8% below the buy price
        stop_loss = round(price * (1 - db_setup.STOP_LOSS_PCT), 2)
        buy_str = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO trades (stock_id, investor_id, buy_date, buy_price, quantity, stop_loss, sell_date, sell_price)
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL);
        """, (stock_id, investor_id, buy_str, price, quantity, stop_loss))
        trade_id = cursor.lastrowid

        # shares should reach the demat account on T+1
        due = db_setup.create_delivery(conn, trade_id, i_row[2], i_row[1], buy_str)
        conn.commit()
    finally:
        conn.close()
    return {'trade_id': trade_id, 'investor': i_row[0], 'broker': i_row[2], 'symbol': s_row[0], 'quantity': quantity,
            'price': price, 'invested': price * quantity, 'stop_loss': stop_loss, 'due': due}

def buy_stock():
    print("\n" + "-"*40)
    print("          BUY A STOCK")
    print("-"*40)
    try:
        investor_id = int(input("Enter Investor ID: "))
        stock_id = int(input("Enter Stock ID to buy: "))
        quantity = int(input("Enter Quantity (number of shares): "))
        r = place_buy(investor_id, stock_id, quantity)
        print(f"\n [OK] Trade #{r['trade_id']}: {r['investor']} bought {quantity} x {r['symbol']} @ Rs {r['price']:,.2f}.")
        print(f"     Investment: Rs {r['invested']:,.2f} | Auto stop-loss: Rs {r['stop_loss']:,.2f} "
              f"({db_setup.STOP_LOSS_PCT * 100:.0f}% below buy price)")
        print(f"     Delivery: shares reach the demat account via {r['broker']} on {r['due']} (T+1) - track it in Option 15.")
    except ValueError as e:
        print(f" [!] Error: {e}")
    except Exception as e:
        print(f" [!] Error buying stock: {e}")

def place_sell(trade_id):
    conn = get_conn()
    try:
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
            raise ValueError("Trade ID not found.")
        stock_id, symbol, buy_str, buy_price, qty, sell_date, investor = row
        if sell_date is not None:
            raise ValueError(f"This position was already sold on {sell_date}.")

        sell_price, _ = _latest_price(cursor, stock_id)
        sell_str = datetime.now().strftime("%Y-%m-%d")
        held_days = max(1, (datetime.now().date() - datetime.strptime(buy_str, "%Y-%m-%d").date()).days)
        cursor.execute("""
            UPDATE trades
            SET sell_date = ?, sell_price = ?
            WHERE trade_id = ?;
        """, (sell_str, sell_price, trade_id))
        conn.commit()
    finally:
        conn.close()
    return {'trade_id': trade_id, 'symbol': symbol, 'investor': investor, 'quantity': qty, 'buy_price': buy_price,
            'sell_price': sell_price, 'held_days': held_days, 'pnl': (sell_price - buy_price) * qty,
            'return_pct': (sell_price / buy_price - 1) * 100}

def sell_stock():
    print("\n" + "-"*40)
    print("      SELL STOCK & CALCULATE PROFIT/LOSS")
    print("-"*40)
    try:
        trade_id = int(input("Enter Trade ID to sell: "))
        r = place_sell(trade_id)
        print(f"\n [OK] Sold {r['quantity']} x {r['symbol']} @ Rs {r['sell_price']:,.2f} for {r['investor']} "
              f"(bought @ Rs {r['buy_price']:,.2f}, held {r['held_days']} days).")
        if r['pnl'] > 0:
            print(f" [OK] PROFIT BOOKED: Rs {r['pnl']:,.2f}  ({r['return_pct']:+.2f}%)")
        elif r['pnl'] == 0:
            print(" [i] BREAK-EVEN: sold at the buy price, no profit and no loss.")
        else:
            print(f" [!] LOSS BOOKED: Rs {r['pnl']:,.2f}  ({r['return_pct']:+.2f}%)")
    except ValueError as e:
        print(f" [i] Notice: {e}")
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
    print("\n" + "-"*40)
    print("      EXPORTING DATA FOR POWER BI")
    print("-"*40)
    try:
        conn = get_conn()
        excel_path = "stock_market_export.xlsx"
        tables = ["sectors", "stocks", "investors", "price_history", "trades", "deliveries"]
        frames = {t: pd.read_sql_query(f"SELECT * FROM {t};", conn) for t in tables}
        conn.close()

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for name, frame in frames.items():
                frame.to_excel(writer, sheet_name=name, index=False)

        print(f" [OK] SUCCESS: Dataset exported to '{excel_path}' with {len(tables)} tables:")
        print("     - " + ", ".join(tables))
        print(" [i] Open POWERBI_GUIDE.md for step-by-step instructions on building the Power BI dashboard.")
    except Exception as e:
        print(f" [!] Error exporting to Excel: {e}")


def _text_gauge(pct, width=30):
    filled = int(round(max(0, min(100, pct)) / 100 * width))
    return "[" + "#" * filled + "-" * (width - filled) + f"] {pct:.1f}%"

def _meaning(text):
    print(f"      -> {text}")

# ---------- Market Dashboard (option 14) ----------
def kpi_dashboard():
    sectors = db_setup.SECTORS
    inr = preprocessing.format_inr

    print("\n" + "=" * 78)
    print("  MARKET DASHBOARD  (Power BI concepts shown in the terminal)")
    print("=" * 78)
    print("  One screen that answers two questions:")
    print("    1. How is the stock MARKET doing today?")
    print("    2. How are our INVESTORS doing - are they making money?")
    print("  First pick the filters. In Power BI these are called SLICERS.")


    print("\n  [SLICER 1] Which sector?      0. All")
    for i, s in enumerate(sectors, 1):
        print(f"                                {i}. {s}")
    s_choice = input("  Select sector (0 = All): ").strip()
    sector = sectors[int(s_choice) - 1] if s_choice.isdigit() and 1 <= int(s_choice) <= len(sectors) else None
    print("\n  [SLICER 2] Which type of investor?  0. All")
    for k_, v in db_setup.RISK_PROFILES.items():
        print(f"                                      {k_}. {v}")
    r_choice = input("  Select investor type (0 = All): ").strip()
    risk = int(r_choice) if r_choice in ('1', '2', '3', '4') else None

    k = preprocessing.get_market_kpis(sector, risk)
    mood, mood_text = preprocessing.market_mood(k['breadth_pct'])
    gainers, losers = preprocessing.get_top_movers(5, sector)
    rising = int(round(k['breadth_pct'] / 100 * k['stocks']))

    print("\n" + "=" * 78)
    print(f"  FILTERS APPLIED -> Sector: {sector or 'All'} | Investor type: {db_setup.RISK_PROFILES.get(risk, 'All')}")
    print("=" * 78)

    print(f"\n  MARKET MOOD: {mood}")
    print(f"  [GAUGE] Stocks in an uptrend {_text_gauge(k['breadth_pct'])}")
    _meaning(f"{rising} of {k['stocks']} stocks trade above their 50-day average price, so {mood_text}.")

    print("\n  [CARDS] Headline numbers")
    print(f"    Stocks tracked          : {k['stocks']}")
    print(f"    Investors / buy orders  : {k['investors']} investors placed {k['total_trades']} orders")
    print(f"    Shares still held       : {k['open_positions']} positions, bought for {inr(k['open_invested'])}, worth {inr(k['open_value'])} today")
    print(f"    Unrealised P&L          : {inr(k['unrealised_pnl'], sign=True)}")
    _meaning("'paper' profit on shares not sold yet - it can still change tomorrow.")
    print(f"    Realised P&L            : {inr(k['realised_pnl'], sign=True)}")
    _meaning("profit/loss already locked in by selling.")

    print("\n  [KPI] Actual vs target")
    change = k['trades_this_month'] - k['trades_last_month']
    arrow = "▲" if change > 0 else ("▼" if change < 0 else "■")
    print(f"    Orders this month: {k['trades_this_month']}  vs last month: {k['trades_last_month']}   {arrow} {change:+d}")
    _meaning("investors are trading " + ("more" if change > 0 else "less" if change < 0 else "the same") + " than last month.")
    status = "ON TARGET" if k['win_rate_pct'] >= 55 else "BELOW TARGET"
    print(f"    Win rate: {k['win_rate_pct']:.1f}%  (target 55%)  {status}")
    _meaning(f"out of every 100 shares sold, about {k['win_rate_pct']:.0f} were sold at a profit.")
    print(f"    Stop-loss alerts: {k['stop_loss_hits']}")
    _meaning("positions that have fallen more than 8% - see Option 9.")

    print("\n  TOP 5 GAINERS TODAY                 TOP 5 LOSERS TODAY")
    for (_, g), (_, l) in zip(gainers.iterrows(), losers.iterrows()):
        print(f"    {g['symbol']:<11} {g['change_1d']:>+6.2f}%              {l['symbol']:<11} {l['change_1d']:>+6.2f}%")


    stocks = preprocessing.get_stock_summary()
    if sector is None:
        print("\n  [DRILL-DOWN] Level 1: Which sector gave the best 1-year return?")
        for name, v in stocks.groupby('sector_name')['return_1y'].mean().sort_values(ascending=False).items():
            bar = ('█' if v >= 0 else '░') * int(abs(v) // 2)
            print(f"    {name:<10} {v:>+7.1f}%  {bar}")
        pick = input("\n  Type a sector name to drill down into its stocks (Enter to skip): ").strip()
        sector_dd = next((s for s in sectors if s.lower() == pick.lower()), None)
    else:
        sector_dd = sector
    if sector_dd:
        print(f"\n  [DRILL-DOWN] Level 2: Stocks inside {sector_dd} (1-year return)")
        for _, r in stocks[stocks['sector_name'] == sector_dd].sort_values('return_1y', ascending=False).iterrows():
            v = r['return_1y']
            print(f"    {r['symbol']:<11} Rs {r['last_close']:>10,.2f} {v:>+7.1f}%  {('█' if v >= 0 else '░') * int(abs(v) // 3)}")
    print()
    visualizations.plot_market_dashboard(sector, risk)


# ---------- Case study: share delivery tracker (option 15) ----------
def supply_chain_case_study():
    regions = ['North', 'West', 'South', 'East']
    region_cities = {}
    for city, region, _, _ in db_setup.INVESTOR_CITIES.values():
        region_cities.setdefault(region, []).append(city)

    print("\n" + "=" * 80)
    print("  CASE STUDY: SUPPLY CHAIN OF THE STOCK MARKET - SHARE DELIVERY TRACKER")
    print("=" * 80)
    print("  When an investor BUYS a share, the share has to be DELIVERED to them,")
    print("  just like a parcel. It travels through this chain:")
    print()
    print("    Investor -> Broker -> NSE Mumbai -> Clearing Corp -> Depository -> Demat account")
    print("    (places     (Zerodha,  (matches      (settles money    (CDSL/NSDL   (shares")
    print("     order)      Groww..)   buyer+seller)  and shares)       moves them)  arrive)")
    print()
    print("  Rule in India: shares must reach the demat account on T+1")
    print("  (T = order day, T+1 = next trading day). Later than that = LATE delivery.")
    print("  Parcel words -> stock words:  shipment = buy order | courier = broker |")
    print("                                warehouse = NSE Mumbai | delivered = shares in demat")

    print("\n  REGION = where the investor lives (filter = Power BI slicer):")
    print("    0. All regions")
    for i, r in enumerate(regions, 1):
        print(f"    {i}. {r:<6} - {', '.join(region_cities.get(r, []))}")
    choice = input("  Select region (0-4): ").strip()
    region = regions[int(choice) - 1] if choice in ('1', '2', '3', '4') else None

    deliv = preprocessing.get_cleaned_deliveries(region)
    if deliv.empty:
        print(" [!] No orders found for this region.")
        return
    done = deliv[deliv['status'].str.startswith('Delivered')]
    on_time = (done['status'] == 'Delivered On-Time (T+1)').mean() * 100 if len(done) else 0.0
    late = (deliv['status'] == 'Delivered Late').sum()
    pending = deliv['status'].str.startswith('Pending').sum()

    print("\n" + "=" * 80)
    print(f"  STEP 1  DELIVERY KPIs  | Region: {region or 'All'}")
    print("=" * 80)
    print(f"    Buy orders (shipments)   : {len(deliv)}  worth {preprocessing.format_inr(deliv['order_value'].sum())}")
    print(f"    Shares delivered         : {int(done['quantity'].sum()):,}")
    print(f"    Delivered on T+1         : {_text_gauge(on_time)}  (target 95%)")
    print(f"    Late / still pending     : {late} late, {pending} pending")
    print(f"    Average time to demat    : T+{done['settle_days'].mean():.2f} trading days")
    _meaning(f"about {round(on_time)} of every 100 investors got their shares on time; "
             + ("this meets the 95% target." if on_time >= 95 else "this is below the 95% target."))

    print(f"\n  STEP 2  ROUTES (investor city -> NSE Mumbai)  = route mapping")
    print(f"    {'From city':<11} {'Region':<7} {'Km to NSE':>9} {'Orders':>7} {'On time':>8} {'Late':>5}")
    routes = deliv.groupby(['from_city', 'region']).agg(
        km=('distance_km', 'first'), n=('delivery_id', 'count'),
        on_time=('status', lambda s: (s == 'Delivered On-Time (T+1)').sum() / max(1, s.str.startswith('Delivered').sum()) * 100),
        late=('status', lambda s: (s == 'Delivered Late').sum())
    ).reset_index().sort_values('n', ascending=False)
    for _, r in routes.iterrows():
        print(f"    {r['from_city']:<11} {r['region']:<7} {r['km']:>9.0f} {r['n']:>7} {r['on_time']:>7.0f}% {r['late']:>5}")
    worst = routes.sort_values('on_time').iloc[0]
    _meaning(f"distance does not slow a digital share; {worst['from_city']} has the lowest on-time rate "
             f"({worst['on_time']:.0f}%) because of its brokers and paperwork, not the km.")

    print("\n  STEP 3  BROKER REPORT CARD  (the 'courier companies' of the stock market)")
    print(f"    {'Broker':<13} {'Orders':>7} {'On time':>8} {'Late':>5} {'Avg days':>9}  Grade")
    score = preprocessing.get_broker_scorecard(region)
    for _, r in score.iterrows():
        print(f"    {r['broker']:<13} {r['orders']:>7} {r['on_time_pct']:>7.0f}% {r['late']:>5} {'T+' + format(r['avg_settle_days'], '.2f'):>9}  {r['grade']}")
    print("    Grade A = 95%+ on time | B = 88-95% | C = below 88% (often late)")
    if len(score):
        best, worst_b = score.iloc[0], score.iloc[-1]
        _meaning(f"{best['broker']} is the most reliable; {worst_b['broker']} delivers late most often.")

    print("\n  STEP 4  WHY WERE DELIVERIES LATE?")
    reasons = deliv[deliv['delay_reason'] != '-']['delay_reason'].value_counts()
    if reasons.empty:
        print("    No late deliveries in this region.")
    for reason, n in reasons.items():
        print(f"    {reason:<36} {n:>3}  {'█' * n}")

    print("\n  INVESTOR TAKEAWAY")
    print(f"    - {on_time:.0f}% of shares reached the demat account on time (T+1).")
    if len(score):
        print(f"    - Choose a Grade A broker ({', '.join(score[score['grade'] == 'A']['broker']) or 'none in this region'}) for the fastest delivery.")
    if not reasons.empty:
        print(f"    - Most common delay: '{reasons.index[0]}' - pay funds on time and keep KYC/demat details correct.")
    print("=" * 80)

    visualizations.plot_supply_chain_dashboard(region)


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

def safe_input(prompt):
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        print("\n [i] Ctrl+C pressed - cancelled. The program keeps running (type 0 in the main menu to exit).")
        return None
    except EOFError:
        print("\n [i] Input stream closed - exiting.")
        sys.exit(0)

def run_safely(action):
    try:
        action()
    except KeyboardInterrupt:
        print("\n [i] Cancelled - back to the menu.")
    except EOFError:
        print("\n [i] Input stream closed - exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"\n [!] Something went wrong: {e}")
        print("     No problem - the menu is still running. Try again or pick another option.")

def visualization_menu():
    while True:
        print("\n" + "=" * 72)
        print("        DATA VISUALIZATION MENU (arranged by syllabus unit)")
        print("=" * 72)
        print_chart_list()
        print("   A. Generate ALL charts (saved to charts/, no windows)")
        print("   0. Back to Main Menu")
        print("=" * 72)

        choice = safe_input(f"Select chart (1-{len(visualizations.CHART_MENU)}, A, 0): ")
        if choice is None:
            continue
        if choice == '0':
            break
        elif choice.lower() == 'a':
            run_safely(visualizations.generate_all_visualizations)
        elif choice.isdigit():
            run_safely(lambda: run_chart(int(choice)))
        else:
            print(" [!] Invalid option.")


# ---------- Main menu ----------
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
        print(" 14. Market Dashboard (KPI Cards, Gauge, Slicers, Drill-down)")
        print(" 15. Supply Chain Case Study: Share Delivery Tracker (Region filter)")
        print(" 16. Export Dataset for Power BI (stock_market_export.xlsx)")
        print(" 17. Open the Website (all pages + 26 charts in the browser)")
        print("  0. Exit")
        print("="*66)

        choice = safe_input("Enter choice (0-17): ")
        if choice is None:
            continue

        actions = {
            '1': view_stocks, '2': add_stock, '3': remove_stock, '4': search_and_analyse,
            '5': view_investors, '6': add_investor, '7': buy_stock, '8': sell_stock,
            '9': view_stop_loss_alerts, '10': investor_portfolio,
            '11': preprocessing.print_cleaning_report, '12': visualization_menu,
            '13': visualizations.generate_all_visualizations, '14': kpi_dashboard,
            '15': supply_chain_case_study, '16': export_for_power_bi, '17': open_website,
        }
        if choice == '0':
            print("\n [OK] Thank you for using the Stock Market Analysis System. Goodbye!\n")
            sys.exit(0)
        elif choice in actions:
            run_safely(actions[choice])
        else:
            print(" [!] Invalid selection. Please enter a valid menu number (0-17).")

def open_website():
    import web_app
    web_app.run()

def parse_args():
    parser = argparse.ArgumentParser(description="Stock Market Analysis System - Data Visualization project (terminal).")
    parser.add_argument('--all', action='store_true', help="generate every chart into charts/ and exit")
    parser.add_argument('--list', action='store_true', help="list all chart numbers and exit")
    parser.add_argument('--chart', type=int, metavar='N', help="open/save chart number N and exit")
    parser.add_argument('--report', action='store_true', help="print the data cleaning & aggregation report and exit")
    parser.add_argument('--export', action='store_true', help="export stock_market_export.xlsx for Power BI and exit")
    parser.add_argument('--web', action='store_true', help="start the website at http://localhost:8000 (Ctrl+C to stop)")
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
    elif args.web:
        open_website()
    elif not args.reset_db:
        main_menu()

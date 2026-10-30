import os
import sqlite3
import pandas as pd
from datetime import datetime

import db_setup

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


def export_for_power_bi():
    excel_path = "stock_market_export.xlsx"
    tables = ["sectors", "stocks", "investors", "price_history", "trades", "deliveries"]
    conn = get_conn()
    frames = {t: pd.read_sql_query(f"SELECT * FROM {t};", conn) for t in tables}
    conn.close()
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for name, frame in frames.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    print(f" [OK] Exported {len(tables)} tables to {excel_path}")


if __name__ == "__main__":
    import web_app
    web_app.run()

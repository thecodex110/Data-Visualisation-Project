import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

from db_setup import RISK_PROFILES

DB_NAME = "stock_market.db"

def get_connection(db_path=DB_NAME):
    return sqlite3.connect(db_path)

def load_raw_data(db_path=DB_NAME):
    conn = get_connection(db_path)

    sectors_df = pd.read_sql_query("SELECT * FROM sectors;", conn)
    investors_df = pd.read_sql_query("SELECT * FROM investors;", conn)
    stocks_df = pd.read_sql_query("SELECT * FROM stocks;", conn)
    trades_df = pd.read_sql_query("SELECT * FROM trades;", conn)

    conn.close()
    return sectors_df, investors_df, stocks_df, trades_df

def get_clean_prices(db_path=DB_NAME):
    conn = get_connection(db_path)
    df = pd.read_sql_query("""
        SELECT p.stock_id, s.symbol, s.company_name, sec.sector_name,
               p.trade_date, p.open, p.high, p.low, p.close, p.volume
        FROM price_history p
        JOIN stocks s ON p.stock_id = s.stock_id
        JOIN sectors sec ON s.sector_id = sec.sector_id
        ORDER BY p.stock_id, p.trade_date;
    """, conn)
    conn.close()

    df['date'] = pd.to_datetime(df['trade_date'])
    df['close_was_missing'] = df['close'].isnull()

    # missing closing price -> use last known price of the same stock
    df['close'] = df.groupby('stock_id')['close'].ffill().bfill()
    df['daily_return'] = df.groupby('stock_id')['close'].pct_change() * 100
    df['month'] = df['date'].dt.to_period('M').astype(str)
    return df

def get_latest_prices(db_path=DB_NAME):
    prices = get_clean_prices(db_path)
    return prices.groupby('stock_id')['close'].last()

def _max_drawdown(close):
    return float(((close / close.cummax()) - 1).min() * 100)

def get_market_index(db_path=DB_NAME):
    prices = get_clean_prices(db_path)
    daily = prices.groupby('date').agg(avg_return=('daily_return', 'mean'), volume=('volume', 'sum')).reset_index()
    daily['avg_return'] = daily['avg_return'].fillna(0)
    daily['index_level'] = 1000 * (1 + daily['avg_return'] / 100).cumprod()
    daily['ma_20'] = daily['index_level'].rolling(20, min_periods=1).mean()
    daily['ma_50'] = daily['index_level'].rolling(50, min_periods=1).mean()
    daily['volatility_20d'] = daily['avg_return'].rolling(20, min_periods=5).std() * np.sqrt(252)
    daily['month'] = daily['date'].dt.to_period('M').astype(str)
    return daily

def get_sector_index(db_path=DB_NAME):
    prices = get_clean_prices(db_path)
    sec = prices.groupby(['date', 'sector_name'])['daily_return'].mean().unstack().fillna(0)
    return 100 * (1 + sec / 100).cumprod()

def get_stock_summary(db_path=DB_NAME):
    prices = get_clean_prices(db_path)
    market = get_market_index(db_path).set_index('date')['avg_return']
    rows = []
    for sid, g in prices.groupby('stock_id'):
        close = g['close'].reset_index(drop=True)
        ret = g.set_index('date')['daily_return'].dropna()
        both = pd.concat([ret, market], axis=1, join='inner').dropna()
        beta = both.iloc[:, 0].cov(both.iloc[:, 1]) / both.iloc[:, 1].var() if len(both) > 5 else 1.0
        rows.append({
            'stock_id': sid, 'symbol': g['symbol'].iloc[0], 'company_name': g['company_name'].iloc[0],
            'sector_name': g['sector_name'].iloc[0],
            'last_close': close.iloc[-1],
            'change_1d': (close.iloc[-1] / close.iloc[-2] - 1) * 100 if len(close) > 1 else 0.0,
            'return_1y': (close.iloc[-1] / close.iloc[0] - 1) * 100,
            'volatility': ret.std() * np.sqrt(252),
            'max_drawdown': _max_drawdown(close),
            'avg_volume': g['volume'].mean(),
            'beta': beta,
            'high_52w': g['high'].max(), 'low_52w': g['low'].min(),
            'dma_20': close.tail(20).mean(), 'dma_50': close.tail(50).mean(),
        })
    summary = pd.DataFrame(rows)
    summary['above_50dma'] = summary['last_close'] > summary['dma_50']
    return summary

def get_cleaned_trades(db_path=DB_NAME):
    conn = get_connection(db_path)

    query = """
    SELECT
        t.trade_id,
        t.stock_id,
        s.symbol,
        s.company_name,
        sec.sector_id,
        sec.sector_name,
        t.investor_id,
        i.name AS investor_name,
        i.risk_profile,
        i.home_state AS investor_state,
        t.buy_date,
        t.buy_price,
        t.quantity,
        t.stop_loss,
        t.sell_date,
        t.sell_price
    FROM trades t
    JOIN stocks s ON t.stock_id = s.stock_id
    JOIN investors i ON t.investor_id = i.investor_id
    JOIN sectors sec ON s.sector_id = sec.sector_id;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    latest = get_latest_prices(db_path)
    today = pd.Timestamp(datetime.now().date())


    df['buy_date_dt'] = pd.to_datetime(df['buy_date'])
    df['sell_date_dt'] = pd.to_datetime(df['sell_date'])
    df['buy_month'] = df['buy_date_dt'].dt.to_period('M').astype(str)
    is_sold = df['sell_date_dt'].notnull()


    df['current_price'] = df['stock_id'].map(latest)
    df['exit_price'] = np.where(is_sold, df['sell_price'], df['current_price'])


    df['holding_days'] = np.where(
        is_sold,
        (df['sell_date_dt'] - df['buy_date_dt']).dt.days,
        (today - df['buy_date_dt']).dt.days
    )
    df['holding_days'] = df['holding_days'].clip(lower=1)


    df['invested'] = df['buy_price'] * df['quantity']
    df['pnl'] = (df['exit_price'] - df['buy_price']) * df['quantity']
    df['return_pct'] = (df['exit_price'] / df['buy_price'] - 1) * 100
    df['stop_loss_hit'] = (~is_sold) & (df['current_price'] <= df['stop_loss'])
    df['risk_label'] = df['risk_profile'].map(RISK_PROFILES)


    conditions = [
        is_sold & (df['pnl'] > 0),
        is_sold & (df['pnl'] <= 0),
        (~is_sold) & (df['pnl'] > 0),
        (~is_sold) & (df['pnl'] <= 0)
    ]
    choices = ['Profit Booked', 'Loss Booked', 'Open - In Profit', 'Open - In Loss']
    df['status'] = np.select(conditions, choices, default='Unknown')


    df['simple_status'] = np.where(df['status'].str.startswith('Open'), 'Open', df['status'])


    df['sell_date_display'] = df['sell_date'].fillna('Open')

    return df

def get_sector_aggregates(db_path=DB_NAME):
    trades = get_cleaned_trades(db_path)
    sectors = load_raw_data(db_path)[0]
    stocks = get_stock_summary(db_path)

    per_sector = stocks.groupby('sector_name').agg(
        stocks=('stock_id', 'count'),
        avg_return_1y=('return_1y', 'mean'),
        avg_volatility=('volatility', 'mean')
    ).reset_index()
    per_sector = pd.merge(sectors, per_sector, on='sector_name', how='left').fillna(0)


    counts = trades.groupby(['sector_name', 'simple_status']).size().unstack(fill_value=0).reset_index()
    for col in ['Profit Booked', 'Loss Booked', 'Open']:
        if col not in counts.columns:
            counts[col] = 0
    counts['total_trades'] = counts['Profit Booked'] + counts['Loss Booked'] + counts['Open']
    value = trades.groupby('sector_name').agg(traded_value=('invested', 'sum'), total_pnl=('pnl', 'sum')).reset_index()

    summary = per_sector.merge(counts, on='sector_name', how='left').merge(value, on='sector_name', how='left').fillna(0)
    summary['traded_value_lakh'] = summary['traded_value'] / 1e5
    return summary

def get_stock_trade_aggregates(db_path=DB_NAME):
    trades = get_cleaned_trades(db_path)
    agg = trades.groupby(['symbol', 'sector_name']).agg(
        total_trades=('trade_id', 'count'),
        traded_value=('invested', 'sum'),
        total_pnl=('pnl', 'sum')
    ).reset_index()
    agg['traded_value_lakh'] = agg['traded_value'] / 1e5
    return agg.sort_values('total_trades', ascending=False)

def get_monthly_sector_returns(db_path=DB_NAME):
    prices = get_clean_prices(db_path)
    monthly = prices.groupby(['stock_id', 'sector_name', 'month'])['close'].last().reset_index()
    monthly['monthly_return'] = monthly.groupby('stock_id')['close'].pct_change() * 100
    pivot = monthly.dropna().pivot_table(index='sector_name', columns='month', values='monthly_return', aggfunc='mean')

    return pivot[sorted(pivot.columns)]

def get_monthly_stock_returns(db_path=DB_NAME):
    prices = get_clean_prices(db_path)
    monthly = prices.groupby(['stock_id', 'symbol', 'sector_name', 'month'])['close'].last().reset_index()
    monthly['monthly_return'] = monthly.groupby('stock_id')['close'].pct_change() * 100
    return monthly.dropna()

def get_monthly_timeseries(db_path=DB_NAME):
    trades = get_cleaned_trades(db_path)
    index = get_market_index(db_path)

    monthly = trades.groupby('buy_month').agg(
        buy_count=('trade_id', 'count'),
        traded_value=('invested', 'sum')
    ).reset_index().rename(columns={'buy_month': 'month'})

    sold = trades[trades['sell_date_dt'].notnull()].copy()
    sold['month'] = sold['sell_date_dt'].dt.to_period('M').astype(str)
    sells = sold.groupby('month').agg(sell_count=('trade_id', 'count'), realised_pnl=('pnl', 'sum')).reset_index()

    idx = index.groupby('month').agg(index_close=('index_level', 'last'), volume=('volume', 'sum')).reset_index()
    monthly = idx.merge(monthly, on='month', how='left').merge(sells, on='month', how='left').fillna(0)
    monthly['month_dt'] = pd.to_datetime(monthly['month'] + '-01')
    monthly = monthly.sort_values('month_dt').reset_index(drop=True)


    monthly['rolling_3m_buys'] = monthly['buy_count'].rolling(window=3, min_periods=1).mean()
    return monthly

def get_investor_summary(db_path=DB_NAME):
    trades = get_cleaned_trades(db_path)
    investors = load_raw_data(db_path)[1]

    agg = trades.groupby('investor_id').agg(
        total_trades=('trade_id', 'count'),
        avg_holding_days=('holding_days', 'mean'),
        win_rate=('pnl', lambda x: (x > 0).mean() * 100),
        total_invested=('invested', 'sum'),
        total_pnl=('pnl', 'sum')
    ).reset_index()

    summary = pd.merge(investors, agg, on='investor_id', how='left').fillna(0)
    summary['total_invested_lakh'] = summary['total_invested'] / 1e5
    summary['total_pnl_lakh'] = summary['total_pnl'] / 1e5
    summary['risk_label'] = summary['risk_profile'].map(RISK_PROFILES)
    return summary

def get_stock_return_matrix(db_path=DB_NAME):
    prices = get_clean_prices(db_path)
    matrix = prices.pivot_table(index='date', columns='symbol', values='daily_return').dropna()
    sectors = prices.drop_duplicates('symbol').set_index('symbol')['sector_name']
    return matrix, sectors

def get_state_geospatial_summary(db_path=DB_NAME):
    trades = get_cleaned_trades(db_path)
    investors = load_raw_data(db_path)[1]

    counts = investors.groupby('home_state').agg(investor_count=('investor_id', 'count')).reset_index()
    value = trades.groupby('investor_state').agg(
        total_trades=('trade_id', 'count'),
        traded_value=('invested', 'sum'),
        total_pnl=('pnl', 'sum')
    ).reset_index().rename(columns={'investor_state': 'home_state'})

    geo = pd.merge(counts, value, on='home_state', how='left').fillna(0)
    geo['traded_value_lakh'] = geo['traded_value'] / 1e5
    return geo

def analyse_stock(stock_id, db_path=DB_NAME, prices=None):
    if prices is None:
        prices = get_clean_prices(db_path)
    g = prices[prices['stock_id'] == stock_id].reset_index(drop=True)
    if g.empty:
        return None, None
    g['dma_20'] = g['close'].rolling(20, min_periods=1).mean()
    g['dma_50'] = g['close'].rolling(50, min_periods=1).mean()


    change = g['close'].diff()
    # RSI (14 days)
    gain = change.clip(lower=0).rolling(14, min_periods=1).mean()
    loss = (-change.clip(upper=0)).rolling(14, min_periods=1).mean()
    g['rsi'] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    g['rsi'] = g['rsi'].fillna(50)

    last = g.iloc[-1]
    def ret(days):
        return (last['close'] / g['close'].iloc[max(0, len(g) - 1 - days)] - 1) * 100

    if last['close'] > last['dma_50'] and last['dma_20'] > last['dma_50']:
        signal = "BULLISH  (price above 50-DMA and 20-DMA above 50-DMA)"
    elif last['close'] < last['dma_50'] and last['dma_20'] < last['dma_50']:
        signal = "BEARISH  (price below 50-DMA and 20-DMA below 50-DMA)"
    else:
        signal = "NEUTRAL  (moving averages are mixed)"

    report = {
        'symbol': last['symbol'], 'company': last['company_name'], 'sector': last['sector_name'],
        'last_close': last['close'], 'last_date': last['trade_date'],
        'ret_1d': ret(1), 'ret_1m': ret(21), 'ret_3m': ret(63), 'ret_1y': ret(len(g) - 1),
        'high_52w': g['high'].max(), 'low_52w': g['low'].min(),
        'volatility': g['daily_return'].std() * np.sqrt(252),
        'max_drawdown': _max_drawdown(g['close']),
        'dma_20': last['dma_20'], 'dma_50': last['dma_50'], 'rsi': last['rsi'],
        'avg_volume': g['volume'].tail(20).mean(), 'signal': signal,
    }
    return report, g

def print_cleaning_report(db_path=DB_NAME):
    sectors, investors, stocks, trades = load_raw_data(db_path)
    conn = get_connection(db_path)
    raw_prices = pd.read_sql_query("SELECT * FROM price_history;", conn)
    conn.close()
    print("\n" + "=" * 70)
    print("          DATA CLEANING & AGGREGATION REPORT")
    print("=" * 70)

    print("\n[1] RAW TABLES (rows x columns)")
    for name, t in [('sectors', sectors), ('investors', investors), ('stocks', stocks),
                    ('price_history', raw_prices), ('trades', trades)]:
        print(f"    {name:<14}: {t.shape[0]:>5} x {t.shape[1]}")

    print("\n[2] MISSING VALUES IN RAW DATA")
    print(f"    price_history.close: {raw_prices['close'].isnull().sum()} nulls  -> data-feed gaps (price not received)")
    for col, n in trades.isnull().sum().items():
        if n:
            print(f"    trades.{col:<11}: {n} nulls  -> meaning: position not sold yet (open position)")
    print(f"    duplicate trade rows: {trades.duplicated().sum()}")

    clean = get_cleaned_trades(db_path)
    prices = get_clean_prices(db_path)
    print("\n[3] CLEANING STEPS APPLIED")
    print("    - trade_date / buy_date / sell_date converted from text to datetime")
    print(f"    - missing closing prices forward-filled per stock -> nulls left: {prices['close'].isnull().sum()}")
    print("    - daily_return (%) = today's close / yesterday's close - 1")
    print("    - null sell_date kept as OPEN position, valued at today's price")
    print("    - holding_days = sell (or today) - buy, clipped at minimum 1")
    print("    - pnl = (exit price - buy price) x quantity ; return_pct = exit / buy - 1")
    print("    - status / simple_status labels derived from sold/open and profit/loss")
    print(f"    cleaned trades shape: {clean.shape[0]} x {clean.shape[1]} (joined with stocks, investors, sectors)")

    print("\n[4] AGGREGATION: trades by sector x status")
    print(clean.pivot_table(index='sector_name', columns='simple_status', values='trade_id',
                            aggfunc='count', fill_value=0).to_string())

    print("\n[5] AGGREGATION: summary statistics of holding days, returns and daily returns")
    stats_df = clean[['holding_days', 'return_pct', 'pnl']].describe()
    stats_df['daily_return'] = prices['daily_return'].describe()
    print(stats_df.round(2).to_string())
    print("=" * 70 + "\n")

def get_market_kpis(sector_name=None, risk_profile=None, db_path=DB_NAME, trades=None, stocks=None):
    trades = get_cleaned_trades(db_path) if trades is None else trades
    stocks = get_stock_summary(db_path) if stocks is None else stocks
    if sector_name:
        trades = trades[trades['sector_name'] == sector_name]
        stocks = stocks[stocks['sector_name'] == sector_name]
    if risk_profile:
        trades = trades[trades['risk_profile'] == risk_profile]

    this_month = pd.Timestamp(datetime.now().date()).to_period('M')
    month_counts = trades['buy_date_dt'].dt.to_period('M').value_counts()
    open_pos = trades[trades['sell_date_dt'].isnull()]
    closed = trades[trades['sell_date_dt'].notnull()]

    return {
        'stocks': int(len(stocks)),
        'investors': int(trades['investor_id'].nunique()),
        'total_trades': int(len(trades)),
        'open_positions': int(len(open_pos)),
        'open_invested': float(open_pos['invested'].sum()),
        'open_value': float((open_pos['current_price'] * open_pos['quantity']).sum()),
        'unrealised_pnl': float(open_pos['pnl'].sum()),
        'realised_pnl': float(closed['pnl'].sum()),
        'win_rate_pct': float((closed['pnl'] > 0).mean() * 100) if len(closed) else 0.0,
        'stop_loss_hits': int(open_pos['stop_loss_hit'].sum()),
        'breadth_pct': float(stocks['above_50dma'].mean() * 100) if len(stocks) else 0.0,
        'trades_this_month': int(month_counts.get(this_month, 0)),
        'trades_last_month': int(month_counts.get(this_month - 1, 0)),
    }

def format_inr(value, sign=False):
    prefix = ('+' if value > 0 else '-' if value < 0 else '') if sign else ('-' if value < 0 else '')
    v = abs(value)
    if v >= 1e7:
        return f"{prefix}Rs {v / 1e7:.2f} Cr"
    if v >= 1e5:
        return f"{prefix}Rs {v / 1e5:.1f} L"
    return f"{prefix}Rs {v:,.0f}"

def get_top_movers(n=5, sector_name=None, db_path=DB_NAME):
    stocks = get_stock_summary(db_path)
    if sector_name:
        stocks = stocks[stocks['sector_name'] == sector_name]
    ranked = stocks.sort_values('change_1d', ascending=False)
    return ranked.head(n), ranked.tail(n).iloc[::-1]

def market_mood(breadth_pct):
    if breadth_pct >= 60:
        return "BULLISH", "most stocks are in an uptrend"
    if breadth_pct >= 40:
        return "NEUTRAL", "the market is mixed - about half the stocks are rising"
    return "BEARISH", "most stocks are in a downtrend"

def get_cleaned_deliveries(region=None, db_path=DB_NAME):
    conn = get_connection(db_path)
    df = pd.read_sql_query("""
        SELECT d.*, t.quantity, t.buy_price, t.investor_id, i.name AS investor_name,
               s.symbol, sec.sector_name
        FROM deliveries d
        JOIN trades t ON d.trade_id = t.trade_id
        JOIN investors i ON t.investor_id = i.investor_id
        JOIN stocks s ON t.stock_id = s.stock_id
        JOIN sectors sec ON s.sector_id = sec.sector_id;
    """, conn)
    conn.close()

    today = pd.Timestamp(datetime.now().date())
    df['order_dt'] = pd.to_datetime(df['order_date'])
    df['expected_dt'] = pd.to_datetime(df['expected_date'])
    df['delivery_dt'] = pd.to_datetime(df['delivery_date'])
    delivered = df['delivery_dt'].notnull()
    end = df['delivery_dt'].fillna(today)


    df['settle_days'] = [np.busday_count(o.date(), e.date()) for o, e in zip(df['order_dt'], end)]
    df['delay_days'] = [max(0, np.busday_count(x.date(), e.date())) for x, e in zip(df['expected_dt'], end)]
    df['order_value'] = df['quantity'] * df['buy_price']
    df['status'] = np.select(
        [delivered & (df['delay_days'] == 0), delivered, ~delivered & (df['delay_days'] > 0)],
        ['Delivered On-Time (T+1)', 'Delivered Late', 'Pending - Delayed'],
        default='Pending (in settlement)'
    )
    df['delay_reason'] = df['delay_reason'].fillna('-')
    df['order_month'] = df['order_dt'].dt.to_period('M').astype(str)
    if region:
        df = df[df['region'] == region]
    return df

def get_broker_scorecard(region=None, db_path=DB_NAME):
    deliv = get_cleaned_deliveries(region, db_path)
    done = deliv[deliv['status'].str.startswith('Delivered')]
    score = done.groupby('broker').agg(
        orders=('delivery_id', 'count'),
        on_time_pct=('status', lambda s: (s == 'Delivered On-Time (T+1)').mean() * 100),
        late=('status', lambda s: (s == 'Delivered Late').sum()),
        avg_settle_days=('settle_days', 'mean')
    ).reset_index()

    score['grade'] = np.select([score['on_time_pct'] >= 95, score['on_time_pct'] >= 88], ['A', 'B'], default='C')
    return score.sort_values('on_time_pct', ascending=False)

if __name__ == "__main__":
    print("Testing Preprocessing Module...")
    df = get_cleaned_trades()
    print(f"Cleaned Trades shape: {df.shape}")
    print(df[['trade_id', 'investor_name', 'symbol', 'holding_days', 'pnl', 'return_pct', 'status']].head())
    print("\nSector Aggregate:")
    print(get_sector_aggregates())

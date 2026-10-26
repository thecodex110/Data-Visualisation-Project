# Power BI Integration & Dashboard Build Guide
## Stock Market Analysis System (NSE, India)

---

### Executive Summary & Architecture Overview
This companion guide details how to integrate the **Stock Market Analysis System** data with **Microsoft Power BI** for business intelligence, portfolio reporting and market analytics.

The Python-based CLI application stores structured data in the SQLite database `stock_market.db` and exports a formatted multi-sheet Excel workbook (`stock_market_export.xlsx`).

> Prices in this project are simulated sample data, so the dashboard is a learning exercise, not investment advice.

---

## 1. Power BI Architecture & Components

Power BI ecosystem consists of three main components:

1. **Power BI Desktop**:
   - **Role**: Free Windows application used to ingest, clean, model data (via Power Query), author DAX measures, and design interactive dashboards.
   - **Use Case here**: Primary authoring environment for the analyst who builds the market and portfolio dashboard.
2. **Power BI Service (SaaS)**:
   - **Role**: Cloud-based portal (`app.powerbi.com`) for sharing, collaborating, scheduling automated dataset refreshes, and embedding reports.
   - **Use Case here**: Distributing read-only dashboards to fund managers, advisors and investors.
3. **Power BI On-Premises Data Gateway**:
   - **Role**: Secure bridge connecting on-premises data sources (e.g. SQLite `stock_market.db` on a local server) to the Power BI Service cloud.
   - **Use Case here**: Daily scheduled auto-refresh after market close, without manual export.

> **Recommendation**: For this project, use **Power BI Desktop** for building and modeling, then publish to **Power BI Service** for web-based access.

---

## 2. Data Export & Loading Options

### Option A: Loading via Excel Export (Primary Connection)
1. Run main menu option `16` in `main.py` (**"Export Dataset for Power BI"**) or `python3 main.py --export`.
2. This generates `stock_market_export.xlsx` containing six separate worksheets:
   - `sectors`
   - `stocks`
   - `investors`
   - `price_history` (daily Open/High/Low/Close/Volume)
   - `trades`
   - `shipments` (case study)
3. In **Power BI Desktop**:
   - Click **Get Data** -> **Excel Workbook**.
   - Select `stock_market_export.xlsx`.
   - Check all six tables in the Navigator dialog and click **Transform Data**.

### Option B: Direct Database Connection (SQLite via ODBC)
1. Install **SQLite ODBC Driver** (32-bit or 64-bit matching Power BI Desktop).
2. In Power BI Desktop:
   - Click **Get Data** -> **ODBC**.
   - Connection String: `DRIVER=SQLite3 ODBC Driver;Database=C:\path\to\stock_market.db;`
   - Select tables: `sectors`, `stocks`, `investors`, `price_history`, `trades`, `shipments`.

### Option C: Web API Endpoint (Cloud Native Integration)
Live prices normally come from a market-data API (for example an end-of-day price feed exposed as JSON):
1. In Power BI Desktop: Click **Get Data** -> **Web**.
2. URL: the provider's endpoint, e.g. `https://api.example.com/eod?symbol=TCS`.
3. Power Query automatically parses the JSON payload into a tabular structure; append it to `price_history`.

---

## 3. Data Transformation in Power Query Editor

Once ingested into Power Query Editor, perform the following data cleaning steps (the same ones `preprocessing.py` does in Python):

### Step 1: Set Explicit Data Types
- `price_history`: Set `trade_date` to **Date**; `open`, `high`, `low`, `close` to **Fixed Decimal Number (₹)**; `volume` to **Whole Number**.
- `trades`: Set `buy_date`, `sell_date` to **Date**; `buy_price`, `sell_price`, `stop_loss` to **Fixed Decimal Number (₹)**; `quantity` to **Whole Number**.

### Step 2: Handle Null Values & Add Custom Columns
1. **Missing closing prices (data-feed gaps)**:
   - Sort `price_history` by `stock_id`, then `trade_date`.
   - Select column `close` -> **Transform** -> **Fill** -> **Down** (forward fill, same as pandas `ffill`).
2. **Add Custom Column - Position Status** (in `trades`):
   - Click **Add Column** -> **Custom Column**.
   - Name: `Is_Open`
   - Formula:
     ```powerquery
     if [sell_date] = null then 1 else 0
     ```
3. **Add Custom Column - Invested Amount**:
   ```powerquery
   Invested = [buy_price] * [quantity]
   ```

### Step 3: Establish Data Model Relationships
In Power BI **Model View**, configure star schema relationships:
- `sectors[sector_id]` 1 : * `stocks[sector_id]` (Single direction)
- `stocks[stock_id]` 1 : * `price_history[stock_id]` (Single direction)
- `stocks[stock_id]` 1 : * `trades[stock_id]` (Single direction)
- `investors[investor_id]` 1 : * `trades[investor_id]` (Single direction)
- `stocks[stock_id]` 1 : * `shipments[stock_id]` (Single direction)

Add a **Latest Price** calculated column on `stocks` so open positions can be valued:
```dax
Latest Price =
VAR LastDate = CALCULATE(MAX(price_history[trade_date]), RELATEDTABLE(price_history))
RETURN CALCULATE(MAX(price_history[close]), RELATEDTABLE(price_history), price_history[trade_date] = LastDate)
```

---

## 4. Key Visuals & Dashboard Layout

Build an executive single-page dashboard containing:

| Visual Type | Configuration & Data Fields | Purpose |
| :--- | :--- | :--- |
| **Card Visuals** | `Total Trades`, `Open Positions`, `Realised P&L (₹)`, `Unrealised P&L (₹)` | Immediate KPI headline figures |
| **KPI Visual** | Indicator: `Trades This Month`<br>Target: `Trades Last Month` | Track trading activity trend |
| **Gauge Visual** | Value: `Win Rate %`<br>Target: `55%` | Measure how often closed trades make money |
| **Line Chart** | Axis: `price_history[trade_date]`<br>Values: `close` (filtered to one stock) + 20/50-day moving average measures | Price trend & signals |
| **Slicers (Filters)** | 1. Sector (`sectors[sector_name]`)<br>2. Risk Profile (`investors[risk_profile]`)<br>3. Date range (`price_history[trade_date]`) | Interactive cross-filtering across entire page |
| **Drill-Down Bar Chart** | Hierarchy Level 1: `sector_name`<br>Hierarchy Level 2: `symbol`<br>Value: `Total Traded Value` | Drill from a sector to the individual stocks |

---

## 5. DAX (Data Analysis Expressions) Measures

Create a **_Measures** table in Power BI and add the following DAX calculations:

```dax
// 1. Total Trades
Total Trades =
COUNTROWS(trades)

// 2. Open Positions
Open Positions =
CALCULATE(COUNTROWS(trades), ISBLANK(trades[sell_date]))

// 3. Realised P&L (closed trades)
Realised P&L =
SUMX(
    FILTER(trades, NOT ISBLANK(trades[sell_date])),
    (trades[sell_price] - trades[buy_price]) * trades[quantity]
)

// 4. Unrealised P&L (open trades valued at the latest price)
Unrealised P&L =
SUMX(
    FILTER(trades, ISBLANK(trades[sell_date])),
    (RELATED(stocks[Latest Price]) - trades[buy_price]) * trades[quantity]
)

// 5. Win Rate %
Win Rate % =
DIVIDE(
    COUNTROWS(FILTER(trades, NOT ISBLANK(trades[sell_date]) && trades[sell_price] > trades[buy_price])),
    COUNTROWS(FILTER(trades, NOT ISBLANK(trades[sell_date]))),
    0
)

// 6. 20-Day Moving Average (use with one stock selected)
MA 20 =
AVERAGEX(
    TOPN(20, FILTER(ALLSELECTED(price_history), price_history[trade_date] <= MAX(price_history[trade_date])), price_history[trade_date], DESC),
    price_history[close]
)
```

---

## 6. Row-Level Security (RLS) & Portal Embedding

### Row-Level Security (RLS)
To ensure a sector analyst (e.g. the IT analyst) can only view data for their own sector:
1. In Power BI Desktop: Click **Modeling** -> **Manage Roles**.
2. Create Role: `IT_Sector_Analyst`.
3. Under `sectors` table filter:
   ```dax
   [sector_name] = "IT"
   ```
4. Assign analyst email addresses to roles in **Power BI Service** under Dataset Security.

A second common pattern is **investor-level RLS** (each investor sees only their own portfolio) with `[investor_email] = USERPRINCIPALNAME()` on an investors table that stores emails.

### Power BI Embedded (Portal Integration)
To embed this dashboard directly into a brokerage or advisory web portal:
1. In Power BI Service: Go to **File** -> **Embed Report** -> **Website or Portal** (or **Power BI Embedded** for custom React/Vue applications).
2. Power BI generates an embed link/code for the report, which the portal team pastes into their page (this project itself has no web frontend).
3. Users authenticate via Microsoft Entra ID (Azure AD) single sign-on (SSO).

---

## 7. Case Study: Supply Chain & Logistics Dashboard (Self-study)

Use the `shipments` sheet to rebuild the Python case-study dashboard (main menu option 15) in Power BI. The shipments are export consignments of the listed manufacturers (Pharma, Auto, FMCG) from their factory hubs to **JNPT Port, Navi Mumbai**.

1. **Power Query** - add custom columns:
   ```powerquery
   Transit_Days = Duration.Days((if [delivery_date] = null then DateTime.Date(DateTime.LocalNow()) else [delivery_date]) - [dispatch_date])
   Is_On_Time   = if [delivery_date] <> null and [delivery_date] <= [expected_date] then 1 else 0
   ```
2. **DAX measures**:
   ```dax
   Total Shipments = COUNTROWS(shipments)
   On-Time % = DIVIDE(SUM(shipments[Is_On_Time]), CALCULATE(COUNTROWS(shipments), NOT ISBLANK(shipments[delivery_date])), 0)
   In Transit = CALCULATE(COUNTROWS(shipments), ISBLANK(shipments[delivery_date]))
   Avg Transit Days = AVERAGE(shipments[Transit_Days])
   ```
3. **Visuals**:
   - Cards: Total Shipments, In Transit, Avg Transit Days
   - Gauge: On-Time % (target 90%)
   - Route mapping: **Map** visual with `origin_city` as location, bubble size = Total Shipments (destination = JNPT Port, Navi Mumbai)
   - Stacked bar: status by `region`
   - Scatter: `On-Time %` (x) vs the company's 1-year return (y), one dot per `stocks[symbol]` — the stock-market link
   - **Slicer on `region`** (North / West / South / East) for filtering by region

---
*Guide generated for the Stock Market Analysis System (DV Mini Project).*

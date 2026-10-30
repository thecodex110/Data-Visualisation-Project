# MarketLens: Stock Market Analysis (NSE, India)
### Data Visualization Project

Repository: https://github.com/thecodex110/Data-Visualisation-Project

MarketLens is a web dashboard that analyses **36 NSE stocks** across six sectors (**IT, Banking, Pharma, Auto, FMCG, Energy**). It stores one year of daily prices, 90 investors, their buy/sell trades and the T+1 delivery of every bought share in a SQLite database, and presents everything through six interactive pages with **26 charts** covering the Data Visualization syllabus (Unit 1 to Unit 5, Power BI and the Supply Chain case study).

> Prices are simulated sample data, not real market prices. Nothing here is investment advice.

---

## Pages

| Page | What it shows |
|---|---|
| **Home** | Market mood, sector indices, index cards, top movers, sector returns |
| **Dashboard** | Sector and investor-type slicers, KPI cards, breadth gauge, top gainers and losers, sector → stock drill-down, watchlist |
| **Stocks** | Search any stock: candlestick or line chart, 20/50-day moving averages, volume, RSI, buy/sell signal, returns and risk |
| **Charts Lab** | All 26 syllabus charts, grouped by unit, with a large spotlight view |
| **Investors & Trade** | Investor directory, portfolio and trade history, buy / sell / add investor, stop-loss alerts |
| **Delivery** | Case study: T+1 share delivery chain, region slicer, route map, broker report card, delay reasons |

Buy, sell and add-investor actions are saved to `stock_market.db`. The home page also has a button to download the whole dataset as an Excel workbook for Power BI.

---

## How to run

You need **Python 3.9 or newer** and a web browser.

### macOS / Linux

```bash
python3 -m venv .venv
```
```bash
source .venv/bin/activate
```
```bash
pip install -r requirements.txt
```
```bash
python3 main.py
```

### Windows (PowerShell)

```powershell
py -m venv .venv
```
```powershell
.venv\Scripts\Activate.ps1
```
```powershell
pip install -r requirements.txt
```
```powershell
python main.py
```

The website opens at **http://localhost:8000**. Press **Ctrl+C** in the terminal to stop it.

- Port 8000 busy? Run `python3 web_app.py --port 8080` and open http://localhost:8080
- macOS: if you see *"library load disallowed by system policy"*, create the virtual environment outside the project folder, e.g. `python3 -m venv ~/.venvs/marketlens`
- Windows: if PowerShell says *"running scripts is disabled"*, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` first
- Linux (Ubuntu/Debian): install venv support with `sudo apt install python3-venv`

---

## Project structure

```
main.py                    Starts the website; buy, sell and Excel export
web_app.py                 Web server: serves the pages and the data API
web_data.py                Builds the page data and the 26 charts from the database
preprocessing.py           Data cleaning, returns, P&L, RSI, KPIs, deliveries
db_setup.py                SQLite schema (6 tables) and the sample data
web/                       HTML pages, style.css, app.js and one script per page
stock_market.db            SQLite database
stock_market_export.xlsx   Excel export for Power BI
POWERBI_GUIDE.md           Building the dashboard in Power BI Desktop
```

---

## Syllabus coverage

| Unit | Charts |
|---|---|
| 1. Introduction | Design principles (poor vs clean chart), categorical / time-series / statistical graphics |
| 2. Pre-processing & Aesthetics | Pairplot, monthly return heatmap, interactive sector explorer, graphical perception, grammar of graphics |
| 3. Visualization Design | Bar, horizontal bar, dot plot, grouped and stacked bars, histogram + KDE, violin, ECDF, Q-Q, log transform |
| 4. Advanced Design | Box/strip vs ridgeline, pie vs bars, parts of total, treemap and nested donut, scatter, correlogram, PCA, slope chart |
| 5. Time Series & Geospatial | Moving averages, LOESS, dose-response, detrending, decomposition, map projections, map layers, choropleth, cartogram |
| 6. Power BI | Dashboard page (slicers, cards, gauge, drill-down), Excel export, `POWERBI_GUIDE.md` |
| Case Study | Supply chain of the stock market: share delivery from order to demat account (T+1) |

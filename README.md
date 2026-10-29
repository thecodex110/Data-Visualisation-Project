# Data-Visualisation-Project-
## Stock Market Analysis System (NSE, India) — Terminal + Web Data Visualization Project

A terminal-only (CLI) Python project that analyses **36 NSE stocks** across six sectors (**IT, Banking, Pharma, Auto, FMCG, Energy**). It keeps one year of daily prices, investors, their buy/sell trades, their profit/loss and the T+1 delivery of every bought share in SQLite. It also generates **26 charts** that cover every topic of the Data Visualization syllabus (Unit 1 to Unit 5, the Power BI unit and the Supply Chain case study), plus a candlestick analysis chart for any stock.

In the terminal, charts are saved as PNGs in `charts/` and open in the system image viewer (Preview on macOS); the interactive chart opens in its own window process.

**New: MarketLens website.** `python3 main.py --web` (or menu option 17) starts a local website at http://localhost:8000 with six pages (Home, Dashboard, Stocks, Charts Lab, Investors & Trade, Delivery). All 26 syllabus charts, the candlestick analysis and both dashboards are drawn and animated in the browser from the same database. Buy, sell and add-investor on the website write to `stock_market.db` exactly like the menu. It uses Python's built-in web server, so there is nothing extra to install. The menu never quits on its own — only option `0` exits, even if a chart window is closed, an error occurs or Ctrl+C is pressed.

> Prices are **simulated sample data** (realistic random walk with market + sector moves), not real market prices. Nothing here is investment advice.

👉 **Full explanation in Hinglish (what is in the project, how it runs, the meaning of every command and menu option, the syllabus mapping and viva Q&A): [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md)**
👉 Every main-menu option and where its code lives: [`MENU_OPTIONS_EXPLAINED.txt`](MENU_OPTIONS_EXPLAINED.txt)
👉 Power BI steps: [`POWERBI_GUIDE.md`](POWERBI_GUIDE.md)

---

## Quick Start

```bash
python3 -m venv ~/.venvs/dv-lms     # venv outside the project folder (see PROJECT_GUIDE.md §0)
source ~/.venvs/dv-lms/bin/activate
pip install -r requirements.txt
python3 main.py                   # opens the main menu
```

| Command | What it does |
|---|---|
| `python3 main.py` | Interactive main menu (17 options) |
| `python3 main.py --all` | Save all 26 charts to `charts/` (no windows) |
| `python3 main.py --list` | List chart numbers by syllabus unit |
| `python3 main.py --chart N` | Build and show chart N |
| `python3 main.py --report` | Data cleaning & aggregation report |
| `python3 main.py --export` | Write `stock_market_export.xlsx` for Power BI |
| `python3 main.py --web` | Start the MarketLens website at http://localhost:8000 (Ctrl+C stops it) |
| `python3 main.py --reset-db` | Re-create `stock_market.db` with fresh sample data |

---

## Main Menu

| # | Option | # | Option |
|---|---|---|---|
| 1 | View Market Watchlist | 9 | View Stop-Loss Alerts |
| 2 | Add New Stock | 10 | Investor Portfolio & Trade History |
| 3 | Remove / Delist Stock | 11 | Data Cleaning & Aggregation Report |
| 4 | Search & Analyse a Stock (signal + candlestick) | 12 | Data Visualization Menu (26 charts) |
| 5 | View Investor Directory | 13 | Generate All Charts |
| 6 | Add New Investor | 14 | Market Dashboard (mood, cards, gauge, top movers, drill-down) |
| 7 | Buy a Stock (auto 8% stop-loss, T+1 delivery) | 15 | Supply Chain Case Study: Share Delivery Tracker (Region filter) |
| 8 | Sell a Stock (auto profit/loss) | 16 | Export Dataset for Power BI |
|  |  | 17 | Open the Website (all pages + 26 charts in the browser) |

---

## Project Structure

```
main.py                  # Entry point: menus, market operations, market dashboard, delivery tracker, CLI flags
db_setup.py              # SQLite schema (6 tables) + simulated market data
preprocessing.py         # Cleaning, returns, P&L, technical indicators, aggregations, KPIs, deliveries
visualizations.py        # 26 charts by syllabus unit (CHART_MENU) + market dashboard + stock analysis chart
web_app.py               # MarketLens website server (built-in http.server): pages + JSON API + buy/sell/add investor
web_data.py              # Builds the website data and the 26 charts as SVG shapes from the database
web/                     # Website pages (HTML), style.css, app.js and one script per page
stock_market.db          # SQLite database
stock_market_export.xlsx # Excel export for Power BI (6 sheets)
charts/                  # Generated PNG charts
```

## Syllabus Coverage (summary)

| Unit | Covered by |
|---|---|
| 1. Introduction | Design principles (bad vs good chart), categorical / time-series / statistical graphics |
| 2. Pre-processing & Aesthetics | Cleaning report (missing prices forward-filled), pairplot, violin, return heatmap, interactive explorer, graphical perception, grammar of graphics, scales |
| 3. Visualization Design | Bar, grouped/stacked, dot plot, heatmap, histogram/KDE of daily returns, multiple distributions, ECDF, Q-Q (fat tails), skewed trade sizes |
| 4. Advanced Design | Box/strip vs ridgeline, pie vs bars vs stacked, stacked densities, parts of total, treemap/nested donut, risk-return scatter, sector correlogram, PCA of stocks, paired slope |
| 5. Time Series & Geospatial | Market & sector indices, moving averages, LOESS, exponential trend, dose-response, multi-response, detrending, decomposition, projections, layers, choropleth, cartogram |
| 6. Power BI | Excel export, Market Dashboard (cards, mood gauge, slicers, drill-down, top movers) in terminal + image, `POWERBI_GUIDE.md` (Power Query, DAX, RLS, Embedded) |
| Case Study | Supply chain of the stock market = share delivery (order → broker → NSE → clearing → depository → demat, T+1): route map, delivery KPIs, broker report card, region filter |

Topic-by-topic mapping: see section 8 of [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md).

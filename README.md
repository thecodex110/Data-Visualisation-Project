# Data-Visualisation-Project-
## Stock Market Analysis System (NSE, India) — Terminal Data Visualization Project

A terminal-only (CLI) Python project that analyses **36 NSE stocks** across six sectors (**IT, Banking, Pharma, Auto, FMCG, Energy**). It keeps one year of daily prices, investors, their buy/sell trades and their profit/loss in SQLite. It also generates **26 charts** that cover every topic of the Data Visualization syllabus (Unit 1 to Unit 5, the Power BI unit and the Supply Chain case study), plus a candlestick analysis chart for any stock.

No web frontend: charts are saved as PNGs in `charts/` and open in a matplotlib window from the menu.

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
| `python3 main.py` | Interactive main menu (16 options) |
| `python3 main.py --all` | Save all 26 charts to `charts/` (no windows) |
| `python3 main.py --list` | List chart numbers by syllabus unit |
| `python3 main.py --chart N` | Build and show chart N |
| `python3 main.py --report` | Data cleaning & aggregation report |
| `python3 main.py --export` | Write `stock_market_export.xlsx` for Power BI |
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
| 6 | Add New Investor | 14 | KPI Dashboard (Cards, KPI, Gauge, Slicers, Drill-down) |
| 7 | Buy a Stock (auto 8% stop-loss) | 15 | Supply Chain & Logistics Case Study (Region filter) |
| 8 | Sell a Stock (auto profit/loss) | 16 | Export Dataset for Power BI |

---

## Project Structure

```
main.py                  # Entry point: menus, market operations, KPI dashboard, case study, CLI flags
db_setup.py              # SQLite schema (6 tables) + simulated market data
preprocessing.py         # Cleaning, returns, P&L, technical indicators, aggregations, KPIs
visualizations.py        # 26 charts, arranged by syllabus unit (CHART_MENU) + stock analysis chart
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
| 6. Power BI | Excel export, terminal KPI cards/gauge/slicers/drill-down, `POWERBI_GUIDE.md` (Power Query, DAX, RLS, Embedded) |
| Case Study | Supply Chain & Logistics dashboard of listed manufacturers: route map, delivery KPIs, region filter, on-time % vs share return |

Topic-by-topic mapping: see section 8 of [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md).

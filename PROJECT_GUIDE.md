# 📘 Project Guide (Hinglish) — Stock Market Analysis System
### Data Visualization Course Project · Pure Terminal (CLI) Project

Is ek file me sab kuch hai: project me **kya hai**, **kaise chalta hai**, **har terminal command ka matlab**, **har menu option ka matlab**, aur **syllabus ka har topic project me kahan hai**.

---

## 📑 Table of Contents
0. [⚡ Sabse pehle: Terminal me project kaise ON karein](#0--sabse-pehle-terminal-me-project-kaise-on-karein)
1. [Project kya hai?](#1-project-kya-hai)
   - [1A. Purana Library project → naya Stock Market project (kya badla)](#1a-purana-library-project--naya-stock-market-project-kya-badla)
2. [Project me kya-kya hai (files & folders)](#2-project-me-kya-kya-hai-files--folders)
3. [Project kaise chalta hai (data flow)](#3-project-kaise-chalta-hai-data-flow)
   - [3A. Code andar se kaise kaam karta hai (step-by-step)](#3a-code-andar-se-kaise-kaam-karta-hai-step-by-step)
4. [Database ke 6 tables](#4-database-ke-6-tables)
5. [Setup + har terminal command ka matlab](#5-setup--har-terminal-command-ka-matlab)
6. [Main Menu (0–16) ka matlab](#6-main-menu-016-ka-matlab)
7. [Visualization Menu (1–26) ka matlab](#7-visualization-menu-126-ka-matlab)
8. [Syllabus → Project Mapping (har topic kahan hai)](#8-syllabus--project-mapping-har-topic-kahan-hai)
9. [Power BI unit project me kaise cover hai](#9-power-bi-unit-project-me-kaise-cover-hai)
10. [Case Study: Supply Chain = Share Delivery Tracker](#10-case-study-supply-chain--share-delivery-tracker)
11. [Stock market ke zaroori shabd (jo project me use hue)](#11-stock-market-ke-zaroori-shabd-jo-project-me-use-hue)
12. [Viva Questions & Answers](#12-viva-questions--answers)
13. [Problem aaye to (Troubleshooting)](#13-problem-aaye-to-troubleshooting)

---

## 0. ⚡ Sabse pehle: Terminal me project kaise ON karein

> Mac ke liye steps. Har command terminal me paste karo aur **Enter** dabao. (Windows ke commands Section 5 me hain.)

### Pehli baar (one-time setup)

**Step 1 — Terminal kholo.** `Cmd + Space` dabao, `Terminal` likho, Enter.

**Step 2 — Project folder me jao**
```bash
cd "/Users/rahil/Developer/Project/DV Project/Data-Visualisation-Project-"
```
`cd` = change directory. Path me space hai, isliye quotes `" "` zaroori hain.

**Step 3 — Project folder ke andar wala purana venv hatao** (agar hai)
```bash
rm -rf venv
```
`rm -rf` = folder aur uske andar sab delete. Sirf `venv` folder hatega, project code nahi.

> ⚠️ **Important (is Mac pe):** venv ko project folder ke **andar** banane par macOS ki security policy kuch library files (`.so`) block/kharab kar deti hai → error aata hai *"library load disallowed by system policy"* ya *"No module named 'pandas'"*. Isliye venv project ke **bahar** `~/.venvs/dv-lms` me banate hain. (`~` = aapka home folder `/Users/rahil`. Naam `dv-lms` purane project se chala aa raha hai, bas ek folder ka naam hai.)

**Step 4 — Naya virtual environment banao** (agar pehle se bana hai to ye step skip karo)
```bash
python3 -m venv ~/.venvs/dv-lms
```
Project ke liye alag Python "box" banta hai, taaki libraries baaki system se mix na hon.

**Step 5 — Virtual environment chalu karo**
```bash
source ~/.venvs/dv-lms/bin/activate
```
Ab prompt ke aage `(dv-lms)` dikhega. Matlab ab jo `python3`/`pip` chalaoge wo is box ka hai.

**Step 6 — Libraries install karo** (1–2 minute, internet chahiye)
```bash
pip install -r requirements.txt
```

**Step 7 — Project chalao**
```bash
python3 main.py
```
Main menu khulega. Number type karo + Enter. Example: `1` = watchlist, `4` = stock analysis, `12` = charts menu, `14` = market dashboard, `15` = share delivery tracker, `0` = exit.

### Agli baar se (roz ka kaam) — sirf 3 commands

```bash
cd "/Users/rahil/Developer/Project/DV Project/Data-Visualisation-Project-"
```
```bash
source ~/.venvs/dv-lms/bin/activate
```
```bash
python3 main.py
```

### Useful shortcuts

```bash
python3 main.py --all
```
Saare 26 charts `charts/` folder me save (koi window nahi khulegi).

```bash
python3 main.py --list
```
Charts ki numbered list.

```bash
python3 main.py --chart 5
```
Sirf chart 5 (interactive explorer) kholo — ye alag interactive window me khulta hai. Koi bhi number 1–26 de sakte ho.

```bash
open charts
```
Saare bane hue charts Finder me dekho.

```bash
deactivate
```
Kaam khatam — venv band.

> 💡 **Program kabhi apne-aap band nahi hota.** Har chart Mac ke **Preview** app me khulta hai aur menu turant wapas aa jaata hai. Preview band karo, `Cmd+Q` karo, galti se `Ctrl+C` dabao, ya koi error aaye — menu chalta rehta hai. Program sirf menu me **`0`** dabane pe band hota hai. Teacher ke saamne demo me baar-baar restart nahi karna padega.

---

## 1. Project kya hai?

Ye ek **Stock Market Analysis System** hai (Indian stock exchange **NSE** ke 36 stocks) jo **sirf terminal (command line) me chalta hai** — koi website, HTML page ya frontend nahi hai.

Do kaam karta hai:
1. **Market ka kaam** — stocks add/remove, investors add, stock **buy/sell**, automatic **profit/loss**, **stop-loss alerts**, kisi bhi stock ka **technical analysis** (moving average, RSI, signal, candlestick chart).
2. **Data Visualization** — market ke data se **26 charts** banata hai jo syllabus ke **Unit 1 se Unit 5** aur **Case Study** ke har topic ko cover karte hain. Charts `charts/` folder me PNG image ban ke save hote hain aur (menu mode me) Preview app me khulte hain; chart 5 ek live interactive window me.

Plus:
- **Power BI** ke liye data ko `stock_market_export.xlsx` me export karta hai (Unit 6).
- Terminal me hi **Market Dashboard**: KPI Cards, Gauge, Slicer, Drill-down, Top Gainers/Losers (Power BI jaisa) + dashboard image.

**Data (sample, simulated but realistic):**
| Cheez | Kitna |
|---|---|
| Sectors | 6 — IT, Banking, Pharma, Auto, FMCG, Energy |
| Stocks | 36 (har sector ki 6 badi NSE companies: TCS, Infosys, HDFC Bank, Sun Pharma, Maruti, ITC, Reliance...) |
| Daily prices | 9,000 rows = 36 stocks × 250 trading days (≈ 1 saal), Open/High/Low/Close/Volume |
| Investors | 90 (risk profile 1–4, India ke 10 states se, har ek ka ek broker: Zerodha, Groww, Upstox, Angel One, ICICI Direct) |
| Trades | 300 buy orders (zyada tar baad me sell hue, kuch abhi bhi open) |
| Share deliveries (case study) | 300 (har buy order ke shares investor ke demat account tak T+1 me pahunche ya late hue) |

> ⚠️ Prices **asli market prices nahi hain** — `db_setup.py` ek realistic random walk se banata hai (market ki chaal + sector ki chaal + company ki apni chaal). Isliye ye project **investment advice nahi** hai, sirf data visualization ka demo hai.

**Tools used (sab Python libraries):**
| Library | Kis kaam ke liye |
|---|---|
| `sqlite3` | Database (Python ke andar hi aata hai) |
| `pandas`, `numpy` | Data cleaning, returns, P&L, pivot tables, price simulation |
| `matplotlib` | Saare charts ka base + candlestick + interactive window (hover, checkbox, slider) |
| `seaborn` | Pairplot, violin, heatmap, KDE, ECDF jaise statistical charts |
| `scipy` | Q-Q plot, KDE, skewness, correlation |
| `statsmodels` | LOESS smoothing, time-series decomposition |
| `scikit-learn` | PCA (dimension reduction) |
| `squarify` | Treemap |
| `faker` | Fake Indian investor names banane ke liye |
| `openpyxl` | Excel file likhne ke liye (Power BI export) |

---

## 1A. Purana Library project → naya Stock Market project (kya badla)

**Structure bilkul same hai** — wahi 4 Python files, wahi 16 menu options, wahi 26 charts, wahi syllabus mapping. Sirf "library" ki jagah "stock market" aa gaya. Agar aapne purana project samjha tha, to ye table sab bata deti hai:

| Purana (Library) | Naya (Stock Market) | Kaise |
|---|---|---|
| Department | **Sector** (IT, Banking, Pharma, Auto, FMCG, Energy) | Har stock ek sector me hai, har sector ka fixed colour |
| Book | **Stock** (TCS, HDFCBANK, MARUTI...) | Watchlist me |
| Student | **Investor** | Year (1–4) ki jagah **risk profile** (1 Conservative → 4 Aggressive) |
| Issue a Book | **Buy a Stock** | Buy price = aaj ka price |
| Due date (+14 din) | **Stop-loss** (buy price se 8% neeche) | Automatic set hota hai |
| Return a Book | **Sell a Stock** | Sell price = aaj ka price |
| Fine (₹5/din late) | **Profit / Loss** = (sell − buy) × quantity | Automatic calculate |
| Overdue Loans | **Stop-Loss Alerts** | Open positions jinka price stop-loss se neeche gir gaya |
| Student Borrowing History | **Investor Portfolio & Trade History** | Open + closed trades, P&L, win rate |
| Search Books | **Search & Analyse a Stock** | Search ke baad stock ID do → analysis + candlestick chart |
| `library.db` (5 tables) | `stock_market.db` (6 tables) | Naya table `price_history` = roz ke prices |
| Publisher → campus book shipments | **Share delivery**: kharide hue shares investor ke **demat account** tak (T+1) | Courier ki jagah **broker**, route = investor ka shehar → NSE Mumbai |
| KPI Dashboard (library) | **Market Dashboard** | Market mood, top gainers/losers, investors ka profit, har number ka matlab |

---

## 2. Project me kya-kya hai (files & folders)

```
Data-Visualisation-Project-/
├── main.py                  # 🎮 Program yahin se start hota hai: menu, buy/sell, analysis, market dashboard, delivery tracker, flags
├── db_setup.py              # 🗄️ Database banata hai: 6 tables + simulated prices, investors, trades, deliveries
├── preprocessing.py         # ⚙️ Data cleaning + analysis: missing prices, returns, P&L, RSI, KPIs, deliveries
├── visualizations.py        # 🎨 Saare 26 charts (unit-wise) + CHART_MENU list + candlestick analysis chart
├── stock_market.db          # 💾 SQLite database file (asli data yahan store hota hai)
├── stock_market_export.xlsx # 📊 Power BI ke liye Excel (6 sheets)
├── requirements.txt         # 📦 Kaunsi Python libraries install karni hain
├── POWERBI_GUIDE.md         # 📑 Power BI Desktop me dashboard banane ka step-by-step guide (Unit 6)
├── PROJECT_GUIDE.md         # 📘 Ye file
├── MENU_OPTIONS_EXPLAINED.txt # Main menu ke 0–16 options + code kis file/function/line me
├── README.md                # Short intro
├── .gitignore               # Git ko batata hai venv/ aur __pycache__/ ignore karo
└── charts/                  # 🖼️ Saare generated PNG charts yahan save hote hain
```

### Har file ka kaam (detail me)

**`main.py`** — Entry point.
- `check_db()` → agar `stock_market.db` nahi hai to bana deta hai.
- Market functions: `view_stocks`, `add_stock`, `remove_stock`, `search_and_analyse`, `view_investors`, `add_investor`, `buy_stock`, `sell_stock`, `view_stop_loss_alerts`, `investor_portfolio`.
- `export_for_power_bi()` → 6 tables ko Excel me likhta hai.
- `kpi_dashboard()` → **Market Dashboard**: terminal me Power BI jaisa Slicer/Cards/KPI/Gauge/Drill-down + top movers + dashboard image.
- `supply_chain_case_study()` → **Share Delivery Tracker**: kahani + region filter + delivery KPIs + routes + broker report card + delay reasons + dashboard chart.
- `visualization_menu()` → 26 charts unit-wise.
- `parse_args()` → command-line flags (`--all`, `--chart`, etc.).

**`db_setup.py`** — Database builder.
- `STOCK_LIST` → 36 companies ki list (symbol, naam, sector, HQ state, starting price).
- `INVESTOR_CITIES`, `BROKERS`, `BROKER_DELAY_RATE`, `DELAY_REASONS` → delivery case study ki settings.
- `init_db()` → purane tables delete karke 6 naye tables banata hai.
- `seed_db()` → sectors, 90 investors, 36 stocks, 9,000 daily prices, 300 trades aur 300 share deliveries daalta hai.
- `build_ohlcv()` → daily returns se Open/High/Low/Close/Volume banata hai.
- `simulate_new_stock_history()` → naya stock add karo to uske liye 1 saal ki history bana deta hai.
- `seed_deliveries()` / `create_delivery()` → har buy order ki share delivery (T+1); `next_trading_day()` → T+1 date; `haversine_km()` → investor ke shehar se NSE Mumbai ki doori (route map ke liye).

**`preprocessing.py`** — Data cleaning & analysis (Unit 2).
- `get_clean_prices()` → missing closing prices **forward-fill**, `daily_return` %.
- `get_cleaned_trades()` → 4 tables JOIN karke ek saaf table: `holding_days`, `pnl`, `return_pct`, `status`, `stop_loss_hit`.
- `get_stock_summary()` → har stock ki ek row: 1Y return, volatility, max drawdown, beta, 20/50-day average.
- `get_market_index()`, `get_sector_index()` → poore market ka aur har sector ka index (base 1000 / 100).
- `get_sector_aggregates()`, `get_stock_trade_aggregates()`, `get_monthly_sector_returns()`, `get_monthly_timeseries()` → group-by / pivot.
- `get_investor_summary()`, `get_stock_return_matrix()` → investor-level aur PCA ke liye data.
- `get_state_geospatial_summary()` → state-wise investors aur traded value (maps ke liye).
- `analyse_stock()` → ek stock ka technical analysis (returns, RSI, signal).
- `print_cleaning_report()` → terminal me cleaning ka report.
- `get_market_kpis()`, `market_mood()`, `get_top_movers()`, `format_inr()` → Market Dashboard ke numbers (slicer filters ke saath).
- `get_cleaned_deliveries()`, `get_broker_scorecard()` → share delivery case study.

**`visualizations.py`** — Charts.
- Upar common settings: colours (har sector ka fixed colour, profit = green, loss = red, open = blue), `save_chart()` helper.
- Phir sections: **Unit 1 → Unit 2 → Unit 3 → Unit 4 → Unit 5 → Market Dashboard → Case Study → Stock Analysis chart**.
- End me `CHART_MENU` list (menu number → chart function) aur `generate_all_visualizations()`.

---

## 3. Project kaise chalta hai (data flow)

```
 db_setup.py                    preprocessing.py                    visualizations.py            charts/*.png
┌────────────────┐  SQL  ┌───────────────────────────────┐ DataFrame ┌────────────────────┐ save ┌──────────┐
│ stock_market.db│ ────► │ JOIN + clean + calculate       │ ────────► │ matplotlib/seaborn │ ───► │ 26 PNGs  │
│ (6 tables)     │       │ (returns, P&L, status, RSI)    │           │ charts             │      └──────────┘
└────────────────┘       └───────────────────────────────┘           └────────────────────┘
       ▲                                                                       ▲
       │ buy/sell/add (INSERT/UPDATE)                                          │ menu option / --chart N
       └──────────────────────────────── main.py (terminal menu) ──────────────┘
                                              │
                                              └──► stock_market_export.xlsx ──► Power BI Desktop
```

**Step by step:**
1. Aap `python3 main.py` chalate ho.
2. `check_db()` dekhta hai database hai ya nahi; nahi hai to `db_setup.py` bana deta hai.
3. Menu aata hai. Market option (jaise *Buy a Stock*) chuno to `main.py` seedha SQL se `stock_market.db` update karta hai.
4. Chart option chuno to `visualizations.py` ka function chalta hai → wo `preprocessing.py` se **cleaned DataFrame** maangta hai → `preprocessing.py` database padh ke clean karta hai → chart banta hai → `charts/` me save → Preview me khulta hai, aur menu turant wapas aa jaata hai.
5. Kyunki charts har baar database se fresh banate hain, **naya trade karo ya naya stock add karo to chart bhi update ho jaata hai**.

**Cleaning ke rules (yaad rakhna, viva me puchte hain):**
- `close` khaali (NULL) = us din price feed nahi aaya (data gap) → **forward fill** = pichle din ka price use karo.
- `daily_return` = aaj ka close ÷ kal ka close − 1 (× 100 = %)
- `sell_date` khaali (NULL) = position abhi **open** hai (investor ke paas share hai) — ye missing value galti nahi, **meaning** hai. Open position ko aaj ke price pe value karte hain.
- `holding_days` = sell date (ya aaj) − buy date, minimum 1
- `pnl` = (exit price − buy price) × quantity; `return_pct` = exit ÷ buy − 1
- `stop_loss_hit` = position open hai **aur** aaj ka price ≤ stop-loss

---

## 3A. Code andar se kaise kaam karta hai (step-by-step)

### (a) Program start hone par (`python3 main.py`)
1. Python `main.py` ko upar se padhta hai → `import db_setup, preprocessing, visualizations` (teeno files load).
2. `visualizations.py` load hote hi chart style set ho jaata hai (`sns.set_theme`, fonts, sector colours).
3. Neeche `if __name__ == "__main__":` block chalta hai → `parse_args()` dekhta hai koi flag (`--all`, `--chart` ...) diya ya nahi.
4. `check_db()`: `stock_market.db` nahi hai → `db_setup.init_db()` (tables banao) + `db_setup.seed_db()` (sample data daalo).
5. Koi flag nahi → `main_menu()` → ek `while True` loop jo menu print karta hai, `input()` se number leta hai, aur `actions` dictionary se sahi function call karta hai (jaise `'7' → buy_stock`). `0` pe `sys.exit(0)`.

### (b) Prices kaise bane (`db_setup.seed_db`, step 4)
1. `trading_dates()` → aaj tak ke pichle 250 weekdays (Saturday-Sunday market band).
2. Har din ka **market move** (sab stocks pe asar) + har sector ka **sector move** + har company ka **apna move** random number se.
3. Random numbers `standard_t(4)` (Student-t distribution) se — normal distribution se zyada "bade jhatke" deta hai, jaise asli market me crash/jump. Isliye chart 13 ke Q-Q plot me **fat tails** dikhti hain.
4. `daily return = drift + beta × market + sector + company` → `build_ohlcv()` se Close = pichla close × (1 + return), aur Open/High/Low/Volume.
5. ~1% closing prices jaan-boojh ke `NULL` kiye (data feed gap) taaki cleaning dikha sakein.
6. Fixed seed (42) → har baar same data.

### (c) Stock buy karna (menu 7 → `buy_stock()`)
1. Investor ID, Stock ID, Quantity input.
2. `SELECT name FROM investors ...` → investor hai ya nahi check; `SELECT symbol FROM stocks ...` → stock hai ya nahi.
3. `_latest_price()` → `price_history` se us stock ka sabse naya close = buy price.
4. `stop_loss = buy_price × (1 − 0.08)` (8% neeche).
5. `INSERT INTO trades (..., sell_date = NULL, sell_price = NULL)`.
6. `conn.commit()` → database me pakka save. Trade ID print hota hai.

### (d) Stock sell karna (menu 8 → `sell_stock()`)
1. Trade ID input → trade + stock + investor JOIN karke laata hai.
2. `sell_date` pehle se bhara hai → "already sold" message.
3. `sell_price` = aaj ka price; `pnl = (sell − buy) × quantity`; `return % = sell ÷ buy − 1`.
4. `UPDATE trades SET sell_date, sell_price` → commit.
5. Profit > 0 → "PROFIT BOOKED", 0 → "BREAK-EVEN", warna "LOSS BOOKED".

### (e) Stock analysis (menu 4 → `search_and_analyse()`)
1. Keyword se search (SQL `LIKE`), list me har stock ka last price.
2. Stock ID do → `preprocessing.analyse_stock(id)`:
   - 20-day aur 50-day **moving average** (`rolling(20).mean()`).
   - **RSI(14)**: pichle 14 din ka average gain ÷ average loss → 0–100 number (70+ = overbought, 30− = oversold).
   - 1D/1M/3M/1Y returns, 52-week high/low, volatility (`std × √252`), max drawdown.
   - **Signal**: price > 50-DMA aur 20-DMA > 50-DMA → BULLISH; dono ulta → BEARISH; warna NEUTRAL.
3. `visualizations.plot_stock_analysis(id)` → 3 panel chart: **candlestick** + moving averages, volume bars, RSI → `charts/stock_analysis_<SYMBOL>.png`.

### (f) Ek chart kaise banta hai (example: chart 8, Bar Plot)
1. Menu 12 → `visualization_menu()` → `print_chart_list()` `CHART_MENU` list se numbered list dikhata hai.
2. Aap `8` daalte ho → `run_chart(8)` → `CHART_MENU[7]` ka function `plot_sector_returns_bar()` call.
3. Function `get_sector_aggregates()` (preprocessing) bulata hai:
   - `get_stock_summary()` → har stock ka 1Y return.
   - `groupby('sector_name')` se sector ka average return + trade counts.
4. `plt.subplots()` → figure; `ax.bar(...)` → bars (green = upar, red = neeche); `ax.text(...)` → har bar pe number; title/labels.
5. `save_chart("sector_returns_bar.png", ...)`:
   - `charts/` folder na ho to banata hai,
   - `savefig(dpi=200)` → PNG save,
   - `SHOW_WINDOWS = True` ho to `open_in_viewer()` → PNG Mac ke **Preview** me khulta hai (`open` command, menu ruka nahi rehta),
   - `plt.close('all')` → memory saaf.

**Program kabhi band kyun nahi hota (3 suraksha):**
- Menu wala program khud **koi matplotlib window nahi kholta** — `matplotlib.use("Agg")` (off-screen drawing). Pehle macOS pe chart window ko `Cmd+Q` ya Dock se "Quit" karne pe **poora program** band ho jaata tha, kyunki window aur menu ek hi process the. Ab chart Preview (alag app) me hai.
- Chart 5 (interactive) `open_live_window()` se **alag Python process** me chalta hai (`DV_LIVE_WINDOW=1`). Us window ko Quit karo → sirf wo chhota process band.
- `main.py` me `run_safely()` har option ko `try/except` me chalata hai (error aaye to message, phir menu), aur `safe_input()` `Ctrl+C` ko sirf "cancel" maanta hai. Program **sirf option 0** se band hota hai.

### (g) `--all` / menu 13 (sab charts ek saath)
`generate_all_visualizations()` → `set_show_windows(False)` (windows band) → `CHART_MENU` ke har function ko loop me call → end me windows setting wapas purani. Isliye ye fast hai aur koi popup nahi aata.

### (h) Interactive Explorer (chart 5) andar se
- Data: `get_sector_index()` → rows = date, columns = sector, value = sector index (shuru me 100).
- Har sector ki ek line (`ax.plot`) → `lines` dictionary me save.
- **CheckButtons** (left box): click → `on_check()` → us line ka `set_visible` ulta → `draw_idle()` se redraw. *(= Power BI slicer jaisa filter)*
- **Slider** (neeche): 1–50 din ka **moving average** → `on_slide()` → har line `rolling(window).mean()` se smooth.
- **Hover**: `mpl_connect('motion_notify_event', on_hover)` → mouse line pe → "Sector, date: value (+x%)" box.
- `fig._widgets = (check, slider)` → widgets ka reference rakhta hai, warna Python unhe delete kar deta aur buttons kaam nahi karte.
- Menu se kholne pe ye chart **alag process** me khulta hai (`open_live_window("plot_interactive_explorer")`), isliye window band karne se menu pe koi asar nahi.

### (i) Market Dashboard (menu 14 → `kpi_dashboard()`)
**Sawaal jiska jawab deta hai:** "Market aaj kaisa hai, aur investors paisa bana rahe hain ya nahi?"
1. **Slicers**: sector aur investor type (risk profile) input (0 = All).
2. `preprocessing.get_market_kpis(sector, risk)` → filter lagake numbers: stocks, investors, orders, open positions, invested, current value, unrealised/realised P&L, win rate, stop-loss alerts, market breadth, is mahine vs pichle mahine orders.
3. `market_mood(breadth)` → **BULLISH** (60%+ stocks uptrend me) / **NEUTRAL** (40–60%) / **BEARISH** (40% se kam).
4. Terminal me: **Gauge** (`[#####-----] 63.9%` = kitne stocks 50-day average se upar), **Cards**, **KPI** (▲▼ change, win rate vs 55% target), **Top 5 Gainers & Losers** (`get_top_movers()`). Har number ke neeche `_meaning()` ki "->" line uska simple matlab batati hai.
5. **Drill-down**: Level 1 = sector-wise 1Y return (█ bars, ░ = negative); sector naam type karo → Level 2 = us sector ke stocks.
6. `plot_market_dashboard(sector, risk)` → Power BI page jaisa image: 4 cards + gauge, top movers bar, drill-down bar, monthly orders (is mahina vs pichla highlighted), profit by investor type → `charts/market_dashboard_<sector>_<type>.png`.

### (j) Share Delivery Tracker = Supply Chain Case Study (menu 15)
1. Pehle screen pe kahani: share kharidne ke baad wo **parcel ki tarah** deliver hota hai: Investor → Broker → NSE Mumbai → Clearing Corp → Depository (CDSL/NSDL) → Demat account. Rule: **T+1** (agle trading din).
2. Region list ke saath shehar: North = New Delhi, Lucknow, Jaipur; West = Pune, Ahmedabad; South = Bengaluru, Chennai, Kochi, Hyderabad; East = Kolkata. Region chuno (0 = All).
3. `get_cleaned_deliveries(region)` → deliveries + trades + investors + stocks JOIN; `settle_days` (trading days, weekend nahi gine), `delay_days`, `status`; region filter.
4. Terminal me 4 steps: **STEP 1** delivery KPIs (on-time % gauge, target 95%) → **STEP 2** routes table (shehar → NSE) → **STEP 3** broker report card (grade A/B/C) → **STEP 4** late hone ke reasons → **INVESTOR TAKEAWAY** (3 lines).
5. `plot_supply_chain_dashboard(region)` → 4 rows ka dashboard:
   - Row 1: `_draw_pipeline()` — 6 boxes ka chain diagram (order se demat tak) + "X orders = on time + late + pending".
   - Row 2: `_kpi_card()` × 4 + `_gauge()` (needle = on-time %, blue mark = 95% target).
   - Row 3: route map (`annotate` arrows: investor city → NSE Mumbai; width = orders, colour = on-time %, dot colour = region) + region-wise stacked bar.
   - Row 4: monthly on-time % line + broker report card + "Why were deliveries late?" bar.
6. File: `charts/supply_chain_dashboard_<region>.png`.

### (k) Delivery data kaise bana (`db_setup.seed_deliveries`)
- Har buy trade = ek delivery. Investor ki home state → shehar + region (`INVESTOR_CITIES`), aur `haversine_km()` se NSE Mumbai ki doori (sirf map ke liye).
- Expected date = `next_trading_day(buy_date)` = **T+1** (weekend skip).
- Late hone ka chance broker pe depend: Zerodha 5%, Groww 7%, Upstox 9%, Angel One 12%, ICICI Direct 15% (`BROKER_DELAY_RATE`). Isliye report card me Zerodha sabse upar aata hai.
- Late ho to 4 me se ek reason (`DELAY_REASONS`): investor ne paisa late diya (+1 din), seller ne share nahi diya → auction (+2–3), bank/settlement holiday (+1), demat/KYC mismatch (+2–4).
- Delivery date aaj ke baad aaye → `NULL` (abhi pending). Menu 7 se naya buy karo → `create_delivery()` ek pending delivery bana deta hai.
- Distance se delay nahi hota (share digital hai) — ye bhi ek seekh hai: route map pe door ke shehar bhi on time ho sakte hain.

### (l) Maps (charts 22–25) bina internet ke
- `STATE_COORDS` = har state ka (latitude, longitude). `EXCHANGE_LOCATION` = NSE, Mumbai.
- **Projection** (`_project()`): Equirectangular = seedha lon/lat; Mercator = `y = ln(tan(45° + lat/2))`; Orthographic = globe ka 3D → 2D formula.
- **Tile map** (`STATE_TILES`): har state ek grid square (column, row) rough geography ke hisaab se → `_draw_state_tiles()` colour (choropleth) ya size (cartogram) data se set karta hai.

### (m) Excel export (menu 16 / `--export`)
6 tables `read_sql_query` → `pd.ExcelWriter(engine='openpyxl')` → har table alag sheet → `stock_market_export.xlsx`. Ye file Power BI Desktop me "Get Data → Excel" se load hoti hai.

---

## 4. Database ke 6 tables

| Table | Columns | Matlab |
|---|---|---|
| `sectors` | sector_id, sector_name | 6 sectors |
| `stocks` | stock_id, symbol, company_name, sector_id, hq_state | 36 companies |
| `price_history` | price_id, stock_id, trade_date, open, high, low, close, volume | Har stock ka har din ka price (9,000 rows) |
| `investors` | investor_id, name, risk_profile, home_state, broker | 90 investors |
| `trades` | trade_id, stock_id, investor_id, buy_date, buy_price, quantity, stop_loss, sell_date, sell_price | Har buy/sell ka record |
| `deliveries` | delivery_id, trade_id, broker, from_city, region, distance_km, order_date, expected_date, delivery_date, delay_reason | Har buy order ke shares ki demat delivery (case study) |

Relations (star schema): `sectors` → `stocks`; `stocks` → `price_history`, `trades`; `investors` → `trades`; `trades` → `deliveries`.

---

## 5. Setup + har terminal command ka matlab

> macOS/Linux me `python3`, Windows me `python` likho. Har command project folder ke andar chalani hai.

### 5.1 Pehli baar setup

```bash
cd "Data-Visualisation-Project-"
```
**Matlab:** terminal ko project folder me le jao (`cd` = change directory).

```bash
python3 -m venv ~/.venvs/dv-lms
```
**Matlab:** `~/.venvs/dv-lms` folder me ek **virtual environment** (alag Python box) banao, taaki is project ki libraries baaki system se mix na hon. `-m venv` = Python ka built-in venv module chalao.

```bash
source ~/.venvs/dv-lms/bin/activate
```
**Matlab:** us virtual environment ko **chalu** karo (macOS/Linux). Iske baad prompt ke aage `(dv-lms)` dikhega. Windows pe venv project folder me bana sakte ho: `python -m venv venv` phir `venv\Scripts\activate`.

> venv project folder ke bahar kyun? Is Mac pe project folder ke andar venv banane par macOS security library files block kar deti hai (Section 0 ka note dekho).

```bash
pip install -r requirements.txt
```
**Matlab:** `pip` = Python ka package installer. `-r requirements.txt` = is file me likhi saari libraries (pandas, matplotlib, seaborn...) ek saath install karo. Sirf pehli baar (ya nayi library add hone pe) chahiye.

### 5.2 Project chalana

```bash
python3 main.py
```
**Matlab:** program start karo → **main menu** khulega. Number type karke Enter dabao. Pehli baar `stock_market.db` na ho to apne-aap ban jaata hai.

### 5.3 Shortcut flags (menu khole bina direct kaam)

| Command | Matlab |
|---|---|
| `python3 main.py --all` | Saare 26 charts bana ke `charts/` me save karo, koi window nahi khulegi, phir band. Sabse fast tareeka sab output banane ka. |
| `python3 main.py --list` | Saare charts ki numbered list (unit-wise) dikhao. |
| `python3 main.py --chart 7` | Sirf chart number 7 banao aur Preview me dikhao (number `--list` se dekho). |
| `python3 main.py --report` | Data Cleaning & Aggregation report terminal me print karo. |
| `python3 main.py --export` | `stock_market_export.xlsx` banao (Power BI ke liye). |
| `python3 main.py --reset-db` | `stock_market.db` delete karke **fresh sample data** ke saath naya banao. ⚠️ Aapke add kiye stocks/investors/trades chale jaayenge. |
| `python3 main.py --help` | Saare flags ki list aur unka matlab dikhao. |

### 5.4 Files ko alag se chalana (optional)

```bash
python3 db_setup.py
```
**Matlab:** database ko **zero se dobara** banao (same as `--reset-db`).

```bash
python3 preprocessing.py
```
**Matlab:** cleaning module ka chhota test — cleaned trades ki pehli rows aur sector summary print karta hai.

### 5.5 Kaam khatam

```bash
deactivate
```
**Matlab:** virtual environment band karo (normal terminal pe wapas).

### 5.6 Charts dekhna

```bash
open charts
```
**Matlab:** macOS pe `charts/` folder Finder me kholo (Windows: `start charts`, Linux: `xdg-open charts`).

### 5.7 (Optional) Database ko seedha dekhna

```bash
sqlite3 stock_market.db "SELECT * FROM stocks LIMIT 5;"
```
**Matlab:** `sqlite3` tool se database me SQL query chalao — yahan stocks table ki pehli 5 rows.

---

## 6. Main Menu (0–16) ka matlab

| # | Option | Kya hota hai |
|---|---|---|
| 1 | View Market Watchlist | Saare stocks: ID, symbol, company, sector, aaj ka price, **1D %** aur **1Y %** change, HQ state. Neeche market breadth (kitne up, kitne down) |
| 2 | Add New Stock | Symbol, company, sector, aaj ka price, HQ state pooch ke stock add karta hai. Saath me 1 saal ki simulated price history bhi banti hai taaki charts me dikhe |
| 3 | Remove / Delist Stock | Stock ko poora hata deta hai (prices + trades ke saath) — agar kisi investor ki **open position** hai to mana kar deta hai |
| 4 | Search & Analyse a Stock | Symbol / company / sector ka keyword → matching stocks. Phir stock ID do → **returns, 52-week range, volatility, moving averages, RSI, BULLISH/BEARISH signal** + candlestick chart |
| 5 | View Investor Directory | Saare investors: ID, naam, risk profile, home state, trades, total P&L |
| 6 | Add New Investor | Naya investor register (naam, risk profile 1–4, home state, broker) |
| 7 | Buy a Stock | Investor ID + Stock ID + quantity → trade banta hai, **buy price = aaj ka price**, **stop-loss = 8% neeche** apne-aap, aur share **delivery T+1** shuru (option 15 me dikhti hai) |
| 8 | Sell a Stock | Trade ID → sell price = aaj ka price, **profit/loss = (sell − buy) × qty** aur return % |
| 9 | View Stop-Loss Alerts | Wo open positions jinka price stop-loss se neeche gir gaya + unka loss |
| 10 | Investor Portfolio & Trade History | Ek investor ke saare trades, open positions ka unrealised P&L, closed trades ka realised P&L, win rate |
| 11 | Data Cleaning & Aggregation Report | **Unit 2**: raw table size, missing values (price gaps + open positions), cleaning steps, sector × status pivot, summary statistics |
| 12 | Data Visualization Menu | 26 charts ka unit-wise menu (Section 7) |
| 13 | Generate All Charts | Saare charts ek saath `charts/` me save (no windows) |
| 14 | Market Dashboard | **Unit 6 (Power BI concepts)**: Slicer (sector, investor type) → **Market Mood** (Bullish/Neutral/Bearish) + Gauge → Cards (invested, value, profit) → KPI (orders ▲▼, win rate vs 55%) → Top 5 Gainers/Losers → Drill-down (sector → stocks). Har number ke saath ek line ka matlab + dashboard image |
| 15 | Share Delivery Tracker (Supply Chain case study) | Kharide hue shares demat account tak T+1 me pahunche ya nahi: region filter (investor kahan rehta hai) → delivery KPIs → routes (shehar → NSE) → broker report card → late hone ke reasons → takeaway + dashboard image |
| 16 | Export for Power BI | `stock_market_export.xlsx` (6 sheets) |
| 0 | Exit | Program band |

---

## 7. Visualization Menu (1–26) ka matlab

Har chart `charts/` me save hota hai. Menu se kholo to Preview me khulta hai (zoom: `Cmd +` / `Cmd -`); menu turant wapas aa jaata hai.

### Unit 1 — Introduction
| # | Chart (file) | Kya dikhata hai / kyun |
|---|---|---|
| 1 | Design Principles (`design_principles_comparison.png`) | Left: kharab 3D colourful bar chart (distortion, clutter). Right: wahi data (sector-wise traded value) clean horizontal bar me. **Design principles + value of visualization** |
| 2 | Data Graphic Types (`data_graphic_types.png`) | **Categorical** (bar: Profit/Loss/Open trades), **Time series** (line: market index), **Statistical** (box plot: trade return % by risk profile) |

### Unit 2 — Pre-processing & Aesthetics
| # | Chart (file) | Kya dikhata hai / kyun |
|---|---|---|
| 3 | Pairplot (`stock_pairplot.png`) | 36 stocks ke 4 metrics (1Y return, volatility, max drawdown, beta) ka har pair scatter + diagonal pe KDE, colour = sector |
| 4 | Heatmap (`return_heatmap.png`) | Sector × Month average return %; **diverging** colour (green = upar, red = neeche, 0 = peela) |
| 5 | Interactive Explorer (`interactive_explorer_snapshot.png`) | **Interactive visualization** (bina HTML ke): line pe mouse → tooltip; left checkboxes se sector on/off (slicer/filter); neeche slider se moving average. *Menu se kholne pe hi interactive hai; `--all` sirf snapshot save karta hai* |
| 6 | Graphical Perception (`graphical_perception.png`) | Sector-wise trades 5 tareeke se: position, length, angle, area, colour. **Cleveland & McGill** — position/length sabse accurate, area/colour sabse kam |
| 7 | Grammar of Graphics (`grammar_of_graphics.png`) | Row 1: **risk vs return** chart layer-by-layer — Layer 1 (data + aes x,y + geom_point) → Layer 2 (+ colour = sector, size = volume) → Layer 3 (+ geom_smooth). Row 2: **Data types & scales** — nominal → qualitative colours, ordinal (risk profile) → sequential, continuous (return %) → diverging (centre = 0% break-even) |

Violin plot chart 12 me hai; Data Cleaning & Aggregation main menu option 11 me.

### Unit 3 — Visualization Design
| # | Chart (file) | Kya dikhata hai |
|---|---|---|
| 8 | Bar Plot (`sector_returns_bar.png`) | Sector-wise average 1Y return (green upar, red neeche, bars zero se shuru) |
| 9 | Horizontal Bar (`most_traded_stocks.png`) | Top 10 sabse zyada trade hone wale stocks + traded value |
| 10 | Cleveland Dot Plot (`dot_stock_returns.png`) | Saare 36 stocks ka 1Y return — 36 bars ki jagah clean dots |
| 11 | Grouped & Stacked Bars (`trade_outcome_breakdown.png`) | Sector × outcome (Profit Booked / Loss Booked / Open) dono tareeke se |
| 12 | Distributions (`return_distributions.png`) | Daily returns ka **single distribution** (histogram + density), **multiple distributions** (6 sectors overlaid KDE), **violin plot** (wider = riskier sector) |
| 13 | ECDF, Q-Q, Skew (`statistical_diagnostics.png`) | ECDF of trade size; Normal **Q-Q plot** of daily returns (ends mud jaate hain = **fat tails**); **highly skewed** trade size vs **log10** transform (skewness number title me) |

Heat map (amounts) = chart 4.

### Unit 4 — Advanced Visualization Design
| # | Chart (file) | Kya dikhata hai |
|---|---|---|
| 14 | Vertical vs Horizontal (`vertical_vs_horizontal.png`) | Monthly stock returns: **vertical axis** = box plot + jittered strip chart; **horizontal axis** = ridgeline plot |
| 15 | Proportions (`proportions.png`) | Sector share of traded value ko **pie** vs **side-by-side bars** vs **stacked bar** + **stacked densities** (holding days ke hisaab se sector mix) — "a case for pie charts" |
| 16 | Parts of Total (`parts_of_total.png`) | Har sector ke trade returns grey total ke upar alag panel me — **proportions separately as parts of the total** |
| 17 | Nested Proportions (`nested_proportions.png`) | Treemap (sector → stock, area = traded value) + nested donut (sector → outcome) |
| 18 | Associations (`associations_and_pca.png`) | **Scatter** (beta vs 1Y return, Pearson r), **Correlogram** (6 sectors ke daily returns kitne saath chalte hain — diversification), **PCA** (har stock ke 250 daily returns → 2 numbers; same sector ke stocks ek saath cluster) |
| 19 | Paired Data (`paired_slope_chart.png`) | Slope chart: har sector ka return pehle 6 mahine vs aakhri 6 mahine |

### Unit 5 — Time Series, Trends & Geospatial
| # | Chart (file) | Kya dikhata hai |
|---|---|---|
| 20 | Time Series & Trends (`time_series_and_trends.png`) | Individual series (market index); multiple series (6 sector indices); **smoothing** (20-day & 50-day moving average + LOESS); **defined functional form** (linear & exponential fit with R² aur yearly growth rate) |
| 21 | Advanced TS (`advanced_time_series.png`) | **Dose–response** curve (holding days → return %); **two response variables** (index level + volatility, dual axis); **detrending** (actual − trend); **decomposition** (trend + seasonal + residual, period = 21 trading days ≈ 1 mahina) |
| 22 | Projections (`map_projections.png`) | Investors ke home states 3 projections me: Equirectangular, Mercator, Orthographic — grid lines ka shape badalta hai |
| 23 | Layers (`map_layers.png`) | Layer 1 base map → +Layer 2 data (investors) → +Layer 3 NSE Mumbai & order flow (width = traded value) |
| 24 | Choropleth (`choropleth_map.png`) | State tiles colour se: raw investors vs **normalised** traded value per investor |
| 25 | Cartograms (`cartogram.png`) | Proportional symbol map + tile cartogram (tile size ∝ traded value) |

> Note: Choropleth/cartogram **tile-grid map** pe bane hain (har state ek square, rough geography ke hisaab se). Isse internet ya shapefile download ki zarurat nahi padti, project offline chalta hai.

### Case Study
| # | Chart (file) | Kya dikhata hai |
|---|---|---|
| 26 | Share Delivery Tracker (`supply_chain_dashboard_all.png`) | 6-step chain diagram (order → demat), KPI cards, on-time (T+1) gauge, **route map** (shehar → NSE Mumbai), status by region, monthly on-time trend, broker report card, delay reasons. Region filter ke liye main menu option 15 (file `supply_chain_dashboard_<region>.png`) |

### Extra (menu 4 aur 14 se)
| Chart (file) | Kya dikhata hai |
|---|---|
| Market Dashboard (`market_dashboard_<sector>_<type>.png`) | Menu 14: cards, market-mood gauge, top gainers/losers, sector drill-down, monthly orders KPI, profit by investor type |
| Stock Analysis (`stock_analysis_<SYMBOL>.png`) | Pichle 120 din ka **candlestick** (green = us din price badha, red = gira), 20/50-day moving averages, volume bars, RSI panel (70+ overbought, 30− oversold) |

---

## 8. Syllabus → Project Mapping (har topic kahan hai)

### Unit 1: Introduction to Data Visualization
| Syllabus topic | Project me kahan |
|---|---|
| Importance of DV in Data Science & Business | Chart 1 (bad vs good), Market Dashboard (menu 14), stock analysis (menu 4) — investor decision lene me help; Section 12 viva |
| Data for Graphics | `preprocessing.py` → cleaned DataFrames; Section 4 tables |
| Design Principles | Chart 1; consistent sector colours sab charts me; profit green / loss red; labels/units har chart pe |
| Value for Visualization | Chart 1 (same data, clear vs confusing) |
| Categorical, Time Series, Statistical Graphics | Chart 2 |
| Introduction to Visualization Tools | Section 1 tools table; Power BI (`POWERBI_GUIDE.md`) |

### Unit 2: Data Pre-processing and Aesthetics
| Syllabus topic | Project me kahan |
|---|---|
| Data Cleaning and Aggregation | Menu 11 / `--report`; `preprocessing.py` (forward fill, returns, P&L) |
| Pairplots | Chart 3 |
| Violin Plots | Chart 12 (3rd panel) |
| Heatmaps | Chart 4, correlogram in chart 18 |
| Interactive Visualizations | Chart 5 (hover, checkbox filter, slider) |
| Graphical Perception Theory | Chart 6 |
| Grammar of Graphics (Layering, Aesthetics, Geometries) | Chart 7 row 1 |
| Aesthetics and types of data | Chart 7 row 2 |
| Scales map data values onto aesthetics | Chart 7 row 2 (qualitative / sequential / diverging), chart 4 colourbar |

### Unit 3: Visualization Design
| Syllabus topic | Project me kahan |
|---|---|
| Bar plots | Charts 8, 9 |
| Grouped and stacked bars | Chart 11 |
| Dot plots and heat maps | Chart 10, chart 4 |
| Histograms and density plots | Chart 12 |
| Visualizing a single distribution | Chart 12 panel 1 |
| Multiple distributions at the same time | Chart 12 panel 2 |
| ECDF | Chart 13 panel 1 |
| Highly skewed distributions | Chart 13 panels 3–4 (log transform) |
| Quantile–quantile plots | Chart 13 panel 2 |

### Unit 4: Advanced Visualization Design
| Syllabus topic | Project me kahan |
|---|---|
| Distributions along the vertical axis | Chart 14 left (box + strip) |
| Distributions along the horizontal axis | Chart 14 right (ridgeline) |
| A case for pie charts | Chart 15 |
| Side-by-side bars, stacked bars, stacked densities | Chart 15 |
| Proportions separately as parts of the total | Chart 16 |
| Nested proportions | Chart 17 |
| Scatter plots | Chart 18 panel 1 |
| Correlograms | Chart 18 panel 2 |
| Dimension reduction | Chart 18 panel 3 (PCA) |
| Paired data | Chart 19 |

### Unit 5: Time Series, Trends and Geospatial Data
| Syllabus topic | Project me kahan |
|---|---|
| Individual time series | Chart 20 panel 1 |
| Multiple time series | Chart 20 panel 2 |
| Dose–response curves | Chart 21 panel 1 |
| Time series of two or more response variables | Chart 21 panel 2 |
| Smoothing | Chart 20 panel 3 (moving averages, LOESS) |
| Trend with defined functional form | Chart 20 panel 4 |
| Detrending | Chart 21 panel 3 |
| Time-series decomposition | Chart 21 panel 4 |
| Projections | Chart 22 |
| Layers | Chart 23 |
| Choropleth mapping | Chart 24 |
| Cartograms | Chart 25 |

### Unit 6: Power BI for Business Intelligence & Dashboarding
| Syllabus topic | Project me kahan |
|---|---|
| Components: Desktop, Service, Gateway | `POWERBI_GUIDE.md` §1 |
| Data loading from Excel, SQL, Web APIs | Menu 16 / `--export` (Excel); `POWERBI_GUIDE.md` §2 (Excel, SQLite ODBC, Web) |
| Power Query for data shaping | `POWERBI_GUIDE.md` §3 |
| Cards, KPIs, Gauges, Slicers, Drill-down | Menu 14 Market Dashboard (terminal + image); chart 26 (cards + gauge); `POWERBI_GUIDE.md` §4 |
| DAX measures | `POWERBI_GUIDE.md` §5 |
| Power BI Embedded, Row-Level Security | `POWERBI_GUIDE.md` §6 |

### Self-study Case Study
| Syllabus requirement | Project me kahan |
|---|---|
| Supply Chain & Logistics Dashboard | Menu 15 Share Delivery Tracker, chart 26 |
| Dataset: shipment and delivery logs | `deliveries` table (har buy order = ek shipment of shares, 300 rows) |
| Tools: Power BI or Dash | Python dashboard (Dash web-based hai, isliye terminal project me matplotlib use kiya); `deliveries` sheet Excel me bhi hai → Power BI me bana sakte ho (`POWERBI_GUIDE.md` §7) |
| Route mapping | Chart 26 route map (investor city → NSE Mumbai) + terminal routes table + 6-step chain diagram |
| Delivery status KPIs | Cards, on-time (T+1) gauge, status %, broker report card |
| Filtering by region | Menu 15 region filter (investor ka region) |

---

## 9. Power BI unit project me kaise cover hai

Power BI ek alag Windows software hai, Python ke andar nahi chalta. Isliye project ye karta hai:
1. **Data ready karta hai** → `stock_market_export.xlsx` (sectors, stocks, investors, price_history, trades, deliveries).
2. **Wahi concepts terminal me dikhata hai** → menu 14 Market Dashboard: Slicer, Card, KPI, Gauge, Drill-down (+ Power BI page jaisi image).
3. **Step-by-step guide** → `POWERBI_GUIDE.md`: Get Data, Power Query, relationships, visuals, DAX measures, RLS, Embedded.

---

## 10. Case Study: Supply Chain = Share Delivery Tracker

**Ye option kyun hai?** Syllabus ki self-study case study **Supply Chain & Logistics Dashboard** maangti hai (shipment logs, route mapping, delivery KPIs, region filter). Stock market ki bhi apni supply chain hoti hai — **shares ki delivery**. Isliye case study seedha stock market ki hai.

**Story (simple shabdon me):** Jab aap Zerodha/Groww jaise app se share **kharidte** ho, to share turant aapke paas nahi aata. Wo ek parcel ki tarah is chain se guzarta hai:

```
Investor ──► Broker ──► NSE Mumbai ──► Clearing Corp ──► Depository ──► Demat account
(order)     (Zerodha)   (buyer+seller   (NSE Clearing     (CDSL/NSDL     (shares aa gaye
                         match)          paise+share)       share move)    = DELIVERED)
```

India me rule hai **T+1**: order ke **agle trading din** shares demat account me aa jaane chahiye. Usse late = **late delivery**.

**Parcel ↔ Stock market (teacher ko aise samjhao):**
| Logistics shabd | Is project me |
|---|---|
| Shipment | Ek buy order (`deliveries` table ki ek row) |
| Courier company | Broker (Zerodha, Groww, Upstox, Angel One, ICICI Direct) |
| Route | Investor ka shehar → NSE Mumbai |
| Delivered on time | Shares T+1 pe demat me aa gaye |
| Region | Investor kahan rehta hai (North / West / South / East) |

**Calculations (`preprocessing.get_cleaned_deliveries`):**
- `settle_days` = order date se delivery (ya aaj) tak **trading days** (Sat-Sun nahi gine) → ideal = 1
- `delay_days` = expected (T+1) se delivery (ya aaj) tak, minimum 0
- `status` = Delivered On-Time (T+1) / Delivered Late / Pending (in settlement) / Pending - Delayed

**Menu 15 me kya milta hai:**
1. Region chuno (= **filtering by region**) — har region ke saamne uske shehar likhe hain.
2. **STEP 1 KPIs**: orders, shares delivered, on-time % gauge (target 95%), late/pending, average days.
3. **STEP 2 Routes**: har shehar → NSE: km, orders, on-time %, late (= **route mapping**).
4. **STEP 3 Broker Report Card**: har broker ka on-time % aur grade **A** (95%+) / **B** (88–95%) / **C** (88% se kam).
5. **STEP 4 Why late?**: funds late, seller short delivery → auction, holiday, KYC mismatch.
6. **Investor Takeaway**: "Grade A broker chuno, paise time pe do, KYC sahi rakho."
7. Dashboard PNG (`charts/supply_chain_dashboard_<region>.png`) — upar 6-box chain diagram, neeche cards, gauge, map, broker report card.

**Live demo idea (viva me):** Menu 7 se ek share kharido → message aata hai "delivery on <kal ki date> (T+1)" → menu 15 kholo → wo order "Pending (in settlement)" me dikhega.

---

## 11. Stock market ke zaroori shabd (jo project me use hue)

| Shabd | Simple matlab |
|---|---|
| **Stock / Share** | Company ka chhota hissa. Symbol = short naam (TCS, HDFCBANK) |
| **NSE** | National Stock Exchange (Mumbai) — jahan shares kharide-beche jaate hain |
| **Sector** | Ek jaisi companies ka group (IT, Banking...) |
| **Return %** | Price kitna % badha/gira. Daily return = aaj vs kal |
| **Volatility** | Price kitna upar-neeche hota hai (risk). Daily returns ka std × √252 (saal ke trading days) |
| **Max Drawdown** | Sabse upar wale point se sabse badi giravat % |
| **Beta** | Market 1% chale to stock kitna chalta hai. Beta > 1 = market se zyada jhoolta hai |
| **Moving Average (20-DMA, 50-DMA)** | Pichle 20/50 din ke closing price ka average — trend dekhne ke liye |
| **RSI** | 0–100 number: 70+ = bahut tezi (overbought), 30− = bahut mandi (oversold) |
| **Stop-loss** | Pehle se tay price jahan loss rokne ke liye share bech dete hain (yahan buy price se 8% neeche) |
| **P&L** | Profit & Loss. Realised = bech diya; Unrealised = abhi open position ka kaagzi profit/loss |
| **Market Breadth / Mood** | Kitne % stocks apne 50-day average se upar hain — 60%+ = Bullish, 40% se kam = Bearish |
| **Top Gainers / Losers** | Aaj sabse zyada badhne / girne wale stocks |
| **Broker** | Company jiske app se aap share kharidte-bechte ho (Zerodha, Groww...) |
| **Demat account** | Bank account jaisa, par paise ki jagah shares rakhta hai |
| **T+1 settlement** | Order (din T) ke agle trading din shares demat me aa jaate hain |
| **Depository (CDSL / NSDL)** | Sabke demat accounts sambhalne wali sanstha |
| **Candlestick** | Ek din ka Open, High, Low, Close ek "candle" me. Green = close > open |

---

## 12. Viva Questions & Answers

**Q1. Project kis cheez ke baare me hai?**
Stock market (NSE ke 36 stocks) ka data manage karta hai — stocks, investors, buy/sell trades, profit/loss — aur usse 26 visualizations banata hai jo DV syllabus ke har unit ko cover karte hain. Pure terminal project hai.

**Q2. Data kahan se aaya? Asli hai?**
Nahi, simulated hai. `db_setup.py` har stock ka 1 saal ka price random walk se banata hai (market + sector + company move, fixed seed 42). Investor naam `faker` se. Isliye har baar same data aur koi internet/API nahi chahiye.

**Q3. Data cleaning me kya kiya?**
~1% closing prices missing the (data feed gap) → har stock ke andar forward-fill kiya. Text dates ko datetime banaya, daily return nikala, NULL sell_date ko "open position" maana aur aaj ke price pe value kiya, `holding_days`, `pnl`, `return_pct`, status labels banaye, 4 tables JOIN kiye. Menu 11 sab dikhata hai.

**Q4. Forward fill hi kyun, average kyun nahi?**
Stock price ek time series hai — agar aaj ka price nahi aaya to sabse sahi andaza kal ka price hai. Average lene se future ka data past me aa jaata (galat).

**Q5. Graphical perception theory kya hai?**
Cleveland & McGill ke hisaab se insaan position aur length sabse sahi padhta hai, angle aur area kam sahi, colour sabse kam. Chart 6 me same data 5 encodings me hai.

**Q6. Grammar of Graphics kya hai?**
Chart = data + aesthetics (x, y, colour, size) + geometries (point, line, bar) + scales + layers. Chart 7 me risk-return chart layer-by-layer bana ke dikhaya hai.

**Q7. Q-Q plot me kya dikha?**
Daily returns ke dono ends red line se door mud jaate hain = **fat tails** — matlab bade crash/jump normal distribution se zyada baar aate hain. Isliye stock returns ko "normal" maan lena risky hai.

**Q8. Skewed data ko kaise handle kiya?**
Trade size right-skewed hai (bahut chhote orders, kuch bahut bade). `log10` transform kiya — chart 13 me skewness ~3.6 se ~0 ke paas aa jaati hai.

**Q9. PCA kyun aur kya mila?**
Har stock ke 250 daily returns ko 2 numbers (PC1, PC2) me compress kiya taaki 2D me dikh sake. Result: same sector ke stocks ek saath cluster karte hain — kyunki unke price ek jaise move karte hain.

**Q10. Correlogram se investor ko kya fayda?**
Agar do sectors ka correlation kam hai to dono me paisa lagane se risk kam hota hai (diversification). Chart 18 panel 2.

**Q11. Smoothing aur detrending me farak?**
Smoothing noise hata ke trend dikhata hai (moving average, LOESS). Detrending trend hata ke short-term ups/downs dikhata hai (actual − trend).

**Q12. Moving average aur signal kaise kaam karta hai?**
20-DMA = pichle 20 din ka average. Price aur 20-DMA dono 50-DMA ke upar → BULLISH (uptrend). Dono neeche → BEARISH. Menu 4.

**Q13. Choropleth me normalise kyun kiya?**
Jis state me zyada investors hain wahan traded value automatically zyada hogi. Traded value per investor se fair comparison hota hai.

**Q14. Interactive visualization bina HTML ke kaise?**
Matplotlib window ke widgets: `CheckButtons` (sector filter), `Slider` (moving average), `motion_notify_event` (hover tooltip). Chart 5.

**Q15. Profit/loss aur stop-loss kaise calculate hota hai?**
Buy pe stop-loss = buy price × 0.92. Sell pe P&L = (sell − buy) × quantity. Open position ka unrealised P&L aaj ke price se.

**Q16. Supply chain case study stock market project me kyun?**
Syllabus ki requirement hai. Stock market ki apni supply chain hai: kharide hue shares investor → broker → NSE → clearing → depository → demat account tak T+1 me "deliver" hote hain. Humne har buy order ko ek shipment maana, broker ko courier, aur on-time delivery %, route map, broker report card aur region filter banaya.

**Q17. T+1 kya hai aur late kyun hota hai?**
Order ke agle trading din shares demat me aane chahiye. Late hone ke reasons: investor ne paisa late diya, seller ne share nahi diye (auction), bank holiday, ya demat/KYC details galat.

**Q18. Market Dashboard me Market Mood kaise nikala?**
Breadth = kitne % stocks apne 50-day average se upar hain. 60%+ = Bullish, 40–60% = Neutral, 40% se kam = Bearish. Ye Power BI ke Gauge visual jaisa dikhaya hai.

**Q19. Demo ke beech program band kyun nahi hota?**
Menu process khud koi GUI window nahi kholta (matplotlib `Agg` backend); charts Preview app me khulte hain aur interactive chart alag process me. Har option `try/except` me chalta hai, aur `Ctrl+C` sirf current kaam cancel karta hai. Sirf option 0 se program band hota hai.

**Q20. Power BI ka role?**
Business users ke liye dashboard. Project Excel export deta hai, aur guide me Power Query, DAX, RLS steps hain.

---

## 13. Problem aaye to (Troubleshooting)

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'pandas'` | venv activate karo (`source ~/.venvs/dv-lms/bin/activate`) aur `pip install -r requirements.txt` chalao |
| `library load disallowed by system policy` | venv project folder ke andar bana hai → macOS block karta hai. `rm -rf venv`, phir venv `~/.venvs/dv-lms` me banao (Section 0) |
| venv toot gaya / python nahi mil raha | `rm -rf ~/.venvs/dv-lms`, phir Section 0 ke Step 4–6 dobara |
| Chart khul nahi raha | `--all` mode charts nahi kholta (by design). Menu 12 ya `--chart N` se kholo, ya `open charts` |
| Chart ke baad program band ho gaya (purana version) | Naye version me ye fix hai: charts Preview me khulte hain aur menu kabhi band nahi hota. Program dobara start karo: `python3 main.py` |
| Galti se `Ctrl+C` dab gaya | Kuch nahi hoga — "cancelled" message aayega aur menu chalta rahega. Band karna ho to `0` |
| Data ajeeb lag raha / kharab ho gaya | `python3 main.py --reset-db` (⚠️ apna added data jayega) |
| Excel export error | `openpyxl` install hai check karo; Excel me file khuli ho to band karo |
| "Symbol already exists" | Wo symbol pehle se watchlist me hai — option 1 me dekho |

# 📘 Project Guide (Hinglish) — Engineering College Library LMS
### Data Visualization Course Project · Pure Terminal (CLI) Project

Is ek file me sab kuch hai: project me **kya hai**, **kaise chalta hai**, **har terminal command ka matlab**, **har menu option ka matlab**, aur **syllabus ka har topic project me kahan hai**.

---

## 📑 Table of Contents
1. [Project kya hai?](#1-project-kya-hai)
2. [Project me kya-kya hai (files & folders)](#2-project-me-kya-kya-hai-files--folders)
3. [Project kaise chalta hai (data flow)](#3-project-kaise-chalta-hai-data-flow)
4. [Database ke 5 tables](#4-database-ke-5-tables)
5. [Setup + har terminal command ka matlab](#5-setup--har-terminal-command-ka-matlab)
6. [Main Menu (0–16) ka matlab](#6-main-menu-016-ka-matlab)
7. [Visualization Menu (1–26) ka matlab](#7-visualization-menu-126-ka-matlab)
8. [Syllabus → Project Mapping (har topic kahan hai)](#8-syllabus--project-mapping-har-topic-kahan-hai)
9. [Power BI unit project me kaise cover hai](#9-power-bi-unit-project-me-kaise-cover-hai)
10. [Case Study: Supply Chain & Logistics Dashboard](#10-case-study-supply-chain--logistics-dashboard)
11. [Viva Questions & Answers](#11-viva-questions--answers)
12. [Problem aaye to (Troubleshooting)](#12-problem-aaye-to-troubleshooting)

---

## 1. Project kya hai?

Ye ek **Engineering College Library Management System (LMS)** hai jo **sirf terminal (command line) me chalta hai** — koi website, HTML page ya frontend nahi hai.

Do kaam karta hai:
1. **Library ka kaam** — books add/remove, students add, book issue/return, fine (₹5/din late), overdue list.
2. **Data Visualization** — library ke data se **26 charts** banata hai jo syllabus ke **Unit 1 se Unit 5** aur **Case Study** ke har topic ko cover karte hain. Charts `charts/` folder me PNG image ban ke save hote hain aur (menu mode me) ek matplotlib window me khulte hain.

Plus:
- **Power BI** ke liye data ko `library_export.xlsx` me export karta hai (Unit 6).
- Terminal me hi **KPI Cards, Gauge, Slicer, Drill-down** dikhata hai (Power BI jaisa).

**Data (sample, fake but realistic):**
| Cheez | Kitna |
|---|---|
| Departments | 6 — Computer Science, AIML, Mechanical, Civil, Electronics, E&TC |
| Books | 54 (har department ki 9 standard textbooks) |
| Students | 90 (Year 1–4, India ke 10 states se) |
| Transactions (loans) | 280 (pichle 12 mahine) |
| Shipments (case study) | 160 (publishers se campus tak book delivery) |

**Tools used (sab Python libraries):**
| Library | Kis kaam ke liye |
|---|---|
| `sqlite3` | Database (Python ke andar hi aata hai) |
| `pandas`, `numpy` | Data cleaning, aggregation, pivot tables |
| `matplotlib` | Saare charts ka base + interactive window (hover, checkbox, slider) |
| `seaborn` | Pairplot, violin, heatmap, KDE, ECDF jaise statistical charts |
| `scipy` | Q-Q plot, KDE, skewness, correlation |
| `statsmodels` | LOESS smoothing, time-series decomposition |
| `scikit-learn` | PCA (dimension reduction) |
| `squarify` | Treemap |
| `faker` | Fake Indian student names banane ke liye |
| `openpyxl` | Excel file likhne ke liye (Power BI export) |

---

## 2. Project me kya-kya hai (files & folders)

```
Data-Visualisation-Project-/
├── main.py              # 🎮 Program yahin se start hota hai: menu, library operations, KPI, case study, flags
├── db_setup.py          # 🗄️ Database banata hai: 5 tables + sample data (students, books, loans, shipments)
├── preprocessing.py     # ⚙️ Data cleaning + aggregation: dates, days_kept, overdue, fine, KPIs, shipments
├── visualizations.py    # 🎨 Saare 26 charts (unit-wise) + CHART_MENU list
├── library.db           # 💾 SQLite database file (asli data yahan store hota hai)
├── library_export.xlsx  # 📊 Power BI ke liye Excel (5 sheets)
├── requirements.txt     # 📦 Kaunsi Python libraries install karni hain
├── POWERBI_GUIDE.md     # 📑 Power BI Desktop me dashboard banane ka step-by-step guide (Unit 6)
├── PROJECT_GUIDE.md     # 📘 Ye file
├── README.md            # Short intro
├── .gitignore           # Git ko batata hai venv/ aur __pycache__/ ignore karo
└── charts/              # 🖼️ Saare generated PNG charts yahan save hote hain
```

### Har file ka kaam (detail me)

**`main.py`** — Entry point.
- `check_db()` → agar `library.db` nahi hai to bana deta hai; agar `shipments` table nahi hai to sirf wo add kar deta hai (purana data safe).
- Library functions: `view_books`, `add_book`, `remove_book`, `search_books`, `view_students`, `add_student`, `issue_book`, `return_book`, `view_overdue_books`, `student_history`.
- `export_for_power_bi()` → 5 tables ko Excel me likhta hai.
- `kpi_dashboard()` → terminal me Power BI jaisa Cards/KPI/Gauge/Slicer/Drill-down.
- `supply_chain_case_study()` → region filter + delivery KPIs + routes table + dashboard chart.
- `visualization_menu()` → 26 charts unit-wise.
- `parse_args()` → command-line flags (`--all`, `--chart`, etc.).

**`db_setup.py`** — Database builder.
- `init_db()` → purane tables delete karke 5 naye tables banata hai.
- `seed_db()` → departments, 90 students, 54 books, 280 loans, aur shipments daalta hai.
- `seed_shipments()` / `ensure_shipments()` → case-study ka shipment log.
- `haversine_km()` → do lat/long points ke beech ki doori (km) nikalta hai.

**`preprocessing.py`** — Data cleaning & aggregation (Unit 2).
- `get_cleaned_transactions()` → 4 tables JOIN karke ek saaf table: `days_kept`, `overdue_days`, `effective_fine`, `status`.
- `get_department_aggregates()`, `get_author_aggregates()`, `get_monthly_matrix()`, `get_monthly_timeseries()` → group-by / pivot.
- `get_student_summary()`, `get_student_feature_matrix()` → har student ki ek row (PCA, scatter, pairplot ke liye).
- `get_state_geospatial_summary()` → state-wise students aur loans (maps ke liye).
- `print_cleaning_report()` → terminal me cleaning ka report.
- `get_library_kpis()` → KPI numbers (slicer filters ke saath).
- `get_cleaned_shipments()` → transit days, delay, delivery status.

**`visualizations.py`** — Charts.
- Upar common settings: colours (har department ka fixed colour), `save_chart()` helper.
- Phir sections: **Unit 1 → Unit 2 → Unit 3 → Unit 4 → Unit 5 → Case Study**.
- End me `CHART_MENU` list (menu number → chart function) aur `generate_all_visualizations()`.

---

## 3. Project kaise chalta hai (data flow)

```
 db_setup.py                 preprocessing.py                  visualizations.py            charts/*.png
┌─────────────┐   SQL   ┌──────────────────────────┐ DataFrame ┌────────────────────┐ save ┌──────────┐
│ library.db  │ ──────► │ JOIN + clean + aggregate │ ────────► │ matplotlib/seaborn │ ───► │ 26 PNGs  │
│ (5 tables)  │         │ (days_kept, fine, status)│           │ charts             │      └──────────┘
└─────────────┘         └──────────────────────────┘           └────────────────────┘
       ▲                                                                ▲
       │ issue/return/add (INSERT/UPDATE)                               │ menu option / --chart N
       └──────────────────────────── main.py (terminal menu) ───────────┘
                                         │
                                         └──► library_export.xlsx ──► Power BI Desktop
```

**Step by step:**
1. Aap `python main.py` chalate ho.
2. `check_db()` dekhta hai database hai ya nahi; nahi hai to `db_setup.py` bana deta hai.
3. Menu aata hai. Library option (jaise *Issue a Book*) chuno to `main.py` seedha SQL se `library.db` update karta hai.
4. Chart option chuno to `visualizations.py` ka function chalta hai → wo `preprocessing.py` se **cleaned DataFrame** maangta hai → `preprocessing.py` database padh ke clean karta hai → chart banta hai → `charts/` me save → window me dikhta hai.
5. Kyunki charts har baar database se fresh banate hain, **naya book issue karo to chart bhi update ho jaata hai**.

**Cleaning ke rules (yaad rakhna, viva me puchte hain):**
- `days_kept` = return date (ya aaj, agar return nahi hua) − issue date, minimum 1
- `overdue_days` = return date (ya aaj) − due date, minimum 0
- `effective_fine` = overdue_days × ₹5
- `return_date` khaali (NULL) = book abhi student ke paas hai (active loan) — ye missing value galti nahi, **meaning** hai.

---

## 4. Database ke 5 tables

| Table | Columns | Matlab |
|---|---|---|
| `departments` | dept_id, dept_name | 6 branches |
| `students` | student_id, name, dept_id, year, home_state | 90 students |
| `books` | book_id, title, author, dept_id, total_copies, available_copies, publisher_state | 54 books |
| `transactions` | txn_id, book_id, student_id, issue_date, due_date, return_date, fine_amount | Har issue/return ka record |
| `shipments` | shipment_id, book_id, quantity, origin_city, origin_state, region, courier, distance_km, freight_cost, dispatch_date, expected_date, delivery_date | Publisher se campus tak book delivery (case study) |

Relations (star schema): `departments` → `students`, `books`; `books` + `students` → `transactions`; `books` → `shipments`.

---

## 5. Setup + har terminal command ka matlab

> macOS/Linux me `python3`, Windows me `python` likho. Har command project folder ke andar chalani hai.

### 5.1 Pehli baar setup

```bash
cd "Data-Visualisation-Project-"
```
**Matlab:** terminal ko project folder me le jao (`cd` = change directory).

```bash
python3 -m venv venv
```
**Matlab:** `venv` naam ka ek **virtual environment** (alag Python box) banao, taaki is project ki libraries baaki system se mix na hon. `-m venv` = Python ka built-in venv module chalao.

```bash
source venv/bin/activate
```
**Matlab:** us virtual environment ko **chalu** karo (macOS/Linux). Iske baad prompt ke aage `(venv)` dikhega. Windows pe: `venv\Scripts\activate`.

```bash
pip install -r requirements.txt
```
**Matlab:** `pip` = Python ka package installer. `-r requirements.txt` = is file me likhi saari libraries (pandas, matplotlib, seaborn...) ek saath install karo. Sirf pehli baar (ya nayi library add hone pe) chahiye.

### 5.2 Project chalana

```bash
python3 main.py
```
**Matlab:** program start karo → **main menu** khulega. Number type karke Enter dabao. Pehli baar `library.db` na ho to apne-aap ban jaata hai.

### 5.3 Shortcut flags (menu khole bina direct kaam)

| Command | Matlab |
|---|---|
| `python3 main.py --all` | Saare 26 charts bana ke `charts/` me save karo, koi window nahi khulegi, phir band. Sabse fast tareeka sab output banane ka. |
| `python3 main.py --list` | Saare charts ki numbered list (unit-wise) dikhao. |
| `python3 main.py --chart 7` | Sirf chart number 7 banao aur window me dikhao (number `--list` se dekho). |
| `python3 main.py --report` | Data Cleaning & Aggregation report terminal me print karo. |
| `python3 main.py --export` | `library_export.xlsx` banao (Power BI ke liye). |
| `python3 main.py --reset-db` | `library.db` delete karke **fresh sample data** ke saath naya banao. ⚠️ Aapke add kiye books/students/loans chale jaayenge. |
| `python3 main.py --help` | Saare flags ki list aur unka matlab dikhao. |

### 5.4 Files ko alag se chalana (optional)

```bash
python3 db_setup.py
```
**Matlab:** database ko **zero se dobara** banao (same as `--reset-db`).

```bash
python3 preprocessing.py
```
**Matlab:** cleaning module ka chhota test — cleaned table ki pehli rows aur department summary print karta hai.

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
sqlite3 library.db "SELECT * FROM books LIMIT 5;"
```
**Matlab:** `sqlite3` tool se database me SQL query chalao — yahan books table ki pehli 5 rows.

---

## 6. Main Menu (0–16) ka matlab

| # | Option | Kya hota hai |
|---|---|---|
| 1 | View Library Catalog | Saari books: ID, title, author, dept, available/total copies, publisher state |
| 2 | Add New Book | Title, author, department, copies, publisher state pooch ke book add karta hai |
| 3 | Remove / Minus Book | (1) copies kam karo, ya (2) book poori delete karo — agar koi copy student ke paas hai to delete nahi hone deta |
| 4 | Search Books | Title / author / department ka keyword daalo, matching books dikhengi (SQL `LIKE`) |
| 5 | View Student Directory | Saare students: ID, naam, dept, year, home state |
| 6 | Add New Student | Naya student register |
| 7 | Issue a Book | Student ID + Book ID → loan banta hai, **due date = aaj + 14 din**, available copies −1. Copy na ho to mana kar deta hai |
| 8 | Return a Book | Transaction ID → return date = aaj, **fine = late days × ₹5**, available copies +1 |
| 9 | View Overdue Loans | Jo loans due date ke baad hain, unki list + fine |
| 10 | Student Borrowing History | Ek student ke saare loans |
| 11 | Data Cleaning & Aggregation Report | **Unit 2**: raw table size, missing values, cleaning steps, dept × status pivot, summary statistics |
| 12 | Data Visualization Menu | 26 charts ka unit-wise menu (Section 7) |
| 13 | Generate All Charts | Saare charts ek saath `charts/` me save (no windows) |
| 14 | KPI Dashboard | **Unit 6 (Power BI concepts) terminal me**: Slicer (dept, year) → Cards → KPI (is mahine vs pichle mahine ▲▼) → Gauge (library utilisation %) → Drill-down (dept → top books) |
| 15 | Supply Chain Case Study | Region filter (North/West/South/East/All) → delivery KPIs, status %, routes table → dashboard chart save |
| 16 | Export for Power BI | `library_export.xlsx` (5 sheets) |
| 0 | Exit | Program band |

---

## 7. Visualization Menu (1–26) ka matlab

Har chart `charts/` me save hota hai. Menu se kholo to window bhi khulti hai (zoom/pan toolbar ke saath).

### Unit 1 — Introduction
| # | Chart (file) | Kya dikhata hai / kyun |
|---|---|---|
| 1 | Design Principles (`design_principles_comparison.png`) | Left: kharab 3D colourful bar chart (distortion, clutter). Right: wahi data clean horizontal bar me. **Design principles + value of visualization** |
| 2 | Data Graphic Types (`data_graphic_types.png`) | **Categorical** (bar: loan status), **Time series** (line: monthly issues), **Statistical** (box plot: days kept by year) |

### Unit 2 — Pre-processing & Aesthetics
| # | Chart (file) | Kya dikhata hai / kyun |
|---|---|---|
| 3 | Pairplot (`borrowing_pairplot.png`) | Student-level 4 metrics ka har pair scatter + diagonal pe KDE, colour = dept |
| 4 | Heatmap (`activity_heatmap.png`) | Department × Month loans; colour scale = intensity |
| 5 | Interactive Explorer (`interactive_explorer_snapshot.png`) | **Interactive visualization** (bina HTML ke): point pe mouse le jao → tooltip; left checkboxes se department on/off (slicer/filter); niche slider se smoothing. *Menu se kholne pe hi interactive hai; `--all` sirf snapshot save karta hai* |
| 6 | Graphical Perception (`graphical_perception.png`) | Same numbers 5 tareeke se: position, length, angle, area, colour. **Cleveland & McGill** — position/length sabse accurate, area/colour sabse kam |
| 7 | Grammar of Graphics (`grammar_of_graphics.png`) | Row 1: Layer 1 (data + aes x,y + geom_point) → Layer 2 (+ colour, size aesthetic) → Layer 3 (+ geom_smooth). Row 2: **Data types & scales** — nominal → qualitative colours, ordinal → sequential, continuous → diverging (centre = due date) |

Violin plot chart 12 me hai; Data Cleaning & Aggregation main menu option 11 me.

### Unit 3 — Visualization Design
| # | Chart (file) | Kya dikhata hai |
|---|---|---|
| 8 | Bar Plot (`books_by_department.png`) | Dept-wise total copies |
| 9 | Horizontal Bar (`author_distribution.png`) | Top 10 most-borrowed authors |
| 10 | Cleveland Dot Plot (`dot_books_per_dept.png`) | Bar ka high data-ink alternative |
| 11 | Grouped & Stacked Bars (`loan_status_breakdown.png`) | Dept × status (Returned/Active/Overdue) dono tareeke se |
| 12 | Distributions (`duration_distributions.png`) | **Single distribution**: histogram + density; **Multiple distributions**: overlaid KDE; **Violin plot** |
| 13 | ECDF, Q-Q, Skew (`statistical_diagnostics.png`) | ECDF of fines; Normal Q-Q plot; **highly skewed** raw fines vs **log1p** transform (skewness number title me) |

Heat map (amounts) = chart 4.

### Unit 4 — Advanced Visualization Design
| # | Chart (file) | Kya dikhata hai |
|---|---|---|
| 14 | Vertical vs Horizontal (`vertical_vs_horizontal.png`) | Many distributions: **vertical axis** = box plot + jittered strip chart; **horizontal axis** = ridgeline plot |
| 15 | Proportions (`proportions.png`) | Same shares ko **pie** vs **side-by-side bars** vs **stacked bar** + **stacked densities** — "a case for pie charts" |
| 16 | Parts of Total (`parts_of_total.png`) | Har department ko grey total ke upar alag panel me — **proportions separately as parts of the total** |
| 17 | Nested Proportions (`nested_proportions.png`) | Treemap (dept → book) + nested donut (dept → status) |
| 18 | Associations (`associations_and_pca.png`) | **Scatter** (loans vs fines, Pearson r), **Correlogram**, **PCA** (dimension reduction) |
| 19 | Paired Data (`paired_slope_chart.png`) | Slope chart: har dept ke loans pehle 6 mahine vs aakhri 6 mahine |

### Unit 5 — Time Series, Trends & Geospatial
| # | Chart (file) | Kya dikhata hai |
|---|---|---|
| 20 | Time Series & Trends (`time_series_and_trends.png`) | Individual series; multiple series (per dept); **smoothing** (3-month moving average + LOESS); **defined functional form** (linear & quadratic fit with R²) |
| 21 | Advanced TS (`advanced_time_series.png`) | **Dose–response** curve (overdue days → fine); **two or more response variables** (issues, returns, fines dual-axis); **detrending** (actual − trend); **decomposition** (trend + seasonal + residual) |
| 22 | Projections (`map_projections.png`) | Same points 3 projections me: Equirectangular, Mercator, Orthographic — grid lines ka shape badalta hai |
| 23 | Layers (`map_layers.png`) | Layer 1 base map → +Layer 2 data (students) → +Layer 3 campus & routes |
| 24 | Choropleth (`choropleth_map.png`) | State tiles colour se: raw students vs **normalised** loans per student |
| 25 | Cartograms (`cartogram.png`) | Proportional symbol map + tile cartogram (tile size ∝ loans) |

> Note: Choropleth/cartogram **tile-grid map** pe bane hain (har state ek square, rough geography ke hisaab se). Isse internet ya shapefile download ki zarurat nahi padti, project offline chalta hai.

### Case Study
| # | Chart (file) | Kya dikhata hai |
|---|---|---|
| 26 | Supply Chain Dashboard (`supply_chain_dashboard_all.png`) | KPI cards, on-time gauge, **route map**, status by region, monthly on-time trend, courier delay. Region filter ke liye main menu option 15 (file `supply_chain_dashboard_<region>.png`) |

---

## 8. Syllabus → Project Mapping (har topic kahan hai)

### Unit 1: Introduction to Data Visualization
| Syllabus topic | Project me kahan |
|---|---|
| Importance of DV in Data Science & Business | Chart 1 (bad vs good), KPI dashboard (menu 14) — decision lene me help; Section 11 viva |
| Data for Graphics | `preprocessing.py` → cleaned DataFrames; Section 4 tables |
| Design Principles | Chart 1; consistent dept colours sab charts me; labels/units har chart pe |
| Value for Visualization | Chart 1 (same data, clear vs confusing) |
| Categorical, Time Series, Statistical Graphics | Chart 2 |
| Introduction to Visualization Tools | Section 1 tools table; Power BI (`POWERBI_GUIDE.md`) |

### Unit 2: Data Pre-processing and Aesthetics
| Syllabus topic | Project me kahan |
|---|---|
| Data Cleaning and Aggregation | Menu 11 / `--report`; `preprocessing.py` |
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
| Smoothing | Chart 20 panel 3 (moving average, LOESS) |
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
| Cards, KPIs, Gauges, Slicers, Drill-down | Menu 14 (terminal); chart 26 (cards + gauge); `POWERBI_GUIDE.md` §4 |
| DAX measures | `POWERBI_GUIDE.md` §5 |
| Power BI Embedded, Row-Level Security | `POWERBI_GUIDE.md` §6 |

### Self-study Case Study
| Syllabus requirement | Project me kahan |
|---|---|
| Supply Chain & Logistics Dashboard | Menu 15, chart 26 |
| Dataset: shipment and delivery logs | `shipments` table (160 rows) |
| Tools: Power BI or Dash | Python dashboard (Dash web-based hai, isliye terminal project me matplotlib use kiya); `shipments` sheet Excel me bhi hai → Power BI me bana sakte ho (`POWERBI_GUIDE.md` §7) |
| Route mapping | Chart 26 route map + terminal routes table |
| Delivery status KPIs | Cards, gauge, status % |
| Filtering by region | Menu 15 region filter |

---

## 9. Power BI unit project me kaise cover hai

Power BI ek alag Windows software hai, Python ke andar nahi chalta. Isliye project ye karta hai:
1. **Data ready karta hai** → `library_export.xlsx` (departments, students, books, transactions, shipments).
2. **Wahi concepts terminal me dikhata hai** → menu 14: Slicer, Card, KPI, Gauge, Drill-down.
3. **Step-by-step guide** → `POWERBI_GUIDE.md`: Get Data, Power Query, relationships, visuals, DAX measures, RLS, Embedded.

---

## 10. Case Study: Supply Chain & Logistics Dashboard

**Story:** College library publishers se books mangwati hai. Publisher 6 cities me hain (Mumbai, Ahmedabad, New Delhi, Bengaluru, Chennai, Kolkata), delivery **Pune campus** pe hoti hai.

**Data:** har shipment ka dispatch date, expected date, delivery date, courier, distance, freight.

**Calculations (`preprocessing.get_cleaned_shipments`):**
- `transit_days` = delivery (ya aaj) − dispatch
- `delay_days` = delivery (ya aaj) − expected, minimum 0
- `status` = Delivered On-Time / Delivered Late / In Transit / Delayed In Transit

**Menu 15 me kya milta hai:** region chuno → shipments, units, freight, on-time % gauge, avg transit days, status KPIs, routes table (km, shipments, late), aur dashboard PNG.

---

## 11. Viva Questions & Answers

**Q1. Project kis cheez ke baare me hai?**
College library ka data (books, students, loans) manage karta hai aur usse 26 visualizations banata hai jo DV syllabus ke har unit ko cover karte hain. Pure terminal project hai.

**Q2. Data kahan se aaya?**
`db_setup.py` `faker` aur `random` se realistic sample data banata hai (fixed seed 42, isliye har baar same).

**Q3. Data cleaning me kya kiya?**
Text dates ko datetime banaya, NULL return_date ko "active loan" maana, `days_kept`, `overdue_days`, `effective_fine` nikale, status labels banaye, 4 tables JOIN kiye. Menu 11 sab dikhata hai.

**Q4. Graphical perception theory kya hai?**
Cleveland & McGill ke hisaab se insaan position aur length sabse sahi padhta hai, angle aur area kam sahi, colour sabse kam. Chart 6 me same data 5 encodings me hai.

**Q5. Grammar of Graphics kya hai?**
Chart = data + aesthetics (x, y, colour, size) + geometries (point, line, bar) + scales + layers. Chart 7 me layer-by-layer bana ke dikhaya hai.

**Q6. ECDF aur Q-Q plot me farak?**
ECDF batata hai kitne % values ek value se kam hain. Q-Q plot data ke quantiles ko normal distribution ke quantiles se compare karta hai — line pe points = normal.

**Q7. Skewed data ko kaise handle kiya?**
Fines right-skewed hain, isliye `log1p` transform kiya. Chart 13 me skewness number pehle aur baad me dikhta hai.

**Q8. Pie chart kab theek hai?**
Jab few parts hon aur "whole ka hissa" dikhana ho. Exact compare ke liye side-by-side bars better. Chart 15 me dono hain.

**Q9. PCA kyun?**
Har student ke 6 numbers (har dept se kitni books) ko 2 numbers (PC1, PC2) me compress kiya taaki 2D scatter me dikh sake.

**Q10. Smoothing aur detrending me farak?**
Smoothing noise hata ke trend dikhata hai (moving average, LOESS). Detrending trend hata ke short-term ups/downs dikhata hai (actual − trend).

**Q11. Choropleth me normalise kyun kiya?**
Jis state me zyada students hain wahan loans automatically zyada honge. Loans per student se fair comparison hota hai.

**Q12. Cartogram kya hai?**
Map jisme shape ka size data ke hisaab se badla jaata hai. Chart 25 me bubble size aur tile size loans ke proportional hain.

**Q13. Interactive visualization bina HTML ke kaise?**
Matplotlib window ke widgets: `CheckButtons` (filter), `Slider` (smoothing), `motion_notify_event` (hover tooltip). Chart 5.

**Q14. Fine kaise calculate hota hai?**
Due date = issue + 14 din. Return pe late days × ₹5.

**Q15. Power BI ka role?**
Business users ke liye dashboard. Project Excel export deta hai, aur guide me Power Query, DAX, RLS steps hain.

---

## 12. Problem aaye to (Troubleshooting)

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'pandas'` | venv activate karo (`source venv/bin/activate`) aur `pip install -r requirements.txt` chalao |
| `venv/bin/python: no such file` / venv toot gaya | Purana venv hata ke naya banao: `rm -rf venv`, phir Section 5.1 dobara |
| Chart window nahi khul raha | `--all` mode windows nahi kholta (by design). Menu 12 ya `--chart N` se kholo |
| Window band karne tak menu ruk jaata hai | Normal hai — chart window band karo, menu wapas aa jayega |
| Data ajeeb lag raha / kharab ho gaya | `python3 main.py --reset-db` (⚠️ apna added data jayega) |
| Excel export error | `openpyxl` install hai check karo; Excel me file khuli ho to band karo |

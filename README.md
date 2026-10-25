# Data-Visualisation-Project-
## Engineering College Library Management System (LMS) — Terminal Data Visualization Project

A terminal-only (CLI) Python project for an engineering college library with six departments (**Computer Science, AIML, Mechanical, Civil, Electronics, E&TC**). It manages books, students and loans in SQLite. It also generates **26 charts** that cover every topic of the Data Visualization syllabus (Unit 1 to Unit 5, the Power BI unit and the Supply Chain case study).

No web frontend: charts are saved as PNGs in `charts/` and open in a matplotlib window from the menu.

👉 **Full explanation in Hinglish (what is in the project, how it runs, the meaning of every command and menu option, the syllabus mapping and viva Q&A): [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md)**
👉 Power BI steps: [`POWERBI_GUIDE.md`](POWERBI_GUIDE.md)

---

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py                   # opens the main menu
```

| Command | What it does |
|---|---|
| `python3 main.py` | Interactive main menu |
| `python3 main.py --all` | Save all 26 charts to `charts/` (no windows) |
| `python3 main.py --list` | List chart numbers by syllabus unit |
| `python3 main.py --chart N` | Build and show chart N |
| `python3 main.py --report` | Data cleaning & aggregation report |
| `python3 main.py --export` | Write `library_export.xlsx` for Power BI |
| `python3 main.py --reset-db` | Re-create `library.db` with fresh sample data |

---

## Project Structure

```
main.py             # Entry point: menus, library operations, KPI dashboard, case study, CLI flags
db_setup.py         # SQLite schema (5 tables) + sample data
preprocessing.py    # Cleaning, feature engineering, aggregations, KPIs
visualizations.py   # 26 charts, arranged by syllabus unit (CHART_MENU)
library.db          # SQLite database
library_export.xlsx # Excel export for Power BI (5 sheets)
charts/             # Generated PNG charts
```

## Syllabus Coverage (summary)

| Unit | Covered by |
|---|---|
| 1. Introduction | Design principles (bad vs good chart), categorical / time-series / statistical graphics |
| 2. Pre-processing & Aesthetics | Cleaning report, pairplot, violin, heatmap, interactive explorer, graphical perception, grammar of graphics, scales |
| 3. Visualization Design | Bar, grouped/stacked, dot plot, heatmap, histogram/KDE, multiple distributions, ECDF, Q-Q, skewed data |
| 4. Advanced Design | Box/strip vs ridgeline, pie vs bars vs stacked, stacked densities, parts of total, treemap/nested donut, scatter, correlogram, PCA, paired slope |
| 5. Time Series & Geospatial | Individual/multiple series, dose-response, multi-response, smoothing, functional form, detrending, decomposition, projections, layers, choropleth, cartogram |
| 6. Power BI | Excel export, terminal KPI cards/gauge/slicers/drill-down, `POWERBI_GUIDE.md` (Power Query, DAX, RLS, Embedded) |
| Case Study | Supply Chain & Logistics dashboard: route map, delivery KPIs, region filter |

Topic-by-topic mapping: see section 8 of [`PROJECT_GUIDE.md`](PROJECT_GUIDE.md).

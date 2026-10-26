# All import
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import TwoSlopeNorm, Normalize
from matplotlib.patches import Wedge, FancyBboxPatch, Rectangle
from matplotlib.widgets import CheckButtons, Slider
import seaborn as sns
from scipy import stats
from sklearn.decomposition import PCA
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
import squarify

from preprocessing import (
    get_clean_prices,
    get_cleaned_trades,
    get_market_index,
    get_sector_index,
    get_stock_summary,
    get_sector_aggregates,
    get_stock_trade_aggregates,
    get_monthly_sector_returns,
    get_monthly_stock_returns,
    get_monthly_timeseries,
    get_investor_summary,
    get_stock_return_matrix,
    get_state_geospatial_summary,
    get_cleaned_shipments,
    get_company_logistics_scorecard,
    analyse_stock
)
from db_setup import PLANT_HUBS, PORT_LOCATION, RISK_PROFILES

CHARTS_DIR = "charts"

# When False (batch mode: `python main.py --all`) charts are only saved, no windows pop up
SHOW_WINDOWS = True

def set_show_windows(flag):
    global SHOW_WINDOWS
    SHOW_WINDOWS = flag

def ensure_dirs():
    os.makedirs(CHARTS_DIR, exist_ok=True)

def show_and_close():
    """Helper to display plot and close figure buffer cleanly without hanging."""
    try:
        if SHOW_WINDOWS and plt.get_backend().lower() != 'agg':
            plt.show()
    except Exception:
        pass
    finally:
        plt.close('all')

def save_chart(filename, label, fig=None):
    """Saves the current (or given) figure to charts/ and then shows it if windows are enabled."""
    ensure_dirs()
    out_path = os.path.join(CHARTS_DIR, filename)
    (fig or plt.gcf()).savefig(out_path, dpi=200, bbox_inches='tight')
    print(f" [Chart Saved] {label} -> {out_path}")
    show_and_close()
    return out_path

# Professional modern styling
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'axes.labelsize': 10,
    'axes.edgecolor': '#CBD5E1',
    'grid.color': '#F1F5F9',
    'grid.linestyle': '--',
    'figure.autolayout': False
})

# One fixed colour per sector across every chart (consistent aesthetic mapping)
SECTOR_PALETTE = {
    'IT': '#1D4ED8',
    'Banking': '#0D9488',
    'Pharma': '#7C3AED',
    'Auto': '#EA580C',
    'FMCG': '#DB2777',
    'Energy': '#CA8A04'
}
SECTOR_ORDER = list(SECTOR_PALETTE)
# Market convention: green = profit, red = loss, blue = still open
STATUS_COLORS = ['#16A34A', '#DC2626', '#2563EB']   # Profit Booked, Loss Booked, Open
STATUS_ORDER = ['Profit Booked', 'Loss Booked', 'Open']
UP, DOWN = '#16A34A', '#DC2626'
RISK_ORDER = [RISK_PROFILES[k] for k in sorted(RISK_PROFILES)]

# Approximate state centroids (latitude, longitude) for geospatial charts
STATE_COORDS = {
    "Maharashtra": (19.7515, 75.7139), "Karnataka": (15.3173, 75.7139),
    "Gujarat": (22.2587, 71.1924), "Delhi": (28.7041, 77.1025),
    "Tamil Nadu": (11.1271, 78.6569), "Uttar Pradesh": (26.8467, 80.9462),
    "Rajasthan": (27.0238, 74.2179), "Kerala": (10.8505, 76.2711),
    "West Bengal": (22.9868, 87.8550), "Telangana": (18.1124, 79.0193)
}
# Tile-grid positions (column, row from top) that keep rough geographic placement
STATE_TILES = {
    "Delhi": (2, 0), "Rajasthan": (1, 1), "Uttar Pradesh": (3, 1),
    "Gujarat": (0, 2), "West Bengal": (4, 2), "Maharashtra": (1, 3),
    "Telangana": (2, 3), "Karnataka": (1, 4), "Kerala": (1, 5), "Tamil Nadu": (2, 5)
}
# National Stock Exchange, BKC Mumbai: where every order is matched
EXCHANGE_LOCATION = ("NSE, Mumbai", 19.0662, 72.8657)

def _clean_axes(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

def _month_ticks(ax, every=1):
    ax.tick_params(axis='x', rotation=45)
    for i, lbl in enumerate(ax.get_xticklabels()):
        lbl.set_visible(i % every == 0)

# ==============================================================================
# UNIT 1: INTRODUCTION (Design Principles; Categorical, Time Series & Statistical Graphics)
# ==============================================================================

def plot_design_principles_demo():
    """Bad vs Good Chart Demonstration: Poor 3D Clutter vs Clean Horizontal Bar Chart."""
    summary = get_sector_aggregates()

    fig = plt.figure(figsize=(14, 5.5))

    # 1. Deliberately Poor Chart (Violates Proportional Ink & Minimal Junk)
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    sectors = summary['sector_name'].tolist()
    values = summary['traded_value_lakh'].tolist()
    colors = ['#FF0000', '#00FF00', '#FF00FF', '#FFFF00', '#00FFFF', '#FFA500']

    x = np.arange(len(sectors))
    ax1.bar3d(x, np.zeros(len(sectors)), np.zeros(len(sectors)), np.ones(len(sectors)) * 0.75,
              np.ones(len(sectors)) * 0.75, values, color=colors, alpha=0.75)
    ax1.set_title("POOR CHART: 3D Distorted Visual Clutter\n(Violates Proportional Ink & Adds Artificial Occlusion)", fontsize=10.5, color='#991B1B', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(sectors, rotation=45, fontsize=8)

    # 2. Corrected Clean Chart (High Data-Ink Ratio, Accurate Linear Scaling)
    ax2 = fig.add_subplot(1, 2, 2)
    summary_sorted = summary.sort_values('traded_value_lakh', ascending=True)
    bars = ax2.barh(summary_sorted['sector_name'], summary_sorted['traded_value_lakh'], color='#2563EB', height=0.6)
    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 1, bar.get_y() + bar.get_height()/2, f'Rs {w:,.0f} L',
                 va='center', ha='left', fontsize=9.5, fontweight='bold', color='#1E3A8A')
    ax2.set_title("CORRECTED CHART: Clean Horizontal Bar Chart\n(High Data-Ink Ratio, Minimal Junk, Proper Encoding)", fontsize=10.5, color='#166534', fontweight='bold')
    ax2.set_xlabel("Total Traded Value (Rs lakh)")
    ax2.set_ylabel("Sector")
    ax2.set_xlim(0, summary['traded_value_lakh'].max() * 1.2)
    _clean_axes(ax2)

    fig.suptitle("Same data - Traded Value by Sector - drawn badly and well", fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    save_chart("design_principles_comparison.png", "Design Principles Comparison")

def plot_data_graphic_types():
    """The three families of data graphics: categorical, time series and statistical."""
    df = get_cleaned_trades()
    idx = get_market_index()

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    # 1. Categorical data -> bar chart
    status_counts = df['simple_status'].value_counts().reindex(STATUS_ORDER).fillna(0)
    axes[0].bar(status_counts.index, status_counts.values, color=STATUS_COLORS, width=0.55)
    for i, v in enumerate(status_counts.values):
        axes[0].text(i, v + 2, f"{int(v)}", ha='center', fontweight='bold')
    axes[0].set_title("Categorical Data Graphic\n(Bar Chart: Trades per Outcome)", fontweight='bold')
    axes[0].set_ylabel("Number of Trades")
    _clean_axes(axes[0])

    # 2. Time series data -> line chart
    axes[1].plot(idx['date'], idx['index_level'], color='#1E3A8A', linewidth=1.8)
    axes[1].set_title("Time Series Data Graphic\n(Line Chart: Market Index, base 1000)", fontweight='bold')
    axes[1].set_ylabel("Index Level")
    axes[1].tick_params(axis='x', rotation=45)
    _clean_axes(axes[1])

    # 3. Statistical data -> box plot
    sns.boxplot(x='risk_label', y='return_pct', data=df, order=RISK_ORDER, ax=axes[2], color='#99F6E4')
    axes[2].axhline(0, color='#64748B', linewidth=1, linestyle='--')
    axes[2].set_title("Statistical Data Graphic\n(Box Plot: Trade Return % by Risk Profile)", fontweight='bold')
    axes[2].set_xlabel("Investor Risk Profile")
    axes[2].set_ylabel("Return per Trade (%)")

    plt.tight_layout()
    save_chart("data_graphic_types.png", "Categorical / Time Series / Statistical Graphics")

# ==============================================================================
# UNIT 2: PRE-PROCESSING & AESTHETICS (Pairplot, Violin, Heatmap, Interactive,
#         Graphical Perception, Grammar of Graphics, Aesthetics & Scales)
# ==============================================================================

def plot_stock_pairplot():
    """Seaborn Pairplot across stock-level risk/return metrics coloured by sector."""
    summary = get_stock_summary()
    pair_df = summary[['return_1y', 'volatility', 'max_drawdown', 'beta', 'sector_name']].rename(columns={
        'return_1y': '1Y Return %', 'volatility': 'Volatility %', 'max_drawdown': 'Max Drawdown %',
        'beta': 'Beta', 'sector_name': 'Sector'})

    g = sns.pairplot(pair_df, hue='Sector', corner=True, palette=SECTOR_PALETTE, hue_order=SECTOR_ORDER,
                     diag_kind='kde', plot_kws={'s': 45, 'alpha': 0.8})
    g.fig.suptitle("Multivariate Pairplot Matrix: Risk & Return of 36 Stocks by Sector", y=1.02, fontsize=12, fontweight='bold')
    save_chart("stock_pairplot.png", "Pairplot Matrix", fig=g.fig)

def plot_monthly_return_heatmap():
    """Sector x Month Heatmap of average monthly return with a diverging colormap centred on 0%."""
    matrix = get_monthly_sector_returns().reindex(SECTOR_ORDER)

    plt.figure(figsize=(12, 5.5))
    lim = np.nanmax(np.abs(matrix.values))
    sns.heatmap(matrix, annot=True, fmt='.1f', cmap='RdYlGn', center=0, vmin=-lim, vmax=lim,
                cbar_kws={'label': 'Average Monthly Return (%)'}, linewidths=0.5)
    plt.title("Heatmap: Monthly Return (%) by Sector\n(Aesthetic Mapping: X=Month, Y=Sector, Color=Return - green up, red down)", pad=10)
    plt.xlabel("Month (YYYY-MM)")
    plt.ylabel("Sector")
    plt.tight_layout()
    save_chart("return_heatmap.png", "Monthly Return Heatmap")

def plot_interactive_explorer():
    """Interactive matplotlib window: hover tooltips, sector check-boxes (slicer) and a moving-average slider."""
    sector_idx = get_sector_index()[SECTOR_ORDER]
    dates = list(sector_idx.index)
    x = np.arange(len(dates))

    fig, ax = plt.subplots(figsize=(13, 6.5))
    plt.subplots_adjust(left=0.24, bottom=0.25, right=0.97)
    lines = {}
    for sector in sector_idx.columns:
        (ln,) = ax.plot(x, sector_idx[sector].values, linewidth=2, color=SECTOR_PALETTE[sector], label=sector)
        lines[sector] = ln
    ax.axhline(100, color='#94A3B8', linewidth=1, linestyle='--')
    # One tick at the first trading day of every month
    ticks = [i for i in x if i == 0 or dates[i].month != dates[i - 1].month]
    ax.set_xticks(ticks)
    ax.set_xticklabels([dates[i].strftime('%b %y') for i in ticks], rotation=45)
    ax.set_ylabel("Sector Index (start = 100)")
    ax.set_title("Interactive Explorer: Sector Indices over One Year\n(Hover a line for details | tick boxes to filter | drag slider for moving average)")
    _clean_axes(ax)

    annot = ax.annotate("", xy=(0, 0), xytext=(12, 12), textcoords='offset points',
                        bbox=dict(boxstyle='round', fc='white', ec='#334155'), arrowprops=dict(arrowstyle='->'))
    annot.set_visible(False)

    # Slicer: sector check-boxes
    rax = fig.add_axes([0.02, 0.35, 0.17, 0.45])
    rax.set_title("Sector filter", fontsize=9)
    check = CheckButtons(rax, list(lines), [True] * len(lines))
    for text in check.labels:
        text.set_color(SECTOR_PALETTE[text.get_text()])
        text.set_fontweight('bold')
    def on_check(label):
        lines[label].set_visible(not lines[label].get_visible())
        fig.canvas.draw_idle()
    check.on_clicked(on_check)

    # Slider: moving-average window (1 = raw data)
    sax = fig.add_axes([0.30, 0.05, 0.55, 0.03])
    slider = Slider(sax, 'Moving average (days)', 1, 50, valinit=1, valstep=1)
    def on_slide(val):
        for sector, ln in lines.items():
            ln.set_ydata(sector_idx[sector].rolling(int(val), min_periods=1).mean().values)
        fig.canvas.draw_idle()
    slider.on_changed(on_slide)

    # Hover tooltip
    def on_hover(event):
        if event.inaxes == ax:
            for sector, ln in lines.items():
                hit, info = ln.contains(event)
                if ln.get_visible() and hit:
                    i = info['ind'][0]
                    annot.xy = (x[i], ln.get_ydata()[i])
                    annot.set_text(f"{sector}\n{dates[i]:%d %b %Y}: {ln.get_ydata()[i]:.1f} ({ln.get_ydata()[i] - 100:+.1f}%)")
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
        if annot.get_visible():
            annot.set_visible(False)
            fig.canvas.draw_idle()
    fig.canvas.mpl_connect('motion_notify_event', on_hover)
    fig._widgets = (check, slider)  # keep widget references alive while the window is open

    save_chart("interactive_explorer_snapshot.png", "Interactive Explorer (snapshot; live window opens in menu mode)", fig=fig)

def plot_graphical_perception():
    """Graphical perception theory: the same numbers encoded by position, length, angle, area and colour."""
    summary = get_sector_aggregates().sort_values('total_trades', ascending=False)
    sectors = summary['sector_name'].tolist()
    vals = summary['total_trades'].values.astype(float)
    colors = [SECTOR_PALETTE[s] for s in sectors]
    y = np.arange(len(sectors))

    fig, axes = plt.subplots(1, 5, figsize=(21, 4.8))

    axes[0].hlines(y, 0, vals, color='#CBD5E1')
    axes[0].scatter(vals, y, color=colors, s=90, zorder=3)
    axes[0].set_xlim(0, vals.max() * 1.1)
    axes[0].set_title("1. Position on common scale\n(most accurate)", fontweight='bold')

    axes[1].barh(y, vals, color=colors, height=0.6)
    axes[1].set_title("2. Length\n(bar chart)", fontweight='bold')
    for ax in axes[:2]:
        ax.set_yticks(y)
        ax.set_yticklabels(sectors)
        ax.invert_yaxis()
        _clean_axes(ax)

    axes[2].pie(vals, labels=sectors, colors=colors, startangle=90, counterclock=False,
                wedgeprops=dict(edgecolor='white'))
    axes[2].set_title("3. Angle\n(pie chart)", fontweight='bold')

    axes[3].scatter(y, np.zeros(len(y)), s=vals * 14, color=colors, alpha=0.8)
    axes[3].set_xticks(y)
    axes[3].set_xticklabels(sectors)
    axes[3].set_yticks([])
    axes[3].set_xlim(-0.8, len(y) - 0.2)
    axes[3].set_title("4. Area\n(bubble size)", fontweight='bold')

    axes[4].imshow(vals.reshape(-1, 1), cmap='Blues', aspect='auto')
    axes[4].set_yticks(y)
    axes[4].set_yticklabels(sectors)
    axes[4].set_xticks([])
    axes[4].grid(False)
    axes[4].set_title("5. Colour intensity\n(least accurate)", fontweight='bold')

    fig.suptitle("Graphical Perception Theory (Cleveland & McGill): Number of Trades per Sector, Five Encodings\n"
                 "Try ranking the two closest sectors in each panel - position & length are easiest, area & colour hardest",
                 fontsize=12, fontweight='bold', y=1.06)
    plt.tight_layout()
    save_chart("graphical_perception.png", "Graphical Perception Ranking")

def plot_grammar_of_graphics():
    """Grammar of Graphics: building a risk-return chart layer by layer, then scales for each type of data."""
    summary = get_stock_summary()
    df = get_cleaned_trades()

    fig, axes = plt.subplots(2, 3, figsize=(17, 10))

    # Row 1: Layering -> data + aesthetics + geometries
    ax = axes[0, 0]
    ax.scatter(summary['volatility'], summary['return_1y'], color='#64748B', s=30)
    ax.set_title("Layer 1: Data + aes(x, y) + geom_point", fontweight='bold')

    ax = axes[0, 1]
    sns.scatterplot(x='volatility', y='return_1y', hue='sector_name', size='avg_volume', hue_order=SECTOR_ORDER,
                    data=summary, palette=SECTOR_PALETTE, sizes=(30, 300), ax=ax, alpha=0.8)
    ax.set_title("Layer 2: + aes(colour = sector, size = avg volume)", fontweight='bold')
    ax.legend(fontsize=7, loc='upper left')

    ax = axes[0, 2]
    sns.scatterplot(x='volatility', y='return_1y', hue='sector_name', size='avg_volume', hue_order=SECTOR_ORDER,
                    data=summary, palette=SECTOR_PALETTE, sizes=(30, 300), ax=ax, alpha=0.8, legend=False)
    sns.regplot(x='volatility', y='return_1y', data=summary, scatter=False, ax=ax, color='#111827')
    ax.set_title("Layer 3: + geom_smooth (regression layer)", fontweight='bold')
    for ax in axes[0]:
        ax.axhline(0, color='#94A3B8', linewidth=0.8)
        ax.set_xlabel("Risk: Annual Volatility (%)")
        ax.set_ylabel("Reward: 1-Year Return (%)")
        _clean_axes(ax)

    # Row 2: Scales map data values onto aesthetics (one per data type)
    ax = axes[1, 0]
    counts = df['sector_name'].value_counts().reindex(SECTOR_ORDER)
    ax.bar(counts.index, counts.values, color=[SECTOR_PALETTE[s] for s in counts.index])
    ax.set_title("Nominal data -> qualitative colour scale\n(Trades per Sector)", fontweight='bold')
    ax.set_ylabel("Trades")
    _clean_axes(ax)

    ax = axes[1, 1]
    risk_trades = df.groupby('risk_profile').size().reindex([1, 2, 3, 4], fill_value=0)
    ax.bar(RISK_ORDER, risk_trades.values, color=sns.color_palette('Blues', 5)[1:])
    ax.set_title("Ordinal data -> sequential colour scale\n(Trades by Risk Profile, low -> high)", fontweight='bold')
    ax.set_xlabel("Risk Profile")
    ax.set_ylabel("Trades")
    _clean_axes(ax)

    ax = axes[1, 2]
    ret = df['return_pct'].clip(-40, 40)
    sc = ax.scatter(df['buy_date_dt'], df['return_pct'], c=ret, cmap='RdYlGn',
                    norm=TwoSlopeNorm(vcenter=0, vmin=ret.min(), vmax=max(ret.max(), 1)), s=18, edgecolors='#64748B', linewidths=0.2)
    fig.colorbar(sc, ax=ax, label="Return % (0 = break-even)")
    ax.axhline(0, color='#111827', linestyle='--', linewidth=1)
    ax.set_title("Continuous data -> diverging colour scale\n(Trade Return %, centred on break-even 0%)", fontweight='bold')
    ax.set_ylabel("Return per Trade (%)")
    ax.tick_params(axis='x', rotation=30)

    fig.suptitle("Grammar of Graphics: Layering, Aesthetics, Geometries & Scales", fontsize=14, fontweight='bold')
    plt.tight_layout()
    save_chart("grammar_of_graphics.png", "Grammar of Graphics & Scales")

# ==============================================================================
# UNIT 3: VISUALIZATION DESIGN (Amounts; Distributions: Hist/KDE, ECDF, Q-Q, Skew)
# ==============================================================================

def plot_sector_returns_bar():
    """Bar plot of the average 1-year return of each sector (bars start at zero, colour = up/down)."""
    summary = get_sector_aggregates().sort_values('avg_return_1y', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    vals = summary['avg_return_1y']
    bars = ax.bar(summary['sector_name'], vals, color=[UP if v >= 0 else DOWN for v in vals], width=0.55)

    # Value annotations on bar tips
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, v + (1 if v >= 0 else -1), f'{v:+.1f}%',
                ha='center', va='bottom' if v >= 0 else 'top', fontsize=9.5, fontweight='bold', color='#111827')

    ax.axhline(0, color='#111827', linewidth=1)
    ax.set_title("Bar Plot: Average 1-Year Return by Sector", pad=12)
    ax.set_xlabel("Sector")
    ax.set_ylabel("Average 1-Year Return (%)")
    ax.set_ylim(min(0, vals.min()) - 6, vals.max() + 6)
    _clean_axes(ax)
    plt.tight_layout()
    save_chart("sector_returns_bar.png", "Sector Returns Bar Plot")

def plot_most_traded_stocks():
    """Horizontal bar plot of the 10 most traded stocks with traded value labels."""
    top = get_stock_trade_aggregates().head(10).sort_values('total_trades', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = np.arange(len(top))
    bars = ax.barh(y_pos, top['total_trades'], color=[SECTOR_PALETTE[s] for s in top['sector_name']], height=0.6, alpha=0.9)

    for bar, (_, row) in zip(bars, top.iterrows()):
        w = bar.get_width()
        ax.text(w + 0.2, bar.get_y() + bar.get_height()/2, f"{int(w)} trades (Rs {row['traded_value_lakh']:.1f} L)",
                va='center', ha='left', fontsize=9, fontweight='bold', color='#1F2937')

    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{r.symbol} ({r.sector_name})" for r in top.itertuples()], fontsize=9.5)
    ax.set_xlabel("Number of Trades by Investors")
    ax.set_xlim(0, top['total_trades'].max() * 1.45)
    ax.set_title("Horizontal Bar Plot: Top 10 Most Traded Stocks\n(colour = sector)", pad=12)
    _clean_axes(ax)
    plt.tight_layout()
    save_chart("most_traded_stocks.png", "Most Traded Stocks")

def plot_cleveland_dot_plot():
    """Cleveland Dot Plot of the 1-year return of all 36 stocks (cleaner than 36 bars)."""
    summary = get_stock_summary().sort_values('return_1y')

    fig, ax = plt.subplots(figsize=(9, 10))
    ax.hlines(y=summary['symbol'], xmin=0, xmax=summary['return_1y'], color='#CBD5E1', linewidth=1.5)
    ax.scatter(summary['return_1y'], summary['symbol'], color=[SECTOR_PALETTE[s] for s in summary['sector_name']],
               s=90, zorder=3, edgecolors='white')
    for _, row in summary.iterrows():
        v = row['return_1y']
        ax.text(v + (2 if v >= 0 else -2), row['symbol'], f"{v:+.0f}%", va='center',
                ha='left' if v >= 0 else 'right', fontsize=8, color='#334155')
    ax.axvline(0, color='#111827', linewidth=1)
    ax.legend([plt.Line2D([], [], marker='o', ls='', color=c) for c in SECTOR_PALETTE.values()], SECTOR_ORDER,
              title="Sector", loc='lower right', fontsize=8)
    ax.set_title("Cleveland Dot Plot: 1-Year Return of Every Stock\n(High Data-Ink Alternative to 36 Bars)", pad=10)
    ax.set_xlabel("1-Year Return (%)")
    lim = summary['return_1y'].abs().max() + 15
    ax.set_xlim(-lim, lim)
    _clean_axes(ax)
    plt.tight_layout()
    save_chart("dot_stock_returns.png", "Cleveland Dot Plot")

def plot_trade_outcome_grouped_stacked():
    """Grouped and Stacked Bar Charts of trade outcome (Profit, Loss, Open) per sector."""
    summary = get_sector_aggregates().set_index('sector_name').reindex(SECTOR_ORDER).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # 1. Grouped Bar Chart
    melted = summary.melt(id_vars=['sector_name'], value_vars=STATUS_ORDER, var_name='Outcome', value_name='Count')
    sns.barplot(x='sector_name', y='Count', hue='Outcome', data=melted, ax=axes[0], palette=STATUS_COLORS)
    axes[0].set_title("Grouped Bar Chart: Trade Outcome by Sector", fontweight='bold')
    axes[0].set_xlabel("Sector")
    axes[0].set_ylabel("Number of Trades")

    # 2. Stacked Bar Chart
    summary.set_index('sector_name')[STATUS_ORDER].plot(kind='bar', stacked=True, ax=axes[1], color=STATUS_COLORS, edgecolor='white')
    axes[1].set_title("Stacked Bar Chart: Trade Outcome by Sector", fontweight='bold')
    axes[1].set_xlabel("Sector")
    axes[1].set_ylabel("Total Trades")
    axes[1].tick_params(axis='x', rotation=0)
    axes[1].legend(title="Outcome")

    plt.tight_layout()
    save_chart("trade_outcome_breakdown.png", "Grouped & Stacked Outcome Breakdown")

def plot_return_distributions():
    """Visualizing single & multiple distributions of daily returns: Histogram + KDE, Overlaid KDEs, and Violin Plot."""
    df = get_clean_prices().dropna(subset=['daily_return'])

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # 1. Single Distribution: Histogram + KDE
    sns.histplot(df['daily_return'], kde=True, ax=axes[0], color='#0D9488', bins=60, stat='density')
    axes[0].axvline(df['daily_return'].mean(), color='#111827', linestyle='--', label=f"Mean {df['daily_return'].mean():.2f}%")
    axes[0].set_title("Single Distribution: Daily Returns of All Stocks\n(Histogram + KDE Density)", fontweight='bold')
    axes[0].set_xlabel("Daily Return (%)")
    axes[0].set_ylabel("Density")
    axes[0].legend(fontsize=8)

    # 2. Overlaid Multiple Distributions across Sectors
    sns.kdeplot(data=df, x='daily_return', hue='sector_name', hue_order=SECTOR_ORDER, ax=axes[1],
                common_norm=False, palette=SECTOR_PALETTE, linewidth=1.8)
    axes[1].set_title("Multiple Distributions at the Same Time\n(Overlaid KDE Across 6 Sectors)", fontweight='bold')
    axes[1].set_xlabel("Daily Return (%)")
    axes[1].set_xlim(-8, 8)
    axes[1].set_ylabel("Density")

    # 3. Violin Plot across Sectors
    sns.violinplot(x='sector_name', y='daily_return', hue='sector_name', data=df, order=SECTOR_ORDER, ax=axes[2],
                   palette=SECTOR_PALETTE, inner='quartile', cut=0, legend=False)
    axes[2].set_title("Violin Plot: Daily Return Spread per Sector\n(Wider violin = riskier sector)", fontweight='bold')
    axes[2].set_xlabel("Sector")
    axes[2].set_ylabel("Daily Return (%)")

    plt.tight_layout()
    save_chart("return_distributions.png", "Return Distributions")

def plot_statistical_diagnostics():
    """Statistical graphics: ECDF, Normal Q-Q Plot (fat tails), and Skewed vs Log Transformation."""
    trades = get_cleaned_trades()
    prices = get_clean_prices().dropna(subset=['daily_return'])
    trade_value = trades['invested'] / 1000
    log_value = np.log10(trade_value)
    sample = prices['daily_return'].sample(1500, random_state=1)

    fig, axes = plt.subplots(1, 4, figsize=(21, 5))

    # 1. ECDF Plot
    sns.ecdfplot(trade_value, ax=axes[0], color='#7C3AED', linewidth=2.2)
    axes[0].axhline(0.5, color='#94A3B8', linestyle=':')
    axes[0].set_title("Empirical Cumulative Distribution Function\n(ECDF of Trade Size)", fontweight='bold')
    axes[0].set_xlabel("Trade Size (Rs thousand)")
    axes[0].set_ylabel("Cumulative Proportion of Trades")

    # 2. Q-Q Plot
    stats.probplot(sample, dist="norm", plot=axes[1])
    axes[1].set_title("Normal Q-Q Plot of Daily Returns\n(ends bend away = fat tails, big crashes/jumps)", fontweight='bold')
    axes[1].get_lines()[0].set_markerfacecolor('#2563EB')
    axes[1].get_lines()[0].set_markersize(4)
    axes[1].get_lines()[1].set_color('#DC2626')

    # 3. Highly skewed distribution (raw)
    sns.histplot(trade_value, bins=25, kde=True, ax=axes[2], color='#DC2626')
    axes[2].set_title(f"Highly Skewed Distribution\n(Raw Trade Size, skewness = {stats.skew(trade_value):.2f})", fontweight='bold')
    axes[2].set_xlabel("Trade Size (Rs thousand)")

    # 4. After log transform
    sns.histplot(log_value, bins=25, kde=True, ax=axes[3], color='#0D9488')
    axes[3].set_title(f"After log10 Transform\n(skewness = {stats.skew(log_value):.2f})", fontweight='bold')
    axes[3].set_xlabel("log10(Trade Size in Rs thousand)")

    plt.tight_layout()
    save_chart("statistical_diagnostics.png", "Statistical Diagnostics (ECDF, Q-Q, Skew & Log Transform)")

# ==============================================================================
# UNIT 4: ADVANCED DESIGN (Many Distributions, Proportions, Nested Proportions, Associations)
# ==============================================================================

def plot_vertical_vs_horizontal_layouts():
    """Many distributions at once: monthly stock returns along the vertical axis (box + strip) vs horizontal axis (ridgeline)."""
    df = get_monthly_stock_returns()

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Vertical axis: boxplots with jittered strip chart
    sns.boxplot(x='sector_name', y='monthly_return', data=df, order=SECTOR_ORDER, ax=axes[0], color='white', fliersize=0)
    sns.stripplot(x='sector_name', y='monthly_return', hue='sector_name', data=df, order=SECTOR_ORDER, ax=axes[0],
                  palette=SECTOR_PALETTE, size=3.5, alpha=0.6, jitter=0.25, legend=False)
    axes[0].axhline(0, color='#64748B', linewidth=1, linestyle='--')
    axes[0].set_title("Distributions along the VERTICAL axis\n(Box Plot + Jittered Strip Chart of Monthly Returns)", fontweight='bold')
    axes[0].set_xlabel("Sector")
    axes[0].set_ylabel("Monthly Return (%)")

    # Horizontal axis: ridgeline plot (one shifted density per sector)
    grid = np.linspace(df['monthly_return'].min() - 3, df['monthly_return'].max() + 3, 300)
    for i, sector in enumerate(reversed(SECTOR_ORDER)):
        kde = stats.gaussian_kde(df[df['sector_name'] == sector]['monthly_return'])
        dens = kde(grid) / kde(grid).max() * 0.9
        axes[1].fill_between(grid, i, i + dens, color=SECTOR_PALETTE[sector], alpha=0.7)
        axes[1].plot(grid, i + dens, color='white', linewidth=1)
    axes[1].axvline(0, color='#64748B', linewidth=1, linestyle='--')
    axes[1].set_yticks(range(len(SECTOR_ORDER)))
    axes[1].set_yticklabels(list(reversed(SECTOR_ORDER)))
    axes[1].set_title("Distributions along the HORIZONTAL axis\n(Ridgeline Plot of Monthly Returns)", fontweight='bold')
    axes[1].set_xlabel("Monthly Return (%)")
    _clean_axes(axes[1])

    plt.tight_layout()
    save_chart("vertical_vs_horizontal.png", "Vertical vs Horizontal Distributions")

def plot_proportions():
    """A case for pie charts: sector share of traded value as pie, side-by-side bars, stacked bar, and stacked densities."""
    summary = get_sector_aggregates().sort_values('traded_value', ascending=False)
    df = get_cleaned_trades()
    sectors = summary['sector_name'].tolist()
    shares = summary['traded_value'] / summary['traded_value'].sum() * 100
    colors = [SECTOR_PALETTE[s] for s in sectors]

    fig, axes = plt.subplots(1, 4, figsize=(22, 5.2))

    # 1. Pie chart
    axes[0].pie(shares, labels=sectors, autopct='%1.1f%%', startangle=90,
                counterclock=False, colors=colors, wedgeprops=dict(edgecolor='white'), textprops={'fontsize': 9})
    axes[0].set_title("Pie Chart\n(Share of Traded Value)", fontweight='bold')

    # 2. Side-by-side bars
    axes[1].bar(sectors, shares, color=colors)
    for i, v in enumerate(shares):
        axes[1].text(i, v + 0.3, f"{v:.1f}%", ha='center', fontsize=9)
    axes[1].set_title("Side-by-Side Bars\n(Same Shares)", fontweight='bold')
    axes[1].set_ylabel("Share of Traded Value (%)")
    _clean_axes(axes[1])

    # 3. Single stacked bar
    left = 0
    for s, v, c in zip(sectors, shares, colors):
        axes[2].barh(0, v, left=left, color=c, edgecolor='white')
        axes[2].text(left + v / 2, 0, f"{s}\n{v:.0f}%", ha='center', va='center', color='white', fontsize=8.5, fontweight='bold')
        left += v
    axes[2].set_xlim(0, 100)
    axes[2].set_yticks([])
    axes[2].set_xlabel("Cumulative Share (%)")
    axes[2].set_title("Stacked Bar\n(Parts Adding up to 100%)", fontweight='bold')

    # 4. Stacked densities: how the sector mix changes with holding period
    sns.kdeplot(data=df, x='holding_days', hue='sector_name', hue_order=SECTOR_ORDER, multiple='fill', palette=SECTOR_PALETTE,
                ax=axes[3], linewidth=0.5, clip=(1, df['holding_days'].max()))
    axes[3].set_title("Stacked Densities\n(Sector Mix vs Holding Period)", fontweight='bold')
    axes[3].set_xlabel("Holding Days")
    axes[3].set_ylabel("Proportion")

    fig.suptitle("Visualizing Proportions: Pie vs Side-by-Side Bars vs Stacked Bar vs Stacked Densities", fontsize=13, fontweight='bold', y=1.03)
    plt.tight_layout()
    save_chart("proportions.png", "Proportions (Pie, Side-by-Side, Stacked, Stacked Densities)")

def plot_parts_of_total():
    """Visualizing proportions separately as parts of the total (each sector's trades against all trades)."""
    df = get_cleaned_trades()
    lo, hi = np.floor(df['return_pct'].quantile(0.01)), np.ceil(df['return_pct'].quantile(0.99))
    bins = np.arange(lo, hi + 5, 5)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
    for ax, sector in zip(axes.flat, SECTOR_ORDER):
        part = df[df['sector_name'] == sector]['return_pct']
        ax.hist(df['return_pct'].clip(lo, hi), bins=bins, color='#CBD5E1', label='All trades (total)')
        ax.hist(part.clip(lo, hi), bins=bins, color=SECTOR_PALETTE[sector], label=sector)
        ax.axvline(0, color='#111827', linewidth=0.8)
        ax.set_title(f"{sector}: {len(part)} of {len(df)} trades ({len(part) / len(df) * 100:.0f}%)", fontweight='bold', fontsize=10.5)
        ax.legend(fontsize=8)
        _clean_axes(ax)
    for ax in axes[1]:
        ax.set_xlabel("Return per Trade (%)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Trades")

    fig.suptitle("Proportions Shown Separately as Parts of the Total\n(Grey = all trades, colour = one sector's part)", fontsize=13, fontweight='bold')
    plt.tight_layout()
    save_chart("parts_of_total.png", "Parts of the Total (Small Multiples)")

def plot_nested_proportions():
    """Nested proportions: treemap (Sector -> Stock) and nested donut (Sector -> Trade Outcome)."""
    df = get_cleaned_trades()

    fig, axes = plt.subplots(1, 2, figsize=(17, 7))

    # 1. Treemap: sectors as blocks, stocks nested inside (area = traded value)
    tree = (df.groupby(['sector_name', 'symbol'])['invested'].sum().reset_index()
              .assign(order=lambda t: t['sector_name'].map(SECTOR_ORDER.index))
              .sort_values(['order', 'invested'], ascending=[True, False]))
    labels = [f"{r.symbol}\nRs {r.invested / 1e5:.0f} L" for r in tree.itertuples()]
    squarify.plot(sizes=tree['invested'], label=labels, color=[SECTOR_PALETTE[s] for s in tree['sector_name']],
                  alpha=0.85, ax=axes[0], text_kwargs={'fontsize': 7, 'color': 'white'}, ec='white', linewidth=1.5)
    axes[0].legend([Rectangle((0, 0), 1, 1, color=c) for c in SECTOR_PALETTE.values()], SECTOR_ORDER,
                   loc='upper left', bbox_to_anchor=(1.0, 1.0), fontsize=8, title="Sector")
    axes[0].set_title("Treemap: Sector -> Stock\n(Area = Traded Value, Colour = Sector)", fontweight='bold')
    axes[0].axis('off')

    # 2. Nested donut: inner ring = sector, outer ring = outcome inside each sector
    nested = df.groupby(['sector_name', 'simple_status']).size().unstack(fill_value=0)
    nested = nested.reindex(columns=STATUS_ORDER, fill_value=0).reindex(SECTOR_ORDER).fillna(0)
    axes[1].pie(nested.sum(axis=1), radius=0.7, labels=nested.index, labeldistance=0.55,
                colors=[SECTOR_PALETTE[s] for s in nested.index], wedgeprops=dict(width=0.35, edgecolor='white'),
                textprops={'color': 'white', 'fontsize': 9, 'fontweight': 'bold'})
    axes[1].pie(nested.values.flatten(), radius=1.0, colors=STATUS_COLORS * len(nested),
                wedgeprops=dict(width=0.3, edgecolor='white'))
    axes[1].legend([Rectangle((0, 0), 1, 1, color=c) for c in STATUS_COLORS], STATUS_ORDER,
                   title="Outer ring: outcome", loc='lower left', fontsize=8.5)
    axes[1].set_title("Nested Donut: Sector (inner) -> Trade Outcome (outer)", fontweight='bold')

    plt.tight_layout()
    save_chart("nested_proportions.png", "Nested Proportions (Treemap & Nested Donut)")

def plot_associations_and_pca():
    """Associations among quantitative variables: risk-return scatter, sector correlogram and PCA of stock returns."""
    summary = get_stock_summary()
    sector_returns = get_clean_prices().groupby(['date', 'sector_name'])['daily_return'].mean().unstack()[SECTOR_ORDER]

    fig = plt.figure(figsize=(18, 5.4))

    # 1. Scatter plot of two quantitative variables
    ax1 = fig.add_subplot(1, 3, 1)
    sns.scatterplot(x='beta', y='return_1y', hue='sector_name', hue_order=SECTOR_ORDER, data=summary, s=60, ax=ax1, palette=SECTOR_PALETTE)
    r, _ = stats.pearsonr(summary['beta'], summary['return_1y'])
    ax1.axhline(0, color='#94A3B8', linewidth=0.8)
    ax1.set_title(f"Scatter Plot: Beta vs 1-Year Return per Stock\n(Pearson r = {r:.2f})", fontweight='bold', fontsize=10.5)
    ax1.set_xlabel("Beta (sensitivity to market)")
    ax1.set_ylabel("1-Year Return (%)")
    ax1.legend(fontsize=7)

    # 2. Correlogram (Correlation Heatmap)
    ax2 = fig.add_subplot(1, 3, 2)
    sns.heatmap(sector_returns.corr(), annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, square=True, ax=ax2, cbar_kws={'shrink': 0.8})
    ax2.set_xlabel("")
    ax2.set_ylabel("")
    ax2.set_title("Correlogram: Daily Returns of 6 Sectors\n(do sectors move together? diversification check)", fontweight='bold', fontsize=10.5)

    # 3. PCA Dimension Reduction: 250 daily returns per stock -> 2 numbers per stock
    ax3 = fig.add_subplot(1, 3, 3)
    matrix, sectors = get_stock_return_matrix()
    pca = PCA(n_components=2, random_state=42)
    standardised = (matrix - matrix.mean()) / matrix.std()
    components = pca.fit_transform(standardised.T.values)
    pca_df = pd.DataFrame(components, columns=['PC1', 'PC2'], index=matrix.columns)
    pca_df['Sector'] = sectors.reindex(pca_df.index).values

    sns.scatterplot(x='PC1', y='PC2', hue='Sector', hue_order=SECTOR_ORDER, data=pca_df, s=70, ax=ax3, palette=SECTOR_PALETTE)
    for sym, row in pca_df.iterrows():
        ax3.text(row['PC1'], row['PC2'], f" {sym}", fontsize=6.5, color='#475569')
    ax3.set_title(f"PCA Dimension Reduction (250 days -> 2D)\nStocks of the same sector cluster together (Explained Var: {sum(pca.explained_variance_ratio_)*100:.1f}%)",
                  fontweight='bold', fontsize=10.5)
    ax3.legend(fontsize=7)

    plt.tight_layout()
    save_chart("associations_and_pca.png", "Associations & PCA")

def plot_paired_slope_chart():
    """Paired data: each sector's return in the first vs second half of the year (slope chart)."""
    sector_idx = get_sector_index()[SECTOR_ORDER]
    mid = len(sector_idx) // 2
    first = (sector_idx.iloc[mid] / sector_idx.iloc[0] - 1) * 100
    second = (sector_idx.iloc[-1] / sector_idx.iloc[mid] - 1) * 100

    fig, ax = plt.subplots(figsize=(8, 6))
    for sector in SECTOR_ORDER:
        a, b = first[sector], second[sector]
        ax.plot([0, 1], [a, b], marker='o', markersize=8, linewidth=2.2, color=SECTOR_PALETTE[sector])
        ax.text(-0.04, a, f"{sector} {a:+.1f}%", ha='right', va='center', fontsize=9, color=SECTOR_PALETTE[sector])
        ax.text(1.04, b, f"{b:+.1f}% {sector}", ha='left', va='center', fontsize=9, color=SECTOR_PALETTE[sector])
    ax.axhline(0, color='#94A3B8', linewidth=1, linestyle='--')
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['First 6 Months', 'Last 6 Months'])
    ax.set_xlim(-0.4, 1.4)
    ax.set_ylabel("Sector Return in the Period (%)")
    ax.set_title("Paired Data Slope Chart: Sector Returns\n(Same sector measured in two periods - who gained momentum?)", pad=10)
    _clean_axes(ax)
    plt.tight_layout()
    save_chart("paired_slope_chart.png", "Paired Slope Chart")

# ==============================================================================
# UNIT 5: TIME SERIES, TRENDS & GEOSPATIAL (Projections, Layers, Choropleth, Cartogram)
# ==============================================================================

def plot_time_series_and_trends():
    """Individual & multiple time series, smoothing (moving averages, LOESS) and defined functional forms."""
    idx = get_market_index()
    sector_idx = get_sector_index()[SECTOR_ORDER]
    x = np.arange(len(idx))
    y = idx['index_level'].values
    dates = idx['date']

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # 1. Individual time series
    axes[0, 0].plot(dates, y, color='#1E3A8A', linewidth=1.6)
    axes[0, 0].fill_between(dates, y, y.min() * 0.98, color='#1E3A8A', alpha=0.08)
    axes[0, 0].set_title(f"Individual Time Series: Market Index ({(y[-1] / y[0] - 1) * 100:+.1f}% in one year)", fontweight='bold')
    axes[0, 0].set_ylabel("Index Level (base 1000)")

    # 2. Multiple time series
    for sector in SECTOR_ORDER:
        axes[0, 1].plot(sector_idx.index, sector_idx[sector], color=SECTOR_PALETTE[sector], linewidth=1.5, label=sector)
    axes[0, 1].axhline(100, color='#94A3B8', linewidth=1, linestyle='--')
    axes[0, 1].set_title("Multiple Time Series: Sector Indices (start = 100)", fontweight='bold')
    axes[0, 1].set_ylabel("Sector Index")
    axes[0, 1].legend(fontsize=8, ncol=2)

    # 3. Smoothing: moving averages and LOESS
    loess = sm.nonparametric.lowess(y, x, frac=0.25)
    axes[1, 0].plot(dates, y, label='Actual Index', alpha=0.45, color='gray')
    axes[1, 0].plot(dates, idx['ma_20'], label='20-Day Moving Average', color='#DC2626', linewidth=2)
    axes[1, 0].plot(dates, idx['ma_50'], label='50-Day Moving Average', color='#D97706', linewidth=2)
    axes[1, 0].plot(dates, loess[:, 1], label='LOESS Smoother', color='#0D9488', linewidth=2)
    axes[1, 0].set_title("Trend Smoothing: Moving Averages vs LOESS", fontweight='bold')
    axes[1, 0].set_ylabel("Index Level")
    axes[1, 0].legend(fontsize=8.5)

    # 4. Trend with a defined functional form (linear & exponential least squares)
    axes[1, 1].plot(dates, y, label='Actual Index', alpha=0.45, color='gray')
    lin = np.polyval(np.polyfit(x, y, 1), x)
    b, a = np.polyfit(x, np.log(y), 1)
    expo = np.exp(a + b * x)
    for fit, color, name in [(lin, '#2563EB', 'Linear  y = a + bx'), (expo, '#D97706', 'Exponential  y = a·e^(bx)')]:
        r2 = 1 - ((y - fit) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        axes[1, 1].plot(dates, fit, color=color, linewidth=2.2, label=f'{name} (R² = {r2:.2f})')
    axes[1, 1].set_title(f"Trend with a Defined Functional Form\n(exponential growth rate = {(np.exp(b * 252) - 1) * 100:.1f}% per year)", fontweight='bold')
    axes[1, 1].set_ylabel("Index Level")
    axes[1, 1].legend(fontsize=8.5)

    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=30)
        _clean_axes(ax)
    plt.tight_layout()
    save_chart("time_series_and_trends.png", "Time Series & Trends")

def plot_advanced_time_series():
    """Dose-response curve, two or more response variables, detrending and time-series decomposition."""
    idx = get_market_index()
    trades = get_cleaned_trades()
    sold = trades[trades['sell_date_dt'].notnull()]
    x = np.arange(len(idx))
    y = idx['index_level'].values

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # 1. Dose-Response Curve (holding period -> trade return)
    sns.regplot(x='holding_days', y='return_pct', data=sold, order=2, ax=axes[0, 0],
                scatter_kws={'alpha': 0.55, 'color': '#D97706', 's': 22}, line_kws={'color': '#1E3A8A', 'linewidth': 2})
    axes[0, 0].axhline(0, color='#94A3B8', linewidth=1, linestyle='--')
    axes[0, 0].set_title("Dose-Response Curve: Does holding longer pay?\n(Holding Days = Dose, Return % = Response)", fontweight='bold')
    axes[0, 0].set_xlabel("Holding Days")
    axes[0, 0].set_ylabel("Return per Sold Trade (%)")

    # 2. Two or more response variables over time (dual axis)
    ax2 = axes[0, 1]
    ax2.plot(idx['date'], idx['index_level'], color='#2563EB', linewidth=1.6, label='Market Index')
    ax2.set_ylabel("Index Level", color='#2563EB')
    ax2.tick_params(axis='x', rotation=30)
    ax2_twin = ax2.twinx()
    ax2_twin.plot(idx['date'], idx['volatility_20d'], color='#DC2626', linewidth=1.4, linestyle='--', label='20-Day Volatility (%)')
    ax2_twin.set_ylabel("Annualised Volatility (%)", color='#DC2626')
    ax2_twin.grid(False)
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, fontsize=8.5, loc='upper left')
    ax2.set_title("Time Series of Two Response Variables\n(Index Level & Volatility - fear rises when prices fall)", fontweight='bold')

    # 3. Detrending: subtract the fitted linear trend
    trend = np.polyval(np.polyfit(x, y, 1), x)
    detrended = y - trend
    axes[1, 0].fill_between(idx['date'], detrended, 0, where=detrended >= 0, color=UP, alpha=0.6, label='Above trend')
    axes[1, 0].fill_between(idx['date'], detrended, 0, where=detrended < 0, color=DOWN, alpha=0.6, label='Below trend')
    axes[1, 0].axhline(0, color='#111827', linewidth=1)
    axes[1, 0].set_title("Detrended Series (Actual - Linear Trend)\n(Short-term swings once the long-run trend is removed)", fontweight='bold')
    axes[1, 0].set_ylabel("Points away from Trend")
    axes[1, 0].tick_params(axis='x', rotation=30)
    axes[1, 0].legend(fontsize=8)

    # 4. Seasonal Decomposition (Trend, Seasonal, Residual)
    ts_decomp = idx.set_index('date')['index_level']
    res = seasonal_decompose(ts_decomp, model='additive', period=21)
    axes[1, 1].plot(ts_decomp.index, ts_decomp.values - ts_decomp.mean(), color='gray', alpha=0.45, label='Observed (centred)')
    axes[1, 1].plot(res.trend - ts_decomp.mean(), color='#DC2626', label='Trend (centred)')
    axes[1, 1].plot(res.seasonal, color='#10B981', label='Seasonal (period = 21 trading days)')
    axes[1, 1].plot(res.resid, color='#7C3AED', alpha=0.7, label='Residual')
    axes[1, 1].set_title("Time Series Decomposition\n(Observed = Trend + Seasonal + Residual)", fontweight='bold')
    axes[1, 1].tick_params(axis='x', rotation=30)
    axes[1, 1].legend(fontsize=8)

    plt.tight_layout()
    save_chart("advanced_time_series.png", "Dose-Response, Multi-Response, Detrending & Decomposition")

def _project(lon, lat, kind, lon0=80.0, lat0=22.0):
    """Converts longitude/latitude (degrees) into x/y for a map projection."""
    lam, phi = np.radians(lon), np.radians(lat)
    if kind == 'mercator':
        return np.degrees(lam), np.degrees(np.log(np.tan(np.pi / 4 + phi / 2)))
    if kind == 'orthographic':
        lam0, phi0 = np.radians(lon0), np.radians(lat0)
        x = np.cos(phi) * np.sin(lam - lam0)
        y = np.cos(phi0) * np.sin(phi) - np.sin(phi0) * np.cos(phi) * np.cos(lam - lam0)
        return x, y
    return np.asarray(lon, dtype=float), np.asarray(lat, dtype=float)   # equirectangular (plate carree)

def plot_map_projections():
    """Geospatial projections: the same investor-location points drawn in three projections."""
    geo = get_state_geospatial_summary()
    geo = geo[geo['home_state'].isin(STATE_COORDS)]
    lats = geo['home_state'].map(lambda s: STATE_COORDS[s][0]).values
    lons = geo['home_state'].map(lambda s: STATE_COORDS[s][1]).values

    fig, axes = plt.subplots(1, 3, figsize=(18, 6.5))
    titles = {'equirectangular': "Equirectangular (Plate Carree)\nx = lon, y = lat",
              'mercator': "Mercator\nlatitude gaps stretch towards the poles",
              'orthographic': "Orthographic (globe view centred on India)\nshape of a 3D globe"}
    for ax, kind in zip(axes, titles):
        for lon in range(60, 101, 10):    # meridians
            gx, gy = _project(np.full(50, lon), np.linspace(0, 60, 50), kind)
            ax.plot(gx, gy, color='#CBD5E1', linewidth=0.8)
        for lat in range(0, 61, 10):      # parallels
            gx, gy = _project(np.linspace(60, 100, 50), np.full(50, lat), kind)
            ax.plot(gx, gy, color='#CBD5E1', linewidth=0.8)
            ax.text(gx[0], gy[0], f"{lat}°N", fontsize=7, color='#94A3B8', ha='right')
        px_, py_ = _project(lons, lats, kind)
        ax.scatter(px_, py_, s=geo['investor_count'] * 25, color='#2563EB', alpha=0.6, edgecolors='#1E3A8A')
        for s, a, b in zip(geo['home_state'], px_, py_):
            ax.text(a, b, s, fontsize=7.5, ha='center', va='bottom')
        ax.set_title(titles[kind], fontweight='bold')
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("Map Projections: Investor Home States (bubble = number of investors)", fontsize=13, fontweight='bold')
    plt.tight_layout()
    save_chart("map_projections.png", "Map Projections")

def plot_map_layers():
    """Geospatial layers: base graticule -> investor data layer -> exchange & order-flow layer."""
    geo = get_state_geospatial_summary()
    geo = geo[geo['home_state'].isin(STATE_COORDS)]
    ex_name, ex_lat, ex_lon = EXCHANGE_LOCATION

    fig, axes = plt.subplots(1, 3, figsize=(18, 6.5), sharex=True, sharey=True)
    for i, ax in enumerate(axes):
        # Layer 1: base layer (lat/lon grid + state labels)
        for s, (lat, lon) in STATE_COORDS.items():
            ax.text(lon, lat - 0.9, s, fontsize=7.5, ha='center', color='#475569')
        ax.set_xlim(66, 92)
        ax.set_ylim(7, 31)
        ax.set_xlabel("Longitude (°E)")
        ax.set_ylabel("Latitude (°N)")
        if i >= 1:
            # Layer 2: data layer (investors per home state)
            for _, r in geo.iterrows():
                lat, lon = STATE_COORDS[r['home_state']]
                ax.scatter(lon, lat, s=r['investor_count'] * 30, color='#3B82F6', alpha=0.55, edgecolors='#1E40AF', zorder=3)
        if i == 2:
            # Layer 3: annotation layer (stock exchange + order flow from each state)
            for _, r in geo.iterrows():
                lat, lon = STATE_COORDS[r['home_state']]
                ax.plot([lon, ex_lon], [lat, ex_lat], color='#DC2626', linewidth=0.5 + r['traded_value_lakh'] / 15, alpha=0.6, zorder=2)
            ax.scatter(ex_lon, ex_lat, marker='*', s=400, color='#DC2626', edgecolors='black', zorder=4)
            ax.text(ex_lon - 0.5, ex_lat + 0.6, ex_name, fontsize=9, fontweight='bold', color='#991B1B', ha='right')
    axes[0].set_title("Layer 1: Base Map\n(coordinate grid + state labels)", fontweight='bold')
    axes[1].set_title("Layer 1 + 2: Data Layer\n(bubble = investors from each state)", fontweight='bold')
    axes[2].set_title("Layer 1 + 2 + 3: Annotation Layer\n(NSE Mumbai + order flow, width = traded value)", fontweight='bold')
    plt.tight_layout()
    save_chart("map_layers.png", "Map Layers")

def _draw_state_tiles(ax, values, cmap, label, fmt="{:.0f}", sizes=None):
    """Draws the tile-grid map; colour from `values`, optional tile size scaling for cartograms."""
    norm = Normalize(vmin=min(values.values()), vmax=max(values.values()))
    cm = plt.get_cmap(cmap)
    for state, (col, row) in STATE_TILES.items():
        v = values.get(state, 0)
        side = sizes[state] if sizes else 0.92
        ax.add_patch(Rectangle((col - side / 2, -row - side / 2), side, side, color=cm(norm(v)), ec='white', linewidth=2))
        text_color = 'white' if norm(v) > 0.55 else '#111827'
        ax.text(col, -row, f"{state}\n{fmt.format(v)}", ha='center', va='center', fontsize=8, color=text_color, fontweight='bold')
    ax.set_xlim(-0.7, 4.7)
    ax.set_ylim(-5.7, 0.7)
    ax.set_aspect('equal')
    ax.axis('off')
    if not sizes:
        sm_ = plt.cm.ScalarMappable(norm=norm, cmap=cm)
        plt.colorbar(sm_, ax=ax, shrink=0.7, label=label)

def plot_choropleth_map():
    """Choropleth (tile-grid) of Indian home states: raw investor counts vs normalised traded value per investor."""
    geo = get_state_geospatial_summary().set_index('home_state')
    investors = geo['investor_count'].to_dict()
    per_investor = (geo['traded_value_lakh'] / geo['investor_count'].replace(0, np.nan)).fillna(0).to_dict()

    fig, axes = plt.subplots(1, 2, figsize=(15, 7.5))
    _draw_state_tiles(axes[0], investors, 'Blues', "Investors")
    axes[0].set_title("Choropleth: Investors per Home State\n(raw count, sequential colour scale)", fontweight='bold')
    _draw_state_tiles(axes[1], per_investor, 'YlOrRd', "Traded value per investor (Rs lakh)", fmt="Rs {:.1f} L")
    axes[1].set_title("Choropleth: Traded Value per Investor\n(normalised rate - fair comparison across states)", fontweight='bold')
    fig.suptitle("Choropleth Mapping on a Tile-Grid Map of India (tiles placed by rough geography)", fontsize=13, fontweight='bold', y=1.04)
    plt.tight_layout()
    save_chart("choropleth_map.png", "Choropleth Map")

def plot_proportional_cartogram():
    """Cartograms: proportional symbol map on lat/lon and a tile cartogram where tile size = traded value."""
    geo = get_state_geospatial_summary()
    geo = geo[geo['home_state'].isin(STATE_COORDS)]

    fig, axes = plt.subplots(1, 2, figsize=(16, 7.5))
    for _, row in geo.iterrows():
        lat, lon = STATE_COORDS[row['home_state']]
        value = row['traded_value_lakh']
        axes[0].scatter(lon, lat, s=value * 30 + 120, alpha=0.55, color='#2563EB', edgecolors='#1E3A8A', linewidth=1.5)
        axes[0].text(lon, lat, f"{row['home_state']}\n(Rs {value:.0f} L)", ha='center', va='center', fontsize=8.5, fontweight='bold')
    axes[0].set_title("Proportional Symbol Map (Projection: WGS84 lat/lon)\nBubble area = total traded value", fontweight='bold')
    axes[0].set_xlabel("Longitude (°E)")
    axes[0].set_ylabel("Latitude (°N)")

    value = geo.set_index('home_state')['traded_value_lakh'].to_dict()
    sizes = {s: 0.98 * np.sqrt(value.get(s, 0) / max(value.values())) for s in STATE_TILES}
    _draw_state_tiles(axes[1], value, 'Blues', "Rs lakh", fmt="Rs {:.0f} L", sizes=sizes)
    axes[1].set_title("Tile Cartogram\nTile area resized in proportion to traded value", fontweight='bold')
    plt.tight_layout()
    save_chart("cartogram.png", "Cartograms")

# ==============================================================================
# SELF-STUDY CASE STUDY: SUPPLY CHAIN & LOGISTICS DASHBOARD
# (Route mapping, delivery status KPIs, filtering by region) - linked to stock returns
# ==============================================================================

def _kpi_card(ax, title, value, color):
    ax.add_patch(FancyBboxPatch((0.03, 0.08), 0.94, 0.84, boxstyle='round,pad=0.02', fc='#F8FAFC', ec=color, linewidth=2))
    ax.text(0.5, 0.62, value, ha='center', va='center', fontsize=20, fontweight='bold', color=color)
    ax.text(0.5, 0.28, title, ha='center', va='center', fontsize=9.5, color='#334155')
    ax.axis('off')

def _gauge(ax, pct, target, caption):
    """Semi-circular gauge (0-100%) with a target marker."""
    for start, end, c in [(0, 60, '#FCA5A5'), (60, 85, '#FDE68A'), (85, 100, '#A7F3D0')]:
        ax.add_patch(Wedge((0, 0), 1, 180 - end * 1.8, 180 - start * 1.8, width=0.3, color=c))
    ang = np.radians(180 - pct * 1.8)
    ax.plot([0, 0.75 * np.cos(ang)], [0, 0.75 * np.sin(ang)], color='#111827', linewidth=3)
    t_ang = np.radians(180 - target * 1.8)
    ax.plot([0.68 * np.cos(t_ang), 1.02 * np.cos(t_ang)], [0.68 * np.sin(t_ang), 1.02 * np.sin(t_ang)], color='#1D4ED8', linewidth=3)
    ax.text(0, -0.22, f"{pct:.1f}%", ha='center', fontsize=16, fontweight='bold')
    ax.text(0, -0.45, f"{caption} (target {target}%)", ha='center', fontsize=8.5, color='#334155')
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.55, 1.1)
    ax.set_aspect('equal')
    ax.axis('off')

def plot_supply_chain_dashboard(region=None):
    """Supply Chain & Logistics dashboard: KPI cards, gauge, route map, status by region, trend, and logistics vs stock return."""
    ship = get_cleaned_shipments(region)
    if ship.empty:
        print(" [!] No shipments for this filter.")
        return None
    delivered = ship[ship['status'].str.startswith('Delivered')]
    on_time_pct = (delivered['status'] == 'Delivered On-Time').mean() * 100 if len(delivered) else 0.0
    status_order = ['Delivered On-Time', 'Delivered Late', 'In Transit', 'Delayed In Transit']
    status_colors = ['#10B981', '#F59E0B', '#3B82F6', '#EF4444']

    fig = plt.figure(figsize=(18, 13))
    gs = fig.add_gridspec(3, 5, height_ratios=[0.8, 2.2, 1.6], hspace=0.5, wspace=0.6)

    # Row 1: KPI cards + gauge
    _kpi_card(fig.add_subplot(gs[0, 0]), "Total Shipments", f"{len(ship)}", '#1E3A8A')
    _kpi_card(fig.add_subplot(gs[0, 1]), "Containers Shipped", f"{ship['quantity'].sum()}", '#0D9488')
    _kpi_card(fig.add_subplot(gs[0, 2]), "Open (In Transit)", f"{(~ship['status'].str.startswith('Delivered')).sum()}", '#3B82F6')
    _kpi_card(fig.add_subplot(gs[0, 3]), "Avg Transit Days", f"{delivered['transit_days'].mean():.1f}", '#D97706')
    _gauge(fig.add_subplot(gs[0, 4]), on_time_pct, 90, "On-time delivery")

    # Row 2 left: route map (factory hubs -> export port)
    ax_map = fig.add_subplot(gs[1, :3])
    port_name, p_lat, p_lon = PORT_LOCATION
    routes = ship.groupby('origin_city').agg(
        shipments=('shipment_id', 'count'),
        on_time=('status', lambda s: (s == 'Delivered On-Time').sum() / max(1, s.str.startswith('Delivered').sum()) * 100)
    ).reset_index()
    cmap = plt.get_cmap('RdYlGn')
    label_offsets = {'Pune': (0.5, -2.0, 'left'), 'Ahmedabad': (-0.6, 0.2, 'right'),
                     'Hyderabad': (0.6, 0.4, 'left'), 'Chennai': (0.6, -1.0, 'left'),
                     'Jamshedpur': (0, 0.8, 'center'), 'Kolkata': (0.4, -1.4, 'left')}
    for _, r in routes.iterrows():
        _, _, lat, lon = PLANT_HUBS[r['origin_city']]
        ax_map.annotate("", xy=(p_lon, p_lat), xytext=(lon, lat),
                        arrowprops=dict(arrowstyle='-|>', color=cmap(r['on_time'] / 100), lw=1 + r['shipments'] / 6,
                                        connectionstyle='arc3,rad=0.15', alpha=0.85))
        ax_map.scatter(lon, lat, s=120, color='#1E3A8A', zorder=3)
        dx, dy, ha = label_offsets.get(r['origin_city'], (0, 0.7, 'center'))
        ax_map.text(lon + dx, lat + dy, f"{r['origin_city']}\n{r['shipments']} shipments, {r['on_time']:.0f}% on-time",
                    ha=ha, fontsize=8.5)
    ax_map.scatter(p_lon, p_lat, marker='*', s=500, color='#DC2626', edgecolors='black', zorder=4)
    ax_map.text(p_lon - 1.1, p_lat + 0.6, port_name, fontsize=10, fontweight='bold', color='#991B1B', ha='right')
    ax_map.set_xlim(66, 92)
    ax_map.set_ylim(10, 31)
    ax_map.set_aspect('equal')
    ax_map.set_xlabel("Longitude (°E)")
    ax_map.set_ylabel("Latitude (°N)")
    ax_map.set_title("Route Map: Factory Hubs -> Export Port\n(arrow width = shipments, colour = on-time %: red low, green high)", fontweight='bold')

    # Row 2 right: delivery status by region (stacked bars)
    ax_reg = fig.add_subplot(gs[1, 3:])
    by_region = ship.groupby(['region', 'status']).size().unstack(fill_value=0).reindex(columns=status_order, fill_value=0)
    by_region.plot(kind='barh', stacked=True, ax=ax_reg, color=status_colors, edgecolor='white')
    ax_reg.set_title("Delivery Status by Region", fontweight='bold')
    ax_reg.set_xlabel("Shipments")
    ax_reg.set_ylabel("Region")
    ax_reg.legend(fontsize=8, loc='lower right')

    # Row 3 has its own grid so the carrier names get room
    row3 = gs[2, :].subgridspec(1, 3, wspace=0.45, width_ratios=[1.3, 0.9, 1.3])

    # Row 3 left: monthly on-time % trend
    ax_tr = fig.add_subplot(row3[0])
    monthly = delivered.groupby('dispatch_month')['status'].apply(lambda s: (s == 'Delivered On-Time').mean() * 100)
    ax_tr.plot(monthly.index, monthly.values, marker='o', color='#0D9488', linewidth=2)
    ax_tr.axhline(90, color='#1D4ED8', linestyle='--', linewidth=1, label='Target 90%')
    ax_tr.set_ylim(0, 105)
    ax_tr.set_ylabel("On-time %")
    _month_ticks(ax_tr, every=2)
    ax_tr.legend(fontsize=8)
    ax_tr.set_title("Monthly On-Time Delivery %", fontweight='bold')

    # Row 3 middle: average delay per carrier
    ax_cr = fig.add_subplot(row3[1])
    carrier = delivered.groupby('carrier')['delay_days'].mean().sort_values()
    ax_cr.barh(carrier.index, carrier.values, color='#F59E0B')
    ax_cr.set_xlabel("Average Delay (days)")
    ax_cr.set_title("Average Delay by Carrier", fontweight='bold')
    _clean_axes(ax_cr)

    # Row 3 right: the stock market link - logistics performance vs share price return
    ax_lk = fig.add_subplot(row3[2])
    score = get_company_logistics_scorecard(region)
    ax_lk.scatter(score['on_time_pct'], score['return_1y'], s=score['shipments'] * 15,
                  color=[SECTOR_PALETTE[s] for s in score['sector_name']], alpha=0.8, edgecolors='white')
    for _, r in score.iterrows():
        ax_lk.text(r['on_time_pct'], r['return_1y'], f" {r['symbol']}", fontsize=7)
    if len(score) > 2:
        fit = np.polyfit(score['on_time_pct'], score['return_1y'], 1)
        xs = np.linspace(score['on_time_pct'].min(), score['on_time_pct'].max(), 10)
        ax_lk.plot(xs, np.polyval(fit, xs), color='#111827', linestyle='--', linewidth=1)
        r_val = np.corrcoef(score['on_time_pct'], score['return_1y'])[0, 1]
        ax_lk.set_title(f"Stock Link: On-Time % vs 1-Year Share Return\n(r = {r_val:.2f}; bubble = shipments, colour = sector)", fontweight='bold')
    ax_lk.axhline(0, color='#94A3B8', linewidth=0.8)
    ax_lk.set_xlabel("On-time Delivery (%)")
    ax_lk.set_ylabel("1-Year Stock Return (%)")
    _clean_axes(ax_lk)

    fig.suptitle(f"Supply Chain & Logistics Dashboard - Export Shipments of Listed Manufacturers | Region filter: {region or 'All Regions'}",
                 fontsize=15, fontweight='bold', y=0.95)
    suffix = (region or 'all').lower()
    return save_chart(f"supply_chain_dashboard_{suffix}.png", f"Supply Chain Dashboard ({region or 'All Regions'})", fig=fig)

# ==============================================================================
# SINGLE STOCK ANALYSIS CHART (used by main menu option 4: Search & Analyse)
# ==============================================================================

def plot_stock_analysis(stock_id, days=120):
    """Candlestick chart with 20/50-day moving averages, volume bars and RSI for one stock."""
    report, g = analyse_stock(stock_id)
    if report is None:
        print(" [!] No price history for this stock.")
        return None
    g = g.tail(days).reset_index(drop=True)
    x = np.arange(len(g))
    up = g['close'] >= g['open']
    colors = np.where(up, UP, DOWN)

    fig, (ax_p, ax_v, ax_r) = plt.subplots(3, 1, figsize=(14, 9), sharex=True,
                                           gridspec_kw={'height_ratios': [3, 1, 1]})
    # Candles: thin line = high-low range, thick bar = open-close body
    ax_p.vlines(x, g['low'], g['high'], color=colors, linewidth=1)
    ax_p.bar(x, (g['close'] - g['open']).abs().clip(lower=g['close'] * 0.0008), bottom=np.minimum(g['open'], g['close']),
             color=colors, width=0.7)
    ax_p.plot(x, g['dma_20'], color='#2563EB', linewidth=1.6, label='20-Day MA')
    ax_p.plot(x, g['dma_50'], color='#D97706', linewidth=1.6, label='50-Day MA')
    ax_p.set_ylabel("Price (Rs)")
    ax_p.legend(loc='upper left', fontsize=9)
    ax_p.set_title(f"{report['symbol']} - {report['company']} ({report['sector']})  |  Last Rs {report['last_close']:,.2f}  "
                   f"|  1Y {report['ret_1y']:+.1f}%  |  Signal: {report['signal'].split()[0]}", fontweight='bold')

    ax_v.bar(x, g['volume'] / 1e5, color=colors, alpha=0.6, width=0.8)
    ax_v.set_ylabel("Volume (lakh)")

    ax_r.plot(x, g['rsi'], color='#7C3AED', linewidth=1.5)
    ax_r.axhspan(70, 100, color='#FEE2E2', alpha=0.6)
    ax_r.axhspan(0, 30, color='#DCFCE7', alpha=0.6)
    ax_r.set_ylim(0, 100)
    ax_r.set_ylabel("RSI (14)")
    ax_r.text(1, 85, "Overbought > 70", fontsize=8, color='#991B1B')
    ax_r.text(1, 10, "Oversold < 30", fontsize=8, color='#166534')

    ticks = x[::15]
    ax_r.set_xticks(ticks)
    ax_r.set_xticklabels([g['date'].iloc[i].strftime('%d %b') for i in ticks])
    for ax in (ax_p, ax_v, ax_r):
        _clean_axes(ax)
    plt.tight_layout()
    safe = report['symbol'].replace('&', 'and').replace('-', '_')
    return save_chart(f"stock_analysis_{safe}.png", f"Stock Analysis ({report['symbol']})", fig=fig)

# ==============================================================================
# CHART REGISTRY (used by the terminal menu and `python main.py --all / --chart N`)
# ==============================================================================

CHART_MENU = [
    ("Unit 1", "Design Principles: Poor 3D Chart vs Clean Bar Chart", plot_design_principles_demo),
    ("Unit 1", "Categorical, Time Series & Statistical Data Graphics", plot_data_graphic_types),
    ("Unit 2", "Pairplot Matrix of Stock Risk & Return", plot_stock_pairplot),
    ("Unit 2", "Heatmap: Monthly Return by Sector", plot_monthly_return_heatmap),
    ("Unit 2", "Interactive Explorer (hover, sector filter, moving-average slider)", plot_interactive_explorer),
    ("Unit 2", "Graphical Perception: Position vs Length vs Angle vs Area vs Colour", plot_graphical_perception),
    ("Unit 2", "Grammar of Graphics: Layers, Aesthetics, Geometries & Scales", plot_grammar_of_graphics),
    ("Unit 3", "Bar Plot: Average 1-Year Return by Sector", plot_sector_returns_bar),
    ("Unit 3", "Horizontal Bar Plot: Top 10 Most Traded Stocks", plot_most_traded_stocks),
    ("Unit 3", "Cleveland Dot Plot: 1-Year Return of Every Stock", plot_cleveland_dot_plot),
    ("Unit 3", "Grouped & Stacked Bars: Trade Outcome by Sector", plot_trade_outcome_grouped_stacked),
    ("Unit 3", "Distributions: Histogram + KDE, Overlaid KDE, Violin (Daily Returns)", plot_return_distributions),
    ("Unit 3", "ECDF, Q-Q Plot, Skewed Data & Log Transform", plot_statistical_diagnostics),
    ("Unit 4", "Many Distributions: Vertical (Box/Strip) vs Horizontal (Ridgeline)", plot_vertical_vs_horizontal_layouts),
    ("Unit 4", "Proportions: Pie, Side-by-Side, Stacked Bar, Stacked Densities", plot_proportions),
    ("Unit 4", "Proportions Separately as Parts of the Total", plot_parts_of_total),
    ("Unit 4", "Nested Proportions: Treemap & Nested Donut", plot_nested_proportions),
    ("Unit 4", "Associations: Scatter, Correlogram, PCA", plot_associations_and_pca),
    ("Unit 4", "Paired Data: Slope Chart of Sector Returns", plot_paired_slope_chart),
    ("Unit 5", "Time Series: Individual, Multiple, Smoothing, Functional Form", plot_time_series_and_trends),
    ("Unit 5", "Dose-Response, Multi-Response, Detrending, Decomposition", plot_advanced_time_series),
    ("Unit 5", "Geospatial: Map Projections", plot_map_projections),
    ("Unit 5", "Geospatial: Map Layers", plot_map_layers),
    ("Unit 5", "Geospatial: Choropleth Map", plot_choropleth_map),
    ("Unit 5", "Geospatial: Cartograms", plot_proportional_cartogram),
    ("Case Study", "Supply Chain & Logistics Dashboard (All Regions)", plot_supply_chain_dashboard),
]

def generate_all_visualizations():
    """Batch generator that saves every chart to charts/ without opening windows."""
    print("\n--- Generating Complete Visual Analytics Suite ---")
    previous = SHOW_WINDOWS
    set_show_windows(False)
    try:
        for _, _, func in CHART_MENU:
            func()
    finally:
        set_show_windows(previous)
    print(f"\n All {len(CHART_MENU)} charts generated successfully in the '{CHARTS_DIR}/' folder!")

# All import
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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
    get_cleaned_transactions,
    get_department_aggregates,
    get_author_aggregates,
    get_monthly_matrix,
    get_monthly_timeseries,
    get_student_feature_matrix,
    get_student_summary,
    get_state_geospatial_summary,
    get_cleaned_shipments
)
from db_setup import PUBLISHER_HUBS, CAMPUS_LOCATION

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

# One fixed colour per department across every chart (consistent aesthetic mapping)
DEPT_PALETTE = {
    'Computer Science': '#1E3A8A',
    'AIML': '#0D9488',
    'Mechanical': '#D97706',
    'Civil': '#DC2626',
    'Electronics': '#7C3AED',
    'E&TC': '#65A30D'
}
DEPT_SHORT = {'Computer Science': 'CS', 'AIML': 'AIML', 'Mechanical': 'Mech',
              'Civil': 'Civil', 'Electronics': 'Elec', 'E&TC': 'E&TC'}
STATUS_COLORS = ['#10B981', '#3B82F6', '#EF4444']   # Returned, Active Issued, Overdue
STATUS_ORDER = ['Returned', 'Active Issued', 'Overdue']

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

def _clean_axes(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# ==============================================================================
# UNIT 1: INTRODUCTION (Design Principles; Categorical, Time Series & Statistical Graphics)
# ==============================================================================

def plot_design_principles_demo():
    """Bad vs Good Chart Demonstration: Poor 3D Clutter vs Clean Horizontal Bar Chart."""
    summary = get_department_aggregates()

    fig = plt.figure(figsize=(14, 5.5))

    # 1. Deliberately Poor Chart (Violates Proportional Ink & Minimal Junk)
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    depts = summary['dept_name'].tolist()
    counts = summary['total_copies'].tolist()
    colors = ['#FF0000', '#00FF00', '#FF00FF', '#FFFF00', '#00FFFF', '#FFA500']

    x = np.arange(len(depts))
    ax1.bar3d(x, np.zeros(len(depts)), np.zeros(len(depts)), np.ones(len(depts)) * 0.75,
              np.ones(len(depts)) * 0.75, counts, color=colors, alpha=0.75)
    ax1.set_title("POOR CHART: 3D Distorted Visual Clutter\n(Violates Proportional Ink & Adds Artificial Occlusion)", fontsize=10.5, color='#991B1B', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(depts, rotation=45, fontsize=8)

    # 2. Corrected Clean Chart (High Data-Ink Ratio, Accurate Linear Scaling)
    ax2 = fig.add_subplot(1, 2, 2)
    summary_sorted = summary.sort_values('total_copies', ascending=True)
    bars = ax2.barh(summary_sorted['dept_name'], summary_sorted['total_copies'], color='#2563EB', height=0.6)
    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 1, bar.get_y() + bar.get_height()/2, f'{int(w)}',
                 va='center', ha='left', fontsize=9.5, fontweight='bold', color='#1E3A8A')
    ax2.set_title("CORRECTED CHART: Clean Horizontal Bar Chart\n(High Data-Ink Ratio, Minimal Junk, Proper Encoding)", fontsize=10.5, color='#166534', fontweight='bold')
    ax2.set_xlabel("Total Book Copies Available")
    ax2.set_ylabel("Department")
    _clean_axes(ax2)

    plt.tight_layout()
    save_chart("design_principles_comparison.png", "Design Principles Comparison")

def plot_data_graphic_types():
    """The three families of data graphics: categorical, time series and statistical."""
    df = get_cleaned_transactions()
    ts = get_monthly_timeseries()

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    # 1. Categorical data -> bar chart
    status_counts = df['simple_status'].value_counts().reindex(STATUS_ORDER).fillna(0)
    axes[0].bar(status_counts.index, status_counts.values, color=STATUS_COLORS, width=0.55)
    for i, v in enumerate(status_counts.values):
        axes[0].text(i, v + 2, f"{int(v)}", ha='center', fontweight='bold')
    axes[0].set_title("Categorical Data Graphic\n(Bar Chart: Loans per Status)", fontweight='bold')
    axes[0].set_ylabel("Number of Loans")
    _clean_axes(axes[0])

    # 2. Time series data -> line chart
    axes[1].plot(ts['issue_month'], ts['issued_count'], marker='o', color='#1E3A8A', linewidth=2.2)
    axes[1].set_title("Time Series Data Graphic\n(Line Chart: Monthly Book Issues)", fontweight='bold')
    axes[1].set_ylabel("Books Issued")
    axes[1].tick_params(axis='x', rotation=45)
    _clean_axes(axes[1])

    # 3. Statistical data -> box plot
    sns.boxplot(x='student_year', y='days_kept', data=df, ax=axes[2], color='#99F6E4')
    axes[2].set_title("Statistical Data Graphic\n(Box Plot: Days Kept by Student Year)", fontweight='bold')
    axes[2].set_xlabel("Student Year")
    axes[2].set_ylabel("Days Kept")

    plt.tight_layout()
    save_chart("data_graphic_types.png", "Categorical / Time Series / Statistical Graphics")

# ==============================================================================
# UNIT 2: PRE-PROCESSING & AESTHETICS (Pairplot, Violin, Heatmap, Interactive,
#         Graphical Perception, Grammar of Graphics, Aesthetics & Scales)
# ==============================================================================

def plot_borrowing_pairplot():
    """Seaborn Pairplot across student-level borrowing metrics coloured by department."""
    summary = get_student_summary()
    pair_df = summary[['total_loans', 'avg_days_kept', 'overdue_loans', 'total_fines', 'primary_dept']]

    g = sns.pairplot(pair_df, hue='primary_dept', corner=True, palette=DEPT_PALETTE, diag_kind='kde',
                     plot_kws={'s': 30, 'alpha': 0.75})
    g.fig.suptitle("Multivariate Pairplot Matrix: Student Borrowing Metrics by Department", y=1.02, fontsize=12, fontweight='bold')
    save_chart("borrowing_pairplot.png", "Pairplot Matrix", fig=g.fig)

def plot_monthly_activity_heatmap():
    """Department x Month Heatmap with continuous colormap."""
    matrix = get_monthly_matrix()

    plt.figure(figsize=(12, 5.5))
    sns.heatmap(matrix, annot=True, fmt='d', cmap='YlGnBu', cbar_kws={'label': 'Monthly Issue Count'}, linewidths=0.5)
    plt.title("Heatmap: Monthly Book Borrowing Intensity by Department\n(Aesthetic Mapping: X=Month, Y=Department, Color=Loan Density)", pad=10)
    plt.xlabel("Month (YYYY-MM)")
    plt.ylabel("Department")
    plt.tight_layout()
    save_chart("activity_heatmap.png", "Activity Heatmap")

def plot_interactive_explorer():
    """Interactive matplotlib window: hover tooltips, department check-boxes (slicer) and a smoothing slider."""
    df = get_cleaned_transactions()
    pivot = df.pivot_table(index='issue_month', columns='dept_name', values='txn_id',
                           aggfunc='count', fill_value=0).sort_index()
    months = list(pivot.index)
    x = np.arange(len(months))

    fig, ax = plt.subplots(figsize=(13, 6.5))
    plt.subplots_adjust(left=0.24, bottom=0.25, right=0.97)
    lines = {}
    for dept in pivot.columns:
        (ln,) = ax.plot(x, pivot[dept].values, marker='o', linewidth=2, color=DEPT_PALETTE.get(dept), label=dept)
        lines[dept] = ln
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45)
    ax.set_ylabel("Books Issued")
    ax.set_title("Interactive Explorer: Monthly Issues by Department\n(Hover a point for details | tick boxes to filter | drag slider to smooth)")
    _clean_axes(ax)

    annot = ax.annotate("", xy=(0, 0), xytext=(12, 12), textcoords='offset points',
                        bbox=dict(boxstyle='round', fc='white', ec='#334155'), arrowprops=dict(arrowstyle='->'))
    annot.set_visible(False)

    # Slicer: department check-boxes
    rax = fig.add_axes([0.02, 0.35, 0.17, 0.45])
    rax.set_title("Department filter", fontsize=9)
    check = CheckButtons(rax, list(lines), [True] * len(lines))
    def on_check(label):
        lines[label].set_visible(not lines[label].get_visible())
        fig.canvas.draw_idle()
    check.on_clicked(on_check)

    # Slider: rolling-mean window (1 = raw data)
    sax = fig.add_axes([0.30, 0.05, 0.55, 0.03])
    slider = Slider(sax, 'Smoothing window (months)', 1, 6, valinit=1, valstep=1)
    def on_slide(val):
        for dept, ln in lines.items():
            ln.set_ydata(pivot[dept].rolling(int(val), min_periods=1).mean().values)
        fig.canvas.draw_idle()
    slider.on_changed(on_slide)

    # Hover tooltip
    def on_hover(event):
        if event.inaxes == ax:
            for dept, ln in lines.items():
                hit, info = ln.contains(event)
                if ln.get_visible() and hit:
                    i = info['ind'][0]
                    annot.xy = (x[i], ln.get_ydata()[i])
                    annot.set_text(f"{dept}\n{months[i]}: {ln.get_ydata()[i]:.1f} issues")
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
    summary = get_department_aggregates().sort_values('total_transactions', ascending=False)
    depts = summary['dept_name'].tolist()
    vals = summary['total_transactions'].values.astype(float)
    colors = [DEPT_PALETTE[d] for d in depts]
    labels = [DEPT_SHORT[d] for d in depts]
    y = np.arange(len(depts))

    fig, axes = plt.subplots(1, 5, figsize=(21, 4.8))

    axes[0].hlines(y, 0, vals, color='#CBD5E1')
    axes[0].scatter(vals, y, color=colors, s=90, zorder=3)
    axes[0].set_xlim(0, vals.max() * 1.1)
    axes[0].set_title("1. Position on common scale\n(most accurate)", fontweight='bold')

    axes[1].barh(y, vals, color=colors, height=0.6)
    axes[1].set_title("2. Length\n(bar chart)", fontweight='bold')
    for ax in axes[:2]:
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        _clean_axes(ax)

    axes[2].pie(vals, labels=labels, colors=colors, startangle=90, counterclock=False,
                wedgeprops=dict(edgecolor='white'))
    axes[2].set_title("3. Angle\n(pie chart)", fontweight='bold')

    axes[3].scatter(y, np.zeros(len(y)), s=vals * 14, color=colors, alpha=0.8)
    axes[3].set_xticks(y)
    axes[3].set_xticklabels(labels)
    axes[3].set_yticks([])
    axes[3].set_xlim(-0.8, len(y) - 0.2)
    axes[3].set_title("4. Area\n(bubble size)", fontweight='bold')

    axes[4].imshow(vals.reshape(-1, 1), cmap='Blues', aspect='auto')
    axes[4].set_yticks(y)
    axes[4].set_yticklabels(labels)
    axes[4].set_xticks([])
    axes[4].grid(False)
    axes[4].set_title("5. Colour intensity\n(least accurate)", fontweight='bold')

    fig.suptitle("Graphical Perception Theory (Cleveland & McGill): Total Loans per Department, Five Encodings\n"
                 "Try ranking CS vs AIML in each panel - position & length are easiest, area & colour hardest",
                 fontsize=12, fontweight='bold', y=1.06)
    plt.tight_layout()
    save_chart("graphical_perception.png", "Graphical Perception Ranking")

def plot_grammar_of_graphics():
    """Grammar of Graphics: building a chart layer by layer, then scales for each type of data."""
    summary = get_student_summary()
    df = get_cleaned_transactions()

    fig, axes = plt.subplots(2, 3, figsize=(17, 10))

    # Row 1: Layering -> data + aesthetics + geometries
    ax = axes[0, 0]
    ax.scatter(summary['total_loans'], summary['total_fines'], color='#64748B', s=25)
    ax.set_title("Layer 1: Data + aes(x, y) + geom_point", fontweight='bold')

    ax = axes[0, 1]
    sns.scatterplot(x='total_loans', y='total_fines', hue='primary_dept', size='avg_days_kept',
                    data=summary, palette=DEPT_PALETTE, sizes=(20, 200), ax=ax, alpha=0.8)
    ax.set_title("Layer 2: + aes(colour = dept, size = avg days kept)", fontweight='bold')
    ax.legend(fontsize=7, loc='upper left')

    ax = axes[0, 2]
    sns.scatterplot(x='total_loans', y='total_fines', hue='primary_dept', size='avg_days_kept',
                    data=summary, palette=DEPT_PALETTE, sizes=(20, 200), ax=ax, alpha=0.8, legend=False)
    sns.regplot(x='total_loans', y='total_fines', data=summary, scatter=False, ax=ax, color='#111827')
    ax.set_title("Layer 3: + geom_smooth (regression layer)", fontweight='bold')
    for ax in axes[0]:
        ax.set_xlabel("Total Loans per Student")
        ax.set_ylabel("Total Fines (Rs)")
        _clean_axes(ax)

    # Row 2: Scales map data values onto aesthetics (one per data type)
    ax = axes[1, 0]
    counts = summary['primary_dept'].value_counts()
    ax.bar([DEPT_SHORT[d] for d in counts.index], counts.values, color=[DEPT_PALETTE[d] for d in counts.index])
    ax.set_title("Nominal data -> qualitative colour scale\n(Students per Department)", fontweight='bold')
    ax.set_ylabel("Students")
    _clean_axes(ax)

    ax = axes[1, 1]
    year_loans = df.groupby('student_year').size()
    ax.bar(year_loans.index.astype(str), year_loans.values, color=sns.color_palette('Blues', 5)[1:])
    ax.set_title("Ordinal data -> sequential colour scale\n(Loans by Student Year 1-4)", fontweight='bold')
    ax.set_xlabel("Student Year")
    ax.set_ylabel("Loans")
    _clean_axes(ax)

    ax = axes[1, 2]
    deviation = df['days_kept'] - 14
    sc = ax.scatter(df['issue_date_dt'], df['days_kept'], c=deviation, cmap='RdBu_r',
                    norm=TwoSlopeNorm(vcenter=0, vmin=deviation.min(), vmax=max(deviation.max(), 1)), s=18)
    fig.colorbar(sc, ax=ax, label="Days vs due date (0 = on due date)")
    ax.axhline(14, color='#111827', linestyle='--', linewidth=1)
    ax.set_title("Continuous data -> diverging colour scale\n(Days Kept, centred on the 14-day due date)", fontweight='bold')
    ax.set_ylabel("Days Kept")
    ax.tick_params(axis='x', rotation=30)

    fig.suptitle("Grammar of Graphics: Layering, Aesthetics, Geometries & Scales", fontsize=14, fontweight='bold')
    plt.tight_layout()
    save_chart("grammar_of_graphics.png", "Grammar of Graphics & Scales")

# ==============================================================================
# UNIT 3: VISUALIZATION DESIGN (Amounts; Distributions: Hist/KDE, ECDF, Q-Q, Skew)
# ==============================================================================

def plot_department_books():
    """Visualizes book holdings across departments (CS, Mech, Civil, AIML, etc.)."""
    summary = get_department_aggregates().sort_values('total_copies', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.bar(summary['dept_name'], summary['total_copies'], color='#2563EB', width=0.55, edgecolor='#1E40AF', linewidth=1)

    # Value annotations on bar tips
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 1, f'{int(height)} copies',
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1E3A8A')

    ax.set_title("Bar Plot: Total Book Copies by Department", pad=12)
    ax.set_xlabel("Academic Department")
    ax.set_ylabel("Total Copies in Inventory")
    ax.set_ylim(0, max(summary['total_copies']) + 8)
    _clean_axes(ax)
    plt.xticks(rotation=15)
    plt.tight_layout()
    save_chart("books_by_department.png", "Books by Department")

def plot_author_analytics():
    """Visualizes top authors by number of book titles and total student borrow count."""
    author_df = get_author_aggregates().head(10).sort_values('total_borrowed', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = np.arange(len(author_df))
    bars = ax.barh(y_pos, author_df['total_borrowed'], color='#0D9488', height=0.6, alpha=0.9)

    for bar, (_, row) in zip(bars, author_df.iterrows()):
        w = bar.get_width()
        ax.text(w + 0.3, bar.get_y() + bar.get_height()/2, f"{int(w)} loans ({int(row['book_titles'])} titles)",
                va='center', ha='left', fontsize=9, fontweight='bold', color='#134E4A')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(author_df['author'], fontsize=9.5)
    ax.set_xlabel("Total Times Borrowed by Students")
    ax.set_title("Horizontal Bar Plot: Top 10 Most Borrowed Authors", pad=12)
    _clean_axes(ax)
    plt.tight_layout()
    save_chart("author_distribution.png", "Author Analytics")

def plot_cleveland_dot_plot():
    """Cleveland Dot Plot comparing department book holdings (cleaner than bar charts)."""
    summary = get_department_aggregates().sort_values('total_copies')

    plt.figure(figsize=(9, 5))
    plt.hlines(y=summary['dept_name'], xmin=0, xmax=summary['total_copies'], color='#94A3B8', alpha=0.8, linewidth=1.5)
    plt.scatter(summary['total_copies'], summary['dept_name'], color='#D97706', s=120, zorder=3, edgecolors='#78350F')

    for _, row in summary.iterrows():
        plt.text(row['total_copies'] + 1, row['dept_name'], f"{int(row['total_copies'])}",
                 va='center', fontsize=9.5, fontweight='bold', color='#78350F')

    plt.title("Cleveland Dot Plot: Department Book Inventory\n(High Data-Ink Alternative to Bar Chart)", pad=10)
    plt.xlabel("Total Book Copies")
    plt.ylabel("Department")
    plt.xlim(0, max(summary['total_copies']) + 10)
    plt.tight_layout()
    save_chart("dot_books_per_dept.png", "Cleveland Dot Plot")

def plot_loan_status_grouped_stacked():
    """Grouped and Stacked Bar Charts of loan status (Returned, Active, Overdue) per department."""
    summary = get_department_aggregates()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # 1. Grouped Bar Chart
    melted = summary.melt(id_vars=['dept_name'], value_vars=STATUS_ORDER, var_name='Status', value_name='Count')
    sns.barplot(x='dept_name', y='Count', hue='Status', data=melted, ax=axes[0], palette=STATUS_COLORS)
    axes[0].set_title("Grouped Bar Chart: Loan Status by Department", fontweight='bold')
    axes[0].set_xlabel("Department")
    axes[0].set_ylabel("Transaction Count")
    axes[0].tick_params(axis='x', rotation=20)

    # 2. Stacked Bar Chart
    summary_idx = summary.set_index('dept_name')[STATUS_ORDER]
    summary_idx.plot(kind='bar', stacked=True, ax=axes[1], color=STATUS_COLORS, edgecolor='white')
    axes[1].set_title("Stacked Bar Chart: Loan Status by Department", fontweight='bold')
    axes[1].set_xlabel("Department")
    axes[1].set_ylabel("Total Transactions")
    axes[1].tick_params(axis='x', rotation=20)
    axes[1].legend(title="Status")

    plt.tight_layout()
    save_chart("loan_status_breakdown.png", "Grouped & Stacked Status Breakdown")

def plot_duration_distributions():
    """Visualizing single & multiple distributions: Histogram + KDE, Overlaid KDEs, and Violin Plot."""
    df = get_cleaned_transactions()

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # 1. Single Distribution: Histogram + KDE
    sns.histplot(df['days_kept'], kde=True, ax=axes[0], color='#0D9488', bins=18, stat='density')
    axes[0].set_title("Single Distribution: Issue Duration (Days Kept)\n(Histogram + KDE Density)", fontweight='bold')
    axes[0].set_xlabel("Days Kept")
    axes[0].set_ylabel("Density")

    # 2. Overlaid Multiple Distributions across Departments
    sns.kdeplot(data=df, x='days_kept', hue='dept_name', ax=axes[1], common_norm=False, palette=DEPT_PALETTE, linewidth=1.8)
    axes[1].set_title("Multiple Distributions at the Same Time\n(Overlaid KDE Across 6 Departments)", fontweight='bold')
    axes[1].set_xlabel("Days Kept")
    axes[1].set_ylabel("Density")

    # 3. Violin Plot across Departments
    sns.violinplot(x='dept_name', y='days_kept', hue='dept_name', data=df, ax=axes[2],
                   palette=DEPT_PALETTE, inner='quartile', cut=0, legend=False)
    axes[2].set_title("Violin Plot: Duration Spread per Dept\n(Density & Quartiles)", fontweight='bold')
    axes[2].set_xlabel("Department")
    axes[2].set_ylabel("Days Kept")
    axes[2].tick_params(axis='x', rotation=25)

    plt.tight_layout()
    save_chart("duration_distributions.png", "Duration Distributions")

def plot_statistical_diagnostics():
    """Statistical graphics: ECDF, Normal Q-Q Plot, and Skewed vs Log Transformation."""
    df = get_cleaned_transactions()
    overdue_fines = df[df['effective_fine'] > 0]['effective_fine']
    log_fines = np.log1p(overdue_fines)

    fig, axes = plt.subplots(1, 4, figsize=(21, 5))

    # 1. ECDF Plot
    sns.ecdfplot(overdue_fines, ax=axes[0], color='#7C3AED', linewidth=2.2)
    axes[0].set_title("Empirical Cumulative Distribution Function\n(ECDF of Overdue Fines)", fontweight='bold')
    axes[0].set_xlabel("Fine Amount (Rs)")
    axes[0].set_ylabel("Cumulative Proportion")

    # 2. Q-Q Plot
    stats.probplot(overdue_fines, dist="norm", plot=axes[1])
    axes[1].set_title("Normal Q-Q Plot\n(Raw Fines: curve = not normal)", fontweight='bold')
    axes[1].get_lines()[0].set_markerfacecolor('#2563EB')
    axes[1].get_lines()[0].set_markersize(5)
    axes[1].get_lines()[1].set_color('#DC2626')

    # 3. Highly skewed distribution (raw)
    sns.histplot(overdue_fines, bins=15, kde=True, ax=axes[2], color='#DC2626')
    axes[2].set_title(f"Highly Skewed Distribution\n(Raw Fines, skewness = {stats.skew(overdue_fines):.2f})", fontweight='bold')
    axes[2].set_xlabel("Fine Amount (Rs)")

    # 4. After log transform
    sns.histplot(log_fines, bins=15, kde=True, ax=axes[3], color='#0D9488')
    axes[3].set_title(f"After log1p Transform\n(skewness = {stats.skew(log_fines):.2f})", fontweight='bold')
    axes[3].set_xlabel("log1p(Fine)")

    plt.tight_layout()
    save_chart("statistical_diagnostics.png", "Statistical Diagnostics (ECDF, Q-Q, Skew & Log Transform)")

# ==============================================================================
# UNIT 4: ADVANCED DESIGN (Many Distributions, Proportions, Nested Proportions, Associations)
# ==============================================================================

def plot_vertical_vs_horizontal_layouts():
    """Many distributions at once: along the vertical axis (box + strip) vs horizontal axis (ridgeline)."""
    df = get_cleaned_transactions()
    depts = [d for d in DEPT_PALETTE if d in df['dept_name'].unique()]

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Vertical axis: boxplots with jittered strip chart
    sns.boxplot(x='dept_name', y='days_kept', data=df, order=depts, ax=axes[0], color='white', fliersize=0)
    sns.stripplot(x='dept_name', y='days_kept', hue='dept_name', data=df, order=depts, ax=axes[0],
                  palette=DEPT_PALETTE, size=3.5, alpha=0.6, jitter=0.25, legend=False)
    axes[0].set_title("Distributions along the VERTICAL axis\n(Box Plot + Jittered Strip Chart)", fontweight='bold')
    axes[0].set_xlabel("Department")
    axes[0].set_ylabel("Days Kept")
    axes[0].tick_params(axis='x', rotation=20)

    # Horizontal axis: ridgeline plot (one shifted density per department)
    grid = np.linspace(0, df['days_kept'].max() + 5, 300)
    for i, dept in enumerate(reversed(depts)):
        kde = stats.gaussian_kde(df[df['dept_name'] == dept]['days_kept'])
        dens = kde(grid) / kde(grid).max() * 0.9
        axes[1].fill_between(grid, i, i + dens, color=DEPT_PALETTE[dept], alpha=0.7)
        axes[1].plot(grid, i + dens, color='white', linewidth=1)
    axes[1].set_yticks(range(len(depts)))
    axes[1].set_yticklabels(list(reversed(depts)))
    axes[1].set_title("Distributions along the HORIZONTAL axis\n(Ridgeline Plot of Days Kept)", fontweight='bold')
    axes[1].set_xlabel("Days Kept")
    _clean_axes(axes[1])

    plt.tight_layout()
    save_chart("vertical_vs_horizontal.png", "Vertical vs Horizontal Distributions")

def plot_proportions():
    """A case for pie charts: the same proportions as pie, side-by-side bars, stacked bar, and stacked densities."""
    summary = get_department_aggregates().sort_values('total_transactions', ascending=False)
    df = get_cleaned_transactions()
    depts = summary['dept_name'].tolist()
    shares = summary['total_transactions'] / summary['total_transactions'].sum() * 100
    colors = [DEPT_PALETTE[d] for d in depts]

    fig, axes = plt.subplots(1, 4, figsize=(22, 5.2))

    # 1. Pie chart
    axes[0].pie(shares, labels=[DEPT_SHORT[d] for d in depts], autopct='%1.1f%%', startangle=90,
                counterclock=False, colors=colors, wedgeprops=dict(edgecolor='white'), textprops={'fontsize': 9})
    axes[0].set_title("Pie Chart\n(Share of Total Loans)", fontweight='bold')

    # 2. Side-by-side bars
    axes[1].bar([DEPT_SHORT[d] for d in depts], shares, color=colors)
    for i, v in enumerate(shares):
        axes[1].text(i, v + 0.3, f"{v:.1f}%", ha='center', fontsize=9)
    axes[1].set_title("Side-by-Side Bars\n(Same Shares)", fontweight='bold')
    axes[1].set_ylabel("Share of Loans (%)")
    _clean_axes(axes[1])

    # 3. Single stacked bar
    left = 0
    for d, v, c in zip(depts, shares, colors):
        axes[2].barh(0, v, left=left, color=c, edgecolor='white')
        axes[2].text(left + v / 2, 0, f"{DEPT_SHORT[d]}\n{v:.0f}%", ha='center', va='center', color='white', fontsize=8.5, fontweight='bold')
        left += v
    axes[2].set_xlim(0, 100)
    axes[2].set_yticks([])
    axes[2].set_xlabel("Cumulative Share (%)")
    axes[2].set_title("Stacked Bar\n(Parts Adding up to 100%)", fontweight='bold')

    # 4. Stacked densities: how the department mix changes along loan length
    sns.kdeplot(data=df, x='days_kept', hue='dept_name', multiple='fill', palette=DEPT_PALETTE,
                ax=axes[3], linewidth=0.5, clip=(1, df['days_kept'].max()))
    axes[3].set_title("Stacked Densities\n(Department Mix vs Days Kept)", fontweight='bold')
    axes[3].set_xlabel("Days Kept")
    axes[3].set_ylabel("Proportion")

    fig.suptitle("Visualizing Proportions: Pie vs Side-by-Side Bars vs Stacked Bar vs Stacked Densities", fontsize=13, fontweight='bold', y=1.03)
    plt.tight_layout()
    save_chart("proportions.png", "Proportions (Pie, Side-by-Side, Stacked, Stacked Densities)")

def plot_parts_of_total():
    """Visualizing proportions separately as parts of the total (each department against all loans)."""
    df = get_cleaned_transactions()
    bins = np.arange(0, df['days_kept'].max() + 4, 3)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
    for ax, dept in zip(axes.flat, DEPT_PALETTE):
        part = df[df['dept_name'] == dept]['days_kept']
        ax.hist(df['days_kept'], bins=bins, color='#CBD5E1', label='All loans (total)')
        ax.hist(part, bins=bins, color=DEPT_PALETTE[dept], label=dept)
        ax.set_title(f"{dept}: {len(part)} of {len(df)} loans ({len(part) / len(df) * 100:.0f}%)", fontweight='bold', fontsize=10.5)
        ax.legend(fontsize=8)
        _clean_axes(ax)
    for ax in axes[1]:
        ax.set_xlabel("Days Kept")
    for ax in axes[:, 0]:
        ax.set_ylabel("Loans")

    fig.suptitle("Proportions Shown Separately as Parts of the Total\n(Grey = all loans, colour = one department's part)", fontsize=13, fontweight='bold')
    plt.tight_layout()
    save_chart("parts_of_total.png", "Parts of the Total (Small Multiples)")

def plot_nested_proportions():
    """Nested proportions: treemap (Department -> Book) and nested donut (Department -> Loan Status)."""
    df = get_cleaned_transactions()

    fig, axes = plt.subplots(1, 2, figsize=(17, 7))

    # 1. Treemap: departments as blocks, books nested inside (top 4 books per dept)
    tree = (df.groupby(['dept_name', 'book_title']).size().reset_index(name='loans')
              .sort_values(['dept_name', 'loans'], ascending=[True, False]).groupby('dept_name').head(4))
    labels = [f"{DEPT_SHORT[r.dept_name]}\n{r.book_title[:18]}\n({r.loans})" for r in tree.itertuples()]
    squarify.plot(sizes=tree['loans'], label=labels, color=[DEPT_PALETTE[d] for d in tree['dept_name']],
                  alpha=0.85, ax=axes[0], text_kwargs={'fontsize': 7, 'color': 'white'}, ec='white', linewidth=1.5)
    axes[0].set_title("Treemap: Department -> Top Book Titles\n(Area = Loans, Colour = Department)", fontweight='bold')
    axes[0].axis('off')

    # 2. Nested donut: inner ring = department, outer ring = status inside each department
    nested = df.groupby(['dept_name', 'simple_status']).size().unstack(fill_value=0)
    nested = nested.reindex(columns=STATUS_ORDER, fill_value=0).loc[[d for d in DEPT_PALETTE if d in nested.index]]
    axes[1].pie(nested.sum(axis=1), radius=0.7, labels=[DEPT_SHORT[d] for d in nested.index], labeldistance=0.55,
                colors=[DEPT_PALETTE[d] for d in nested.index], wedgeprops=dict(width=0.35, edgecolor='white'),
                textprops={'color': 'white', 'fontsize': 9, 'fontweight': 'bold'})
    axes[1].pie(nested.values.flatten(), radius=1.0, colors=STATUS_COLORS * len(nested),
                wedgeprops=dict(width=0.3, edgecolor='white'))
    axes[1].legend([Rectangle((0, 0), 1, 1, color=c) for c in STATUS_COLORS], STATUS_ORDER,
                   title="Outer ring: status", loc='lower left', fontsize=8.5)
    axes[1].set_title("Nested Donut: Department (inner) -> Loan Status (outer)", fontweight='bold')

    plt.tight_layout()
    save_chart("nested_proportions.png", "Nested Proportions (Treemap & Nested Donut)")

def plot_associations_and_pca():
    """Associations among quantitative variables: scatter plot, correlogram and PCA dimension reduction."""
    summary = get_student_summary()

    fig = plt.figure(figsize=(17, 5.2))

    # 1. Scatter plot of two quantitative variables
    ax1 = fig.add_subplot(1, 3, 1)
    sns.scatterplot(x='total_loans', y='total_fines', hue='primary_dept', data=summary, s=55, ax=ax1, palette=DEPT_PALETTE)
    r, _ = stats.pearsonr(summary['total_loans'], summary['total_fines'])
    ax1.set_title(f"Scatter Plot: Loans vs Fines per Student\n(Pearson r = {r:.2f})", fontweight='bold', fontsize=10.5)
    ax1.set_xlabel("Total Loans")
    ax1.set_ylabel("Total Fines (Rs)")
    ax1.legend(fontsize=7)

    # 2. Correlogram (Correlation Heatmap)
    ax2 = fig.add_subplot(1, 3, 2)
    corr_vars = summary[['total_loans', 'avg_days_kept', 'overdue_loans', 'total_fines', 'year']].corr()
    sns.heatmap(corr_vars, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, square=True, ax=ax2, cbar_kws={'shrink': 0.8})
    ax2.set_title("Correlogram: Matrix of Quantitative Variables\n(Linear Association Strength)", fontweight='bold', fontsize=10.5)

    # 3. PCA Dimension Reduction of Student Borrowing Profiles
    ax3 = fig.add_subplot(1, 3, 3)
    matrix = get_student_feature_matrix()
    dept_cols = [c for c in matrix.columns if c not in ['student_id', 'name', 'dept_id', 'home_state', 'primary_dept']]
    pca = PCA(n_components=2, random_state=42)
    components = pca.fit_transform(matrix[dept_cols].values)
    pca_df = pd.DataFrame(components, columns=['PC1', 'PC2'])
    pca_df['Primary Dept'] = matrix['primary_dept']

    sns.scatterplot(x='PC1', y='PC2', hue='Primary Dept', data=pca_df, s=60, ax=ax3, palette=DEPT_PALETTE)
    ax3.set_title(f"PCA Dimension Reduction (2D Projection)\nStudent Borrowing Profiles (Explained Var: {sum(pca.explained_variance_ratio_)*100:.1f}%)",
                  fontweight='bold', fontsize=10.5)
    ax3.legend(fontsize=7)

    plt.tight_layout()
    save_chart("associations_and_pca.png", "Associations & PCA")

def plot_paired_slope_chart():
    """Paired data: each department's loans in the first vs second half of the year (slope chart)."""
    df = get_cleaned_transactions()
    midpoint = df['issue_date_dt'].min() + (df['issue_date_dt'].max() - df['issue_date_dt'].min()) / 2
    df['half'] = np.where(df['issue_date_dt'] < midpoint, 'First 6 Months', 'Last 6 Months')
    paired = df.groupby(['dept_name', 'half']).size().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(8, 6))
    for dept, row in paired.iterrows():
        a, b = row['First 6 Months'], row['Last 6 Months']
        ax.plot([0, 1], [a, b], marker='o', markersize=8, linewidth=2.2, color=DEPT_PALETTE[dept])
        ax.text(-0.04, a, f"{DEPT_SHORT[dept]} {a}", ha='right', va='center', fontsize=9, color=DEPT_PALETTE[dept])
        ax.text(1.04, b, f"{b} {DEPT_SHORT[dept]} ({'+' if b >= a else ''}{b - a})", ha='left', va='center', fontsize=9, color=DEPT_PALETTE[dept])
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['First 6 Months', 'Last 6 Months'])
    ax.set_xlim(-0.35, 1.35)
    ax.set_ylabel("Loans")
    ax.set_title("Paired Data Slope Chart: Loans per Department\n(Same department measured in two periods)", pad=10)
    _clean_axes(ax)
    plt.tight_layout()
    save_chart("paired_slope_chart.png", "Paired Slope Chart")

# ==============================================================================
# UNIT 5: TIME SERIES, TRENDS & GEOSPATIAL (Projections, Layers, Choropleth, Cartogram)
# ==============================================================================

def plot_time_series_and_trends():
    """Individual & multiple time series, smoothing (moving average, LOESS) and defined functional forms."""
    ts = get_monthly_timeseries()
    df = get_cleaned_transactions()
    monthly_dept = df.groupby(['issue_month', 'dept_name']).size().reset_index(name='issued_count')
    x = np.arange(len(ts))
    y = ts['issued_count'].values

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # 1. Individual time series
    axes[0, 0].plot(ts['issue_month'], y, marker='o', color='#1E3A8A', linewidth=2.2)
    axes[0, 0].set_title("Individual Time Series: Monthly Book Issues", fontweight='bold')

    # 2. Multiple time series
    sns.lineplot(x='issue_month', y='issued_count', hue='dept_name', data=monthly_dept, marker='o',
                 ax=axes[0, 1], palette=DEPT_PALETTE)
    axes[0, 1].set_title("Multiple Time Series: Issues by Department", fontweight='bold')
    axes[0, 1].legend(fontsize=8)

    # 3. Smoothing: moving average and LOESS
    loess = sm.nonparametric.lowess(y, x, frac=0.5)
    axes[1, 0].plot(ts['issue_month'], y, label='Actual Issues', alpha=0.5, color='gray', linestyle='--', marker='o')
    axes[1, 0].plot(ts['issue_month'], ts['rolling_3m_issues'], label='3-Month Moving Average', color='#DC2626', linewidth=2.2)
    axes[1, 0].plot(ts['issue_month'], loess[:, 1], label='LOESS Smoother', color='#0D9488', linewidth=2.2)
    axes[1, 0].set_title("Trend Smoothing: Moving Average vs LOESS", fontweight='bold')
    axes[1, 0].legend(fontsize=8.5)

    # 4. Trend with a defined functional form (linear & quadratic least squares)
    axes[1, 1].plot(ts['issue_month'], y, label='Actual Issues', alpha=0.5, color='gray', marker='o')
    for deg, color, name in [(1, '#2563EB', 'Linear'), (2, '#D97706', 'Quadratic')]:
        fit = np.polyval(np.polyfit(x, y, deg), x)
        r2 = 1 - ((y - fit) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        axes[1, 1].plot(ts['issue_month'], fit, color=color, linewidth=2.2, label=f'{name} fit (R² = {r2:.2f})')
    axes[1, 1].set_title("Trend with a Defined Functional Form", fontweight='bold')
    axes[1, 1].legend(fontsize=8.5)

    for ax in axes.flat:
        ax.set_xlabel("Month (YYYY-MM)")
        ax.set_ylabel("Books Issued")
        ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    save_chart("time_series_and_trends.png", "Time Series & Trends")

def plot_advanced_time_series():
    """Dose-response curve, two or more response variables, detrending and time-series decomposition."""
    ts = get_monthly_timeseries()
    df = get_cleaned_transactions()
    overdue_df = df[df['overdue_days'] > 0]
    x = np.arange(len(ts))
    y = ts['issued_count'].values

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # 1. Dose-Response Curve (Fine buildup vs overdue days)
    sns.regplot(x='overdue_days', y='effective_fine', data=overdue_df, order=2, ax=axes[0, 0],
                scatter_kws={'alpha': 0.6, 'color': '#D97706'}, line_kws={'color': '#1E3A8A', 'linewidth': 2})
    axes[0, 0].set_title("Dose-Response Curve: Fine Buildup\n(Overdue Days = Dose, Fine Rs = Response)", fontweight='bold')
    axes[0, 0].set_xlabel("Overdue Days")
    axes[0, 0].set_ylabel("Fine Amount (Rs)")

    # 2. Two or more response variables over time (dual axis)
    ax2 = axes[0, 1]
    ax2.plot(ts['issue_month'], ts['issued_count'], color='#2563EB', marker='o', label='Issued Books')
    ax2.plot(ts['issue_month'], ts['returned_count'], color='#10B981', marker='s', label='Returned Books')
    ax2.set_ylabel("Book Count")
    ax2.tick_params(axis='x', rotation=45)
    ax2_twin = ax2.twinx()
    ax2_twin.plot(ts['issue_month'], ts['total_fines'], color='#DC2626', marker='^', linestyle='--', label='Fines (Rs)')
    ax2_twin.set_ylabel("Fines (Rs)", color='#DC2626')
    ax2_twin.grid(False)
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, fontsize=8.5, loc='upper left')
    ax2.set_title("Time Series of Multiple Response Variables\n(Issues, Returns & Fines)", fontweight='bold')

    # 3. Detrending: subtract the fitted linear trend
    trend = np.polyval(np.polyfit(x, y, 1), x)
    detrended = y - trend
    axes[1, 0].bar(ts['issue_month'], detrended, color=np.where(detrended >= 0, '#10B981', '#EF4444'))
    axes[1, 0].axhline(0, color='#111827', linewidth=1)
    axes[1, 0].set_title("Detrended Series (Actual - Linear Trend)\n(Above/below the long-run trend)", fontweight='bold')
    axes[1, 0].set_ylabel("Deviation from Trend")
    axes[1, 0].tick_params(axis='x', rotation=45)

    # 4. Seasonal Decomposition (Trend, Seasonal, Residual)
    ts_decomp = ts.set_index('issue_month_dt')['issued_count']
    res = seasonal_decompose(ts_decomp, model='additive', period=3)
    axes[1, 1].plot(ts_decomp.index, ts_decomp.values, color='gray', alpha=0.5, label='Observed')
    axes[1, 1].plot(res.trend, color='#DC2626', label='Trend')
    axes[1, 1].plot(res.seasonal, color='#10B981', label='Seasonal (period = 3 months)')
    axes[1, 1].plot(res.resid, color='#7C3AED', label='Residual')
    axes[1, 1].set_title("Time Series Decomposition\n(Observed = Trend + Seasonal + Residual)", fontweight='bold')
    axes[1, 1].tick_params(axis='x', rotation=45)
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
    """Geospatial projections: the same student-origin points drawn in three projections."""
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
        ax.scatter(px_, py_, s=geo['student_count'] * 25, color='#2563EB', alpha=0.6, edgecolors='#1E3A8A')
        for s, a, b in zip(geo['home_state'], px_, py_):
            ax.text(a, b, s, fontsize=7.5, ha='center', va='bottom')
        ax.set_title(titles[kind], fontweight='bold')
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("Map Projections: Student Home States (bubble = number of students)", fontsize=13, fontweight='bold')
    plt.tight_layout()
    save_chart("map_projections.png", "Map Projections")

def plot_map_layers():
    """Geospatial layers: base graticule -> student-origin data layer -> campus & travel-route layer."""
    geo = get_state_geospatial_summary()
    geo = geo[geo['home_state'].isin(STATE_COORDS)]
    campus_name, campus_lat, campus_lon = CAMPUS_LOCATION

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
            # Layer 2: data layer (students per home state)
            for _, r in geo.iterrows():
                lat, lon = STATE_COORDS[r['home_state']]
                ax.scatter(lon, lat, s=r['student_count'] * 30, color='#3B82F6', alpha=0.55, edgecolors='#1E40AF', zorder=3)
        if i == 2:
            # Layer 3: annotation layer (campus + routes students travel)
            for _, r in geo.iterrows():
                lat, lon = STATE_COORDS[r['home_state']]
                ax.plot([lon, campus_lon], [lat, campus_lat], color='#DC2626', linewidth=0.5 + r['total_issues'] / 25, alpha=0.6, zorder=2)
            ax.scatter(campus_lon, campus_lat, marker='*', s=400, color='#DC2626', edgecolors='black', zorder=4)
            ax.text(campus_lon - 0.5, campus_lat - 1.2, campus_name, fontsize=9, fontweight='bold', color='#991B1B', ha='right')
    axes[0].set_title("Layer 1: Base Map\n(coordinate grid + state labels)", fontweight='bold')
    axes[1].set_title("Layer 1 + 2: Data Layer\n(bubble = students from each state)", fontweight='bold')
    axes[2].set_title("Layer 1 + 2 + 3: Annotation Layer\n(campus + routes, width = book loans)", fontweight='bold')
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
    """Choropleth (tile-grid) of Indian home states: raw counts vs normalised rate."""
    geo = get_state_geospatial_summary().set_index('home_state')
    students = geo['student_count'].to_dict()
    per_student = (geo['total_issues'] / geo['student_count'].replace(0, np.nan)).fillna(0).to_dict()

    fig, axes = plt.subplots(1, 2, figsize=(15, 7.5))
    _draw_state_tiles(axes[0], students, 'Blues', "Students")
    axes[0].set_title("Choropleth: Students per Home State\n(raw count, sequential colour scale)", fontweight='bold')
    _draw_state_tiles(axes[1], per_student, 'YlOrRd', "Loans per student", fmt="{:.1f}")
    axes[1].set_title("Choropleth: Book Loans per Student\n(normalised rate - fair comparison across states)", fontweight='bold')
    fig.suptitle("Choropleth Mapping on a Tile-Grid Map of India (tiles placed by rough geography)", fontsize=13, fontweight='bold', y=1.04)
    plt.tight_layout()
    save_chart("choropleth_map.png", "Choropleth Map")

def plot_proportional_cartogram():
    """Cartograms: proportional symbol map on lat/lon and a tile cartogram where tile size = loans."""
    geo = get_state_geospatial_summary()
    geo = geo[geo['home_state'].isin(STATE_COORDS)]

    fig, axes = plt.subplots(1, 2, figsize=(16, 7.5))
    for _, row in geo.iterrows():
        lat, lon = STATE_COORDS[row['home_state']]
        issues = row['total_issues']
        axes[0].scatter(lon, lat, s=issues * 45 + 120, alpha=0.55, color='#2563EB', edgecolors='#1E3A8A', linewidth=1.5)
        axes[0].text(lon, lat, f"{row['home_state']}\n({int(issues)})", ha='center', va='center', fontsize=8.5, fontweight='bold')
    axes[0].set_title("Proportional Symbol Map (Projection: WGS84 lat/lon)\nBubble area = total book loans", fontweight='bold')
    axes[0].set_xlabel("Longitude (°E)")
    axes[0].set_ylabel("Latitude (°N)")

    issues = geo.set_index('home_state')['total_issues'].to_dict()
    sizes = {s: 0.98 * np.sqrt(issues.get(s, 0) / max(issues.values())) for s in STATE_TILES}
    _draw_state_tiles(axes[1], issues, 'Blues', "Loans", sizes=sizes)
    axes[1].set_title("Tile Cartogram\nTile area resized in proportion to total book loans", fontweight='bold')
    plt.tight_layout()
    save_chart("cartogram.png", "Cartograms")

# ==============================================================================
# SELF-STUDY CASE STUDY: SUPPLY CHAIN & LOGISTICS DASHBOARD
# (Route mapping, delivery status KPIs, filtering by region)
# ==============================================================================

def _kpi_card(ax, title, value, color):
    ax.add_patch(FancyBboxPatch((0.03, 0.08), 0.94, 0.84, boxstyle='round,pad=0.02', fc='#F8FAFC', ec=color, linewidth=2))
    ax.text(0.5, 0.62, value, ha='center', va='center', fontsize=20, fontweight='bold', color=color)
    ax.text(0.5, 0.28, title, ha='center', va='center', fontsize=9.5, color='#334155')
    ax.axis('off')

def _gauge(ax, pct, target):
    """Semi-circular gauge (0-100%) with a target marker."""
    for start, end, c in [(0, 60, '#FCA5A5'), (60, 85, '#FDE68A'), (85, 100, '#A7F3D0')]:
        ax.add_patch(Wedge((0, 0), 1, 180 - end * 1.8, 180 - start * 1.8, width=0.3, color=c))
    ang = np.radians(180 - pct * 1.8)
    ax.plot([0, 0.75 * np.cos(ang)], [0, 0.75 * np.sin(ang)], color='#111827', linewidth=3)
    t_ang = np.radians(180 - target * 1.8)
    ax.plot([0.68 * np.cos(t_ang), 1.02 * np.cos(t_ang)], [0.68 * np.sin(t_ang), 1.02 * np.sin(t_ang)], color='#1D4ED8', linewidth=3)
    ax.text(0, -0.22, f"{pct:.1f}%", ha='center', fontsize=16, fontweight='bold')
    ax.text(0, -0.45, f"On-time delivery (target {target}%)", ha='center', fontsize=8.5, color='#334155')
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.55, 1.1)
    ax.set_aspect('equal')
    ax.axis('off')

def plot_supply_chain_dashboard(region=None):
    """Supply Chain & Logistics dashboard: KPI cards, gauge, route map, status by region, monthly trend."""
    ship = get_cleaned_shipments(region)
    if ship.empty:
        print(" [!] No shipments for this filter.")
        return None
    delivered = ship[ship['status'].str.startswith('Delivered')]
    on_time_pct = (delivered['status'] == 'Delivered On-Time').mean() * 100 if len(delivered) else 0.0
    status_order = ['Delivered On-Time', 'Delivered Late', 'In Transit', 'Delayed In Transit']
    status_colors = ['#10B981', '#F59E0B', '#3B82F6', '#EF4444']

    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 5, height_ratios=[0.8, 2.2, 1.4], hspace=0.45, wspace=0.55)

    # Row 1: KPI cards + gauge
    _kpi_card(fig.add_subplot(gs[0, 0]), "Total Shipments", f"{len(ship)}", '#1E3A8A')
    _kpi_card(fig.add_subplot(gs[0, 1]), "Units Shipped", f"{ship['quantity'].sum()}", '#0D9488')
    _kpi_card(fig.add_subplot(gs[0, 2]), "Open (In Transit)", f"{(~ship['status'].str.startswith('Delivered')).sum()}", '#3B82F6')
    _kpi_card(fig.add_subplot(gs[0, 3]), "Avg Transit Days", f"{delivered['transit_days'].mean():.1f}", '#D97706')
    _gauge(fig.add_subplot(gs[0, 4]), on_time_pct, 90)

    # Row 2 left: route map (publisher hubs -> campus)
    ax_map = fig.add_subplot(gs[1, :3])
    campus_name, c_lat, c_lon = CAMPUS_LOCATION
    routes = ship.groupby(['origin_city', 'origin_state']).agg(
        shipments=('shipment_id', 'count'),
        on_time=('status', lambda s: (s == 'Delivered On-Time').sum() / max(1, s.str.startswith('Delivered').sum()) * 100)
    ).reset_index()
    cmap = plt.get_cmap('RdYlGn')
    label_offsets = {'Mumbai': (-0.6, -0.4, 'right'), 'Ahmedabad': (-0.6, 0, 'right'),
                     'Bengaluru': (-0.6, -1.4, 'right'), 'Chennai': (0.6, -1.2, 'left')}
    for _, r in routes.iterrows():
        _, _, lat, lon = PUBLISHER_HUBS[r['origin_state']]
        ax_map.annotate("", xy=(c_lon, c_lat), xytext=(lon, lat),
                        arrowprops=dict(arrowstyle='-|>', color=cmap(r['on_time'] / 100), lw=1 + r['shipments'] / 6,
                                        connectionstyle='arc3,rad=0.15', alpha=0.85))
        ax_map.scatter(lon, lat, s=120, color='#1E3A8A', zorder=3)
        dx, dy, ha = label_offsets.get(r['origin_city'], (0, 0.7, 'center'))
        ax_map.text(lon + dx, lat + dy, f"{r['origin_city']}\n{r['shipments']} shipments, {r['on_time']:.0f}% on-time",
                    ha=ha, fontsize=8.5)
    ax_map.scatter(c_lon, c_lat, marker='*', s=500, color='#DC2626', edgecolors='black', zorder=4)
    ax_map.text(c_lon + 0.6, c_lat - 0.8, campus_name, fontsize=10, fontweight='bold', color='#991B1B')
    ax_map.set_xlim(68, 92)
    ax_map.set_ylim(9, 31)
    ax_map.set_aspect('equal')
    ax_map.set_xlabel("Longitude (°E)")
    ax_map.set_ylabel("Latitude (°N)")
    ax_map.set_title("Route Map: Publisher Hubs -> Campus\n(arrow width = shipments, colour = on-time %: red low, green high)", fontweight='bold')

    # Row 2 right: delivery status by region (stacked bars)
    ax_reg = fig.add_subplot(gs[1, 3:])
    by_region = ship.groupby(['region', 'status']).size().unstack(fill_value=0).reindex(columns=status_order, fill_value=0)
    by_region.plot(kind='barh', stacked=True, ax=ax_reg, color=status_colors, edgecolor='white')
    ax_reg.set_title("Delivery Status by Region", fontweight='bold')
    ax_reg.set_xlabel("Shipments")
    ax_reg.set_ylabel("Region")
    ax_reg.legend(fontsize=8, loc='lower right')

    # Row 3: monthly on-time % trend and shipments per courier
    ax_tr = fig.add_subplot(gs[2, :3])
    monthly = delivered.groupby('dispatch_month')['status'].apply(lambda s: (s == 'Delivered On-Time').mean() * 100)
    ax_tr.plot(monthly.index, monthly.values, marker='o', color='#0D9488', linewidth=2)
    ax_tr.axhline(90, color='#1D4ED8', linestyle='--', linewidth=1, label='Target 90%')
    ax_tr.set_ylim(0, 105)
    ax_tr.set_ylabel("On-time %")
    ax_tr.tick_params(axis='x', rotation=45)
    ax_tr.legend(fontsize=8)
    ax_tr.set_title("Monthly On-Time Delivery % (by dispatch month)", fontweight='bold')

    ax_cr = fig.add_subplot(gs[2, 3:])
    courier = delivered.groupby('courier')['delay_days'].mean().sort_values()
    ax_cr.barh(courier.index, courier.values, color='#F59E0B')
    ax_cr.set_xlabel("Average Delay (days)")
    ax_cr.set_title("Average Delay by Courier", fontweight='bold')
    _clean_axes(ax_cr)

    fig.suptitle(f"Supply Chain & Logistics Dashboard - Book Procurement Shipments | Region filter: {region or 'All Regions'}",
                 fontsize=15, fontweight='bold', y=0.98)
    suffix = (region or 'all').lower()
    return save_chart(f"supply_chain_dashboard_{suffix}.png", f"Supply Chain Dashboard ({region or 'All Regions'})", fig=fig)

# ==============================================================================
# CHART REGISTRY (used by the terminal menu and `python main.py --all / --chart N`)
# ==============================================================================

CHART_MENU = [
    ("Unit 1", "Design Principles: Poor 3D Chart vs Clean Bar Chart", plot_design_principles_demo),
    ("Unit 1", "Categorical, Time Series & Statistical Data Graphics", plot_data_graphic_types),
    ("Unit 2", "Pairplot Matrix of Student Borrowing Metrics", plot_borrowing_pairplot),
    ("Unit 2", "Heatmap: Monthly Borrowing Intensity", plot_monthly_activity_heatmap),
    ("Unit 2", "Interactive Explorer (hover, filter, smoothing slider)", plot_interactive_explorer),
    ("Unit 2", "Graphical Perception: Position vs Length vs Angle vs Area vs Colour", plot_graphical_perception),
    ("Unit 2", "Grammar of Graphics: Layers, Aesthetics, Geometries & Scales", plot_grammar_of_graphics),
    ("Unit 3", "Bar Plot: Books by Department", plot_department_books),
    ("Unit 3", "Horizontal Bar Plot: Top Authors", plot_author_analytics),
    ("Unit 3", "Cleveland Dot Plot: Book Inventory", plot_cleveland_dot_plot),
    ("Unit 3", "Grouped & Stacked Bars: Loan Status", plot_loan_status_grouped_stacked),
    ("Unit 3", "Distributions: Histogram + KDE, Overlaid KDE, Violin", plot_duration_distributions),
    ("Unit 3", "ECDF, Q-Q Plot, Skewed Data & Log Transform", plot_statistical_diagnostics),
    ("Unit 4", "Many Distributions: Vertical (Box/Strip) vs Horizontal (Ridgeline)", plot_vertical_vs_horizontal_layouts),
    ("Unit 4", "Proportions: Pie, Side-by-Side, Stacked Bar, Stacked Densities", plot_proportions),
    ("Unit 4", "Proportions Separately as Parts of the Total", plot_parts_of_total),
    ("Unit 4", "Nested Proportions: Treemap & Nested Donut", plot_nested_proportions),
    ("Unit 4", "Associations: Scatter, Correlogram, PCA", plot_associations_and_pca),
    ("Unit 4", "Paired Data: Slope Chart", plot_paired_slope_chart),
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

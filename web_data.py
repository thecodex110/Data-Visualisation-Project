import math
import numpy as np
import pandas as pd
from scipy import stats
import squarify
from statsmodels.nonparametric.smoothers_lowess import lowess
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.decomposition import PCA
import db_setup as dbs
import preprocessing as p
SEC = ["IT", "Banking", "Pharma", "Auto", "FMCG", "Energy"]
SC = {"IT": "#4F46E5", "Banking": "#0891B2", "Pharma": "#9333EA", "Auto": "#EA580C", "FMCG": "#DB2777", "Energy": "#CA8A04"}
UP, DN, INK, MUT, GRID, ACC = "#08805A", "#D12B42", "#0E1324", "#5B6478", "#E6E8F0", "#4F46E5"
STATUS_C = {"Profit Booked": UP, "Loss Booked": DN, "Open": "#6366F1"}

def r1(v): return round(float(v), 1)
def r2(v): return round(float(v), 2)


W, H = 480, 300
class Chart:
    def __init__(s, cid, unit, title, desc, insight):
        s.d = dict(id=cid, unit=unit, title=title, desc=desc, insight=insight, rs=[], ps=[], cs=[], ts=[])
        s.n = 0
    def _a(s, a, dl):
        return (a + " dl%d" % min(19, dl)).strip() if a else ""
    def rect(s, x, y, w, h, f, rx=0, o=1, a="", dl=0, sk="none"):
        s.d["rs"].append(dict(x=r1(x), y=r1(y), w=r1(max(w, 0)), h=r1(max(h, 0)), f=f, rx=rx, o=o, a=s._a(a, dl), sk=sk))
    def path(s, d, st="none", f="none", w=1.6, o=1, a="", dl=0, da=""):
        s.d["ps"].append(dict(d=d, s=st, f=f, w=w, o=o, a=s._a(a, dl), da=da))
    def circ(s, x, y, r, f, o=1, a="", dl=0, st="none"):
        s.d["cs"].append(dict(x=r1(x), y=r1(y), r=r1(r), f=f, o=o, a=s._a(a, dl), s=st))
    def text(s, x, y, v, size=10, f=MUT, an="start", wt=500):
        s.d["ts"].append(dict(x=r1(x), y=r1(y), v=str(v), z=size, f=f, an=an, wt=wt))
    def out(s): return s.d

class Panel:
    def __init__(s, ch, x, y, w, h, xr, yr, title=None):
        s.ch, s.x, s.y, s.w, s.h, s.xr, s.yr = ch, x, y, w, h, xr, yr
        if title: ch.text(x, y - 8, title, 10.5, INK, wt=650)
    def X(s, v): return s.x + (v - s.xr[0]) / (s.xr[1] - s.xr[0] or 1) * s.w
    def Y(s, v): return s.y + s.h - (v - s.yr[0]) / (s.yr[1] - s.yr[0] or 1) * s.h
    def grid(s, n=4, labels=True, fmt="{:.0f}", xaxis=True):
        for i in range(n + 1):
            v = s.yr[0] + (s.yr[1] - s.yr[0]) * i / n
            s.ch.rect(s.x, s.Y(v), s.w, 1, GRID)
            if labels: s.ch.text(s.x - 5, s.Y(v) + 3, fmt.format(v), 8.5, MUT, "end")
        if s.yr[0] < 0 < s.yr[1]: s.ch.rect(s.x, s.Y(0), s.w, 1.2, "#9AA1B2")
    def line(s, xs, ys):
        return "M" + " L".join("%.1f,%.1f" % (s.X(a), s.Y(b)) for a, b in zip(xs, ys))
    def area(s, xs, ys, base=None):
        b = s.yr[0] if base is None else base
        return s.line(xs, ys) + " L%.1f,%.1f L%.1f,%.1f Z" % (s.X(xs[-1]), s.Y(b), s.X(xs[0]), s.Y(b))

def nice(lo, hi, pad=0.08):
    span = hi - lo or 1
    return lo - span * pad, hi + span * pad

def kde(vals, grid):
    k = stats.gaussian_kde(vals)
    return k(grid)

def arc(cx, cy, r0, r1_, a0, a1):
    def pt(r, a): return cx + r * math.sin(a), cy - r * math.cos(a)
    large = 1 if a1 - a0 > math.pi else 0
    x0, y0 = pt(r1_, a0); x1, y1 = pt(r1_, a1); x2, y2 = pt(r0, a1); x3, y3 = pt(r0, a0)
    d = "M%.1f,%.1f A%.1f,%.1f 0 %d 1 %.1f,%.1f " % (x0, y0, r1_, r1_, large, x1, y1)
    if r0 > 0:
        d += "L%.1f,%.1f A%.1f,%.1f 0 %d 0 %.1f,%.1f Z" % (x2, y2, r0, r0, large, x3, y3)
    else:
        d += "L%.1f,%.1f Z" % (cx, cy)
    return d

def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def diverge(v, m):
    t = max(-1, min(1, v / (m or 1)))
    return mix("#FFFFFF", UP, t * 0.9) if t >= 0 else mix("#FFFFFF", DN, -t * 0.9)

def seq(t, c=ACC):
    return mix("#EEF0FF", c, max(0, min(1, t)))


# returns (charts, data) for the website
def build_all():

    prices = p.get_clean_prices()
    summary = p.get_stock_summary()
    hq = pd.read_sql_query("SELECT stock_id, hq_state FROM stocks", p.get_connection())
    summary = summary.merge(hq, on="stock_id")
    trades = p.get_cleaned_trades()
    mindex = p.get_market_index()
    secidx = p.get_sector_index()
    sector_agg = p.get_sector_aggregates()
    msec = p.get_monthly_sector_returns()
    mstock = p.get_monthly_stock_returns()
    mts = p.get_monthly_timeseries()
    inv = p.get_investor_summary()
    geo = p.get_state_geospatial_summary()
    deliv_all = p.get_cleaned_deliveries()

    charts = []
    sec_ret = summary.groupby("sector_name")["return_1y"].mean().reindex(SEC)


    c = Chart(1, "Unit 1", "Design Principles: Poor 3D Chart vs Clean Bar Chart",
              "The same sector returns drawn twice: a cluttered fake-3D rainbow chart, then a clean sorted chart.",
              "Sorting, one colour and direct labels make the best sector readable in a second.")
    pa = Panel(c, 40, 50, 170, 210, (0, 6), nice(sec_ret.min(), sec_ret.max()), "Before: fake 3D, unsorted")
    rain = ["#FF0000", "#FF9900", "#FFFF00", "#00CC00", "#0066FF", "#9900FF"]
    for i in range(9): c.rect(40, 50 + i * 26, 170, 1, "#C9CCD6")
    for i, s_ in enumerate(SEC):
        v = sec_ret[s_]; x = pa.X(i + 0.15); y0, y1 = pa.Y(0), pa.Y(v)
        c.rect(x + 7, min(y0, y1) - 7, 18, abs(y1 - y0), "#555", o=0.5, a="f", dl=i)
        c.rect(x, min(y0, y1), 18, abs(y1 - y0), rain[i], a="g" if v >= 0 else "gn", dl=i)
        c.text(x + 9, 275, s_, 7.5, MUT, "middle")
    order = sec_ret.sort_values()
    pb = Panel(c, 300, 50, 160, 210, nice(min(0, order.min()), order.max(), 0.15), (0, 6), "After: sorted, labelled")
    for i, (s_, v) in enumerate(order.items()):
        y = pb.Y(i + 0.85); col = ACC if i == 5 else "#A5ABBD"
        c.rect(min(pb.X(0), pb.X(v)), y, abs(pb.X(v) - pb.X(0)), 22, col, 3, a="gx" if v >= 0 else "gxn", dl=i + 6)
        c.text(296, y + 15, s_, 9, INK, "end")
        c.text(max(pb.X(v), pb.X(0)) + 4, y + 15, "%+.1f%%" % v, 8.5, INK if v >= 0 else DN, "start", 650)
    c.rect(pb.X(0), 50, 1.2, 210, "#9AA1B2")
    charts.append(c.out())


    c = Chart(2, "Unit 1", "Categorical, Time Series & Statistical Data Graphics",
              "Three kinds of data, three right chart types: bars for categories, a line for time, a histogram for spread.",
              "Pick the chart from the data type: category, time or distribution.")
    cnt = trades.groupby("sector_name").size().reindex(SEC)
    pa = Panel(c, 28, 60, 120, 190, (0, 6), (0, cnt.max() * 1.15), "Categorical")
    for i, s_ in enumerate(SEC):
        c.rect(pa.X(i + 0.15), pa.Y(cnt[s_]), 14, pa.Y(0) - pa.Y(cnt[s_]), SC[s_], 3, a="g", dl=i)
        c.text(pa.X(i + 0.15) + 7, 266, s_[:3], 7.5, MUT, "middle")
    lv = mindex["index_level"].values
    pb = Panel(c, 180, 60, 130, 190, (0, len(lv) - 1), nice(lv.min(), lv.max()), "Time series")
    c.path(pb.area(range(len(lv)), lv), f="url(#gA)", o=0.9, a="f")
    c.path(pb.line(range(len(lv)), lv), ACC, w=1.8, a="d")
    c.text(180, 266, "Market index, 1 year", 7.5)
    r = summary["return_1y"].values
    bins = np.histogram_bin_edges(r, 9); hist, _ = np.histogram(r, bins)
    pc = Panel(c, 340, 60, 120, 190, (bins[0], bins[-1]), (0, hist.max() * 1.15), "Statistical")
    for i, h_ in enumerate(hist):
        c.rect(pc.X(bins[i]) + 1, pc.Y(h_), pc.X(bins[i + 1]) - pc.X(bins[i]) - 2, pc.Y(0) - pc.Y(h_), "#9333EA", 2, a="g", dl=i)
    c.text(340, 266, "1Y return of 36 stocks", 7.5)
    charts.append(c.out())


    c = Chart(3, "Unit 2", "Pairplot Matrix of Stock Risk & Return",
              "Every pair of 1-year return, volatility and max drawdown, one dot per stock, coloured by sector.",
              "Higher volatility comes with deeper drawdowns: risk shows up in both columns.")
    vars_ = [("return_1y", "1Y ret %"), ("volatility", "Volatility %"), ("max_drawdown", "Drawdown %")]
    cw, chh, ox, oy = 130, 72, 70, 26
    for i, (vy, ly) in enumerate(vars_):
        for j, (vx, lx) in enumerate(vars_):
            x0, y0 = ox + j * (cw + 12), oy + i * (chh + 14)
            c.rect(x0, y0, cw, chh, "#F7F8FC", 4)
            xr = nice(summary[vx].min(), summary[vx].max()); yr = nice(summary[vy].min(), summary[vy].max())
            pn = Panel(c, x0, y0, cw, chh, xr, yr)
            if i == j:
                hist, b = np.histogram(summary[vx], 8)
                pn.yr = (0, hist.max() * 1.15)
                for k, h_ in enumerate(hist):
                    c.rect(pn.X(b[k]) + 1, pn.Y(h_), pn.X(b[k + 1]) - pn.X(b[k]) - 2, pn.Y(0) - pn.Y(h_), "#A5ABBD", 1, a="g", dl=k)
            else:
                for k, (_, rw) in enumerate(summary.iterrows()):
                    c.circ(pn.X(rw[vx]), pn.Y(rw[vy]), 2.6, SC[rw["sector_name"]], 0.85, "pop", k // 3)
            if j == 0: c.text(x0 - 6, y0 + chh / 2 + 3, ly, 8, INK, "end", 600)
            if i == 2: c.text(x0 + cw / 2, y0 + chh + 12, lx, 8, INK, "middle", 600)
    charts.append(c.out())


    c = Chart(4, "Unit 2", "Heatmap: Monthly Return by Sector",
              "Average monthly return of each sector. Green = the sector gained that month, red = it fell.",
              "Colour turns a 6 x 12 table into a pattern you can scan in seconds.")
    months = list(msec.columns)[-12:]
    m = np.nanmax(np.abs(msec[months].values))
    cw = (W - 80) / len(months); chh = 34
    for i, s_ in enumerate(SEC):
        c.text(66, 46 + i * (chh + 3) + chh / 2 + 3, s_, 9, INK, "end", 600)
        for j, mo in enumerate(months):
            v = msec.loc[s_, mo]
            c.rect(72 + j * cw, 46 + i * (chh + 3), cw - 3, chh, diverge(v, m), 4, a="f", dl=(i + j) // 1)
            c.text(72 + j * cw + (cw - 3) / 2, 46 + i * (chh + 3) + chh / 2 + 3, "%.0f" % v, 7.5, INK if abs(v) < m * 0.6 else "#FFFFFF", "middle", 600)
    for j, mo in enumerate(months):
        c.text(72 + j * cw + (cw - 3) / 2, 34, pd.Period(mo).strftime("%b"), 8, MUT, "middle")
    charts.append(c.out())


    c = Chart(5, "Unit 2", "Interactive Explorer: Sector Indices with Moving Average",
              "Six sector indices (base 100). On the website, hover any line and switch sectors on the Stock page.",
              "Interaction lets the reader ask their own question instead of reading a fixed one.")
    yr = nice(secidx.values.min(), secidx.values.max())
    pn = Panel(c, 40, 30, 370, 240, (0, len(secidx) - 1), yr)
    pn.grid(4)
    for k, s_ in enumerate(SEC):
        v = secidx[s_].values
        c.path(pn.line(range(len(v)), v), SC[s_], w=1.7, a="d", dl=k * 2)
        c.circ(pn.X(len(v) - 1), pn.Y(v[-1]), 3, SC[s_], a="pop", dl=12)
    ends = sorted([(secidx[s_].values[-1], s_) for s_ in SEC])
    lasty = -999
    for v, s_ in reversed(ends):
        y = max(pn.Y(v) + 3, lasty + 11); lasty = y
        c.text(416, y, "%s %.0f" % (s_, v), 8.5, SC[s_], wt=650)
    charts.append(c.out())


    c = Chart(6, "Unit 2", "Graphical Perception: Position vs Length vs Angle vs Area vs Colour",
              "The same six sector traded values encoded five ways. Compare how easily you can rank them.",
              "Position and length are read most accurately; angle, area and colour are hardest.")
    tv = sector_agg.set_index("sector_name")["traded_value_lakh"].reindex(SEC)
    mx = tv.max(); colw = 88
    heads = ["Position", "Length", "Angle", "Area", "Colour"]
    for k, hname in enumerate(heads):
        c.text(14 + k * colw + 40, 30, hname, 9.5, INK, "middle", 650)
    for i, s_ in enumerate(SEC):
        y = 52 + i * 38; v = tv[s_]
        c.rect(18, y + 8, 70, 1, GRID); c.circ(18 + v / mx * 70, y + 8, 4, ACC, a="pop", dl=i)
        c.rect(18 + colw, y + 2, v / mx * 70, 12, ACC, 2, a="gx", dl=i)
        c.text(10, y + 11, s_[:3], 7, MUT, "end")
        rr = 13 * math.sqrt(v / mx); c.circ(14 + 3 * colw + 40, y + 8, rr, ACC, 0.85, "pop", i)
        c.rect(14 + 4 * colw + 20, y - 4, 40, 26, seq(v / mx), 4, a="f", dl=i)
    tot = tv.sum(); a0 = 0
    for i, s_ in enumerate(SEC):
        a1 = a0 + tv[s_] / tot * 2 * math.pi
        c.path(arc(14 + 2 * colw + 40, 160, 0, 38, a0, a1), "#FFFFFF", mix("#C7CBFF", ACC, i / 5), 1.2, a="f", dl=i); a0 = a1
    charts.append(c.out())


    c = Chart(7, "Unit 2", "Grammar of Graphics: Layers, Aesthetics, Geometries & Scales",
              "A chart built layer by layer: data -> points -> line geometry -> smoothing stat -> colour aesthetic.",
              "Every chart is data + aesthetic mapping + geometry + statistics + scales.")
    mlv = mts["index_close"].values; xs = list(range(len(mlv)))
    sm = lowess(mlv, xs, frac=0.6)[:, 1]
    steps = ["1. Data + points", "2. + line geom", "3. + smooth stat", "4. + colour scale"]
    for k, t_ in enumerate(steps):
        x0, y0 = 24 + (k % 2) * 228, 34 + (k // 2) * 136
        c.rect(x0, y0, 210, 112, "#F7F8FC", 6)
        pn = Panel(c, x0 + 12, y0 + 22, 186, 80, (0, len(mlv) - 1), nice(mlv.min(), mlv.max()))
        c.text(x0 + 10, y0 + 15, t_, 9, INK, wt=650)
        if k >= 1: c.path(pn.line(xs, mlv), "#A5ABBD" if k < 3 else "#C7CBFF", w=1.5, a="d", dl=k * 3)
        if k >= 2: c.path(pn.line(xs, sm), "#EA580C", w=2, a="d", dl=k * 3 + 2, da="4 3")
        for i, v in enumerate(mlv):
            col = ACC if k < 3 else (UP if i and v >= mlv[i - 1] else DN)
            c.circ(pn.X(i), pn.Y(v), 3, col, a="pop", dl=k * 3 + i // 4)
    charts.append(c.out())


    c = Chart(8, "Unit 3", "Bar Plot: Average 1-Year Return by Sector",
              "Mean 1-year return of the six stocks in each sector, sorted from best to worst.",
              "%s led the year at %+.1f%%; %s trailed at %+.1f%%." % (sec_ret.idxmax(), sec_ret.max(), sec_ret.idxmin(), sec_ret.min()))
    o = sec_ret.sort_values(ascending=False)
    pn = Panel(c, 46, 30, 410, 230, (0, 6), nice(min(0, o.min()), o.max(), 0.15))
    pn.grid(4, fmt="{:.0f}%")
    for i, (s_, v) in enumerate(o.items()):
        x = pn.X(i + 0.18); y0, y1 = pn.Y(0), pn.Y(v)
        c.rect(x, min(y0, y1), pn.w / 6 * 0.64, abs(y1 - y0), SC[s_], 5, a="g" if v >= 0 else "gn", dl=i * 2)
        c.text(x + pn.w / 6 * 0.32, (y1 - 6) if v >= 0 else (y1 + 13), "%+.1f%%" % v, 9, INK, "middle", 700)
        c.text(x + pn.w / 6 * 0.32, 278, s_, 9, INK, "middle", 600)
    charts.append(c.out())


    c = Chart(9, "Unit 3", "Horizontal Bar Plot: Top 10 Most Traded Stocks",
              "Number of buy orders per stock. Horizontal bars leave room for long stock names.",
              "Horizontal bars are the right layout when category labels are long.")
    mt = p.get_stock_trade_aggregates().head(10).iloc[::-1]
    pn = Panel(c, 100, 20, 340, 260, (0, mt["total_trades"].max() * 1.12), (0, 10))
    for i, (_, rw) in enumerate(mt.iterrows()):
        y = pn.Y(i + 0.85)
        c.rect(100, y, pn.X(rw["total_trades"]) - 100, 19, SC[rw["sector_name"]], 4, a="gx", dl=(9 - i))
        c.text(94, y + 13, rw["symbol"], 9, INK, "end", 600)
        c.text(pn.X(rw["total_trades"]) + 5, y + 13, "%d" % rw["total_trades"], 9, INK, wt=700)
    charts.append(c.out())


    c = Chart(10, "Unit 3", "Cleveland Dot Plot: 1-Year Return of Every Stock",
              "All 36 stocks sorted by 1-year return. A dot per stock is cleaner than 36 bars.",
              "Dots keep the focus on position, so ranks and gaps stand out.")
    s36 = summary.sort_values("return_1y", ascending=False).reset_index(drop=True)
    xr = nice(s36["return_1y"].min(), s36["return_1y"].max(), 0.05)
    for half in range(2):
        sub = s36.iloc[half * 18:(half + 1) * 18]
        x0 = 74 + half * 236
        pn = Panel(c, x0, 22, 150, 260, xr, (0, 18))
        c.rect(pn.X(0), 22, 1.2, 260, "#9AA1B2")
        for i, (_, rw) in enumerate(sub.iterrows()):
            y = 30 + i * 14.3
            c.rect(x0, y, 150, 1, GRID)
            c.circ(pn.X(rw["return_1y"]), y, 3.6, UP if rw["return_1y"] >= 0 else DN, a="pop", dl=i)
            c.text(x0 - 6, y + 3, rw["symbol"], 7.5, INK, "end", 600)
            c.text(x0 + 154, y + 3, "%+.0f" % rw["return_1y"], 7, MUT)
    charts.append(c.out())


    c = Chart(11, "Unit 3", "Grouped & Stacked Bars: Trade Outcome by Sector",
              "Left: profit, loss and open trades side by side. Right: the same counts stacked to 100%.",
              "Grouped bars compare counts; stacked 100% bars compare shares.")
    oc = trades.groupby(["sector_name", "simple_status"]).size().unstack(fill_value=0).reindex(SEC)
    sts = ["Profit Booked", "Loss Booked", "Open"]
    pa = Panel(c, 34, 36, 210, 220, (0, 6), (0, oc.values.max() * 1.15))
    pa.grid(3)
    for i, s_ in enumerate(SEC):
        for k, st_ in enumerate(sts):
            v = oc.loc[s_, st_]; x = pa.X(i + 0.12) + k * 9.5
            c.rect(x, pa.Y(v), 9, pa.Y(0) - pa.Y(v), STATUS_C[st_], 1.5, a="g", dl=i + k)
        c.text(pa.X(i + 0.5), 272, s_[:4], 7.5, MUT, "middle")
    pb = Panel(c, 290, 36, 170, 220, (0, 6), (0, 1))
    for i, s_ in enumerate(SEC):
        tot_ = oc.loc[s_].sum(); acc = 0
        for k, st_ in enumerate(sts):
            f = oc.loc[s_, st_] / tot_
            c.rect(pb.X(i + 0.15), pb.Y(acc + f), 20, pb.Y(acc) - pb.Y(acc + f) - 1, STATUS_C[st_], 2, a="f", dl=i * 2 + k)
            acc += f
        c.text(pb.X(i + 0.15) + 10, 272, s_[:4], 7.5, MUT, "middle")
    for k, st_ in enumerate(sts):
        c.circ(40 + k * 100, 18, 4, STATUS_C[st_]); c.text(48 + k * 100, 21, st_, 8.5, INK)
    charts.append(c.out())


    c = Chart(12, "Unit 3", "Distributions: Histogram + KDE, Violin (Daily Returns)",
              "Left: every daily stock return as a histogram with a smooth density curve. Right: one violin per sector.",
              "Most days move less than 2%; Auto and Energy have the widest violins = most volatile.")
    dr = prices["daily_return"].dropna().clip(-6, 6).values
    bins = np.linspace(-6, 6, 31); hist, _ = np.histogram(dr, bins, density=True)
    pa = Panel(c, 30, 30, 210, 230, (-6, 6), (0, hist.max() * 1.15), "Histogram + KDE")
    for i, h_ in enumerate(hist):
        c.rect(pa.X(bins[i]) + 0.5, pa.Y(h_), pa.X(bins[i + 1]) - pa.X(bins[i]) - 1, pa.Y(0) - pa.Y(h_), "#C7CBFF", 1, a="g", dl=i // 2)
    gx = np.linspace(-6, 6, 80); kd = kde(dr[::3], gx)
    c.path(pa.line(gx, kd), ACC, w=2.2, a="d", dl=8)
    for v in (-4, -2, 0, 2, 4): c.text(pa.X(v), 275, "%d%%" % v, 7.5, MUT, "middle")
    pb = Panel(c, 280, 30, 180, 230, (0, 6), (-6, 6), "Violin by sector")
    pb.grid(4, fmt="{:.0f}%")
    gy = np.linspace(-5, 5, 50)
    for i, s_ in enumerate(SEC):
        v = prices.loc[prices["sector_name"] == s_, "daily_return"].dropna().clip(-6, 6).values[::2]
        d_ = kde(v, gy); d_ = d_ / d_.max() * 12; cx = pb.X(i + 0.5)
        pts = ["%.1f,%.1f" % (cx + a, pb.Y(b)) for a, b in zip(d_, gy)] + ["%.1f,%.1f" % (cx - a, pb.Y(b)) for a, b in zip(d_[::-1], gy[::-1])]
        c.path("M" + " L".join(pts) + " Z", SC[s_], SC[s_], 1, 0.75, "f", i)
        c.rect(cx - 1, pb.Y(np.percentile(v, 75)), 2, pb.Y(np.percentile(v, 25)) - pb.Y(np.percentile(v, 75)), INK)
        c.text(cx, 275, s_[:4], 7.5, MUT, "middle")
    charts.append(c.out())


    c = Chart(13, "Unit 3", "ECDF, Q-Q Plot, Skewed Data & Log Transform",
              "ECDF and Q-Q of daily returns (fat tails vs normal), and how a log scale fixes skewed trade sizes.",
              "Real returns have fatter tails than a normal curve; log transform makes skewed money data readable.")
    srt = np.sort(dr[::4]); ec = np.arange(1, len(srt) + 1) / len(srt)
    pa = Panel(c, 40, 34, 170, 92, (-6, 6), (0, 1), "ECDF of daily returns")
    pa.grid(2, fmt="{:.1f}")
    idx = np.linspace(0, len(srt) - 1, 120).astype(int)
    c.path(pa.line(srt[idx], ec[idx]), ACC, w=2, a="d")
    qs = np.linspace(0.01, 0.99, 50); th = stats.norm.ppf(qs); emp = np.quantile(dr, qs); emp = (emp - dr.mean()) / dr.std()
    pb = Panel(c, 280, 34, 170, 92, (-3, 3), (-4, 4), "Q-Q vs normal")
    c.path(pb.line([-3, 3], [-3, 3]), "#9AA1B2", w=1.2, da="4 3")
    for i, (a_, b_) in enumerate(zip(th, emp)): c.circ(pb.X(a_), pb.Y(b_), 2.6, "#9333EA", a="pop", dl=i // 4)
    invd = trades["invested"].values
    hist, b = np.histogram(invd, 14)
    pc = Panel(c, 40, 170, 170, 92, (b[0], b[-1]), (0, hist.max() * 1.1), "Trade size (Rs): right-skewed")
    for i, h_ in enumerate(hist): c.rect(pc.X(b[i]) + 0.5, pc.Y(h_), pc.X(b[i + 1]) - pc.X(b[i]) - 1, pc.Y(0) - pc.Y(h_), "#EA580C", 1, a="g", dl=i)
    lg = np.log10(invd); hist, b = np.histogram(lg, 14)
    pd_ = Panel(c, 280, 170, 170, 92, (b[0], b[-1]), (0, hist.max() * 1.1), "log10(trade size): balanced")
    for i, h_ in enumerate(hist): c.rect(pd_.X(b[i]) + 0.5, pd_.Y(h_), pd_.X(b[i + 1]) - pd_.X(b[i]) - 1, pd_.Y(0) - pd_.Y(h_), UP, 1, a="g", dl=i)
    charts.append(c.out())


    c = Chart(14, "Unit 4", "Many Distributions: Vertical (Box/Strip) vs Horizontal (Ridgeline)",
              "Monthly stock returns per sector two ways: boxplots with every point, and stacked density ridges.",
              "Boxplots summarise; ridgelines show the full shape of each distribution.")
    pa = Panel(c, 40, 30, 200, 236, (0, 6), (-25, 25), "Box + strip")
    pa.grid(4, fmt="{:.0f}%")
    rng = np.random.default_rng(3)
    for i, s_ in enumerate(SEC):
        v = mstock.loc[mstock["sector_name"] == s_, "monthly_return"].clip(-25, 25).values
        q1, q2, q3 = np.percentile(v, [25, 50, 75]); cx = pa.X(i + 0.5)
        c.rect(cx - 11, pa.Y(q3), 22, pa.Y(q1) - pa.Y(q3), SC[s_], 3, 0.25, "f", i)
        c.rect(cx - 11, pa.Y(q2), 22, 2, SC[s_])
        for k, vv in enumerate(v[::2]): c.circ(cx + rng.uniform(-8, 8), pa.Y(vv), 1.6, SC[s_], 0.7, "pop", i)
        c.text(cx, 282, s_[:4], 7.5, MUT, "middle")
    gx = np.linspace(-25, 25, 70)
    pb = Panel(c, 300, 40, 160, 220, (-25, 25), (0, 7), "Ridgeline")
    for i, s_ in enumerate(SEC[::-1]):
        v = mstock.loc[mstock["sector_name"] == s_, "monthly_return"].clip(-25, 25).values
        d_ = kde(v, gx); d_ = d_ / d_.max() * 1.6 + i
        c.path(pb.area(gx, d_, i), "#FFFFFF", SC[s_], 1.2, 0.9, "f", 6 - i)
        c.text(296, pb.Y(i) - 2, s_, 8, INK, "end", 600)
    charts.append(c.out())


    c = Chart(15, "Unit 4", "Proportions: Pie, Side-by-Side Bars, Stacked Bar",
              "Share of all 300 trades that booked profit, booked loss or are still open, three ways.",
              "Pies show part-of-whole; bars make close shares easier to compare.")
    tot_s = trades["simple_status"].value_counts().reindex(sts)
    a0 = 0
    for k, st_ in enumerate(sts):
        a1 = a0 + tot_s[st_] / tot_s.sum() * 2 * math.pi
        c.path(arc(108, 150, 38, 70, a0, a1), "#FFFFFF", STATUS_C[st_], 2, a="f", dl=k * 2)
        mid = (a0 + a1) / 2; c.text(108 + 86 * math.sin(mid), 150 - 86 * math.cos(mid) + 3, "%.0f%%" % (tot_s[st_] / tot_s.sum() * 100), 9, INK, "middle", 700)
        a0 = a1
    c.text(108, 148, "%d" % tot_s.sum(), 16, INK, "middle", 750); c.text(108, 163, "trades", 8, MUT, "middle")
    pb = Panel(c, 215, 50, 110, 200, (0, 3), (0, tot_s.max() * 1.15), "Side by side")
    for k, st_ in enumerate(sts):
        c.rect(pb.X(k + 0.15), pb.Y(tot_s[st_]), 24, pb.Y(0) - pb.Y(tot_s[st_]), STATUS_C[st_], 4, a="g", dl=k)
        c.text(pb.X(k + 0.15) + 12, pb.Y(tot_s[st_]) - 5, "%d" % tot_s[st_], 9, INK, "middle", 700)
        c.text(pb.X(k + 0.15) + 12, 266, st_.split()[0], 7.5, MUT, "middle")
    c.text(360, 42, "Stacked", 10.5, INK, wt=650)
    acc = 0
    for k, st_ in enumerate(sts):
        f = tot_s[st_] / tot_s.sum()
        c.rect(370, 50 + acc * 200, 46, f * 200 - 2, STATUS_C[st_], 3, a="f", dl=k * 2)
        c.text(424, 50 + (acc + f / 2) * 200 + 3, st_, 8.5, INK); acc += f
    charts.append(c.out())


    c = Chart(16, "Unit 4", "Proportions Separately as Parts of the Total",
              "Each sector's traded value drawn against the full market total (grey), one small panel each.",
              "Small multiples show each part against the whole without a busy legend.")
    tot = tv.sum()
    for i, s_ in enumerate(SEC):
        x0, y0 = 30 + (i % 3) * 148, 40 + (i // 3) * 128
        c.text(x0, y0, s_, 10, INK, wt=650)
        c.text(x0 + 130, y0, "%.0f%%" % (tv[s_] / tot * 100), 10, SC[s_], "end", 750)
        c.rect(x0, y0 + 12, 130, 80, "#EEF0F5", 6)
        c.rect(x0, y0 + 12 + 80 * (1 - tv[s_] / tot), 130, 80 * tv[s_] / tot, SC[s_], 6, a="g", dl=i * 2)
        c.text(x0, y0 + 106, "Rs %.1f L of Rs %.1f L" % (tv[s_], tot), 7.5, MUT)
    charts.append(c.out())


    c = Chart(17, "Unit 4", "Nested Proportions: Treemap & Nested Donut",
              "Traded value split by sector, then by stock inside each sector.",
              "Treemaps and nested donuts show a part-of-a-part in one picture.")
    stv = p.get_stock_trade_aggregates()
    secs_sorted = tv.sort_values(ascending=False)
    rects = squarify.squarify(squarify.normalize_sizes(secs_sorted.values, 250, 250), 14, 26, 250, 250)
    k_ = 0
    for (s_, v), rc in zip(secs_sorted.items(), rects):
        sub = stv[stv["sector_name"] == s_].sort_values("traded_value", ascending=False)
        inner = squarify.squarify(squarify.normalize_sizes(sub["traded_value"].values, rc["dx"], rc["dy"]), rc["x"], rc["y"], rc["dx"], rc["dy"])
        for j, (ir, (_, rw)) in enumerate(zip(inner, sub.iterrows())):
            c.rect(ir["x"] + 1, ir["y"] + 1, ir["dx"] - 2, ir["dy"] - 2, mix(SC[s_], "#FFFFFF", 0.12 * j), 3, a="f", dl=k_ // 2); k_ += 1
            if ir["dx"] > 36 and ir["dy"] > 14: c.text(ir["x"] + 4, ir["y"] + 12, rw["symbol"][:9], 7, "#FFFFFF", wt=650)
    cx, cy = 375, 150; a0 = 0; tot = tv.sum()
    for i, (s_, v) in enumerate(secs_sorted.items()):
        a1 = a0 + v / tot * 2 * math.pi
        c.path(arc(cx, cy, 30, 62, a0, a1), "#FFFFFF", SC[s_], 1.5, a="f", dl=i)
        sub = stv[stv["sector_name"] == s_].sort_values("traded_value", ascending=False); b0 = a0
        for j, (_, rw) in enumerate(sub.iterrows()):
            b1 = b0 + rw["traded_value"] / stv["traded_value"].sum() * 2 * math.pi
            c.path(arc(cx, cy, 65, 92, b0, b1), "#FFFFFF", mix(SC[s_], "#FFFFFF", 0.12 * j), 1, a="f", dl=8 + i); b0 = b1
        a0 = a1
    c.text(cx, cy + 4, "Sector", 8, MUT, "middle"); c.text(cx, 270, "inner = sector, outer = stock", 8, MUT, "middle")
    charts.append(c.out())


    c = Chart(18, "Unit 4", "Associations: Scatter, Correlogram, PCA",
              "Risk vs return per stock, how sectors move together, and all 36 stocks squeezed into two PCA axes.",
              "Stocks from the same sector cluster together in the PCA view: they share a common driver.")
    pa = Panel(c, 30, 40, 130, 210, nice(summary["volatility"].min(), summary["volatility"].max()), nice(summary["return_1y"].min(), summary["return_1y"].max()), "Risk vs return")
    pa.grid(3, labels=False)
    for k, (_, rw) in enumerate(summary.iterrows()): c.circ(pa.X(rw["volatility"]), pa.Y(rw["return_1y"]), 3, SC[rw["sector_name"]], 0.85, "pop", k // 3)
    c.text(95, 268, "volatility ->", 7.5, MUT, "middle")
    secret = prices.groupby(["date", "sector_name"])["daily_return"].mean().unstack()[SEC].corr()
    cs_ = 20
    for i, a_ in enumerate(SEC):
        c.text(196, 50 + i * cs_ + 13, a_[:4], 7, MUT, "end")
        for j, b_ in enumerate(SEC):
            v = secret.loc[a_, b_]
            c.rect(200 + j * cs_, 50 + i * cs_, cs_ - 2, cs_ - 2, seq((v - 0.2) / 0.8, "#4338CA"), 3, a="f", dl=i + j)
            if i != j: c.text(200 + j * cs_ + 9, 50 + i * cs_ + 12, "%.1f" % v, 6, INK if v < 0.6 else "#FFFFFF", "middle")
    c.text(200, 40, "Correlogram", 10.5, INK, wt=650)
    mat, secmap = p.get_stock_return_matrix()
    pcs = PCA(2).fit((mat - mat.mean()) / mat.std()).components_
    pc = Panel(c, 345, 40, 120, 210, nice(pcs[0].min(), pcs[0].max()), nice(pcs[1].min(), pcs[1].max()), "PCA of stocks")
    pc.grid(3, labels=False)
    for k, sym in enumerate(mat.columns): c.circ(pc.X(pcs[0][k]), pc.Y(pcs[1][k]), 3.4, SC[secmap[sym]], 0.9, "pop", k // 3)
    c.text(405, 268, "PC1 ->", 7.5, MUT, "middle")
    charts.append(c.out())


    c = Chart(19, "Unit 4", "Paired Data: Slope Chart of Sector Returns",
              "Each sector's return in the first half of the year vs the second half.",
              "Crossing lines show sectors that swapped places between the two halves.")
    half = len(secidx) // 2
    h1 = (secidx.iloc[half] / secidx.iloc[0] - 1) * 100; h2 = (secidx.iloc[-1] / secidx.iloc[half] - 1) * 100
    yr = nice(min(h1.min(), h2.min()), max(h1.max(), h2.max()))
    pn = Panel(c, 130, 40, 220, 220, (0, 1), yr)
    c.rect(130, 40, 1.5, 220, "#C9CCD6"); c.rect(350, 40, 1.5, 220, "#C9CCD6")
    c.text(130, 30, "First half", 9.5, INK, "middle", 650); c.text(350, 30, "Second half", 9.5, INK, "middle", 650)
    for i, s_ in enumerate(SEC):
        c.path(pn.line([0, 1], [h1[s_], h2[s_]]), SC[s_], w=2.4, a="d", dl=i * 2)
        c.circ(130, pn.Y(h1[s_]), 4, SC[s_], a="pop", dl=i); c.circ(350, pn.Y(h2[s_]), 4, SC[s_], a="pop", dl=i + 6)
    for side, vals, x, an in ((0, h1, 122, "end"), (1, h2, 358, "start")):
        last = -999
        for s_ in vals.sort_values(ascending=False).index:
            y = max(pn.Y(vals[s_]) + 3, last + 11); last = y
            txt = "%s %+.0f%%" % (s_, vals[s_]) if side == 0 else "%+.0f%% %s" % (vals[s_], s_)
            c.text(x, y, txt, 8, SC[s_], an, 650)
    charts.append(c.out())


    c = Chart(20, "Unit 5", "Time Series: Moving Averages, LOESS Smoothing & Trend",
              "The equal-weight market index with 20 and 50-day moving averages and a LOESS smooth.",
              "Smoothing hides daily noise so the real trend shows.")
    lv = mindex["index_level"].values; xs = np.arange(len(lv))
    pn = Panel(c, 46, 34, 410, 230, (0, len(lv) - 1), nice(lv.min(), lv.max()))
    pn.grid(4)
    c.path(pn.area(xs, lv), f="url(#gA)", o=0.8, a="f")
    c.path(pn.line(xs, lv), "#A5ABBD", w=1.2, a="d")
    c.path(pn.line(xs, mindex["ma_20"].values), ACC, w=1.8, a="d", dl=4)
    c.path(pn.line(xs, mindex["ma_50"].values), "#EA580C", w=1.8, a="d", dl=7)
    c.path(pn.line(xs, lowess(lv, xs, frac=0.3)[:, 1]), UP, w=2.2, a="d", dl=10, da="5 4")
    for k, (lab, col) in enumerate([("Index", "#A5ABBD"), ("20-DMA", ACC), ("50-DMA", "#EA580C"), ("LOESS", UP)]):
        c.rect(56 + k * 80, 18, 14, 3, col); c.text(74 + k * 80, 22, lab, 8.5, INK)
    for i in range(0, len(lv), 42): c.text(pn.X(i), 280, mindex["date"].iloc[i].strftime("%b"), 8, MUT, "middle")
    charts.append(c.out())


    c = Chart(21, "Unit 5", "Dose-Response, Multi-Response, Detrending, Decomposition",
              "Holding days vs return, index vs volume, the index with its trend removed, and its repeating cycle.",
              "Decomposition splits a series into trend + season + noise.")
    pa = Panel(c, 34, 34, 180, 92, nice(0, trades["holding_days"].max()), (-30, 40), "Dose-response: hold days vs return")
    for k, (_, rw) in enumerate(trades.sample(120, random_state=1).iterrows()):
        c.circ(pa.X(rw["holding_days"]), pa.Y(max(-30, min(40, rw["return_pct"]))), 1.8, "#A5ABBD", 0.8, "pop", k // 10)
    lw = lowess(trades["return_pct"], trades["holding_days"], frac=0.5)
    c.path(pa.line(lw[:, 0], lw[:, 1]), DN, w=2.2, a="d", dl=6)
    mm = mts["index_close"].values; vv = mts["volume"].values
    pb = Panel(c, 270, 34, 180, 92, (0, len(mm) - 1), (0, 1), "Multi-response: index & volume")
    c.path(pb.line(range(len(mm)), (mm - mm.min()) / (np.ptp(mm) or 1)), ACC, w=2, a="d")
    c.path(pb.line(range(len(vv)), (vv - vv.min()) / (np.ptp(vv) or 1)), "#EA580C", w=2, a="d", dl=4, da="4 3")
    trend = np.polyval(np.polyfit(xs, lv, 1), xs); det = lv - trend
    pc = Panel(c, 34, 170, 180, 92, (0, len(lv) - 1), nice(det.min(), det.max()), "Detrended index")
    c.rect(34, pc.Y(0), 180, 1, "#9AA1B2")
    c.path(pc.area(xs, det, 0), f="#C7CBFF", o=0.8, a="f"); c.path(pc.line(xs, det), ACC, w=1.4, a="d", dl=3)
    dec = seasonal_decompose(pd.Series(lv), period=21, two_sided=True, extrapolate_trend="freq")
    sea = dec.seasonal.values[:63]
    pd_ = Panel(c, 270, 170, 180, 92, (0, len(sea) - 1), nice(sea.min(), sea.max()), "Seasonal part (21-day cycle)")
    c.path(pd_.line(range(len(sea)), sea), "#9333EA", w=2, a="d", dl=5)
    charts.append(c.out())


    cities = {}
    for st_, (city, reg, la, lo) in dbs.INVESTOR_CITIES.items(): cities[st_] = (city, reg, la, lo)
    NSE = (dbs.EXCHANGE[1], dbs.EXCHANGE[2])
    REGC = {"North": "#4F46E5", "West": "#EA580C", "South": "#0891B2", "East": "#9333EA"}
    def merc(la): return math.log(math.tan(math.pi / 4 + math.radians(la) / 2))


    c = Chart(22, "Unit 5", "Geospatial: Map Projections",
              "The 10 investor cities and NSE Mumbai under three projections. Same places, different shapes.",
              "Every flat map distorts something: area, shape or distance.")
    projs = [("Equirectangular", lambda lo, la: (lo, la)), ("Mercator", lambda lo, la: (lo, math.degrees(merc(la)))),
             ("Sinusoidal", lambda lo, la: ((lo - 80) * math.cos(math.radians(la)) + 80, la))]
    for k, (nm, f) in enumerate(projs):
        x0 = 20 + k * 152
        pts = [f(lo, la) for (_, _, la, lo) in cities.values()] + [f(NSE[1], NSE[0])]
        xs_ = [a for a, _ in pts]; ys_ = [b for _, b in pts]
        pn = Panel(c, x0, 40, 136, 200, nice(66, 92, 0), nice(min(ys_) - 2, max(ys_) + 2, 0), nm)
        c.rect(x0, 40, 136, 200, "#F7F8FC", 6)
        for g in range(68, 92, 4): c.path(pn.line([f(g, la)[0] for la in range(6, 32, 2)], [f(g, la)[1] for la in range(6, 32, 2)]), "#D5D9E4", w=0.8)
        for g in range(8, 32, 4): c.path(pn.line([f(lo, g)[0] for lo in range(66, 94, 2)], [f(lo, g)[1] for lo in range(66, 94, 2)]), "#D5D9E4", w=0.8)
        for j, (st_, (city, reg, la, lo)) in enumerate(cities.items()):
            x, y = f(lo, la); c.circ(pn.X(x), pn.Y(y), 3.5, REGC[reg], a="pop", dl=j)
        x, y = f(NSE[1], NSE[0]); c.circ(pn.X(x), pn.Y(y), 5, INK, a="pop", dl=12)
    c.circ(30, 262, 4, INK); c.text(38, 265, "NSE Mumbai", 8.5, INK)
    for k, (rg, col) in enumerate(REGC.items()): c.circ(130 + k * 70, 262, 4, col); c.text(138 + k * 70, 265, rg, 8.5, INK)
    charts.append(c.out())


    c = Chart(23, "Unit 5", "Geospatial: Map Layers",
              "Layer 1 grid, layer 2 cities sized by investors, layer 3 order routes to NSE Mumbai, layer 4 labels.",
              "A map is a stack of layers; each adds one kind of information.")
    pn = Panel(c, 40, 20, 300, 260, (66, 92), (7, 31))
    c.rect(40, 20, 300, 260, "#F7F8FC", 8)
    for g in range(68, 92, 4): c.rect(pn.X(g), 20, 1, 260, "#E1E4EC")
    for g in range(8, 32, 4): c.rect(40, pn.Y(g), 300, 1, "#E1E4EC")
    icnt = inv.groupby("home_state").size()
    for j, (st_, (city, reg, la, lo)) in enumerate(cities.items()):
        x, y = pn.X(lo), pn.Y(la); nx, ny = pn.X(NSE[1]), pn.Y(NSE[0])
        c.path("M%.1f,%.1f Q%.1f,%.1f %.1f,%.1f" % (x, y, (x + nx) / 2, min(y, ny) - 30, nx, ny), REGC[reg], w=1.4, o=0.7, a="d", dl=4 + j, da="")
    for j, (st_, (city, reg, la, lo)) in enumerate(cities.items()):
        c.circ(pn.X(lo), pn.Y(la), 2.5 + icnt.get(st_, 0) * 0.45, REGC[reg], 0.8, "pop", j)
        c.text(pn.X(lo) + 8, pn.Y(la) + 3, city, 8, INK, wt=600)
    c.circ(pn.X(NSE[1]), pn.Y(NSE[0]), 7, INK, a="pop", dl=14); c.text(pn.X(NSE[1]) - 10, pn.Y(NSE[0]) + 4, "NSE", 8.5, INK, "end", 750)
    for k, t_ in enumerate(["1  Grid / base", "2  Cities (size = investors)", "3  Routes to NSE", "4  Labels"]):
        c.rect(356, 60 + k * 44, 110, 34, "#FFFFFF", 6, a="f", dl=k * 3, sk="#D5D9E4"); c.text(364, 81 + k * 44, t_, 8.5, INK, wt=600)
    charts.append(c.out())


    TILES = {"Delhi": (2, 0), "Rajasthan": (1, 1), "Uttar Pradesh": (3, 1), "Gujarat": (0, 2), "West Bengal": (4, 2),
             "Maharashtra": (1, 3), "Telangana": (2, 3), "Karnataka": (1, 4), "Kerala": (1, 5), "Tamil Nadu": (2, 5)}
    ABBR = {"Delhi": "DL", "Rajasthan": "RJ", "Uttar Pradesh": "UP", "Gujarat": "GJ", "West Bengal": "WB", "Maharashtra": "MH",
            "Telangana": "TG", "Karnataka": "KA", "Kerala": "KL", "Tamil Nadu": "TN"}
    g_ = geo.set_index("home_state")
    c = Chart(24, "Unit 5", "Geospatial: Choropleth Map",
              "Indian states as tiles, shaded by traded value (Rs lakh) of investors living there.",
              "%s and %s investors traded the most." % tuple(g_["traded_value_lakh"].sort_values(ascending=False).index[:2]))
    mx = g_["traded_value_lakh"].max()
    for j, (st_, (cx_, cy_)) in enumerate(TILES.items()):
        v = g_.loc[st_, "traded_value_lakh"] if st_ in g_.index else 0
        x, y = 90 + cx_ * 62, 20 + cy_ * 44
        c.rect(x, y, 58, 40, seq(v / mx), 6, a="f", dl=j)
        c.text(x + 29, y + 18, ABBR[st_], 10, "#FFFFFF" if v / mx > 0.55 else INK, "middle", 750)
        c.text(x + 29, y + 31, "%.0f L" % v, 8, "#FFFFFF" if v / mx > 0.55 else MUT, "middle")
    for k in range(6): c.rect(420, 60 + k * 30, 20, 28, seq(1 - k / 5), 3)
    c.text(446, 74, "%.0f L" % mx, 8, INK); c.text(446, 224, "0", 8, INK)
    charts.append(c.out())

    c = Chart(25, "Unit 5", "Geospatial: Cartograms",
              "Each state tile is resized by its number of investors, so size means people, not land area.",
              "Cartograms swap land area for the number that matters.")
    mx = g_["investor_count"].max()
    for j, (st_, (cx_, cy_)) in enumerate(TILES.items()):
        v = g_.loc[st_, "investor_count"] if st_ in g_.index else 0
        s_ = 54 * math.sqrt(v / mx); x, y = 90 + cx_ * 62 + (58 - s_) / 2, 20 + cy_ * 44 + (40 - s_ * 0.74) / 2
        c.rect(x, y, s_, s_ * 0.74, REGC[cities[st_][1]], 5, a="pop", dl=j)
        c.text(90 + cx_ * 62 + 29, 20 + cy_ * 44 + 24, "%s %d" % (ABBR[st_], v), 8, "#FFFFFF" if s_ > 34 else INK, "middle", 700)
    for k, (rg, col) in enumerate(REGC.items()): c.circ(420, 80 + k * 22, 5, col); c.text(430, 83 + k * 22, rg, 9, INK)
    charts.append(c.out())


    c = Chart(26, "Case Study", "Supply Chain: Share Delivery Tracker (All Regions)",
              "Every buy order travels Investor -> Broker -> NSE -> Clearing -> Depository -> Demat. Target: T+1.",
              "Delay comes from brokers and paperwork, not distance.")
    steps = ["Investor", "Broker", "NSE", "Clearing", "Depository", "Demat"]
    for k, s_ in enumerate(steps):
        x = 30 + k * 76
        c.rect(x, 28, 64, 36, ACC if k in (0, 5) else "#EEF0FF", 8, a="f", dl=k * 2)
        c.text(x + 32, 50, s_, 8.5, "#FFFFFF" if k in (0, 5) else INK, "middle", 650)
        if k < 5: c.path("M%.1f,46 L%.1f,46" % (x + 64, x + 76), ACC, w=1.6, a="d", dl=k * 2 + 1)
    score = p.get_broker_scorecard()
    pn = Panel(c, 110, 96, 190, 170, (60, 100), (0, 5), "Broker on-time %")
    for k, (_, rw) in enumerate(score.iloc[::-1].iterrows()):
        y = pn.Y(k + 0.85); col = UP if rw["grade"] == "A" else ("#CA8A04" if rw["grade"] == "B" else DN)
        c.rect(110, y, pn.X(rw["on_time_pct"]) - 110, 22, col, 4, a="gx", dl=k * 2)
        c.text(104, y + 15, rw["broker"], 8.5, INK, "end", 600)
        c.text(pn.X(rw["on_time_pct"]) + 4, y + 15, "%.0f%% %s" % (rw["on_time_pct"], rw["grade"]), 8.5, INK, wt=700)
    done = deliv_all[deliv_all["status"].str.startswith("Delivered")]
    ot = (done["status"] == "Delivered On-Time (T+1)").mean() * 100
    c.path(arc(395, 190, 50, 66, -math.pi / 2, math.pi / 2), "none", "#EEF0F5")
    c.path(arc(395, 190, 50, 66, -math.pi / 2, -math.pi / 2 + math.pi * ot / 100), "none", UP, a="f", dl=8)
    c.text(395, 182, "%.0f%%" % ot, 17, INK, "middle", 750); c.text(395, 205, "on time (T+1)", 8, MUT, "middle"); c.text(395, 222, "target 95%", 8, MUT, "middle")
    charts.append(c.out())


    dates = [d.strftime("%Y-%m-%d") for d in mindex["date"]]
    g = prices.sort_values(["stock_id", "date"])
    stocks = []
    for _, rw in summary.sort_values("stock_id").iterrows():
        rep, h = p.analyse_stock(int(rw["stock_id"]), prices=prices)
        stocks.append(dict(id=int(rw["stock_id"]), sym=rw["symbol"], name=rw["company_name"], sec=rw["sector_name"], hq=rw["hq_state"],
            px=r2(rw["last_close"]), d1=r2(rw["change_1d"]), y1=r1(rw["return_1y"]), vol=r1(rw["volatility"]), dd=r1(rw["max_drawdown"]),
            beta=r2(rw["beta"]), h52=r2(rw["high_52w"]), l52=r2(rw["low_52w"]), m1=r1(rep["ret_1m"]), m3=r1(rep["ret_3m"]),
            rsi=r1(rep["rsi"]), sig=rep["signal"].split()[0], avgv=int(rep["avg_volume"]),
            o=[r2(v) for v in h["open"]], h=[r2(v) for v in h["high"]], l=[r2(v) for v in h["low"]],
            c=[r2(v) for v in h["close"]], v=[int(v) for v in h["volume"]]))

    kpis = {}
    for s_ in [None] + SEC:
        for rk in [None, 1, 2, 3, 4]:
            k_ = p.get_market_kpis(s_, rk, trades=trades, stocks=summary)
            kpis["%s|%s" % (s_ or "All", rk or 0)] = {a: (r1(b) if isinstance(b, float) else b) for a, b in k_.items()}

    pnl_risk = []
    for rk, lab in dbs.RISK_PROFILES.items():
        t = trades[trades["risk_profile"] == rk]
        pnl_risk.append(dict(risk=lab, real=r1(t[t["sell_date_dt"].notnull()]["pnl"].sum() / 1e5), unreal=r1(t[t["sell_date_dt"].isnull()]["pnl"].sum() / 1e5)))
    mc = trades["buy_date_dt"].dt.to_period("M").value_counts().sort_index().tail(12)
    monthly_orders = [dict(m=str(k_), label=k_.strftime("%b"), n=int(v)) for k_, v in mc.items()]

    investors = [dict(id=int(r["investor_id"]), name=r["name"], risk=r["risk_label"], state=r["home_state"], broker=r["broker"],
                      trades=int(r["total_trades"]), pnl=int(r["total_pnl"]), inv=int(r["total_invested"]), win=r1(r["win_rate"]))
                 for _, r in inv.iterrows()]
    tlist = [dict(id=int(r["trade_id"]), inv=int(r["investor_id"]), who=r["investor_name"], sym=r["symbol"], sec=r["sector_name"], q=int(r["quantity"]),
                  bd=r["buy_date"], bp=r2(r["buy_price"]), sd=r["sell_date_display"], xp=r2(r["exit_price"]), sl=r2(r["stop_loss"]),
                  ret=r1(r["return_pct"]), pnl=int(r["pnl"]), st=r["simple_status"], hit=bool(r["stop_loss_hit"]))
             for _, r in trades.sort_values("trade_id").iterrows()]

    delivery = {}
    for rg in [None, "North", "West", "South", "East"]:
        d = p.get_cleaned_deliveries(rg); done = d[d["status"].str.startswith("Delivered")]
        routes = d.groupby(["from_city", "region"]).agg(km=("distance_km", "first"), n=("delivery_id", "count"),
            ot=("status", lambda s: (s == "Delivered On-Time (T+1)").sum() / max(1, s.str.startswith("Delivered").sum()) * 100),
            late=("status", lambda s: (s == "Delivered Late").sum())).reset_index().sort_values("n", ascending=False)
        sc_ = p.get_broker_scorecard(rg)
        reasons = d[d["delay_reason"] != "-"]["delay_reason"].value_counts()
        mon = (d.assign(ot=d["status"] == "Delivered On-Time (T+1)", dn=d["status"].str.startswith("Delivered"))
               .groupby("order_month")[["ot", "dn"]].sum())
        mon = (mon["ot"] / mon["dn"].clip(lower=1) * 100).tail(12)
        delivery[rg or "All"] = dict(
            orders=int(len(d)), value=r1(d["order_value"].sum()), shares=int(done["quantity"].sum()),
            ontime=r1((done["status"] == "Delivered On-Time (T+1)").mean() * 100 if len(done) else 0),
            late=int((d["status"] == "Delivered Late").sum()), pending=int(d["status"].str.startswith("Pending").sum()),
            avgdays=r2(done["settle_days"].mean()),
            routes=[dict(city=r["from_city"], region=r["region"], km=int(r["km"]), n=int(r["n"]), ot=r1(r["ot"]), late=int(r["late"])) for _, r in routes.iterrows()],
            brokers=[dict(b=r["broker"], n=int(r["orders"]), ot=r1(r["on_time_pct"]), late=int(r["late"]), days=r2(r["avg_settle_days"]), g=r["grade"]) for _, r in sc_.iterrows()],
            reasons=[dict(r=k_, n=int(v)) for k_, v in reasons.items()],
            monthly=[dict(m=pd.Period(k_).strftime("%b"), v=r1(v)) for k_, v in mon.items()])
    city_xy = [dict(city=v[0], region=v[1], lat=v[2], lon=v[3]) for v in dbs.INVESTOR_CITIES.values()]

    data = dict(asOf=dates[-1], dates=dates,
        index=dict(lv=[r1(v) for v in mindex["index_level"]], ma20=[r1(v) for v in mindex["ma_20"]], ma50=[r1(v) for v in mindex["ma_50"]]),
        sectors={s_: [r1(v) for v in secidx[s_]] for s_ in SEC}, secColors=SC,
        secRet={s_: r1(sec_ret[s_]) for s_ in SEC}, stocks=stocks, kpis=kpis, pnlRisk=pnl_risk, monthlyOrders=monthly_orders,
        investors=investors, trades=tlist, delivery=delivery, cities=city_xy, nse=dict(lat=NSE[0], lon=NSE[1]))
    return charts, data

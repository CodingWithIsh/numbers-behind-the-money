"""Publication charts for 'What it really costs to send money from the UK'.
Static PNGs sized for Substack (1456 px wide = 2x the 728 px column)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch
import seaborn as sns

# ---- tokens (validated: blue/orange pass CVD + contrast on white) ----
SURFACE = "#ffffff"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
UK_LINE, GLOBAL_LINE = "#1f1f1e", "#a3a29c"
FEE, FX = "#2a78d6", "#eb6834"
W_IN, DPI = 7.28, 200
SOURCE = ("Source: World Bank, Remittance Prices Worldwide (2011 to Q3 2025). Simple averages of services that disclose "
          "their exchange rate, following the World Bank's method. Chart: Numbers Behind the Money")

sns.set_theme(style="white", font="Liberation Sans", rc={
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.size": 9.5, "xtick.labelsize": 9, "ytick.labelsize": 9, "axes.titlesize": 14,
})


def frame(height_in, top_in=1.05, bottom_in=1.0, left_in=0.55, right_in=0.25):
    fig = plt.figure(figsize=(W_IN, height_in), dpi=DPI)
    ax = fig.add_axes([left_in / W_IN, bottom_in / height_in,
                       1 - (left_in + right_in) / W_IN, 1 - (top_in + bottom_in) / height_in])
    return fig, ax


def heading(fig, title, subtitle, height_in):
    fig.text(0.18 / W_IN, 1 - 0.30 / height_in, title, fontsize=14.5, fontweight="bold", color=INK, va="top")
    fig.text(0.18 / W_IN, 1 - 0.62 / height_in, subtitle, fontsize=10, color=INK2, va="top")


def footer(fig, height_in, note=None):
    import textwrap
    lines = []
    for chunk in ([note] if note else []) + [SOURCE]:
        lines += textwrap.wrap(chunk, 132)
    fig.text(0.18 / W_IN, 0.09 / height_in, "\n".join(lines), fontsize=7.2, color=MUTED, va="bottom", linespacing=1.4)


def tidy(ax, grid_axis="y"):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(length=0)
    ax.tick_params(axis="x", pad=6)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.6, linestyle="-")
    ax.set_axisbelow(True)


def target_line(ax, x=None, y=None, label="", where="right"):
    kw = dict(color=INK2, linewidth=0.9, linestyle=(0, (4, 3)), zorder=2)
    if y is not None:
        ax.axhline(y, **kw)
        ax.text(ax.get_xlim()[1], y, label, ha="right", va="bottom", fontsize=8.5, color=INK2)
    else:
        ax.axvline(x, **kw)


def round_end_bar(ax, x0, x1, yc, h, rx, ry, color):
    """Horizontal bar from x0 to x1 with a rounded right end (square at the baseline)."""
    rx = min(rx, (x1 - x0)); ry = min(ry, h / 2); k = 0.5523
    y0, y1 = yc - h / 2, yc + h / 2
    verts = [(x0, y0), (x1 - rx, y0),
             (x1 - rx + k * rx, y0), (x1, y0 + ry - k * ry), (x1, y0 + ry),
             (x1, y1 - ry),
             (x1, y1 - ry + k * ry), (x1 - rx + k * rx, y1), (x1 - rx, y1),
             (x0, y1), (x0, y0)]
    codes = [MPath.MOVETO, MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO,
             MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.LINETO, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), facecolor=color, edgecolor="none", zorder=3))


def px_units(fig, ax):
    """Data units per output pixel along x and y (after limits are fixed)."""
    bb = ax.get_window_extent()
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    return (x1 - x0) / bb.width, abs(y1 - y0) / bb.height


def stacked_hbars(fig, ax, labels, fee, fx, bar_px=34, gap_px=4, radius_px=8):
    n = len(labels)
    ys = np.arange(n)
    ax.set_ylim(-0.7, n - 0.3)
    ux, uy = px_units(fig, ax)
    h, gap = bar_px * uy, gap_px * ux
    for y, f, m in zip(ys, fee, fx):
        # fee segment (square both ends: it sits on the baseline and abuts the margin segment)
        ax.add_patch(plt.Rectangle((0, y - h / 2), f, h, facecolor=FEE, edgecolor="none", zorder=3))
        round_end_bar(ax, f + gap, f + max(m, 0), y, h, radius_px * ux, radius_px * uy, FX)
    ax.set_yticks(ys, labels)
    return ys


def save(fig, path):
    fig.savefig(path, dpi=DPI)
    plt.close(fig)


# ---------------- Chart 1: UK vs global over time ----------------
def chart_trend(tr, path):
    H = 4.95
    fig, ax = frame(H, left_in=0.5, right_in=1.05)
    heading(fig, "Sending money from the UK costs 42% less than in 2011",
            "Average total cost of sending £120 (or $200 elsewhere), % of the amount sent", H)
    t = tr.index.values
    ax.plot(t, tr["global"], color=GLOBAL_LINE, lw=1.9, solid_capstyle="round", zorder=3, label="Global average")
    ax.plot(t, tr["uk"], color=UK_LINE, lw=2.1, solid_capstyle="round", zorder=4, label="From the UK")
    ax.set_xlim(2010.8, 2025.8); ax.set_ylim(0, 10)
    ax.set_yticks(range(0, 11, 2), [f"{v}%" for v in range(0, 11, 2)])
    ax.set_xticks(range(2011, 2026, 2), [str(v) for v in range(2011, 2026, 2)])
    tidy(ax)
    target_line(ax, y=3, label="UN 2030 target: 3%")
    for col, colr, dy in (("uk", UK_LINE, -0.05), ("global", GLOBAL_LINE, 0.05)):
        y_end, y_start = tr[col].iloc[-1], tr[col].iloc[0]
        ax.plot([t[-1]], [y_end], "o", ms=6.5, color=colr, mec=SURFACE, mew=1.6, zorder=5)
        ax.plot([t[0]], [y_start], "o", ms=6.5, color=colr, mec=SURFACE, mew=1.6, zorder=5)
        name = "UK" if col == "uk" else "Global"
        ax.annotate(f"{name} {y_end:.1f}%", (t[-1], y_end), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=9.5, color=INK, fontweight="bold" if col == "uk" else "normal",
                    annotation_clip=False)
    ax.annotate(f"UK {tr['uk'].iloc[0]:.1f}%", (t[0], tr["uk"].iloc[0]), xytext=(4, -16),
                textcoords="offset points", fontsize=9, color=INK)
    ax.annotate(f"Global {tr['global'].iloc[0]:.1f}%", (t[0], tr["global"].iloc[0]), xytext=(4, 9),
                textcoords="offset points", fontsize=9, color=INK2)
    leg = ax.legend(loc="lower left", frameon=False, fontsize=9, handlelength=1.6)
    for txt in leg.get_texts(): txt.set_color(INK2)
    footer(fig, H, note="Survey rounds were twice a year until 2013, then quarterly. There is no Q2 2025 round.")
    save(fig, path)


# ---------------- Chart 2: fee vs exchange-rate margin ----------------
def chart_split(tr, path):
    H = 4.95
    fig, ax = frame(H, left_in=0.5, right_in=1.75)
    heading(fig, "The fee has fallen by more than half. The exchange-rate margin hasn't",
            "Sending £120 from the UK: average fee and exchange-rate margin, % of the amount sent", H)
    t = tr.index.values
    ax.plot(t, tr["uk_fee"], color=FEE, lw=2.1, solid_capstyle="round", zorder=4, label="Upfront fee")
    ax.plot(t, tr["uk_fx"], color=FX, lw=2.1, solid_capstyle="round", zorder=4, label="Exchange-rate margin")
    ax.set_xlim(2010.8, 2025.8); ax.set_ylim(0, 6)
    ax.set_yticks(range(0, 7, 1), [f"{v}%" for v in range(0, 7, 1)])
    ax.set_xticks(range(2011, 2026, 2), [str(v) for v in range(2011, 2026, 2)])
    tidy(ax)
    for col, colr, name, dy in (("uk_fee", FEE, "Fee", -9), ("uk_fx", FX, "Exchange-rate margin", 9)):
        ye, ys = tr[col].iloc[-1], tr[col].iloc[0]
        for xx, yy in ((t[-1], ye), (t[0], ys)):
            ax.plot([xx], [yy], "o", ms=6.5, color=colr, mec=SURFACE, mew=1.6, zorder=5)
        ax.annotate(f"{name} {ye:.1f}%", (t[-1], ye), xytext=(8, dy), textcoords="offset points",
                    va="center", fontsize=9.5, color=INK, annotation_clip=False)
        ax.annotate(f"{ys:.1f}%", (t[0], ys), xytext=(6, 8 if col == "uk_fee" else -14),
                    textcoords="offset points", fontsize=9, color=INK)
    leg = ax.legend(loc="upper right", frameon=False, fontsize=9, handlelength=1.6)
    for txt in leg.get_texts(): txt.set_color(INK2)
    share0 = tr["uk_fx"].iloc[0] / tr["uk"].iloc[0] * 100; share1 = tr["uk_fx"].iloc[-1] / tr["uk"].iloc[-1] * 100
    footer(fig, H, note=(f"The exchange-rate margin was {share0:.0f}% of the total cost in Q1 2011 and {share1:.0f}% "
                         "in Q3 2025. Margin = gap between the provider's rate and the interbank rate."))
    save(fig, path)


# ---------------- Chart 3: corridors ----------------
def chart_corridors(cor, path, small_n=5):
    c = cor.sort_values("total")  # most expensive ends up at the top
    labels = [f"{d}*" if n < small_n else d for d, n in zip(c.index, c["services"])]
    n = len(c); H = 0.24 * n + 2.55
    fig, ax = frame(H, top_in=1.5, bottom_in=1.0, left_in=1.25, right_in=0.6)
    heading(fig, "Where it costs most to send £120 from the UK",
            "Average total cost by destination, Q3 2025: upfront fee + exchange-rate margin", H)
    ax.set_xlim(0, 13.2)
    ys = stacked_hbars(fig, ax, labels, c["fee"].values, c["fx"].values, bar_px=26, gap_px=4, radius_px=7)
    for y, tot in zip(ys, c["total"].values):
        ax.text(tot + 0.15, y, f"{tot:.1f}%", va="center", fontsize=8.6, color=INK, zorder=6,
                bbox=dict(boxstyle="square,pad=0.12", facecolor=SURFACE, edgecolor="none"))
    ax.set_xticks(range(0, 14, 2), [f"{v}%" for v in range(0, 14, 2)])
    tidy(ax, grid_axis="x")
    target_line(ax, x=3)
    target_line(ax, x=5)
    ax.text(3, n - 0.25, "UN target: 3%", ha="right", va="bottom", fontsize=8, color=INK2)
    ax.text(5.08, n - 0.25, "UN: no route above 5%", ha="left", va="bottom", fontsize=8, color=INK2)
    # legend keys (identity never by colour alone)
    fx0 = 1.25 / W_IN
    fig.patches.extend([plt.Rectangle((fx0, 1 - 1.0 / H), 0.12 / W_IN, 0.1 / H, transform=fig.transFigure, color=FEE),
                        plt.Rectangle((fx0 + 1.05 / W_IN, 1 - 1.0 / H), 0.12 / W_IN, 0.1 / H, transform=fig.transFigure, color=FX)])
    fig.text(fx0 + 0.17 / W_IN, 1 - 0.95 / H, "Upfront fee", fontsize=9, color=INK2, va="center")
    fig.text(fx0 + 1.22 / W_IN, 1 - 0.95 / H, "Exchange-rate margin", fontsize=9, color=INK2, va="center")
    ax.tick_params(axis="y", labelsize=9, labelcolor=INK)
    small = [d for d, k in zip(c.index, c["services"]) if k < small_n]
    note = (f"* {', '.join(small)}: only {int(c.loc[small[0], 'services'])} services surveyed, so treat with caution. "
            if small else "") + f"{int(c['services'].sum())} services across {n} UK routes."
    footer(fig, H, note=note)
    save(fig, path)


# ---------------- Chart 4: how you send and receive ----------------
def chart_channels(ch, path, amount=120):
    c = ch.iloc[::-1]
    labels = [f"{i}\n{int(k)} services" for i, k in zip(c.index, c["services"])]
    H = 4.05
    fig, ax = frame(H, top_in=1.25, bottom_in=1.0, left_in=2.15, right_in=0.95)
    heading(fig, "How you send and collect the money changes the price",
            "Average total cost of sending £120 from the UK, Q3 2025", H)
    ax.set_xlim(0, 12.5)
    ys = stacked_hbars(fig, ax, labels, c["fee"].values, c["fx"].values, bar_px=40, gap_px=4, radius_px=8)
    for y, tot in zip(ys, c["total"].values):
        ax.text(tot + 0.18, y, f"{tot:.1f}%  (£{tot * amount / 100:.2f})", va="center", fontsize=9.5, color=INK)
    ax.set_xticks(range(0, 13, 2), [f"{v}%" for v in range(0, 13, 2)])
    tidy(ax, grid_axis="x")
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", labelsize=9.2, labelcolor=INK)
    for lab in ax.get_yticklabels(): lab.set_linespacing(1.3)
    fx0 = 2.15 / W_IN
    fig.patches.extend([plt.Rectangle((fx0, 1 - 0.98 / H), 0.12 / W_IN, 0.1 / H, transform=fig.transFigure, color=FEE),
                        plt.Rectangle((fx0 + 1.05 / W_IN, 1 - 0.98 / H), 0.12 / W_IN, 0.1 / H, transform=fig.transFigure, color=FX)])
    fig.text(fx0 + 0.17 / W_IN, 1 - 0.93 / H, "Upfront fee", fontsize=9, color=INK2, va="center")
    fig.text(fx0 + 1.22 / W_IN, 1 - 0.93 / H, "Exchange-rate margin", fontsize=9, color=INK2, va="center")
    footer(fig, H, note="Online = paid on a website or app by card or bank transfer. Agent = paid in cash at a shop or counter.")
    save(fig, path)


# ---------------- Chart 5 (seaborn): every service, same route ----------------
def chart_spread(df_uk_latest, path, top=12):
    d = df_uk_latest.copy()
    counts = d["destination"].value_counts()
    keep = counts.index[:top]
    d = d[d["destination"].isin(keep)]
    order = d.groupby("destination")["total"].median().sort_values().index
    H = 0.36 * len(order) + 2.2
    fig, ax = frame(H, top_in=1.1, bottom_in=1.0, left_in=1.25, right_in=0.3)
    heading(fig, "Same route, very different prices",
            f"Every service surveyed on the UK's {top} most-covered routes, Q3 2025 (one dot per service)", H)
    sns.stripplot(data=d, x="total", y="destination", order=order, ax=ax, color=FEE, size=4.2, alpha=0.55,
                  jitter=0.22, linewidth=0, zorder=3)
    med = d.groupby("destination")["total"].median().reindex(order)
    ax.scatter(med.values, range(len(order)), marker="|", s=260, color=INK, linewidths=1.6, zorder=4, label="Median")
    ax.set_xlim(-2, 21); ax.set_xticks(range(0, 21, 5), [f"{v}%" for v in range(0, 21, 5)])
    ax.set_xlabel(""); ax.set_ylabel("")
    tidy(ax, grid_axis="x")
    target_line(ax, x=3)
    ax.text(3.2, -0.65, "UN target 3%", fontsize=8, color=INK2, va="bottom")
    ax.tick_params(axis="y", labelsize=9, labelcolor=INK)
    leg = ax.legend(loc="lower right", frameon=False, fontsize=9)
    for txt in leg.get_texts(): txt.set_color(INK2)
    footer(fig, H, note="Total cost of sending £120 = fee + exchange-rate margin. A few services price "
                        "slightly better than the interbank rate, so a dot can sit below 0%.")
    save(fig, path)


# ---------------- Chart 6: the model ----------------
def chart_model(res, imp, labels, path):
    """Top: test error by model (main model highlighted). Bottom: permutation importance."""
    import matplotlib.gridspec as gs
    H = 6.6
    fig = plt.figure(figsize=(W_IN, H), dpi=DPI)
    heading(fig, "A model can predict the price, roughly",
            "Predicting what UK transfers cost in 2025, trained only on earlier data (Q2 2016 to 2024)", H)
    left, right = 2.55 / W_IN, 0.75 / W_IN
    ax1 = fig.add_axes([left, 1 - 3.15 / H, 1 - left - right, 1.75 / H])
    ax2 = fig.add_axes([left, 1.05 / H, 1 - left - right, 1.95 / H])

    r = res["test_mae_2025"].iloc[::-1]
    main = "Gradient boosting"
    ax1.set_xlim(0, 3.6)
    ys = np.arange(len(r)); ax1.set_ylim(-0.6, len(r) - 0.4)
    ux, uy = px_units(fig, ax1)
    for y, (name, v) in zip(ys, r.items()):
        round_end_bar(ax1, 0, v, y, 30 * uy, 7 * ux, 7 * uy, FEE if name == main else GLOBAL_LINE)
        ax1.text(v + 0.05, y, f"{v:.2f}", va="center", fontsize=9, color=INK)
    ax1.set_yticks(ys, list(r.index)); tidy(ax1, grid_axis="x"); ax1.spines["bottom"].set_visible(False)
    ax1.set_xticks([0, 1, 2, 3], ["0", "1", "2", "3"])
    ax1.tick_params(axis="y", labelsize=9, labelcolor=INK)
    ax1.set_title("Average error on 2025 prices (percentage points, lower is better)", loc="left",
                  fontsize=9.5, color=INK2, pad=6, x=-0.33)

    i = imp.rename(index=labels).iloc[::-1]
    ax2.set_xlim(0, 1.45)
    ys = np.arange(len(i)); ax2.set_ylim(-0.6, len(i) - 0.4)
    ux, uy = px_units(fig, ax2)
    for y, v in zip(ys, i.values):
        if v > 0.005:
            round_end_bar(ax2, 0, v, y, 24 * uy, 6 * ux, 6 * uy, FEE)
        ax2.text(max(v, 0) + 0.02, y, f"+{max(v, 0):.2f}", va="center", fontsize=8.6, color=INK)
    ax2.set_yticks(ys, list(i.index)); tidy(ax2, grid_axis="x"); ax2.spines["bottom"].set_visible(False)
    ax2.set_xticks([0, 0.5, 1.0], ["0", "0.5", "1.0"])
    ax2.tick_params(axis="y", labelsize=9, labelcolor=INK)
    ax2.set_title("What the gradient-boosting model relies on: extra error if a feature is scrambled", loc="left",
                  fontsize=9.5, color=INK2, pad=6, x=-0.33)
    footer(fig, H, note=("Test set: 1,625 UK price quotes from Q1 and Q3 2025 (median cost 4.0%). Settings tuned on 2024. "
                         "Feature importance shows what helps prediction, not what causes prices, and related features share credit."))
    save(fig, path)

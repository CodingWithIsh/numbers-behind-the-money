"""One-page figure of the Gaia DR3 data for alpha, beta and gamma Trianguli.

Reads data/trianguli_summary.csv (built from the ESA Gaia archive query) and
data/hip2_tri.csv (Hipparcos, van Leeuwen 2007), and writes
trianguli_gaia_dr3.png and trianguli_gaia_dr3.pdf next to this script.
"""
import csv
import math
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = Path(__file__).resolve().parent
LY_PER_PC = 3.261563777
YEARS = 30_000  # length of the proper-motion arrows on the sky map

# One accent hue for Gaia values, the de-emphasis grey for Hipparcos fill-ins
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
GAIA = "#2a78d6"
HIP = "#898781"
GAIA_TINT = "#e0ecfb"
HIP_TINT = "#efeeea"

plt.rcParams.update({
    "font.family": "Helvetica Neue",
    "font.size": 11,
    "text.color": INK,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK_2,
    "axes.labelsize": 11,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK_2,
    "ytick.labelcolor": INK_2,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})

GREEK = {"alpha Tri": "α", "beta Tri": "β", "gamma Tri": "γ"}
NUMERIC = ["G_mag", "ra_deg", "ra_err_mas", "dec_deg", "dec_err_mas",
           "parallax_mas", "parallax_err_mas", "dist_pc", "dist_err_pc",
           "dist_ly", "dist_err_ly", "pmra_masyr", "pmra_err", "pmdec_masyr",
           "pmdec_err", "pm_total_masyr", "rv_kms", "rv_err_kms", "ruwe"]


def load():
    with open(HERE / "data" / "trianguli_summary.csv") as f:
        stars = list(csv.DictReader(f))
    with open(HERE / "data" / "hip2_tri.csv") as f:
        hip = {r["hip"]: r for r in csv.DictReader(f)}
    for s in stars:
        s["letter"] = GREEK[s["star"]]
        s["from_gaia"] = s["src_astrometry"] == "Gaia DR3"
        for k in NUMERIC:
            s[k] = float(s[k]) if s[k] else None
    return stars, hip


def bottom_of(fig, artist):
    fig.canvas.draw()
    return artist.get_window_extent().transformed(fig.transFigure.inverted()).y0


def panel_title(fig, x, y, title, subtitle):
    fig.text(x, y, title, size=15, weight="bold", va="bottom")
    fig.text(x, y - 0.005, subtitle, size=10.5, color=INK_2, va="top", linespacing=1.4)


def sky_map(ax, stars):
    dec0 = 31.5
    ax.set_xlim(35.6, 27.4)  # right ascension increases to the left (east), as on a star chart
    ax.set_ylim(26.9, 36.0)
    ax.set_aspect(1 / math.cos(math.radians(dec0)))
    ax.set_anchor("W")
    ticks = [(1, 50), (2, 0), (2, 10), (2, 20)]
    ax.set_xticks([15 * (h + m / 60) for h, m in ticks])
    ax.set_xticklabels([f"{h}h {m:02d}m" for h, m in ticks])
    ax.set_yticks(range(28, 37, 2))
    ax.set_yticklabels([f"+{d}°" for d in range(28, 37, 2)])
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=6)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.set_xlabel("Right ascension", labelpad=8)
    ax.set_ylabel("Declination", labelpad=8)

    # The constellation's stick figure is the triangle itself
    by_name = {s["star"]: s for s in stars}
    outline = ["alpha Tri", "beta Tri", "gamma Tri", "alpha Tri"]
    ax.plot([by_name[n]["ra_deg"] for n in outline], [by_name[n]["dec_deg"] for n in outline],
            color=AXIS, lw=1, zorder=1)

    # Label side and extra clearance (points) for each star, chosen to stay clear of its
    # arrow and the triangle's edges; gamma's label sits inside the triangle's corner
    sides = {"alpha Tri": ("lower left", 0), "beta Tri": ("right", 0), "gamma Tri": ("right", 18)}
    for s in stars:
        ra, dec = s["ra_deg"], s["dec_deg"]
        deg = YEARS / 3.6e6
        end = (ra + s["pmra_masyr"] * deg / math.cos(math.radians(dec)), dec + s["pmdec_masyr"] * deg)
        ax.add_patch(FancyArrowPatch((ra, dec), end, arrowstyle="-|>", mutation_scale=16, lw=2,
                                     color=GAIA if s["from_gaia"] else HIP, zorder=2,
                                     shrinkA=0, shrinkB=0))
        # Dot area scales with brightness (flux relative to G = 3)
        size = 650 * 10 ** (-0.4 * (s["G_mag"] - 3.0))
        ax.scatter(ra, dec, s=size, color=INK, edgecolor=SURFACE, linewidth=2, zorder=3)

        side, extra = sides[s["star"]]
        r = math.sqrt(size / math.pi) + 8 + extra  # clearance from the dot's edge, in points
        if side == "right":
            xy, ha, va_name = (r, 1), "left", "bottom"
        else:
            xy, ha, va_name = (-r * 0.75, -r * 0.55), "right", "top"
        name = ax.annotate(f"{s['letter']} Trianguli", (ra, dec), xytext=xy,
                           textcoords="offset points", ha=ha, va=va_name, size=12.5,
                           weight="bold", zorder=4)
        anchor = (0, 0) if ha == "left" else (1, 0)
        ax.annotate(f"magnitude {s['G_mag']:.1f}", xy=anchor, xycoords=name, xytext=(0, -2),
                    textcoords="offset points", ha=ha, va="top", size=9.5, color=INK_2, zorder=4)


def rounded_bar(ax, y, length, height, colour, fig):
    """Horizontal bar with a 4px-style rounded end, square at the baseline."""
    pos = ax.get_position()
    width_in, height_in = fig.get_size_inches()
    x_per_in = (ax.get_xlim()[1] - ax.get_xlim()[0]) / (pos.width * width_in)
    y_per_in = abs(ax.get_ylim()[1] - ax.get_ylim()[0]) / (pos.height * height_in)
    r = 0.045 * x_per_in
    ax.add_patch(FancyBboxPatch((0, y - height / 2), length, height,
                                boxstyle=f"round,pad=0,rounding_size={r}",
                                mutation_aspect=y_per_in / x_per_in, color=colour, lw=0))
    ax.add_patch(Rectangle((0, y - height / 2), 2 * r, height, color=colour, lw=0))


def distance_chart(ax, stars, fig):
    ax.set_xlim(0, 140)
    ax.set_ylim(len(stars) - 0.55, -0.85)
    ax.set_xticks(range(0, 141, 20))
    ax.set_yticks([])
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=6)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.set_xlabel("Light years from the Sun", labelpad=8)

    for i, s in enumerate(stars):
        colour = GAIA if s["from_gaia"] else HIP
        rounded_bar(ax, i, s["dist_ly"], 0.26, colour, fig)
        name = ax.text(0, i - 0.24, f"{s['letter']} Tri", size=12, weight="bold", va="bottom")
        value = ax.annotate(f"{s['dist_ly']:.1f} ± {s['dist_err_ly']:.1f} ly   ({s['dist_pc']:.2f} pc)",
                            xy=(1, 0), xycoords=name, xytext=(8, 0), textcoords="offset points",
                            va="bottom", size=11)
        ax.annotate("Gaia DR3" if s["from_gaia"] else "Hipparcos", xy=(1, 0), xycoords=value,
                    xytext=(8, 0), textcoords="offset points", va="bottom", size=10, color=MUTED)


def key_points(fig, x, y, stars, hip):
    gamma = next(s for s in stars if s["star"] == "gamma Tri")
    gamma_hip_ly = 1000 / float(hip["10670"]["plx"]) * LY_PER_PC
    points = [
        f"γ Tri has a complete Gaia record: position, parallax, proper motion and radial "
        f"velocity ({gamma['rv_kms']:+.1f} km/s, moving away from us).",
        "α and β Tri are among the brightest stars Gaia observed, and DR3 gives only their "
        "positions. Their distances and motions here come from Hipparcos.",
        "Neither α nor β Tri has a Gaia radial velocity. Both are binary stars, so that speed "
        "changes as they orbit.",
        f"γ Tri's Gaia fit is flagged as slightly uncertain (RUWE {gamma['ruwe']:.2f}; the usual "
        f"cut-off is 1.4). Hipparcos puts it a little closer, at {gamma_hip_ly:.0f} ly.",
    ]
    heading = fig.text(x, y, "What's in the data, and what's missing", size=13, weight="bold",
                       va="top")
    y = bottom_of(fig, heading) - 0.012
    for p in points:
        fig.text(x, y, "•", size=11, color=INK_2, va="top")
        body = fig.text(x + 0.013, y, "\n".join(textwrap.wrap(p, 74)), size=11, color=INK,
                        va="top", linespacing=1.45)
        y = bottom_of(fig, body) - 0.011


def table(ax, stars):
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(1, 0)
    col_x = [0, 0.19, 0.46, 0.73, 1.0]
    header_h = 0.11
    gap_x, gap_y = 0.0017, 0.0038  # the 2px surface gap between cells
    pad = 0.012

    def astrometry(s, main, sub=""):
        if s["from_gaia"]:
            return main, sub, "gaia"
        return main, f"{sub}  ·  Hipparcos" if sub else "Hipparcos value", "hip"

    rows = [
        ("Gaia DR3 source ID", "",
         lambda s: (s["gaia_dr3_source_id"], f"HIP {s['hip']}", "gaia")),
        ("Right ascension", "ICRS, epoch 2016.0",
         lambda s: (s["ra_hms"], f"{s['ra_deg']:.6f}°   ± {s['ra_err_mas']:.2f} mas", "gaia")),
        ("Declination", "ICRS, epoch 2016.0",
         lambda s: (s["dec_dms"], f"{s['dec_deg']:+.6f}°   ± {s['dec_err_mas']:.2f} mas", "gaia")),
        ("Parallax", "",
         lambda s: astrometry(s, f"{s['parallax_mas']:.2f} ± {s['parallax_err_mas']:.2f} mas")),
        ("Distance", "1 / parallax",
         lambda s: astrometry(s, f"{s['dist_ly']:.1f} ± {s['dist_err_ly']:.1f} light years",
                              f"{s['dist_pc']:.2f} ± {s['dist_err_pc']:.2f} parsecs")),
        ("Proper motion, RA", "μα cos δ",
         lambda s: astrometry(s, f"{s['pmra_masyr']:+.2f} ± {s['pmra_err']:.2f} mas/yr")),
        ("Proper motion, Dec", "μδ",
         lambda s: astrometry(s, f"{s['pmdec_masyr']:+.2f} ± {s['pmdec_err']:.2f} mas/yr")),
        ("Radial velocity", "along our line of sight",
         lambda s: (f"{s['rv_kms']:+.1f} ± {s['rv_err_kms']:.1f} km/s", "moving away from us", "gaia")
         if s["rv_kms"] is not None else ("Not in Gaia DR3", "binary star, so it varies", "missing")),
    ]
    row_h = (1 - header_h) / len(rows)

    # Header: one column per star
    for j, s in enumerate(stars):
        x = col_x[j + 1] + pad
        ax.text(x, header_h * 0.42, f"{s['letter']} Trianguli", size=15, weight="bold", va="center")
        ax.text(x, header_h * 0.80, f"Gaia G magnitude {s['G_mag']:.2f}", size=9.5, color=INK_2,
                va="center")
    ax.plot([0, 1], [header_h - gap_y, header_h - gap_y], color=AXIS, lw=1)

    for i, (label, sublabel, cell) in enumerate(rows):
        top = header_h + i * row_h
        mid = top + row_h / 2
        ax.text(pad * 0.3, mid - (0.012 if sublabel else 0), label, size=11.5, weight="medium",
                va="center")
        if sublabel:
            ax.text(pad * 0.3, mid + 0.021, sublabel, size=9.5, color=MUTED, va="center")
        for j, s in enumerate(stars):
            main, sub, kind = cell(s)
            x0, x1 = col_x[j + 1], col_x[j + 2]
            fill = {"gaia": GAIA_TINT, "hip": HIP_TINT}.get(kind)
            if fill:
                ax.add_patch(Rectangle((x0 + gap_x, top + gap_y), x1 - x0 - 2 * gap_x,
                                       row_h - 2 * gap_y, color=fill, lw=0))
            missing = kind == "missing"
            ax.text(x0 + pad, mid - (0.012 if sub else 0), main, size=12,
                    color=MUTED if missing else INK, style="italic" if missing else "normal",
                    va="center")
            if sub:
                ax.text(x0 + pad, mid + 0.021, sub, size=9.5, color=INK_2, va="center")


def legend_row(fig, x, y):
    items = [(GAIA, "Measured by Gaia DR3"),
             (HIP, "Not in Gaia DR3, so the Hipparcos value is shown (observed 1989–93, re-analysed 2007)"),
             (None, "Not available")]
    for colour, text in items:
        if colour:
            fig.patches.append(Rectangle((x, y - 0.004), 0.011, 0.008, color=colour, lw=0,
                                         transform=fig.transFigure, figure=fig))
            t = fig.text(x + 0.016, y, text, size=11, color=INK_2, va="center")
        else:
            t = fig.text(x, y, "—  " + text, size=11, color=MUTED, style="italic", va="center")
        fig.canvas.draw()
        x = t.get_window_extent().transformed(fig.transFigure.inverted()).x1 + 0.03


def main():
    stars, hip = load()
    fig = plt.figure(figsize=(14, 15.5))

    fig.text(0.05, 0.972, "α, β and γ Trianguli in Gaia's latest data release", size=25,
             weight="bold", va="center")
    fig.text(0.05, 0.950, "Positions, distances and motions of the three stars that form the "
             "Triangle, from ESA's Gaia Data Release 3 (DR3)", size=13, color=INK_2, va="center")
    legend_row(fig, 0.05, 0.924)

    panel_title(fig, 0.05, 0.884, "Where they are on the sky",
                "Gaia positions at epoch 2016.0. East is to the left, as on a star\n"
                "chart; dot size shows brightness. Arrows show how far each star\n"
                f"drifts across the sky in {YEARS:,} years at its current speed.")
    sky_map(fig.add_axes([0.075, 0.465, 0.36, 0.345]), stars)

    panel_title(fig, 0.50, 0.884, "How far away they are",
                "Distance = 1 / parallax. The ± uncertainties are too small to show at this scale.")
    distance_chart(fig.add_axes([0.50, 0.735, 0.45, 0.115]), stars, fig)
    key_points(fig, 0.50, 0.672, stars, hip)

    panel_title(fig, 0.05, 0.408, "The numbers", "Cell colour shows where each value comes from.")
    table(fig.add_axes([0.05, 0.045, 0.90, 0.335]), stars)

    fig.text(0.05, 0.02,
             "Sources: ESA Gaia DR3 (gaiadr3.gaia_source, Gaia archive, Nov 2026); Hipparcos new reduction "
             "(van Leeuwen 2007). 1 parsec = 3.26 light years. mas = milliarcsecond (1/1000 of an arcsecond).",
             size=9.5, color=MUTED, va="center")

    for ext in ("png", "pdf"):
        fig.savefig(HERE / f"trianguli_gaia_dr3.{ext}", dpi=200)
    print("wrote", HERE / "trianguli_gaia_dr3.png")


if __name__ == "__main__":
    main()

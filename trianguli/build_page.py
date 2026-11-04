"""Build the interactive Trianguli page from the Gaia DR3 / Hipparcos query results.

Reads data/trianguli_summary.csv and data/hip2_tri.csv, works out the derived
values (3D position from Earth, speed across the sky, direction of motion) and
writes them into page_template.html, producing dominic_3d_model_project.html.
"""
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
LY_PER_PC = 3.261563777
KMS_PER_ARCSEC_PC = 4.740470  # tangential speed in km/s for 1 arcsec/yr at 1 pc
GREEK = {"alpha Tri": "α", "beta Tri": "β", "gamma Tri": "γ"}
COMPASS = ["north", "north-north-east", "north-east", "east-north-east", "east",
           "east-south-east", "south-east", "south-south-east", "south",
           "south-south-west", "south-west", "west-south-west", "west",
           "west-north-west", "north-west", "north-north-west"]


def num(value):
    return float(value) if value else None


def main():
    with open(HERE / "data" / "trianguli_summary.csv") as f:
        rows = list(csv.DictReader(f))
    with open(HERE / "data" / "hip2_tri.csv") as f:
        hip = {r["hip"]: r for r in csv.DictReader(f)}

    stars = []
    for r in rows:
        letter = GREEK[r["star"]]
        ra, dec = num(r["ra_deg"]), num(r["dec_deg"])
        d_pc = num(r["dist_pc"])
        pmra, pmdec = num(r["pmra_masyr"]), num(r["pmdec_masyr"])
        pm = math.hypot(pmra, pmdec)
        pa = math.degrees(math.atan2(pmra, pmdec)) % 360  # position angle, north through east
        a, b = math.radians(ra), math.radians(dec)
        unit = [math.cos(b) * math.cos(a), math.cos(b) * math.sin(a), math.sin(b)]
        stars.append({
            "letter": letter, "name": f"{letter} Trianguli", "short": f"{letter} Tri",
            "hip": r["hip"], "source_id": r["gaia_dr3_source_id"], "G": num(r["G_mag"]),
            "ra": ra, "dec": dec, "ra_hms": r["ra_hms"], "dec_dms": r["dec_dms"],
            "ra_err": num(r["ra_err_mas"]), "dec_err": num(r["dec_err_mas"]),
            "astro_src": "gaia" if r["src_astrometry"] == "Gaia DR3" else "hip",
            "plx": num(r["parallax_mas"]), "plx_err": num(r["parallax_err_mas"]),
            "d_pc": d_pc, "d_pc_err": num(r["dist_err_pc"]),
            "d_ly": num(r["dist_ly"]), "d_ly_err": num(r["dist_err_ly"]),
            "pmra": pmra, "pmra_err": num(r["pmra_err"]),
            "pmdec": pmdec, "pmdec_err": num(r["pmdec_err"]),
            "pm": pm, "pa": pa, "dir": COMPASS[round(pa / 22.5) % 16],
            "v_tan": KMS_PER_ARCSEC_PC * pm / 1000 * d_pc,
            "rv": num(r["rv_kms"]), "rv_err": num(r["rv_err_kms"]), "ruwe": num(r["ruwe"]),
            "xyz_pc": [d_pc * u for u in unit],
            "xyz_ly": [d_pc * LY_PER_PC * u for u in unit],
        })

    g = hip["10670"]
    g_pc = 1000 / float(g["plx"])
    data = {
        "stars": stars,
        "hip_gamma": {"plx": float(g["plx"]), "plx_err": float(g["e_plx"]),
                      "d_ly": g_pc * LY_PER_PC,
                      "d_ly_err": g_pc * LY_PER_PC * float(g["e_plx"]) / float(g["plx"])},
    }
    page = (HERE / "page_template.html").read_text()
    out = HERE / "dominic_3d_model_project.html"
    out.write_text(page.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False, indent=1)))
    print("wrote", out)


if __name__ == "__main__":
    main()

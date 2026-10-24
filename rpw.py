"""Numbers Behind the Money - UK remittance costs from the World Bank's
Remittance Prices Worldwide (RPW) dataset, 2011 to Q3 2025.

Method (the World Bank's): total cost = upfront fee + exchange-rate margin, as a %
of the amount sent; averages are simple averages across services; services that do
not disclose their exchange rate ("transparent" = no) are excluded.
Check: this reproduces the published global average of 6.36% for Q3 2025.
"""
from pathlib import Path
import pandas as pd

XLSX = Path(__file__).parent / "data" / "rpw_dataset_2011_2025_q3.xlsx"
SHEETS = ["Dataset (up to Q1 2016)", "Dataset (from Q2 2016)"]
LATEST = "2025_3Q"
FIRST = "2011_1Q"


def load(xlsx=XLSX, cache=True):
    """Read both data sheets and add clean numeric fields. Keeps transparent services only."""
    pkl = Path(xlsx).with_suffix(".clean.pkl")
    if cache and pkl.exists():
        return pd.read_pickle(pkl)
    parts = [pd.read_excel(xlsx, sheet_name=s, engine="openpyxl") for s in SHEETS]
    parts[1] = parts[1].loc[:, ~parts[1].columns.astype(str).str.startswith("Unnamed")]
    df = pd.concat(parts, ignore_index=True)          # union of columns; newer fields are blank before Q2 2016
    df["transparent"] = df["transparent"].astype(str).str.strip().str.lower().eq("yes")
    num = {"cc1 total cost %": "total", "cc1 fx margin": "fx", "cc1 lcu fee": "fee",
           "cc1 lcu amount": "amount", "cc2 total cost %": "total_500", "cc2 lcu amount": "amount_500"}
    for col, name in num.items():
        df[name] = pd.to_numeric(df[col], errors="coerce")
    df["fee_pct"] = df["fee"] / df["amount"] * 100   # total = fee_pct + fx (checked)
    df["year"] = df["period"].str[:4].astype(int)
    df["quarter"] = df["period"].str[5].astype(int)
    df["t"] = df["year"] + (df["quarter"] - 1) / 4
    df["destination"] = df["destination_name"].replace({"Gambia, The": "The Gambia"})
    df = df[df["transparent"]].copy()
    if cache:
        df.to_pickle(pkl)
    return df


def uk(df):
    return df[df["source_code"] == "GBR"]


def trend(df):
    """UK and global average total cost per survey round, plus the UK fee / FX split."""
    g = df.groupby("t")["total"].mean().rename("global")
    u = uk(df).groupby("t").agg(uk=("total", "mean"), uk_fee=("fee_pct", "mean"),
                                uk_fx=("fx", "mean"), services=("total", "size"),
                                corridors=("destination", "nunique"))
    return u.join(g)


def corridors(df, period=LATEST):
    u = uk(df)
    u = u[u["period"] == period]
    return (u.groupby("destination")
              .agg(services=("total", "size"), total=("total", "mean"),
                   fee=("fee_pct", "mean"), fx=("fx", "mean"),
                   cheapest=("total", "min"), dearest=("total", "max"))
              .sort_values("total"))


CHANNELS = [  # (label, access point, pickup method) - fields exist from Q2 2016
    ("Online → bank account", "Internet", "Bank account"),
    ("Online → mobile wallet", "Internet", "Mobile wallet"),
    ("Online → cash pickup", "Internet", "Cash"),
    ("Cash at an agent → cash pickup", "Agent", "Cash"),
]


def channels(df, period=LATEST):
    u = uk(df)
    u = u[u["period"] == period]
    rows = []
    for label, access, pickup in CHANNELS:
        s = u[(u["access point"] == access) & (u["pickup method"] == pickup)]
        rows.append({"channel": label, "services": len(s), "total": s["total"].mean(),
                     "fee": s["fee_pct"].mean(), "fx": s["fx"].mean()})
    return pd.DataFrame(rows).set_index("channel")


def like_for_like(df, start=FIRST, end=LATEST):
    """UK average over corridors surveyed in both periods."""
    u = uk(df)
    both = set(u[u["period"] == start]["destination"]) & set(u[u["period"] == end]["destination"])
    s = u[u["destination"].isin(both)]
    out = s[s["period"].isin([start, end])].groupby("period").agg(
        total=("total", "mean"), fee=("fee_pct", "mean"), fx=("fx", "mean"))
    per = (s[s["period"].isin([start, end])].groupby(["destination", "period"])["total"].mean()
           .unstack())
    per["change"] = per[end] - per[start]
    return sorted(both), out, per.sort_values("change")

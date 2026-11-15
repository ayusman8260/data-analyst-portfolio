"""Cohort retention, RFM segmentation and a simple LTV estimate on the Olist database.

Usage: python src/cohort_rfm.py [path_to_olist.db]
(build the database first with 01-olist-sql-analysis/load_db.py)
"""
import sqlite3
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


FIRST_FULL_MONTH = "2017-01"  # Nov-Dec 2016 have almost no orders (data gap), so earlier cohorts are distorted
LAST_FULL_MONTH = "2018-08"   # data after this is sparse/partial
MIN_COHORT_SIZE = 100         # tiny cohorts (e.g. 1 customer in Dec 2016) give meaningless percentages


def _month_diff(a, b):
    """Whole months from YYYY-MM string a to b."""
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:7]) - int(a[5:7])


def cohort_retention(con):
    sql = Path(__file__).resolve().parent.parent.joinpath("sql", "cohort.sql").read_text()
    long = pd.read_sql_query(sql, con)
    counts = long.pivot(index="cohort_month", columns="month_index", values="customers")
    # A missing cell means nobody came back (0) if that month is observable, otherwise unknown (NaN).
    for cohort in counts.index:
        observable = _month_diff(cohort, LAST_FULL_MONTH)
        for m in counts.columns:
            if m <= observable and pd.isna(counts.loc[cohort, m]):
                counts.loc[cohort, m] = 0
            if m > observable:
                counts.loc[cohort, m] = np.nan
    size = counts[0]
    keep = (size >= MIN_COHORT_SIZE) & (counts.index >= FIRST_FULL_MONTH) & (counts.index < LAST_FULL_MONTH)  # last cohort has no follow-up month
    counts = counts[keep]
    retention = counts.div(counts[0], axis=0) * 100
    retention.round(2).to_csv(OUT / "cohort_retention_pct.csv")

    shown = retention.iloc[:, :13]  # first 12 months after acquisition
    plt.figure(figsize=(12, 7))
    sns.heatmap(shown, annot=True, fmt=".2f", cmap="Blues", vmin=0, vmax=1.0,
                cbar_kws={"label": "% of cohort active"})
    plt.title("Monthly cohort retention (%), cohorts of 100+ customers. Month 0 = acquisition month")
    plt.xlabel("Months since first order")
    plt.ylabel("Cohort")
    plt.tight_layout()
    plt.savefig(OUT / "cohort_retention_heatmap.png", dpi=150)
    plt.close()

    m1_mean = retention[1].mean()
    m1_pooled = 100 * counts[1].sum() / counts[0].sum()
    print(f"Cohorts analysed: {len(counts)} ({counts.index[0]} to {counts.index[-1]}), {int(counts[0].sum()):,} customers")
    print(f"Month-1 retention: mean across cohorts {m1_mean:.2f}% | pooled {m1_pooled:.2f}%")
    pd.DataFrame([{"cohorts": len(counts), "customers": int(counts[0].sum()),
                   "month1_retention_mean_pct": round(m1_mean, 3),
                   "month1_retention_pooled_pct": round(m1_pooled, 3)}]).to_csv(OUT / "retention_summary.csv", index=False)
    return counts, retention


def load_orders(con):
    q = """
    SELECT c.customer_unique_id,
           o.order_id,
           o.order_purchase_timestamp AS ts,
           SUM(oi.price) AS value
    FROM orders o
    JOIN customers c   ON c.customer_id = o.customer_id
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY o.order_id
    """
    df = pd.read_sql_query(q, con, parse_dates=["ts"])
    return df


def rfm(orders):
    snapshot = orders["ts"].max() + pd.Timedelta(days=1)
    t = orders.groupby("customer_unique_id").agg(
        recency=("ts", lambda s: (snapshot - s.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("value", "sum"),
    )
    # R and M: quintiles (rank first so ties don't break qcut).
    t["R"] = pd.qcut(t["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    t["M"] = pd.qcut(t["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    # F: Olist has very few repeat buyers (most customers have exactly 1 order), so quintiles would
    # split identical customers arbitrarily. Use fixed, explainable bands instead.
    t["F"] = np.select([t["frequency"] >= 3, t["frequency"] == 2], [5, 3], default=1)

    # ~97% of customers bought exactly once, so repeat buyers are their own segment and
    # one-time buyers are split by recency (R) and spend (M).
    def segment(r):
        if r.frequency >= 2:
            return "Repeat buyers"
        if r.R >= 4 and r.M >= 4:
            return "Recent high-value (1 order)"
        if r.R >= 4:
            return "Recent lower-value (1 order)"
        if r.R <= 2 and r.M >= 4:
            return "Lapsed high-value (1 order)"
        if r.R <= 2:
            return "Lapsed lower-value (1 order)"
        return "Mid-recency (1 order)"

    t["segment"] = t.apply(segment, axis=1)
    summary = t.groupby("segment").agg(customers=("monetary", "size"), revenue=("monetary", "sum"),
                                       avg_value=("monetary", "mean"))
    summary["pct_customers"] = 100 * summary["customers"] / summary["customers"].sum()
    summary["pct_revenue"] = 100 * summary["revenue"] / summary["revenue"].sum()
    summary = summary.sort_values("revenue", ascending=False).round(2)
    summary.to_csv(OUT / "rfm_segments.csv")
    t.to_csv(OUT / "rfm_customers.csv")
    print("\nRFM segments:\n", summary.to_string())

    plt.figure(figsize=(8, 4.5))
    summary["pct_revenue"].sort_values().plot.barh(color="#4C72B0")
    plt.xlabel("% of revenue")
    plt.title("Revenue share by RFM segment")
    plt.tight_layout()
    plt.savefig(OUT / "rfm_revenue_share.png", dpi=150)
    plt.close()
    return t


def simple_ltv(orders, rfm_table):
    """Historical LTV = AOV x purchase frequency (orders per customer).
    This is a descriptive figure over the data window, NOT a forecast.
    Assumptions are printed so they can be quoted in the README."""
    aov = orders["value"].mean()
    freq = orders["order_id"].nunique() / orders["customer_unique_id"].nunique()
    ltv = aov * freq
    repeat = (rfm_table["frequency"] >= 2).mean() * 100
    print(f"\nAOV: {aov:,.2f} | orders per customer: {freq:.3f} | historical LTV: {ltv:,.2f} | repeat rate: {repeat:.2f}%")
    pd.DataFrame([{"aov": aov, "orders_per_customer": freq, "historical_ltv": ltv, "repeat_rate_pct": repeat}]
                 ).round(3).to_csv(OUT / "ltv_summary.csv", index=False)


def main(db="../01-olist-sql-analysis/olist.db"):
    con = sqlite3.connect(db)
    cohort_retention(con)
    orders = load_orders(con)
    table = rfm(orders)
    simple_ltv(orders, table)
    con.close()
    print(f"\nOutputs written to {OUT.resolve()}")


if __name__ == "__main__":
    main(*sys.argv[1:2])

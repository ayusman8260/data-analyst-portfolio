"""Transform: data-quality checks and KPI tables."""
import logging
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Raised when the input data is not fit to report on."""


def check_quality(tables, min_orders=100):
    """Fail loudly instead of publishing a wrong report."""
    orders, items = tables["orders"], tables["items"]
    problems = []
    if len(orders) < min_orders:
        problems.append(f"only {len(orders)} orders (expected at least {min_orders})")
    if orders["order_id"].duplicated().any():
        problems.append(f"{int(orders['order_id'].duplicated().sum())} duplicate order_ids")
    if orders["order_purchase_timestamp"].isna().mean() > 0.01:
        problems.append("more than 1% of orders have no purchase timestamp")
    orphan = ~items["order_id"].isin(orders["order_id"])
    if orphan.any():
        problems.append(f"{int(orphan.sum())} order_items rows reference unknown orders")
    if (items["price"] < 0).any():
        problems.append("negative item prices")
    if problems:
        raise DataQualityError("; ".join(problems))
    log.info("Data quality checks passed (%d orders)", len(orders))


def build_order_facts(tables):
    """One row per valid order with revenue, lateness and review score."""
    orders = tables["orders"]
    orders = orders[~orders["order_status"].isin(["canceled", "unavailable"])].copy()
    revenue = tables["items"].groupby("order_id")["price"].sum().rename("revenue")
    review = tables["reviews"].groupby("order_id")["review_score"].mean().rename("review_score")
    facts = orders.merge(revenue, on="order_id", how="left").merge(review, on="order_id", how="left")
    facts["revenue"] = facts["revenue"].fillna(0)
    delivered = facts["order_delivered_customer_date"].notna()
    facts["is_delivered"] = delivered
    facts["is_late"] = delivered & (facts["order_delivered_customer_date"] > facts["order_estimated_delivery_date"])
    facts["week"] = facts["order_purchase_timestamp"].dt.to_period("W-SUN").dt.start_time
    return facts


def weekly_kpis(facts):
    g = facts.groupby("week")
    k = pd.DataFrame({
        "orders": g["order_id"].nunique(),
        "revenue": g["revenue"].sum(),
        "avg_review": g["review_score"].mean(),
        "late_rate_pct": 100 * g["is_late"].sum() / g["is_delivered"].sum().replace(0, np.nan),
    }).astype({"late_rate_pct": float})
    k["aov"] = k["revenue"] / k["orders"]
    k["revenue_wow_pct"] = k["revenue"].pct_change() * 100
    k["orders_wow_pct"] = k["orders"].pct_change() * 100
    return k.round(2)


def repeat_rate(tables):
    """% of customers (by customer_unique_id) with 2+ valid orders."""
    o = tables["orders"]
    o = o[~o["order_status"].isin(["canceled", "unavailable"])]
    merged = o.merge(tables["customers"][["customer_id", "customer_unique_id"]], on="customer_id")
    per = merged.groupby("customer_unique_id")["order_id"].nunique()
    return round(100 * (per >= 2).mean(), 2)


def reporting_window(kpis, start_ratio=0.1, min_ratio=0.5, lookback=8):
    """Trim the weekly table to the weeks that are reasonable to report on.

    - Leading weeks with fewer than `start_ratio` x (median weekly orders) are dropped
      (platform ramp-up / sparse data). The threshold is relative, so it scales with the business.
    - Trailing weeks are dropped while their order volume is below `min_ratio` x the median of the
      previous `lookback` weeks: those are almost certainly incomplete (partial week or data lag).
      This rule is deliberately modest: a real dip (e.g. a strike or outage) can look the same as
      missing data, so the report also flags large week-over-week moves for a human to check.
    Returns (trimmed_table, number_of_trailing_weeks_dropped).
    """
    if kpis.empty:
        return kpis, 0
    big = kpis.index[kpis["orders"] >= start_ratio * kpis["orders"].median()]
    k = kpis.loc[big[0]:]
    for i in range(len(k) - 1, 0, -1):
        base = k["orders"].iloc[max(0, i - lookback):i].median()
        if k["orders"].iloc[i] >= min_ratio * base:
            return k.iloc[: i + 1], len(k) - (i + 1)
    return k.iloc[:1], len(k) - 1

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from transform import (DataQualityError, build_order_facts, check_quality, repeat_rate,  # noqa: E402
                       reporting_window, weekly_kpis)


def make_tables():
    orders = pd.DataFrame({
        "order_id": ["a", "b", "c", "d"],
        "customer_id": ["c1", "c2", "c3", "c4"],
        "order_status": ["delivered", "delivered", "canceled", "delivered"],
        "order_purchase_timestamp": pd.to_datetime(["2018-01-01", "2018-01-02", "2018-01-03", "2018-01-09"]),
        "order_delivered_customer_date": pd.to_datetime(["2018-01-05", "2018-01-12", None, "2018-01-12"]),
        "order_estimated_delivery_date": pd.to_datetime(["2018-01-10", "2018-01-10", "2018-01-10", "2018-01-15"]),
    })
    items = pd.DataFrame({"order_id": ["a", "b", "c", "d"], "price": [100.0, 50.0, 20.0, 30.0]})
    reviews = pd.DataFrame({"order_id": ["a", "b", "d"], "review_score": [5, 1, 4]})
    customers = pd.DataFrame({"customer_id": ["c1", "c2", "c3", "c4"],
                              "customer_unique_id": ["u1", "u1", "u2", "u3"]})
    return {"orders": orders, "items": items, "payments": pd.DataFrame(), "reviews": reviews, "customers": customers}


def test_canceled_orders_excluded():
    facts = build_order_facts(make_tables())
    assert set(facts.order_id) == {"a", "b", "d"}


def test_late_flag():
    facts = build_order_facts(make_tables()).set_index("order_id")
    assert not facts.loc["a", "is_late"]
    assert facts.loc["b", "is_late"]  # delivered 12th, promised 10th


def test_weekly_kpis_values():
    k = weekly_kpis(build_order_facts(make_tables()))
    first = k.iloc[0]
    assert first.orders == 2 and first.revenue == 150
    assert first.late_rate_pct == 50.0


def test_repeat_rate():
    # u1 has two valid orders; u3 has one (u2's only order was canceled) -> 1 of 2 customers
    assert repeat_rate(make_tables()) == 50.0


def test_quality_check_catches_duplicates():
    t = make_tables()
    t["orders"] = pd.concat([t["orders"], t["orders"].iloc[[0]]])
    try:
        check_quality(t, min_orders=1)
    except DataQualityError as e:
        assert "duplicate" in str(e)
    else:
        raise AssertionError("expected DataQualityError")


def test_reporting_window_drops_sparse_start_and_incomplete_tail():
    weeks = pd.date_range("2018-01-01", periods=12, freq="7D")
    orders = [3, 500, 520, 510, 530, 500, 515, 525, 505, 510, 150, 2]  # sparse start, partial + near-empty tail
    k = pd.DataFrame({"orders": orders}, index=weeks)
    trimmed, dropped = reporting_window(k)
    assert trimmed.index[0] == weeks[1]      # week with 3 orders removed
    assert trimmed.index[-1] == weeks[9]     # weeks with 150 and 2 orders removed
    assert dropped == 2

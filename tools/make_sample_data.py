"""Generate SMALL SYNTHETIC datasets that mimic the schemas of the real ones.

Use this only to smoke-test the code before downloading the real data.
NEVER report numbers from synthetic data on your resume.

Usage:
    python tools/make_sample_data.py olist  <out_dir>
    python tools/make_sample_data.py telco  <out_dir>
    python tools/make_sample_data.py cookie <out_dir>
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)


def olist(out, n_customers=3000, n_orders=4500):
    out.mkdir(parents=True, exist_ok=True)
    states = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC"]
    cats = ["cama_mesa_banho", "beleza_saude", "esporte_lazer", "informatica_acessorios", "moveis_decoracao"]
    cat_en = ["bed_bath_table", "health_beauty", "sports_leisure", "computers_accessories", "furniture_decor"]

    uniq = [f"u{i:05d}" for i in range(n_customers)]
    owners = rng.choice(uniq, n_orders, p=None)
    cust_state = {u: rng.choice(states, p=[.4, .2, .15, .08, .07, .05, .05]) for u in uniq}
    orders = pd.DataFrame({"order_id": [f"o{i:06d}" for i in range(n_orders)],
                           "customer_id": [f"c{i:06d}" for i in range(n_orders)]})
    customers = pd.DataFrame({"customer_id": orders.customer_id, "customer_unique_id": owners,
                              "customer_zip_code_prefix": 1000,
                              "customer_city": "city", "customer_state": [cust_state[o] for o in owners]})
    start = pd.Timestamp("2017-01-01")
    purchase = start + pd.to_timedelta(rng.integers(0, 600 * 24 * 3600, n_orders), unit="s")
    est = purchase + pd.to_timedelta(rng.integers(10, 30, n_orders), unit="D")
    actual = purchase + pd.to_timedelta(rng.integers(5, 35, n_orders), unit="D")
    status = rng.choice(["delivered", "canceled", "shipped", "unavailable"], n_orders, p=[.95, .02, .02, .01])
    fmt = "%Y-%m-%d %H:%M:%S"
    orders["order_status"] = status
    orders["order_purchase_timestamp"] = purchase.strftime(fmt)
    orders["order_approved_at"] = purchase.strftime(fmt)
    orders["order_delivered_carrier_date"] = purchase.strftime(fmt)
    orders["order_delivered_customer_date"] = np.where(status == "delivered", actual.strftime(fmt), None)
    orders["order_estimated_delivery_date"] = est.strftime(fmt)

    sellers = pd.DataFrame({"seller_id": [f"s{i:04d}" for i in range(120)],
                            "seller_zip_code_prefix": 1000, "seller_city": "city",
                            "seller_state": rng.choice(states, 120)})
    products = pd.DataFrame({"product_id": [f"p{i:04d}" for i in range(400)],
                             "product_category_name": rng.choice(cats, 400)})
    rows = []
    for oid in orders.order_id:
        for k in range(rng.choice([1, 1, 1, 2, 3])):
            rows.append((oid, k + 1, rng.choice(products.product_id), rng.choice(sellers.seller_id),
                         round(float(rng.lognormal(4.3, .7)), 2), round(float(rng.uniform(5, 40)), 2)))
    items = pd.DataFrame(rows, columns=["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"])
    items["shipping_limit_date"] = "2017-06-01 00:00:00"
    tot = items.groupby("order_id").apply(lambda d: (d.price + d.freight_value).sum(), include_groups=False).rename("payment_value").reset_index()
    tot["payment_sequential"] = 1
    tot["payment_type"] = rng.choice(["credit_card", "boleto", "voucher", "debit_card"], len(tot), p=[.74, .19, .05, .02])
    tot["payment_installments"] = rng.integers(1, 11, len(tot))
    reviews = pd.DataFrame({"review_id": [f"r{i}" for i in range(n_orders)], "order_id": orders.order_id,
                            "review_score": rng.choice([1, 2, 3, 4, 5], n_orders, p=[.1, .04, .08, .2, .58]),
                            "review_comment_title": None, "review_comment_message": None,
                            "review_creation_date": "2018-01-01 00:00:00", "review_answer_timestamp": "2018-01-02 00:00:00"})
    trans = pd.DataFrame({"product_category_name": cats, "product_category_name_english": cat_en})
    names = {"olist_orders_dataset": orders, "olist_customers_dataset": customers, "olist_order_items_dataset": items,
             "olist_order_payments_dataset": tot, "olist_order_reviews_dataset": reviews,
             "olist_products_dataset": products, "olist_sellers_dataset": sellers,
             "product_category_name_translation": trans}
    for n, d in names.items():
        d.to_csv(out / f"{n}.csv", index=False)


def telco(out, n=3000):
    out.mkdir(parents=True, exist_ok=True)
    contract = rng.choice(["Month-to-month", "One year", "Two year"], n, p=[.55, .21, .24])
    tenure = rng.integers(0, 73, n)
    internet = rng.choice(["DSL", "Fiber optic", "No"], n, p=[.34, .44, .22])
    monthly = np.round(np.where(internet == "Fiber optic", rng.normal(90, 12, n),
                       np.where(internet == "DSL", rng.normal(55, 10, n), rng.normal(22, 4, n))), 2)
    logit = (-0.5 + 1.4 * (contract == "Month-to-month") - 0.03 * tenure + 0.8 * (internet == "Fiber optic")
             - 0.8 * (contract == "Two year") + 0.005 * (monthly - 60))
    churn = rng.random(n) < 1 / (1 + np.exp(-logit))
    total = np.round(monthly * tenure, 2).astype(str)
    total[tenure == 0] = " "
    df = pd.DataFrame({
        "customerID": [f"{i:04d}-X" for i in range(n)], "gender": rng.choice(["Male", "Female"], n),
        "SeniorCitizen": rng.choice([0, 1], n, p=[.84, .16]), "Partner": rng.choice(["Yes", "No"], n),
        "Dependents": rng.choice(["Yes", "No"], n, p=[.3, .7]), "tenure": tenure,
        "PhoneService": rng.choice(["Yes", "No"], n, p=[.9, .1]), "InternetService": internet,
        "Contract": contract, "PaperlessBilling": rng.choice(["Yes", "No"], n),
        "PaymentMethod": rng.choice(["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"], n),
        "MonthlyCharges": monthly, "TotalCharges": total, "Churn": np.where(churn, "Yes", "No")})
    df.to_csv(out / "WA_Fn-UseC_-Telco-Customer-Churn.csv", index=False)


def cookie(out, n=20000):
    out.mkdir(parents=True, exist_ok=True)
    version = rng.choice(["gate_30", "gate_40"], n)
    rounds = np.minimum(rng.geometric(0.03, n), 40000)
    r1 = rng.random(n) < 0.445
    r7 = rng.random(n) < np.where(version == "gate_30", 0.19, 0.182)
    pd.DataFrame({"userid": np.arange(n), "version": version, "sum_gamerounds": rounds,
                  "retention_1": r1, "retention_7": r7}).to_csv(out / "cookie_cats.csv", index=False)


if __name__ == "__main__":
    kind, out = sys.argv[1], Path(sys.argv[2])
    {"olist": olist, "telco": telco, "cookie": cookie}[kind](out)
    print(f"wrote sample {kind} data to {out}")

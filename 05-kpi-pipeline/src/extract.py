"""Extract: read the raw Olist CSVs into DataFrames."""
from pathlib import Path
import pandas as pd

FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
}
DATE_COLS = ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]


def load_tables(data_dir):
    data_dir = Path(data_dir)
    tables = {name: pd.read_csv(data_dir / fname) for name, fname in FILES.items()}
    for c in DATE_COLS:
        tables["orders"][c] = pd.to_datetime(tables["orders"][c], errors="coerce")
    return tables

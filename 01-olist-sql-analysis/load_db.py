"""Load the Olist CSVs from ./data into a SQLite database (olist.db).

Usage: python load_db.py [data_dir] [db_path]
"""
import sqlite3
import sys
from pathlib import Path
import pandas as pd

FILES = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
    "olist_customers_dataset.csv": "customers",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}

def main(data_dir="data", db_path="olist.db"):
    data_dir = Path(data_dir)
    con = sqlite3.connect(db_path)
    for fname, table in FILES.items():
        df = pd.read_csv(data_dir / fname)
        df.to_sql(table, con, if_exists="replace", index=False)
        print(f"{table:22s} {len(df):>8,} rows")
    cur = con.cursor()
    for stmt in [
        "CREATE INDEX IF NOT EXISTS ix_oi_order ON order_items(order_id)",
        "CREATE INDEX IF NOT EXISTS ix_oi_seller ON order_items(seller_id)",
        "CREATE INDEX IF NOT EXISTS ix_oi_product ON order_items(product_id)",
        "CREATE INDEX IF NOT EXISTS ix_pay_order ON payments(order_id)",
        "CREATE INDEX IF NOT EXISTS ix_rev_order ON reviews(order_id)",
        "CREATE INDEX IF NOT EXISTS ix_ord_cust ON orders(customer_id)",
        "CREATE INDEX IF NOT EXISTS ix_cust_id ON customers(customer_id)",
    ]:
        cur.execute(stmt)
    con.commit()
    con.close()
    print(f"\nDatabase written to {db_path}")

if __name__ == "__main__":
    main(*sys.argv[1:3])

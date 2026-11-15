"""Make README charts from the query outputs (run run_queries.py first)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT = Path("outputs")

m = pd.read_csv(OUT / "q01_monthly_revenue.csv")
m = m[(m.month >= "2017-01") & (m.month <= "2018-08")]   # complete months only
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(m.month, m.revenue / 1e3, marker="o", color="#4C72B0")
ax.set_title("Monthly revenue (thousand BRL, item price, complete months only)")
ax.set_xticks(range(0, len(m), 2))
ax.set_xticklabels(m.month.iloc[::2], rotation=45)
plt.tight_layout(); plt.savefig(OUT / "monthly_revenue.png", dpi=150); plt.close()

s = pd.read_csv(OUT / "q08_late_rate_by_state.csv").sort_values("late_pct")
fig, ax = plt.subplots(figsize=(7, 7))
ax.barh(s.customer_state, s.late_pct, color="#C44E52")
ax.set_title("Late-delivery rate by customer state (%)")
plt.tight_layout(); plt.savefig(OUT / "late_rate_by_state.png", dpi=150); plt.close()

q = pd.read_csv(OUT / "q04_seller_concentration.csv")
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(q.quintile.astype(str), q.pct_of_revenue, color="#4C72B0")
ax.set_xlabel("Seller quintile (1 = top 20% by revenue)"); ax.set_ylabel("% of revenue")
ax.set_title("Seller revenue concentration")
plt.tight_layout(); plt.savefig(OUT / "seller_concentration.png", dpi=150); plt.close()
print("charts written")

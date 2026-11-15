"""Report: charts plus a markdown summary."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _fmt(x, pct=False):
    if x != x:  # NaN
        return "n/a"
    return f"{x:+.1f}%" if pct else f"{x:,.2f}"


def write_report(kpis, repeat, out_dir, dropped_weeks=0):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    kpis.to_csv(out / "weekly_kpis.csv")

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    kpis["revenue"].plot(ax=axes[0], color="#4C72B0")
    axes[0].set_title("Weekly revenue")
    kpis["late_rate_pct"].plot(ax=axes[1], color="#C44E52")
    axes[1].set_title("Late-delivery rate (%)")
    plt.tight_layout()
    plt.savefig(out / "weekly_kpis.png", dpi=150)
    plt.close()

    last, prev = kpis.iloc[-1], kpis.iloc[-2] if len(kpis) > 1 else None
    lines = [
        "# Weekly KPI report", "",
        f"Latest complete week: **week starting {kpis.index[-1].date()}**"
        + (f" ({dropped_weeks} later week(s) excluded as incomplete)" if dropped_weeks else ""), "",
        "| KPI | Latest week | Week-over-week |", "|---|---|---|",
        f"| Orders | {last.orders:,.0f} | {_fmt(last.orders_wow_pct, True)} |",
        f"| Revenue | {_fmt(last.revenue)} | {_fmt(last.revenue_wow_pct, True)} |",
        f"| Average order value | {_fmt(last.aov)} | |",
        f"| Late-delivery rate | {_fmt(last.late_rate_pct)}% | |",
        f"| Average review score | {_fmt(last.avg_review)} | |", "",
        f"Overall repeat-customer rate: **{repeat}%**", "",
        "![weekly kpis](weekly_kpis.png)", "",
    ]
    wow = last.revenue_wow_pct
    if wow == wow and abs(wow) > 30:   # NaN-safe
        lines[4:4] = [f"> **Warning:** revenue moved {wow:+.1f}% week-over-week. Check whether this is a real "
                        "change (campaign, outage, strike) or incomplete data before acting on it.", ""]
    (out / "kpi_report.md").write_text("\n".join(lines))
    return out / "kpi_report.md"

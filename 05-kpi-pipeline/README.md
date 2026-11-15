# Automated KPI Reporting Pipeline

**Problem:** weekly KPI reports built by hand are slow and error-prone. This pipeline rebuilds them from raw data, refuses to run on bad data, handles incomplete weeks, and is scheduled with GitHub Actions.

```
extract.py -> transform.py (quality checks + KPIs + week selection) -> report.py -> outputs/kpi_report.md + weekly_kpis.png
```

Tested on the real Olist data (99,441 orders): the full run takes about 2 seconds.

## KPIs
Orders, revenue, average order value, late-delivery rate, average review score, week-over-week change, and the overall repeat-customer rate.

## Safeguards
- **Data-quality gate:** `check_quality()` fails the run (exit code 1) on too few orders, duplicate order IDs, missing purchase timestamps, orphaned order items, or negative prices.
- **Incomplete-week handling:** sparse leading weeks are dropped, and trailing weeks with under 50% of the recent median volume are excluded (the report says how many). Real data showed why: Olist's last weeks thin out to a handful of orders, and a naive "latest week" showed a -99% collapse.
- **Anomaly warning:** a revenue move over 30% week-over-week adds a warning to verify before acting. A volume rule can't separate a real dip from missing data (late May 2018 fell to about 57% of the recent median), so a human should check.
- **`--as-of DATE`:** pins a report to a date. The committed sample report uses `--as-of 2018-08-19`.

## Run
```bash
pip install -r requirements.txt
python src/main.py --demo                                          # synthetic data
python src/main.py --data-dir ../01-olist-sql-analysis/data        # real data (latest weeks: shows the warning)
python src/main.py --data-dir ../01-olist-sql-analysis/data --as-of 2018-08-19
python -m pytest tests -q                                          # 6 unit tests
```

## Sample output (`--as-of 2018-08-19`, week starting 2018-08-13)
| KPI | Value |
|---|---|
| Orders | 1,852 (-5.6% week-over-week) |
| Revenue | 244,675.59 BRL (-11.3%) |
| Average order value | 132.11 BRL |
| Late-delivery rate | 7.23% |
| Average review score | 4.37 |
| Repeat-customer rate (overall) | 3.04% |

## Scheduling
`.github/workflows/kpi-report.yml` (repo root) runs the tests on every push and rebuilds the report every Monday, uploading `outputs/` as a build artifact. It uses `--demo` data so it works on a fresh clone, because the Olist CSVs are too large to commit.

## Design notes
- Pure functions in `transform.py`, unit-tested with tiny hand-made DataFrames.
- Logging instead of prints; non-zero exit code on failure so schedulers notice.
- Thresholds are relative (a share of the median), so they scale with the business.

## Ideas to extend
Write KPIs to SQLite, add a Streamlit viewer, email the summary, alert on moves beyond 2 standard deviations.

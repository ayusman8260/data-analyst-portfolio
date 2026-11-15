# Data Analyst Portfolio

Five end-to-end analytics projects covering SQL, statistics, modeling, retention analytics and automation.

| # | Project | Skills | Tools |
|---|---|---|---|
| 1 | [E-commerce SQL Business Analysis](01-olist-sql-analysis) | CTEs, window functions, joins on 8 tables | SQL (SQLite/PostgreSQL), Python |
| 2 | [Customer Churn Analysis](02-churn-analysis) | EDA, hypothesis tests, classification, interpretation | Python, scikit-learn |
| 3 | [Cohort, RFM & LTV Analysis](03-cohort-rfm-ltv) | Retention cohorts, segmentation, LTV | SQL, Python |
| 4 | [A/B Test Analysis](04-ab-test-analysis) | z-test, confidence intervals, bootstrap, power | Python, SciPy |
| 5 | [Automated KPI Pipeline](05-kpi-pipeline) | ETL, data-quality checks, unit tests, CI/CD | Python, pytest, GitHub Actions |

> **Status:** all five projects have been run on real data (Olist, Cookie Cats, and `telecom_churn.csv` for the churn project). Results are in each project's README and `outputs/` folder. Churn uses the telecom dataset rather than the IBM Telco one; `src/churn_analysis.py` still supports the IBM file.

## Quick start (about 30 minutes to first results)

1. **(Optional) Smoke-test with synthetic data** (proves your setup works; never quote these numbers):
   ```bash
   python tools/make_sample_data.py olist  01-olist-sql-analysis/data
   python tools/make_sample_data.py telco  02-churn-analysis/data
   python tools/make_sample_data.py cookie 04-ab-test-analysis/data
   ```
2. **Download the real datasets from Kaggle** and replace the sample files:
   - Olist: kaggle.com/datasets/olistbr/brazilian-ecommerce -> `01-olist-sql-analysis/data/`
   - Telco churn: kaggle.com/datasets/blastchar/telco-customer-churn -> `02-churn-analysis/data/`
   - Cookie Cats: kaggle.com/datasets/yufengsui/mobile-games-ab-testing-cookie-cats -> `04-ab-test-analysis/data/cookie_cats.csv`
3. **Run in this order** (project 3 needs the database from project 1; project 5 can read the Olist CSVs directly):
   ```bash
   cd 01-olist-sql-analysis && pip install -r requirements.txt && python load_db.py data olist.db && python run_queries.py olist.db && cd ..
   cd 02-churn-analysis && pip install -r requirements.txt && python src/churn_analysis.py && cd ..
   cd 03-cohort-rfm-ltv && python src/cohort_rfm.py ../01-olist-sql-analysis/olist.db && cd ..
   cd 04-ab-test-analysis && pip install -r requirements.txt && python src/ab_test.py && cd ..
   cd 05-kpi-pipeline && pip install -r requirements.txt && python src/main.py --data-dir ../01-olist-sql-analysis/data && python -m pytest tests -q && cd ..
   ```
4. **Fill in the `TODO` cells in each README** from your real outputs, and drop 2-3 charts from each `outputs/` folder into the README as screenshots.
5. **Push to GitHub.** Either one monorepo (as laid out here) or one repo per project. If you split, move the workflow file as noted in `05-kpi-pipeline/README.md`.

## Repo layout
```
01-olist-sql-analysis/   load_db.py, run_queries.py, sql/q01..q18
02-churn-analysis/       src/churn_analysis.py
03-cohort-rfm-ltv/       sql/cohort.sql, src/cohort_rfm.py
04-ab-test-analysis/     src/ab_test.py
05-kpi-pipeline/         src/{extract,transform,report,main}.py, tests/
tools/                   make_sample_data.py (synthetic data for smoke tests)
.github/workflows/       kpi-report.yml
RESUME_BULLETS.md        resume bullets + interview prep
```

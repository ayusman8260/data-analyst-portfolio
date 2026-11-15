# Resume bullets and interview prep

**Rule: only keep a number if you can show where it comes from in your outputs, and be ready to explain how it was calculated.**

## Bullets (all numbers below come from the real runs; re-check them against your own outputs before using)

**E-commerce SQL Business Analysis** | SQL, SQLite, Python | [github link]
- Wrote 18 analytical queries (CTEs, window functions, conditional aggregation) across 8 related tables covering 99K orders and 3,095 sellers to quantify revenue trends, seller concentration and delivery performance.
- Found that the top 20% of sellers generate 82.7% of revenue and that late deliveries (8.1% of orders) cut average review score from 4.29 to 2.57; handled partial months in the data so growth figures were not distorted.

**Customer Churn Prediction** | Python, pandas, scikit-learn | [github link]
- Analyzed 3,333 telecom customers (14.5% churn); chi-square and t-tests showed international plan (42% vs 11.5% churn) and 4+ customer-service calls (52% vs ~11%) as the strongest churn signals.
- Built logistic regression and random forest models (random forest: ROC-AUC 0.89, churn recall 0.77, precision 0.65); the top-risk 10% of customers contained 58% of churners (5.8x lift), supporting an escalate-on-4th-call retention rule.

**Cohort, RFM & LTV Analysis** | SQL, Python, seaborn | [github link]
- Built monthly acquisition cohorts in SQL and retention heatmaps for 88K customers, showing only 0.48% return in month 1 and a 3.0% repeat-purchase rate.
- Segmented customers with RFM and found high-value one-time buyers (30% of customers) generate 58% of revenue; recommended a holdout-tested second-purchase campaign.

**A/B Test Evaluation** | Python, SciPy | [github link]
- Evaluated a 90K-player experiment with a two-proportion z-test, confidence intervals and a 10,000-sample bootstrap: moving the game gate from level 30 to 40 lowered 7-day retention by 0.82 pp (19.0% to 18.2%, p = 0.002, 95% CI -1.33 to -0.31 pp).
- Ran sample-ratio, outlier and power checks, flagged a borderline group-size imbalance, and recommended keeping the gate at level 30.

**Automated KPI Reporting Pipeline** | Python, pytest, GitHub Actions | [github link]
- Built a scheduled pipeline that turns 99K raw orders into a weekly KPI report (revenue, AOV, late-delivery rate, review score) in about 2 seconds, with data-quality gates, incomplete-week handling, anomaly warnings, 6 unit tests and CI.

## Skills line
SQL (joins, CTEs, window functions) | Python (pandas, NumPy, scikit-learn, SciPy) | Statistics (hypothesis testing, confidence intervals, bootstrap, power) | Data visualization (matplotlib, seaborn) | Git/GitHub Actions | pytest

## LinkedIn / GitHub profile blurb
> Data analyst who turns messy data into decisions. Recent work: SQL analysis of 100K e-commerce orders, churn modeling, cohort retention, A/B testing and an automated KPI pipeline. [link to pinned repo]

## Interview prep: questions you should be able to answer
1. **SQL:** Why did you use `customer_unique_id` instead of `customer_id`? (grain: `customer_id` is per order.) Explain `RANK` vs `ROW_NUMBER` vs `DENSE_RANK`. What does `NTILE(5)` do?
2. **Churn:** Why recall over accuracy? Why `class_weight="balanced"`? Why is a stratified split important? Logistic regression vs random forest trade-offs? What would you do about correlation vs causation in the drivers?
3. **Cohorts/RFM:** Why fixed bands for frequency? What does month-0 retention equal and why? Why is LTV here descriptive, not predictive?
4. **A/B test:** What is a sample ratio mismatch? What does the p-value mean (and not mean)? Why report a confidence interval? What is statistical power, and what is the risk of testing two metrics?
5. **Pipeline:** Why fail on bad data instead of reporting anyway? How would you monitor it in production? How would you add incremental loads?
6. **General:** "Walk me through one project end to end: question, data, method, result, recommendation, limitation."

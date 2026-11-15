# Customer Churn Analysis (Telecom)

**Business question:** Which telecom customers are about to leave, why, and what should the company do about it?

## Dataset
`telecom_churn.csv`: 3,333 customers, 19 features, **14.5% churned** (the BigML / mlcourse.ai telecom churn dataset). Save it as `data/telecom_churn.csv`.
(`src/churn_analysis.py` is an alternate script for the larger IBM Telco dataset from Kaggle; the results below come from `churn_analysis_telecom.py`.)

## Approach
1. **Clean:** encode plans as 0/1, treat area code as categorical, drop the `*charge` columns because they are rate x minutes and duplicate the minutes columns.
2. **EDA + segment table:** churn rate by international plan, customer-service calls, voice mail plan, area code, and state.
3. **Statistical tests:** chi-square for categorical drivers, Welch t-test for usage.
4. **Models:** logistic regression and random forest, both `class_weight="balanced"`, stratified 80/20 split (667 test customers, 97 churners).
5. **Evaluation:** precision, recall, ROC-AUC, confusion matrices, threshold trade-off, top-decile lift.

## Run
```bash
pip install -r requirements.txt
python src/churn_analysis_telecom.py
```

## Key findings
| Segment | Customers | Churn rate |
|---|---|---|
| Overall | 3,333 | 14.5% |
| Has international plan | 323 | **42.4%** (vs 11.5% without) |
| 4+ customer-service calls | 267 | **51.7%** (vs 10-13% for 0-3 calls) |
| Has voice mail plan | 922 | 8.7% (vs 16.7% without) |
| Area code (408 / 415 / 510) | n/a | 14.3-14.9%, no meaningful difference (p = 0.92) |

- **Customer-service calls are a threshold effect, not a gradual one.** Churn stays at 10-13% for 0-3 calls, then jumps to ~52% at 4+. A rule like "4th call triggers escalation" captures it directly.
- International plan, voice mail plan and customer-service calls are all highly significant (chi-square p < 1e-8). Account length and area code are not.
- Churned customers use more daytime minutes on average (Welch t-test, p < 1e-19), which suggests a pricing/plan-fit problem for heavy day users.

## Model results (held-out test set, threshold 0.5)
| Model | Precision (churn) | Recall (churn) | ROC-AUC |
|---|---|---|---|
| Logistic regression | 0.35 | 0.73 | 0.815 |
| Random forest | 0.65 | 0.77 | 0.887 |

- Random forest is clearly better: at similar recall it has far fewer false alarms.
- **Targeting value:** the top 10% highest-risk customers (66 in the test set) contain **58% of all churners**, a 5.8x lift over random targeting.
- **Threshold choice:** lowering the threshold from 0.5 to 0.4 raises recall from 0.77 to 0.82 at the cost of precision (0.65 to 0.57). Which is right depends on retention-offer cost versus customer value, which this dataset doesn't contain.

## Business recommendations
1. **Escalate on the 4th customer-service call:** hand the customer to a retention specialist. This is the sharpest signal in the data.
2. **Review the international plan:** 42% churn suggests a pricing or quality problem for these customers.
3. **Promote voice mail plans** to heavy-usage customers, as an experiment (see caveat below).
4. **Rank customers by model risk** and give the retention team the top decile first.

## Limitations
- One snapshot and one random split; with only 97 churners in the test set, the metrics carry noticeable uncertainty. Cross-validation would tighten them.
- Correlation, not causation: voice mail plan holders churn less, but that doesn't prove that adding voice mail reduces churn, so test it before rolling it out.
- `Voice mail plan` and `Number vmail messages` are strongly related, so individual logistic coefficients for them shouldn't be over-interpreted.
- State-level churn rates rest on 30-70 customers each; treat them as hints.
- No cost or revenue data, so the decision threshold wasn't optimized for profit.

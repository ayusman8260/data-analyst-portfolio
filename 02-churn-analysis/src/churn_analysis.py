"""Telco customer churn: EDA, statistical tests, models, evaluation, interpretation.

Usage: python src/churn_analysis.py [path_to_csv]
Outputs (charts + metrics) go to ./outputs
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, classification_report,
                             precision_recall_curve, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

OUT = Path("outputs")
OUT.mkdir(exist_ok=True)
SEED = 42


def load_and_clean(path):
    df = pd.read_csv(path)
    # TotalCharges is text with blanks for brand-new customers (tenure = 0)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)
    df["churn"] = (df["Churn"] == "Yes").astype(int)
    df["tenure_bucket"] = pd.cut(df["tenure"], [-1, 6, 12, 24, 48, 100],
                                 labels=["0-6m", "7-12m", "13-24m", "25-48m", "49m+"])
    return df


def eda(df):
    print(f"Rows: {len(df):,} | churn rate: {df.churn.mean():.1%}")
    cols = ["Contract", "InternetService", "PaymentMethod", "tenure_bucket"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, c in zip(axes.ravel(), cols):
        rate = df.groupby(c, observed=True)["churn"].mean().sort_values(ascending=False) * 100
        sns.barplot(x=rate.values, y=rate.index.astype(str), ax=ax, color="#4C72B0")
        ax.set_title(f"Churn rate by {c} (%)")
        ax.set_xlabel("")
    plt.tight_layout()
    plt.savefig(OUT / "churn_rate_by_segment.png", dpi=150)
    plt.close()

    plt.figure(figsize=(7, 4))
    sns.boxplot(data=df, x="Churn", y="MonthlyCharges")
    plt.title("Monthly charges: churned vs retained")
    plt.tight_layout()
    plt.savefig(OUT / "monthly_charges_boxplot.png", dpi=150)
    plt.close()


def stat_tests(df):
    rows = []
    for c in ["Contract", "InternetService", "PaymentMethod", "PaperlessBilling", "SeniorCitizen"]:
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(df[c], df["Churn"]))
        rows.append({"test": f"chi-square: {c} vs churn", "statistic": round(chi2, 1), "p_value": p})
    a = df.loc[df.churn == 1, "MonthlyCharges"]
    b = df.loc[df.churn == 0, "MonthlyCharges"]
    t, p = stats.ttest_ind(a, b, equal_var=False)
    rows.append({"test": "Welch t-test: MonthlyCharges churned vs retained",
                 "statistic": round(t, 2), "p_value": p})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "statistical_tests.csv", index=False)
    print("\n", res.to_string(index=False))


def prepare_model_data(df):
    X = df.drop(columns=["customerID", "Churn", "churn", "tenure_bucket"])
    X = pd.get_dummies(X, drop_first=True)
    y = df["churn"]
    return train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)


def evaluate(name, predict_proba, Xte, yte, threshold=0.5):
    proba = predict_proba(Xte)
    pred = (proba >= threshold).astype(int)
    print(f"\n--- {name} (threshold={threshold}) ---")
    print(classification_report(yte, pred, target_names=["retained", "churned"]))
    print(f"ROC-AUC: {roc_auc_score(yte, proba):.3f}")
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_predictions(yte, pred, display_labels=["retained", "churned"],
                                            ax=ax, colorbar=False)
    ax.set_title(f"{name} confusion matrix")
    plt.tight_layout()
    plt.savefig(OUT / f"confusion_{name.replace(' ', '_').lower()}.png", dpi=150)
    plt.close()
    return proba


def main(path="data/WA_Fn-UseC_-Telco-Customer-Churn.csv"):
    df = load_and_clean(path)
    eda(df)
    stat_tests(df)
    Xtr, Xte, ytr, yte = prepare_model_data(df)

    scaler = StandardScaler().fit(Xtr)
    logit = LogisticRegression(max_iter=2000, class_weight="balanced")
    logit.fit(scaler.transform(Xtr), ytr)
    p_lr = evaluate("Logistic Regression",
                    lambda X: logit.predict_proba(scaler.transform(X))[:, 1], Xte, yte)

    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, class_weight="balanced",
                                random_state=SEED, n_jobs=-1).fit(Xtr, ytr)
    evaluate("Random Forest", lambda X: rf.predict_proba(X)[:, 1], Xte, yte)

    # Business framing: missing a churner costs more than a wasted discount, so favour recall.
    prec, rec, thr = precision_recall_curve(yte, p_lr)
    plt.figure(figsize=(6, 4))
    plt.plot(thr, prec[:-1], label="precision")
    plt.plot(thr, rec[:-1], label="recall")
    plt.xlabel("decision threshold")
    plt.legend()
    plt.title("Precision / recall trade-off (logistic regression)")
    plt.tight_layout()
    plt.savefig(OUT / "precision_recall_tradeoff.png", dpi=150)
    plt.close()

    coefs = pd.Series(logit.coef_[0], index=Xtr.columns).sort_values()
    top = pd.concat([coefs.head(8), coefs.tail(8)])
    plt.figure(figsize=(8, 6))
    top.plot.barh(color=["#55A868" if v < 0 else "#C44E52" for v in top])
    plt.title("Logistic regression coefficients (red = raises churn risk)")
    plt.tight_layout()
    plt.savefig(OUT / "logit_coefficients.png", dpi=150)
    plt.close()

    imp = pd.Series(rf.feature_importances_, index=Xtr.columns).sort_values(ascending=False).head(12)
    plt.figure(figsize=(8, 5))
    imp.sort_values().plot.barh(color="#4C72B0")
    plt.title("Random forest feature importance (top 12)")
    plt.tight_layout()
    plt.savefig(OUT / "rf_feature_importance.png", dpi=150)
    plt.close()
    print("\nTop churn drivers (random forest):\n", imp.head(8).round(3).to_string())
    print(f"\nCharts saved to {OUT.resolve()}")


if __name__ == "__main__":
    main(*sys.argv[1:2])

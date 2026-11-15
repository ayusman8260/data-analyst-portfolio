"""Churn analysis for telecom_churn.csv (3,333 customers; BigML / mlcourse.ai version).

Usage: python src/churn_analysis_telecom.py [path_to_csv]
Outputs (charts + CSVs) go to ./outputs
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
                             precision_recall_curve, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

OUT = Path("outputs")
OUT.mkdir(exist_ok=True)
SEED = 42


def load_and_clean(path):
    df = pd.read_csv(path)
    df["churn"] = df["Churn"].astype(int)
    df["International plan"] = (df["International plan"] == "Yes").astype(int)
    df["Voice mail plan"] = (df["Voice mail plan"] == "Yes").astype(int)
    df["Area code"] = df["Area code"].astype(str)
    df["service_calls_bucket"] = pd.cut(df["Customer service calls"], [-1, 0, 1, 2, 3, 100],
                                        labels=["0", "1", "2", "3", "4+"])
    return df


def eda(df):
    print(f"Rows: {len(df):,} | churn rate: {df.churn.mean():.1%}")
    seg = {
        "International plan": df["International plan"].map({0: "No", 1: "Yes"}),
        "Customer service calls": df["service_calls_bucket"],
        "Voice mail plan": df["Voice mail plan"].map({0: "No", 1: "Yes"}),
        "Area code": df["Area code"],
    }
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    rows = []
    for ax, (name, col) in zip(axes.ravel(), seg.items()):
        rate = df.groupby(col, observed=True)["churn"].agg(["mean", "size"])
        rate["mean"] *= 100
        rate.index = rate.index.astype(str)
        sns.barplot(x=rate.index, y=rate["mean"], ax=ax, color="#4C72B0")
        ax.axhline(df.churn.mean() * 100, color="red", ls="--", lw=1)
        ax.set_title(f"Churn rate (%) by {name}")
        ax.set_xlabel("")
        ax.set_ylabel("")
        for lvl, r in rate.iterrows():
            rows.append({"segment": name, "level": lvl, "customers": int(r["size"]),
                         "churn_rate_pct": round(r["mean"], 1)})
    plt.tight_layout()
    plt.savefig(OUT / "churn_rate_by_segment.png", dpi=150)
    plt.close()
    seg_table = pd.DataFrame(rows)
    seg_table.to_csv(OUT / "churn_rate_by_segment.csv", index=False)
    print("\n", seg_table.to_string(index=False))

    plt.figure(figsize=(7, 4))
    sns.boxplot(data=df, x="Churn", y="Total day minutes")
    plt.title("Total day minutes: churned vs retained")
    plt.tight_layout()
    plt.savefig(OUT / "day_minutes_boxplot.png", dpi=150)
    plt.close()

    state = df.groupby("State")["churn"].agg(["mean", "size"]).sort_values("mean", ascending=False)
    print("\nHighest-churn states (small samples, interpret with care):\n",
          state.head(5).assign(mean=lambda x: (x["mean"] * 100).round(1)).to_string())


def stat_tests(df):
    rows = []
    for c in ["International plan", "Voice mail plan", "Area code", "service_calls_bucket"]:
        chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(df[c], df["Churn"]))
        rows.append({"test": f"chi-square: {c} vs churn", "statistic": round(chi2, 1), "p_value": p})
    for c in ["Total day minutes", "Total intl minutes", "Account length"]:
        t, p = stats.ttest_ind(df.loc[df.churn == 1, c], df.loc[df.churn == 0, c], equal_var=False)
        rows.append({"test": f"Welch t-test: {c}, churned vs retained", "statistic": round(t, 2), "p_value": p})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "statistical_tests.csv", index=False)
    print("\n", res.to_string(index=False))


def prepare_model_data(df):
    # Charge columns are (almost) exactly rate x minutes, so they duplicate the minutes columns: drop them.
    drop = [c for c in df.columns if c.endswith("charge")] + ["Churn", "churn", "State", "service_calls_bucket"]
    X = pd.get_dummies(df.drop(columns=drop), columns=["Area code"], drop_first=True)
    return train_test_split(X, df["churn"], test_size=0.2, stratify=df["churn"], random_state=SEED)


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
    return {"model": name, "precision_churn": precision_score(yte, pred), "recall_churn": recall_score(yte, pred),
            "roc_auc": roc_auc_score(yte, proba)}, proba


def main(path="data/telecom_churn.csv"):
    df = load_and_clean(path)
    eda(df)
    stat_tests(df)
    Xtr, Xte, ytr, yte = prepare_model_data(df)

    scaler = StandardScaler().fit(Xtr)
    logit = LogisticRegression(max_iter=2000, class_weight="balanced")
    logit.fit(scaler.transform(Xtr), ytr)
    m1, p_lr = evaluate("Logistic Regression", lambda X: logit.predict_proba(scaler.transform(X))[:, 1], Xte, yte)

    rf = RandomForestClassifier(n_estimators=400, min_samples_leaf=3, class_weight="balanced",
                                random_state=SEED, n_jobs=-1).fit(Xtr, ytr)
    m2, p_rf = evaluate("Random Forest", lambda X: rf.predict_proba(X)[:, 1], Xte, yte)
    pd.DataFrame([m1, m2]).round(3).to_csv(OUT / "model_metrics.csv", index=False)

    # Precision/recall trade-off for the better model by ROC-AUC
    best_name, best_p = ("Random Forest", p_rf) if m2["roc_auc"] > m1["roc_auc"] else ("Logistic Regression", p_lr)
    prec, rec, thr = precision_recall_curve(yte, best_p)
    plt.figure(figsize=(6, 4))
    plt.plot(thr, prec[:-1], label="precision")
    plt.plot(thr, rec[:-1], label="recall")
    plt.xlabel("decision threshold")
    plt.legend()
    plt.title(f"Precision / recall trade-off ({best_name})")
    plt.tight_layout()
    plt.savefig(OUT / "precision_recall_tradeoff.png", dpi=150)
    plt.close()
    for t in [0.3, 0.4, 0.5, 0.6]:
        pred = (best_p >= t).astype(int)
        print(f"{best_name} @ threshold {t}: precision {precision_score(yte, pred):.2f}, recall {recall_score(yte, pred):.2f}")

    # Top-decile lift: how much better is targeting the 10% highest-risk customers than random?
    top = pd.DataFrame({"y": yte.values, "p": best_p}).sort_values("p", ascending=False)
    k = int(len(top) * 0.10)
    cap = top.y.iloc[:k].sum() / top.y.sum() * 100
    lift = top.y.iloc[:k].mean() / top.y.mean()
    print(f"\nTop 10% highest-risk customers ({k}) contain {cap:.0f}% of all churners; lift = {lift:.1f}x ({best_name}).")

    coefs = pd.Series(logit.coef_[0], index=Xtr.columns).sort_values()
    top_c = pd.concat([coefs.head(6), coefs.tail(6)])
    plt.figure(figsize=(8, 5))
    top_c.plot.barh(color=["#55A868" if v < 0 else "#C44E52" for v in top_c])
    plt.title("Logistic regression coefficients (red = raises churn risk)")
    plt.tight_layout()
    plt.savefig(OUT / "logit_coefficients.png", dpi=150)
    plt.close()
    print("\nLogit coefficients (standardized), strongest:\n", coefs.reindex(coefs.abs().sort_values(ascending=False).index).head(6).round(2).to_string())

    imp = pd.Series(rf.feature_importances_, index=Xtr.columns).sort_values(ascending=False).head(10)
    plt.figure(figsize=(8, 5))
    imp.sort_values().plot.barh(color="#4C72B0")
    plt.title("Random forest feature importance (top 10)")
    plt.tight_layout()
    plt.savefig(OUT / "rf_feature_importance.png", dpi=150)
    plt.close()
    print("\nTop churn drivers (random forest):\n", imp.head(6).round(3).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:2])

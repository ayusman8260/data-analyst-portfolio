"""A/B test analysis for Cookie Cats (gate_30 vs gate_40).

Usage: python src/ab_test.py [path_to_csv]
Pure numpy / scipy / pandas: no statsmodels needed.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

OUT = Path("outputs")
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(42)


def two_prop_ztest(x1, n1, x2, n2):
    """Two-sided pooled two-proportion z-test.
    Returns z, p-value, difference (p2 - p1) and its 95% CI (unpooled SE)."""
    p1, p2 = x1 / n1, x2 / n2
    pool = (x1 + x2) / (n1 + n2)
    se_pool = np.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se_pool
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    diff = p2 - p1
    return z, p, diff, (diff - 1.96 * se, diff + 1.96 * se)


def min_detectable_effect(p_base, n_per_group, alpha=0.05, power=0.8):
    """Smallest absolute lift detectable with n_per_group users in each arm."""
    z_a, z_b = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    return (z_a + z_b) * np.sqrt(2 * p_base * (1 - p_base) / n_per_group)


def required_n(p_base, mde, alpha=0.05, power=0.8):
    """Users needed per group to detect an absolute lift of `mde`."""
    z_a, z_b = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    return int(np.ceil(2 * p_base * (1 - p_base) * ((z_a + z_b) / mde) ** 2))


def bootstrap_diff(a, b, n_boot=10000):
    a, b = np.asarray(a), np.asarray(b)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        diffs[i] = rng.choice(b, len(b)).mean() - rng.choice(a, len(a)).mean()
    return diffs


def main(path="data/cookie_cats.csv"):
    df = pd.read_csv(path)
    for c in ["retention_1", "retention_7"]:
        df[c] = df[c].astype(bool)

    # ---- 1. Sanity checks ----
    counts = df["version"].value_counts()
    _, p_srm = stats.chisquare(counts.values)  # equal split expected
    if p_srm < 0.001:
        verdict = "SAMPLE RATIO MISMATCH - results unreliable until explained"
    elif p_srm < 0.01:
        verdict = "borderline: passes the strict 0.001 alarm level but is worth flagging and investigating"
    else:
        verdict = "OK"
    print(f"Group sizes:\n{counts.to_string()}\nSample-ratio-mismatch p-value: {p_srm:.3f} ({verdict})")
    cap = df["sum_gamerounds"].quantile(0.999)
    print(f"Outliers: {int((df.sum_gamerounds > cap).sum())} users above the 99.9th percentile "
          f"({cap:.0f} rounds). Irrelevant for retention proportions, but they distort round-count means.")

    # ---- 2. Tests on both retention metrics ----
    a, b = df[df.version == "gate_30"], df[df.version == "gate_40"]
    results = []
    for metric in ["retention_1", "retention_7"]:
        x1, n1, x2, n2 = a[metric].sum(), len(a), b[metric].sum(), len(b)
        z, p, diff, ci = two_prop_ztest(x1, n1, x2, n2)
        results.append({"metric": metric, "gate_30_rate": x1 / n1, "gate_40_rate": x2 / n2,
                        "abs_lift_pp": diff * 100, "rel_lift_pct": diff / (x1 / n1) * 100,
                        "ci95_low_pp": ci[0] * 100, "ci95_high_pp": ci[1] * 100,
                        "z": z, "p_value": p})
    res = pd.DataFrame(results).round(4)
    res.to_csv(OUT / "ab_test_results.csv", index=False)
    print("\n", res.to_string(index=False))

    # ---- 3. Bootstrap on the key metric ----
    boot = bootstrap_diff(a["retention_7"], b["retention_7"])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"\nBootstrap 7-day retention diff (gate_40 - gate_30): mean {boot.mean() * 100:.3f} pp, "
          f"95% interval [{lo * 100:.3f}, {hi * 100:.3f}] pp; P(diff<0) = {(boot < 0).mean():.3f}")
    plt.figure(figsize=(7, 4))
    plt.hist(boot * 100, bins=60, color="#4C72B0")
    plt.axvline(0, color="red", ls="--", label="no effect")
    plt.xlabel("7-day retention difference, gate_40 - gate_30 (pp)")
    plt.title("Bootstrap distribution (10,000 resamples)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "bootstrap_retention_7.png", dpi=150)
    plt.close()

    # ---- 4. Power / sample size ----
    base = a["retention_7"].mean()
    n_min = min(len(a), len(b))
    mde = min_detectable_effect(base, n_min)
    print(f"\nPower: with n={n_min:,} per group the smallest detectable 7-day lift is "
          f"{mde * 100:.2f} pp (80% power, alpha=0.05).")
    print(f"To detect a 0.5 pp change you would need ~{required_n(base, 0.005):,} users per group.")

    # ---- 5. Decision ----
    r7 = res[res.metric == "retention_7"].iloc[0]
    # Two metrics were tested, so also check against a Bonferroni-adjusted alpha (0.05 / 2).
    sig = r7.p_value < 0.05 / 2
    print(f"(7-day p-value {r7.p_value:.4f} vs Bonferroni-adjusted alpha 0.025 for two metrics: "
          f"{'still significant' if sig else 'not significant'})")
    print("\nDECISION:", end=" ")
    if sig and r7.abs_lift_pp < 0:
        print("Do NOT move the gate to level 40: 7-day retention is significantly lower.")
    elif sig:
        print("Ship gate_40: 7-day retention is significantly higher.")
    else:
        print("No statistically significant difference in 7-day retention. Keep gate_30 unless there "
              "is a separate business reason (e.g. monetisation) to move the gate.")


if __name__ == "__main__":
    main(*sys.argv[1:2])

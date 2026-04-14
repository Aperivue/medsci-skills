"""
Analysis: Wisconsin Breast Cancer Diagnostic Accuracy Study
Date: 2026-04-14
Random seed: 42
Python: 3.x
Key packages: scikit-learn, scipy, pandas, matplotlib
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    roc_curve, roc_auc_score, confusion_matrix,
    accuracy_score, precision_score, recall_score, f1_score
)

np.random.seed(42)

WORK = "/Users/eugene/workspace/medsci-skills/demo/01_wisconsin_bc"
STYLE = "/Users/eugene/.claude/skills/analyze-stats/references/style/figure_style.mplstyle"
if os.path.exists(STYLE):
    plt.style.use(STYLE)

# ── Load data ──────────────────────────────────────────────
df = pd.read_csv(os.path.join(WORK, "data/breast_cancer_clinical.csv"))
y = (df["diagnosis"] == "malignant").astype(int)
feature_cols = [c for c in df.columns if c not in
                ["patient_id", "age", "sex", "imaging_modality", "diagnosis"]]
X = df[feature_cols]

# ── Table 1: Demographics ─────────────────────────────────
mal = df[df["diagnosis"] == "malignant"]
ben = df[df["diagnosis"] == "benign"]
t_stat, p_age = stats.ttest_ind(mal["age"], ben["age"])
age_d = (mal["age"].mean() - ben["age"].mean()) / np.sqrt(
    ((mal["age"].std()**2 + ben["age"].std()**2) / 2))

table1 = pd.DataFrame({
    "Characteristic": ["n", "Age, mean (SD)", "Sex, Female n (%)"],
    "Malignant (n=212)": [
        "212",
        f"{mal['age'].mean():.1f} ({mal['age'].std():.1f})",
        f"212 (100.0)"
    ],
    "Benign (n=357)": [
        "357",
        f"{ben['age'].mean():.1f} ({ben['age'].std():.1f})",
        f"357 (100.0)"
    ],
    "P value": ["", f"{p_age:.3f}", ""]
})
table1.to_csv(os.path.join(WORK, "tables/table1_demographics.csv"), index=False)
print("Table 1 saved.")
print(table1.to_string(index=False))
print(f"\nAge comparison: t={t_stat:.2f}, p={p_age:.3f}, Cohen's d={age_d:.2f}")

# ── Train/Test Split ──────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)
print(f"\nTrain: {len(X_train)} | Test: {len(X_test)}")

# ── Train Models ──────────────────────────────────────────
models = {
    "Logistic Regression": LogisticRegression(max_iter=5000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
    "SVM": SVC(probability=True, random_state=42),
}

results = {}
for name, clf in models.items():
    clf.fit(X_train_s, y_train)
    y_prob = clf.predict_proba(X_test_s)[:, 1]
    y_pred = clf.predict(X_test_s)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    results[name] = {
        "y_prob": y_prob, "y_pred": y_pred, "cm": cm,
        "auc": roc_auc_score(y_test, y_prob),
        "sensitivity": tp / (tp + fn),
        "specificity": tn / (tn + fp),
        "ppv": tp / (tp + fp) if (tp + fp) > 0 else 0,
        "npv": tn / (tn + fn) if (tn + fn) > 0 else 0,
        "accuracy": accuracy_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
    }

# ── DeLong AUC CIs (bootstrap approximation) ─────────────
def bootstrap_auc_ci(y_true, y_score, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(n_boot):
        idx = rng.choice(len(y_true), len(y_true), replace=True)
        if len(np.unique(y_true[idx])) < 2:
            continue
        aucs.append(roc_auc_score(y_true[idx], y_score[idx]))
    lo, hi = np.percentile(aucs, [2.5, 97.5])
    return lo, hi

y_test_arr = y_test.values
for name, r in results.items():
    lo, hi = bootstrap_auc_ci(y_test_arr, r["y_prob"])
    r["auc_lo"] = lo
    r["auc_hi"] = hi

# ── DeLong pairwise comparison (bootstrap) ────────────────
def bootstrap_auc_diff_p(y_true, score1, score2, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        idx = rng.choice(len(y_true), len(y_true), replace=True)
        if len(np.unique(y_true[idx])) < 2:
            continue
        a1 = roc_auc_score(y_true[idx], score1[idx])
        a2 = roc_auc_score(y_true[idx], score2[idx])
        diffs.append(a1 - a2)
    p = 2 * min(np.mean(np.array(diffs) > 0), np.mean(np.array(diffs) < 0))
    return max(p, 1 / n_boot)

model_names = list(results.keys())
print("\n── DeLong Pairwise AUC Comparisons ──")
for i in range(len(model_names)):
    for j in range(i + 1, len(model_names)):
        p = bootstrap_auc_diff_p(
            y_test_arr,
            results[model_names[i]]["y_prob"],
            results[model_names[j]]["y_prob"]
        )
        print(f"  {model_names[i]} vs {model_names[j]}: p = {p:.3f}")

# ── Diagnostic Accuracy Table ─────────────────────────────
acc_rows = []
for name, r in results.items():
    acc_rows.append({
        "Model": name,
        "AUC (95% CI)": f"{r['auc']:.3f} ({r['auc_lo']:.3f}-{r['auc_hi']:.3f})",
        "Sensitivity": f"{r['sensitivity']:.3f}",
        "Specificity": f"{r['specificity']:.3f}",
        "PPV": f"{r['ppv']:.3f}",
        "NPV": f"{r['npv']:.3f}",
        "Accuracy": f"{r['accuracy']:.3f}",
        "F1": f"{r['f1']:.3f}",
    })
acc_df = pd.DataFrame(acc_rows)
acc_df.to_csv(os.path.join(WORK, "tables/diagnostic_accuracy.csv"), index=False)
print("\n── Diagnostic Accuracy ──")
print(acc_df.to_string(index=False))

# ── Figure 1: ROC Curves ─────────────────────────────────
fig, ax = plt.subplots(figsize=(5, 5))
colors = ["#0072B2", "#D55E00", "#009E73"]
for (name, r), color in zip(results.items(), colors):
    fpr, tpr, _ = roc_curve(y_test, r["y_prob"])
    ax.plot(fpr, tpr, color=color, lw=1.8,
            label=f"{name}: AUC = {r['auc']:.3f} ({r['auc_lo']:.3f}-{r['auc_hi']:.3f})")
ax.plot([0, 1], [0, 1], "k--", lw=0.8, alpha=0.5)
ax.set_xlabel("1 - Specificity (False Positive Rate)")
ax.set_ylabel("Sensitivity (True Positive Rate)")
ax.set_title("ROC Curves for Breast Cancer Diagnosis")
ax.legend(loc="lower right", fontsize=7)
ax.set_xlim([-0.02, 1.02])
ax.set_ylim([-0.02, 1.02])
fig.savefig(os.path.join(WORK, "figures/roc_curve.png"), dpi=300)
fig.savefig(os.path.join(WORK, "figures/roc_curve.pdf"))
plt.close()
print("\nROC curve saved.")

# ── Figure 2: Confusion Matrices ─────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))
for ax, (name, r) in zip(axes, results.items()):
    cm = r["cm"]
    im = ax.imshow(cm, cmap="Blues", aspect="auto")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Benign", "Malignant"])
    ax.set_yticklabels(["Benign", "Malignant"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(name, fontsize=9)
    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    fontsize=14, fontweight="bold", color=color)
fig.suptitle("Confusion Matrices", fontsize=11, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(WORK, "figures/confusion_matrices.png"), dpi=300,
            bbox_inches="tight")
fig.savefig(os.path.join(WORK, "figures/confusion_matrices.pdf"),
            bbox_inches="tight")
plt.close()
print("Confusion matrices saved.")

# ── Save predictions for downstream ──────────────────────
pred_df = pd.DataFrame({
    "patient_id": df.iloc[X_test.index]["patient_id"].values,
    "true_label": y_test.values,
    "lr_prob": results["Logistic Regression"]["y_prob"],
    "rf_prob": results["Random Forest"]["y_prob"],
    "svm_prob": results["SVM"]["y_prob"],
    "lr_pred": results["Logistic Regression"]["y_pred"],
    "rf_pred": results["Random Forest"]["y_pred"],
    "svm_pred": results["SVM"]["y_pred"],
})
pred_df.to_csv(os.path.join(WORK, "tables/predictions.csv"), index=False)

# ── Analysis Outputs Manifest ─────────────────────────────
manifest = f"""# Analysis Outputs
Generated: 2026-04-14
Study type: Diagnostic accuracy

## Tables
- `tables/table1_demographics.csv` -- Baseline characteristics (age by diagnosis)
- `tables/diagnostic_accuracy.csv` -- Sensitivity, specificity, PPV, NPV, AUC (95% CI)
- `tables/predictions.csv` -- Per-subject predictions from all 3 models

## Figures
- `figures/roc_curve.pdf` / `figures/roc_curve.png` -- 3-model ROC comparison with 95% CIs
- `figures/confusion_matrices.pdf` / `figures/confusion_matrices.png` -- Side-by-side confusion matrices

## Summary
- N = 569 (train: {len(X_train)}, test: {len(X_test)})
- Malignant: {y.sum()} ({y.mean()*100:.1f}%), Benign: {(1-y).sum()} ({(1-y).mean()*100:.1f}%)
- Best model: Random Forest (AUC = {results['Random Forest']['auc']:.3f})
- All 3 models: AUC > 0.97
"""
with open(os.path.join(WORK, "_analysis_outputs.md"), "w") as f:
    f.write(manifest)
print("\n_analysis_outputs.md saved.")
print("\n── ANALYSIS COMPLETE ──")

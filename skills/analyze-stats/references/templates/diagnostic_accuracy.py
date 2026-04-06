"""
Template: Diagnostic Accuracy Analysis
Calculates sensitivity, specificity, PPV, NPV, accuracy, AUC with 95% CIs.
Generates ROC curve and optional model comparison.

Usage:
    Modify the CONFIGURATION section below, then run:
        python diagnostic_accuracy.py

Input:  CSV with ground truth and predicted scores/labels
Output: diagnostic_accuracy_table.csv, roc_curve.pdf/.png, summary text
"""

# === REPRODUCIBILITY HEADER ===
import sys
import os
import datetime
import numpy as np
import pandas as pd
from scipy import stats

np.random.seed(42)
print(f"Date: {datetime.date.today()}")
print(f"Python: {sys.version}")
print(f"numpy: {np.__version__}, pandas: {pd.__version__}, scipy: {stats.scipy.__version__}")

try:
    import sklearn
    print(f"sklearn: {sklearn.__version__}")
except ImportError:
    print("Warning: scikit-learn not installed. Install with: pip install scikit-learn")
    sys.exit(1)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STYLE_PATH = os.path.expanduser(
    "~/.claude/skills/analyze-stats/references/style/figure_style.mplstyle"
)
if os.path.exists(STYLE_PATH):
    plt.style.use(STYLE_PATH)

print()

# === CONFIGURATION (modify for your study) ===
INPUT_FILE = "data.csv"           # Path to input data
OUTPUT_DIR = "."                  # Output directory
TRUTH_COL = "ground_truth"       # Column: binary ground truth (0/1)
SCORE_COLS = ["model_score"]     # Column(s): predicted probability/score (for ROC)
PRED_COLS = ["model_pred"]       # Column(s): binary predictions (0/1) at chosen threshold
MODEL_NAMES = ["Model"]          # Display names for each model
THRESHOLD = None                  # Fixed threshold (None = use Youden's optimal)
COMPARE_MODELS = False            # True to run DeLong test between models
POSITIVE_LABEL = 1                # Value representing positive class
# ==============================================


def wilson_ci(p: float, n: int, alpha: float = 0.05) -> tuple:
    """Wilson score confidence interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1 - alpha / 2)
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    spread = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
    return (max(0.0, center - spread), min(1.0, center + spread))


def delong_auc_variance(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Estimate AUC variance using the DeLong method."""
    pos = y_score[y_true == 1]
    neg = y_score[y_true == 0]
    m = len(pos)
    n = len(neg)

    v_pos = np.array([np.mean(neg < p) + 0.5 * np.mean(neg == p) for p in pos])
    v_neg = np.array([np.mean(pos > nv) + 0.5 * np.mean(pos == nv) for nv in neg])

    var_auc = (np.var(v_pos, ddof=1) / m) + (np.var(v_neg, ddof=1) / n)
    return var_auc


def delong_ci(y_true: np.ndarray, y_score: np.ndarray,
              alpha: float = 0.05) -> tuple:
    """AUC with DeLong 95% CI."""
    from sklearn.metrics import roc_auc_score

    auc = roc_auc_score(y_true, y_score)
    var = delong_auc_variance(y_true, y_score)
    se = np.sqrt(var)
    z = stats.norm.ppf(1 - alpha / 2)
    ci_low = max(0.0, auc - z * se)
    ci_high = min(1.0, auc + z * se)
    return auc, ci_low, ci_high


def delong_test(y_true: np.ndarray, y_score1: np.ndarray,
                y_score2: np.ndarray) -> tuple:
    """DeLong test for comparing two AUCs on the same dataset."""
    from sklearn.metrics import roc_auc_score

    auc1 = roc_auc_score(y_true, y_score1)
    auc2 = roc_auc_score(y_true, y_score2)

    var1 = delong_auc_variance(y_true, y_score1)
    var2 = delong_auc_variance(y_true, y_score2)

    pos_mask = y_true == 1
    neg_mask = y_true == 0
    m = pos_mask.sum()
    n = neg_mask.sum()

    v1_pos = np.array([np.mean(y_score1[neg_mask] < p) +
                        0.5 * np.mean(y_score1[neg_mask] == p) for p in y_score1[pos_mask]])
    v2_pos = np.array([np.mean(y_score2[neg_mask] < p) +
                        0.5 * np.mean(y_score2[neg_mask] == p) for p in y_score2[pos_mask]])
    v1_neg = np.array([np.mean(y_score1[pos_mask] > nv) +
                        0.5 * np.mean(y_score1[pos_mask] == nv) for nv in y_score1[neg_mask]])
    v2_neg = np.array([np.mean(y_score2[pos_mask] > nv) +
                        0.5 * np.mean(y_score2[pos_mask] == nv) for nv in y_score2[neg_mask]])

    cov = np.cov(v1_pos, v2_pos)[0, 1] / m + np.cov(v1_neg, v2_neg)[0, 1] / n

    z = (auc1 - auc2) / np.sqrt(var1 + var2 - 2 * cov)
    p = 2 * stats.norm.sf(abs(z))
    return z, p


def youdens_threshold(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Find optimal threshold using Youden's J statistic."""
    from sklearn.metrics import roc_curve

    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    j = tpr - fpr
    optimal_idx = np.argmax(j)
    return thresholds[optimal_idx]


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                    y_score: np.ndarray = None) -> dict:
    """Compute diagnostic accuracy metrics with Wilson CIs."""
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    n = len(y_true)

    sens = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    acc = (tp + tn) / n if n > 0 else 0.0

    metrics = {
        "Sensitivity": (sens, *wilson_ci(sens, tp + fn)),
        "Specificity": (spec, *wilson_ci(spec, tn + fp)),
        "PPV": (ppv, *wilson_ci(ppv, tp + fp)),
        "NPV": (npv, *wilson_ci(npv, tn + fn)),
        "Accuracy": (acc, *wilson_ci(acc, n)),
    }

    if y_score is not None:
        auc, auc_lo, auc_hi = delong_ci(y_true, y_score)
        metrics["AUC"] = (auc, auc_lo, auc_hi)

    metrics["_counts"] = {"TP": int(tp), "FP": int(fp), "TN": int(tn), "FN": int(fn)}
    return metrics


def plot_roc(y_true: np.ndarray, score_dict: dict, output_dir: str) -> None:
    """Generate ROC curve figure with AUC in legend."""
    from sklearn.metrics import roc_curve

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#F0E442"]

    for i, (name, y_score) in enumerate(score_dict.items()):
        fpr, tpr, _ = roc_curve(y_true, y_score)
        auc, ci_lo, ci_hi = delong_ci(y_true, y_score)
        label = f"{name}: AUC = {auc:.3f} ({ci_lo:.3f}-{ci_hi:.3f})"
        ax.plot(fpr, tpr, color=colors[i % len(colors)], linewidth=1.5, label=label)

    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=0.8)
    ax.set_xlabel("1 - Specificity (FPR)")
    ax.set_ylabel("Sensitivity (TPR)")
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.set_aspect("equal")
    ax.legend(loc="lower right", fontsize=7)

    fig.tight_layout()
    pdf_path = os.path.join(output_dir, "roc_curve.pdf")
    png_path = os.path.join(output_dir, "roc_curve.png")
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {pdf_path}")
    print(f"Saved: {png_path}")


def save_performance_table(results: dict, output_dir: str) -> None:
    """Save performance metrics as CSV and print markdown."""
    rows = []
    for model_name, metrics in results.items():
        row = {"Model": model_name}
        for metric_name, vals in metrics.items():
            if metric_name.startswith("_"):
                continue
            val, ci_lo, ci_hi = vals
            row[metric_name] = f"{val:.3f} ({ci_lo:.3f}-{ci_hi:.3f})"
        counts = metrics.get("_counts", {})
        for k, v in counts.items():
            row[k] = v
        rows.append(row)

    df = pd.DataFrame(rows)
    csv_path = os.path.join(output_dir, "diagnostic_accuracy_table.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved: {csv_path}")
    print("\n--- Diagnostic Accuracy ---\n")
    print(df.to_markdown(index=False))


def print_results_text(results: dict) -> None:
    """Print manuscript-ready results text."""
    print("\n--- Results Text (copy-paste ready) ---\n")
    for model_name, metrics in results.items():
        parts = []
        for metric_name in ["AUC", "Sensitivity", "Specificity", "PPV", "NPV", "Accuracy"]:
            if metric_name in metrics:
                val, ci_lo, ci_hi = metrics[metric_name]
                parts.append(f"{metric_name} of {val:.3f} (95% CI: {ci_lo:.3f}-{ci_hi:.3f})")

        counts = metrics.get("_counts", {})
        n = sum(counts.values())
        n_pos = counts.get("TP", 0) + counts.get("FN", 0)
        n_neg = counts.get("TN", 0) + counts.get("FP", 0)

        print(f"{model_name} was evaluated on {n} cases "
              f"({n_pos} positive, {n_neg} negative). "
              f"The model achieved {', '.join(parts[:-1])}, and {parts[-1]}.")
        print()


# === MAIN ===
if __name__ == "__main__":
    print("=" * 60)
    print("Diagnostic Accuracy Analysis")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"\nLoaded: {INPUT_FILE} ({df.shape[0]} rows, {df.shape[1]} columns)")

    y_true = df[TRUTH_COL].values

    # Prevalence
    prev = y_true.mean()
    print(f"Prevalence: {int(y_true.sum())}/{len(y_true)} ({100*prev:.1f}%)")

    all_results = {}
    score_dict = {}

    for i, (score_col, pred_col, name) in enumerate(
        zip(SCORE_COLS, PRED_COLS, MODEL_NAMES)
    ):
        print(f"\n--- {name} ---")
        y_score = df[score_col].values if score_col in df.columns else None
        if y_score is not None:
            score_dict[name] = y_score

        # Determine threshold
        if THRESHOLD is not None:
            thresh = THRESHOLD
        elif y_score is not None:
            thresh = youdens_threshold(y_true, y_score)
            print(f"Youden's optimal threshold: {thresh:.4f}")
        else:
            thresh = 0.5

        # Get predictions
        if pred_col in df.columns:
            y_pred = df[pred_col].values
        elif y_score is not None:
            y_pred = (y_score >= thresh).astype(int)
        else:
            raise ValueError(f"Neither prediction column '{pred_col}' nor "
                             f"score column '{score_col}' found.")

        metrics = compute_metrics(y_true, y_pred, y_score)
        all_results[name] = metrics

    # ROC curve
    if score_dict:
        plot_roc(y_true, score_dict, OUTPUT_DIR)

    # Model comparison (DeLong test)
    if COMPARE_MODELS and len(SCORE_COLS) >= 2:
        print("\n--- Model Comparison (DeLong Test) ---\n")
        for i in range(len(SCORE_COLS)):
            for j in range(i + 1, len(SCORE_COLS)):
                s1 = df[SCORE_COLS[i]].values
                s2 = df[SCORE_COLS[j]].values
                z, p = delong_test(y_true, s1, s2)
                from sklearn.metrics import roc_auc_score
                auc1 = roc_auc_score(y_true, s1)
                auc2 = roc_auc_score(y_true, s2)
                print(f"{MODEL_NAMES[i]} (AUC={auc1:.3f}) vs "
                      f"{MODEL_NAMES[j]} (AUC={auc2:.3f}): "
                      f"z = {z:.3f}, p = {p:.3f}")

    # Save outputs
    save_performance_table(all_results, OUTPUT_DIR)
    print_results_text(all_results)

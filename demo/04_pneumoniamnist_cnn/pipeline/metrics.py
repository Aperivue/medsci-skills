"""Quick held-out metrics from predictions.csv (medsci-skills CNN demo).

A fast sanity readout on the GPU node — AUROC / AUPRC / accuracy from the real test
predictions. The AUTHORITATIVE reporting (bootstrap 95% CIs, calibration, subgroup slices)
is done afterwards with /model-evaluation + /analyze-stats; nothing here is hard-coded.
"""
import csv
from sklearn.metrics import roc_auc_score, average_precision_score, accuracy_score

y, p = [], []
with open("predictions.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        y.append(int(r["label"]))
        p.append(float(r["prob_positive"]))

pred = [1 if q >= 0.5 else 0 for q in p]
print("n_test      = %d" % len(y))
print("AUROC       = %.4f" % roc_auc_score(y, p))
print("AUPRC       = %.4f" % average_precision_score(y, p))
print("Accuracy    = %.4f (threshold 0.5)" % accuracy_score(y, pred))
print("prevalence  = %.3f" % (sum(y) / len(y)))

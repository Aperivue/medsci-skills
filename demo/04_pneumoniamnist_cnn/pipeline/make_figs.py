"""Publication figures for the medsci-skills CNN demo, from the real executed results only.
  Fig1 training curves (3 seeds) · Fig2 ROC (ensemble) + bootstrap CI · Fig3 reliability/ECE ·
  Fig4 Grad-CAM panel. No number is hard-coded here — all read from results/.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import roc_curve, roc_auc_score

R = Path("results")
F = Path("figures"); F.mkdir(exist_ok=True)
res = json.loads((R / "results.json").read_text())
cal = json.loads((R / "calibration.json").read_text())

NAVY, CORAL = "#1B2A4E", "#B83E3A"

# Fig 1 — training curves
plt.figure(figsize=(5, 3.2))
for s, curve in res["training_curves_val_loss"].items():
    plt.plot(range(len(curve)), curve, marker=".", label=f"seed {s}")
plt.xlabel("epoch"); plt.ylabel("validation loss"); plt.title("Training (val loss, 3 seeds)")
plt.legend(fontsize=8); plt.tight_layout(); plt.savefig(F / "fig1_training.png", dpi=150); plt.close()

# Fig 2 — ROC (ensemble) + bootstrap CI text
import csv
y, p = [], []
with open(R / "predictions_ensemble.csv") as f:
    for row in csv.DictReader(f):
        y.append(int(row["label"])); p.append(float(row["prob_positive"]))
y, p = np.array(y), np.array(p)
fpr, tpr, _ = roc_curve(y, p)
auc = roc_auc_score(y, p)
lo, hi = res["ensemble"]["auroc_ci95"]
plt.figure(figsize=(4, 4))
plt.plot(fpr, tpr, color=NAVY, lw=2, label=f"AUROC {auc:.3f}\n(95% CI {lo:.3f}–{hi:.3f})")
plt.plot([0, 1], [0, 1], "--", color="gray", lw=1)
plt.xlabel("1 − specificity"); plt.ylabel("sensitivity"); plt.title("ROC — PneumoniaMNIST (test)")
plt.legend(loc="lower right", fontsize=9); plt.tight_layout()
plt.savefig(F / "fig2_roc.png", dpi=150); plt.close()

# Fig 3 — reliability / calibration
bins = cal["bins"]
conf = [b["conf"] for b in bins]; acc = [b["acc"] for b in bins]
plt.figure(figsize=(4, 4))
plt.plot([0, 1], [0, 1], "--", color="gray", lw=1, label="perfect")
plt.plot(conf, acc, marker="o", color=CORAL, label=f"model (ECE {cal['ece']:.3f})")
plt.xlabel("predicted probability"); plt.ylabel("observed frequency")
plt.title("Calibration (reliability)"); plt.legend(fontsize=9); plt.tight_layout()
plt.savefig(F / "fig3_calibration.png", dpi=150); plt.close()

# Fig 4 — Grad-CAM panel
d = np.load(R / "gradcam_examples.npz")
imgs, maps, labels, pred = d["imgs"], d["maps"], d["labels"], d["pred"]
n = min(8, len(imgs))
fig, ax = plt.subplots(2, n, figsize=(1.5 * n, 3.2))
for i in range(n):
    ax[0, i].imshow(imgs[i], cmap="gray"); ax[0, i].axis("off")
    ax[0, i].set_title(f"y={labels[i]} p̂={pred[i]}", fontsize=7)
    ax[1, i].imshow(imgs[i], cmap="gray")
    ax[1, i].imshow(maps[i], cmap="jet", alpha=0.5); ax[1, i].axis("off")
ax[0, 0].set_ylabel("image", fontsize=8); ax[1, 0].set_ylabel("Grad-CAM", fontsize=8)
fig.suptitle("Grad-CAM (attribution; no lesion GT — sanity-checked, not localization proof)", fontsize=8)
plt.tight_layout(); plt.savefig(F / "fig4_gradcam.png", dpi=150); plt.close()

print("wrote", ", ".join(sorted(q.name for q in F.glob("*.png"))))

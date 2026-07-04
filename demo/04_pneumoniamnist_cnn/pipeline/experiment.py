"""3-seed experiment driver for the medsci-skills CNN demo (PneumoniaMNIST).

Reuses the hygiene-gated components (model.py / losses.py / dataset.py) and runs the same
train->val-select->test protocol for seeds 42/43/44, so held-out performance is reported as
mean +/- SD over >= 3 seeds (deep runs move with seed/backend — the scaffold's rule). Also
builds a 3-seed probability ENSEMBLE and bootstraps a 95% CI on the test set. Every number
comes from this executed run; results/results.json is the single source of truth the
manuscript quotes.
"""
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import roc_auc_score, average_precision_score, accuracy_score

from dataset import ScaffoldDataset
from losses import build_loss
from model import build_model

SEEDS = [42, 43, 44]
EPOCHS = 20
BOOT = 2000
OUT = Path("results")
OUT.mkdir(exist_ok=True)


def device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def seed_everything(s):
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def run_seed(seed, dev):
    seed_everything(seed)
    tr = DataLoader(ScaffoldDataset("", ".", "train"), batch_size=128, shuffle=True, num_workers=0)
    va = DataLoader(ScaffoldDataset("", ".", "val"), batch_size=256, shuffle=False, num_workers=0)
    te = DataLoader(ScaffoldDataset("", ".", "test"), batch_size=256, shuffle=False, num_workers=0)
    model = build_model().to(dev)
    crit = build_loss()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    best_val, best_state, curve = float("inf"), None, []
    for ep in range(EPOCHS):
        model.train()
        for x, y in tr:
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad()
            loss = crit(model(x), y)
            loss.backward()
            opt.step()
        model.eval()
        vl = 0.0
        with torch.no_grad():
            for x, y in va:
                x, y = x.to(dev), y.to(dev)
                vl += crit(model(x), y).item()
        vl /= max(len(va), 1)
        curve.append(vl)
        if vl < best_val:
            best_val, best_state = vl, {k: v.cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    model.eval()
    probs, labels = [], []
    with torch.no_grad():
        for x, y in te:
            p = torch.softmax(model(x.to(dev)), dim=1)[:, 1].cpu().numpy()
            probs.append(p)
            labels.append(y.numpy().ravel())
    probs = np.concatenate(probs)
    labels = np.concatenate(labels)
    return probs, labels, curve, best_val


def metrics(y, p):
    pred = (p >= 0.5).astype(int)
    return {"auroc": float(roc_auc_score(y, p)),
            "auprc": float(average_precision_score(y, p)),
            "accuracy": float(accuracy_score(y, pred))}


def boot_ci(y, p, fn, n=BOOT, seed=42):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y))
    vals = []
    for _ in range(n):
        s = rng.choice(idx, size=len(idx), replace=True)
        if len(np.unique(y[s])) < 2:
            continue
        vals.append(fn(y[s], p[s]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def main():
    dev = device()
    print("device:", dev)
    per_seed, all_probs, labels_ref, curves = [], [], None, {}
    for s in SEEDS:
        probs, labels, curve, bv = run_seed(s, dev)
        m = metrics(labels, probs)
        per_seed.append({"seed": s, "best_val_loss": bv, **m})
        all_probs.append(probs)
        labels_ref = labels
        curves[str(s)] = curve
        with open(OUT / f"predictions_seed{s}.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["prob_positive", "label"])
            w.writerows(zip(probs.tolist(), labels.tolist()))
        print(f"seed {s}: AUROC {m['auroc']:.4f}  AUPRC {m['auprc']:.4f}  Acc {m['accuracy']:.4f}")

    def agg(k):
        v = np.array([d[k] for d in per_seed])
        return {"mean": float(v.mean()), "sd": float(v.std(ddof=1))}

    ens = np.mean(np.stack(all_probs), axis=0)
    ens_m = metrics(labels_ref, ens)
    ens_ci = {"auroc": boot_ci(labels_ref, ens, roc_auc_score),
              "auprc": boot_ci(labels_ref, ens, average_precision_score)}

    results = {
        "dataset": "PneumoniaMNIST (MedMNIST v2, CC BY 4.0)",
        "n_test": int(len(labels_ref)),
        "prevalence": float(labels_ref.mean()),
        "seeds": SEEDS, "epochs": EPOCHS, "device": str(dev),
        "per_seed": per_seed,
        "over_seeds_mean_sd": {k: agg(k) for k in ("auroc", "auprc", "accuracy")},
        "ensemble": {**ens_m, "auroc_ci95": ens_ci["auroc"], "auprc_ci95": ens_ci["auprc"],
                     "bootstrap_n": BOOT},
        "training_curves_val_loss": curves,
    }
    with open(OUT / "results.json", "w") as f:
        json.dump(results, f, indent=2)
    with open(OUT / "predictions_ensemble.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["prob_positive", "label"])
        w.writerows(zip(ens.tolist(), labels_ref.tolist()))

    a = results["over_seeds_mean_sd"]["auroc"]
    print(f"\nAUROC over {len(SEEDS)} seeds: {a['mean']:.4f} +/- {a['sd']:.4f}")
    print(f"Ensemble AUROC: {ens_m['auroc']:.4f} (95% CI {ens_ci['auroc'][0]:.4f}-{ens_ci['auroc'][1]:.4f})")
    print("wrote results/results.json + per-seed + ensemble predictions")


if __name__ == "__main__":
    main()

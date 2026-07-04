"""Calibration + explainability for the medsci-skills CNN demo (PneumoniaMNIST).

- Calibration: ECE (10 bins) + Brier score + reliability-curve data, from the 3-seed ensemble
  test predictions (results/predictions_ensemble.csv).
- Grad-CAM (captum LayerGradCam on the last conv) attribution maps for example test cases.
- Adebayo model-randomization SANITY CHECK: Grad-CAM from a randomly-initialised model should
  differ from the trained model's; low similarity => the attribution is model-dependent (passes).

Honest limitation recorded for the explainability gate: PneumoniaMNIST has NO lesion masks, so
a quantitative localization metric (IoU / pointing game) is not computable — the maps are
attribution, not localization proof. Every number comes from this executed run.
"""
import csv
import json
import random
from pathlib import Path

import numpy as np
import torch
from captum.attr import LayerGradCam, LayerAttribution

from dataset import ScaffoldDataset
from model import build_model

OUT = Path("results")
OUT.mkdir(exist_ok=True)


def device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_ensemble():
    y, p = [], []
    with open(OUT / "predictions_ensemble.csv") as f:
        for r in csv.DictReader(f):
            y.append(int(r["label"])); p.append(float(r["prob_positive"]))
    return np.array(y), np.array(p)


def calibration(y, p, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    rows, ece = [], 0.0
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= edges[i + 1])
        if m.sum() == 0:
            continue
        conf, acc, w = float(p[m].mean()), float(y[m].mean()), int(m.sum())
        rows.append({"bin_mid": float((edges[i] + edges[i + 1]) / 2), "conf": conf,
                     "acc": acc, "n": w})
        ece += (w / len(y)) * abs(acc - conf)
    brier = float(np.mean((p - y) ** 2))
    return {"ece": float(ece), "brier": brier, "bins": rows}


def _last_conv(model):
    convs = [m for m in model.features if isinstance(m, torch.nn.Conv2d)]
    return convs[-1]


def gradcam_maps(model, imgs, dev):
    """Grad-CAM for the predicted class, upsampled to the image size; returns (N,H,W) in [0,1]."""
    model.eval()
    lgc = LayerGradCam(model, _last_conv(model))
    x = torch.from_numpy(imgs).float().unsqueeze(1).to(dev)  # (N,1,28,28)
    with torch.no_grad():
        cls = model(x).argmax(1)
    maps = []
    for i in range(len(x)):
        a = lgc.attribute(x[i:i + 1], target=int(cls[i]))
        a = LayerAttribution.interpolate(a, (28, 28)).squeeze().detach().cpu().numpy()
        a = np.maximum(a, 0)
        a = a / (a.max() + 1e-8)
        maps.append(a)
    return np.stack(maps), cls.cpu().numpy()


def main():
    dev = device()
    y, p = load_ensemble()
    cal = calibration(y, p)
    (OUT / "calibration.json").write_text(json.dumps(cal, indent=2))
    print(f"ECE {cal['ece']:.4f}  Brier {cal['brier']:.4f}")

    # trained model (seed-42 best.pt from the single train.py run)
    model = build_model().to(dev)
    model.load_state_dict(torch.load("best.pt", map_location=dev)["model"])

    # example test images (first 8 of each class for a cohort-representative, non-cherry-picked panel)
    test = ScaffoldDataset("", ".", "test")
    imgs = test.imgs.astype(np.float32) / 255.0
    labels = test.labels.ravel()
    pos = np.where(labels == 1)[0][:6]
    neg = np.where(labels == 0)[0][:6]
    sel = np.concatenate([pos, neg])
    maps, pred_cls = gradcam_maps(model, imgs[sel], dev)
    np.savez(OUT / "gradcam_examples.npz", imgs=imgs[sel], maps=maps,
             labels=labels[sel], pred=pred_cls)

    def mean_sim(a_maps, b_maps):
        s = []
        for a, b in zip(a_maps, b_maps):
            av, bv = a.ravel(), b.ravel()
            if av.std() < 1e-6 or bv.std() < 1e-6:
                continue
            s.append(float(np.corrcoef(av, bv)[0, 1]))
        return float(np.mean(s)) if s else float("nan")

    # Adebayo sanity 1 — MODEL randomization: Grad-CAM from a fresh random-init model.
    random.seed(0); torch.manual_seed(0)
    rand_model = build_model().to(dev)
    rand_maps, _ = gradcam_maps(rand_model, imgs[sel], dev)
    sim_model = mean_sim(maps, rand_maps)

    # Adebayo sanity 2 — DATA randomization: retrain on PERMUTED labels; Grad-CAM should change.
    seed_all = lambda s: (random.seed(s), np.random.seed(s), torch.manual_seed(s))
    seed_all(0)
    from losses import build_loss
    from torch.utils.data import DataLoader
    perm_model = build_model().to(dev)
    tr = ScaffoldDataset("", ".", "train")
    y_perm = np.random.permutation(tr.labels.ravel())            # shuffle labels
    xb = torch.from_numpy(tr.imgs.astype(np.float32) / 255.0).unsqueeze(1)
    yb = torch.from_numpy(y_perm).long()
    opt = torch.optim.Adam(perm_model.parameters(), lr=1e-3)
    crit = build_loss()
    perm_model.train()
    for _ep in range(10):
        for i in range(0, len(xb), 128):
            xx, yy = xb[i:i + 128].to(dev), yb[i:i + 128].to(dev)
            opt.zero_grad(); crit(perm_model(xx), yy).backward(); opt.step()
    perm_maps, _ = gradcam_maps(perm_model, imgs[sel], dev)
    sim_data = mean_sim(maps, perm_maps)

    passes = bool(sim_model < 0.5 and sim_data < 0.5)
    sanity = {"tests": ["model_randomization", "data_randomization"],
              "reference": "Adebayo et al. 2018",
              "mean_pearson_trained_vs_random_model": sim_model,
              "mean_pearson_trained_vs_permuted_label_model": sim_data,
              "passes": passes, "n_examples": int(len(sel))}
    (OUT / "explainability.json").write_text(json.dumps(
        {"method": "grad-cam", "tool": "captum LayerGradCam (last conv)",
         "cohort_level": True, "n_examples": int(len(sel)),
         "localization_metric": "none",
         "localization_note": "PneumoniaMNIST has no lesion masks; IoU/pointing-game not computable",
         "interpretation": "attribution",
         "sanity_checks": ["model_randomization", "data_randomization"],
         "sanity_detail": sanity}, indent=2))
    print(f"Adebayo model-rand: r={sim_model:.3f} | data-rand(permuted labels): r={sim_data:.3f} "
          f"-> {'PASS' if passes else 'CHECK'}")
    print("wrote results/calibration.json, explainability.json, gradcam_examples.npz")


if __name__ == "__main__":
    main()

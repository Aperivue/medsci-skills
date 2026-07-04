"""Held-out evaluation (PneumoniaMNIST; medsci-skills CNN demo).
Inference under model.eval() + torch.no_grad() on the TEST split (touched once); writes
per-case positive-class probability + true label to predictions.csv. Compute AUROC + AUPRC
with bootstrap CIs downstream via /model-evaluation + /analyze-stats — no metric is hard-coded
here."""
import csv
import torch
from torch.utils.data import DataLoader
from dataset import ScaffoldDataset
from model import build_model

REPO_ROOT = "."
MANIFEST = "_seed_manifest.csv"  # unused (MedMNIST ships its official split)


def _device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def main():
    device = _device()
    test_loader = DataLoader(ScaffoldDataset(MANIFEST, REPO_ROOT, split="test"),
                             batch_size=256, shuffle=False)
    model = build_model().to(device)
    model.load_state_dict(torch.load("best.pt", map_location=device)["model"])
    model.eval()
    rows = []
    with torch.no_grad():
        for x, y in test_loader:
            probs = torch.softmax(model(x.to(device)), dim=1)[:, 1].cpu().tolist()
            for p, lbl in zip(probs, y.tolist()):
                rows.append({"prob_positive": p, "label": int(lbl)})
    with open("predictions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["prob_positive", "label"])
        w.writeheader()
        w.writerows(rows)
    print("wrote predictions.csv (%d test cases)" % len(rows))


if __name__ == "__main__":
    main()

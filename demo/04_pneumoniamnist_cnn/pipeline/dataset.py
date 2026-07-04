"""MedMNIST dataset reading the OFFICIAL split (PneumoniaMNIST; medsci-skills CNN demo).

Uses MedMNIST v2's predefined train/val/test split (the accepted image-level benchmark
protocol; Yang et al., Scientific Data 2023, CC BY 4.0) — no custom split. The constructor
signature is preserved from the model-scaffold template so train.py / evaluate.py are
unchanged and stay hygiene-clean. MedMNIST is an image-level benchmark: each 28x28 sample is
independent (there is no patient grouping to split on); for a real patient dataset you would
instead split by patient_id (see build_split.py's note).
"""
import numpy as np
import torch
from torch.utils.data import Dataset
from medmnist import PneumoniaMNIST

_SPLIT = {"train": "train", "val": "val", "test": "test"}


class ScaffoldDataset(Dataset):
    def __init__(self, manifest_csv, repo_root, split, transform=None):
        # manifest_csv / repo_root are unused: MedMNIST ships its own official split + data.
        ds = PneumoniaMNIST(split=_SPLIT[split], download=True, size=28)
        self.imgs = ds.imgs            # (N, 28, 28) uint8
        self.labels = ds.labels        # (N, 1) int
        self.transform = transform

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, i):
        x = torch.from_numpy(self.imgs[i].astype(np.float32) / 255.0).unsqueeze(0)  # [1,28,28]
        y = torch.tensor(int(self.labels[i][0]), dtype=torch.long)                  # single-label
        if self.transform is not None:
            x = self.transform(x)
        return x, y

"""Hand-rolled fine-tuning train.py: hygiene-clean BUT loads pretrained weights with no
provenance record in the repo (no PRETRAINED.md, no config.yaml pretrained block).
Fixture for PRETRAINED_PROVENANCE_MISSING — the only verdict this repo should raise."""
import random
import numpy as np
import timm
import torch
from torch.utils.data import DataLoader
from dataset import ScaffoldDataset


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


seed_everything(42)
model = timm.create_model("resnet50", pretrained=True, num_classes=2)   # pretrained load, no provenance
train_ds = ScaffoldDataset("m.csv", ".", split="train")
train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)

"""Classification loss (medsci-skills CNN demo — PneumoniaMNIST is single-label binary)."""
import torch.nn as nn


def build_loss(weight=None):
    """Single-label classification: CrossEntropy over the 2 class logits (use weight for
    class imbalance). For a multi-label task, swap to nn.BCEWithLogitsLoss()."""
    return nn.CrossEntropyLoss(weight=weight)

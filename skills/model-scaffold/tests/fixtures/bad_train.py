import numpy as np
import torch
from torch.utils.data import DataLoader
from dataset import ScaffoldDataset

np.random.seed(0)                                   # only numpy seeded -> SEED_INCOMPLETE
                                                    # no cudnn.deterministic -> CUDNN_NONDETERMINISTIC
test_ds = ScaffoldDataset("m.csv", ".", split="test")
train_loader = DataLoader(test_ds, batch_size=4, shuffle=True)   # -> TRAIN_ON_NONTRAIN_SPLIT

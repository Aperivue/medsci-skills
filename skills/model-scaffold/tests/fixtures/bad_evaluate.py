import torch
from torch.utils.data import DataLoader
from model import build_model
from dataset import ScaffoldDataset

test_ds = ScaffoldDataset("m.csv", ".", split="test")
loader = DataLoader(test_ds, batch_size=1, shuffle=True)   # -> EVAL_SHUFFLE
model = build_model()
for x, y in loader:                                        # no eval()/no_grad() -> MISSING_EVAL_MODE
    pred = model(x)

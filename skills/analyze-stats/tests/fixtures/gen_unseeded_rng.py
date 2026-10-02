"""
Analysis: synthetic BAD fixture -- an explicitly UNSEEDED generator.
`default_rng()` with no argument draws fresh OS entropy on every run, and the
per-resample `random_state=` values come from it, so the bootstrap CI changes
on every run. The word "seed" appearing in `random_state=` must not clear it.
Date: 2026-01-01
"""
import numpy as np
import pandas as pd

df = pd.read_csv("cohort.csv")
rng = np.random.default_rng()
boot = [df.sample(frac=1, replace=True, random_state=rng.integers(1e9))["auc"].mean()
        for _ in range(1000)]
print(np.percentile(boot, [2.5, 97.5]))

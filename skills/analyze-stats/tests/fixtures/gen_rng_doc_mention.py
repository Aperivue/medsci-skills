"""
Analysis: synthetic CLEAN fixture -- unseeded-generator calls are only MENTIONED.
Never write `rng = np.random.default_rng()` or `np.random.seed()` here: both
draw fresh OS entropy. This docstring and the comments below name those calls;
the code itself seeds every generator, so the gate must stay quiet.
Date: 2026-01-01
Random seed: 2026
"""
import numpy as np
import pandas as pd

SEED = 2026
# not default_rng() and not RandomState(None): those are unseeded
rng = np.random.default_rng(SEED)


def bootstrap_mean(x, gen, n_boot=1000):
    """Resample x with the caller's generator (never a bare default_rng())."""
    return [float(np.mean(gen.choice(x, size=len(x), replace=True))) for _ in range(n_boot)]


df = pd.read_csv("cohort.csv")
boot = bootstrap_mean(df["auc"].values, rng)  # set.seed(NULL) would be the R analogue
pd.DataFrame({"boot_mean": boot}).to_csv("boot_means.csv", index=False)
print(np.percentile(boot, [2.5, 97.5]))

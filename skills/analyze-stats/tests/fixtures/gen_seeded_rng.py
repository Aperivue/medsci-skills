"""
Analysis: synthetic CLEAN fixture -- a seeded Generator, passed down explicitly.
`random_state=None` appears only as a function default in a signature, which is
idiomatic and must not be flagged; every call site passes the seeded generator.
Date: 2026-01-01
Random seed: 2026
"""
import numpy as np
import pandas as pd

SEED = 2026
rng = np.random.default_rng(SEED)


def bootstrap_mean(x, n_boot=1000, random_state=None):
    gen = random_state if random_state is not None else np.random.default_rng(SEED)
    return [float(np.mean(gen.choice(x, size=len(x), replace=True))) for _ in range(n_boot)]


df = pd.read_csv("cohort.csv")
boot = bootstrap_mean(df["auc"].values, random_state=rng)
pd.DataFrame({"boot_mean": boot}).to_csv("boot_means.csv", index=False)
print(np.percentile(boot, [2.5, 97.5]))

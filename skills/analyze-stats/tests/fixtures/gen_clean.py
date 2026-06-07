"""
Analysis: synthetic CLEAN fixture for the generated-code quality gate.
Date: 2026-01-01
Random seed: 42
"""
import numpy as np
import pandas as pd

np.random.seed(42)

# portable relative path; no hand-typed data
df = pd.read_csv("cohort.csv")

# seeded randomness -> reproducible
boot = np.random.choice(df["auc"].values, size=1000, replace=True)
boot_mean = float(np.mean(boot))

# derived output written to a NEW path, not the source
summary = df["auc"].describe()
summary.to_csv("auc_summary.csv")
print(f"bootstrap mean AUC = {boot_mean:.3f}")

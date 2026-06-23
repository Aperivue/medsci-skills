"""
Analysis: synthetic CLEAN fixture exercising the colorblind-safe palette.
A hex-color list must NOT be flagged HARDCODED_DATA_LITERAL even alongside a
data-file read (regression for the WONG-palette false positive).
Date: 2026-01-01
Random seed: 42
"""
import numpy as np
import pandas as pd

np.random.seed(42)

# The Wong (2011) colorblind-safe palette that make-figures recommends. Eight
# string literals; the digits live inside the hex codes, not in tabular data.
WONG = ["#000000", "#E69F00", "#56B4E9", "#009E73",
        "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]

# portable relative path; no hand-typed numeric data
df = pd.read_csv("cohort.csv")

means = df.groupby("group")["auc"].mean()
print(WONG[0], float(means.iloc[0]))

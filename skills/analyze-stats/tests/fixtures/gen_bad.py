"""
Analysis: synthetic BAD fixture for the generated-code quality gate.
Date: 2020-01-01
Random seed: (intentionally missing)
"""
import numpy as np
import pandas as pd
import json  # unused import (dead dependency)

# absolute path literal + source read
df = pd.read_csv("/Users/researcher/data/cohort.csv")

# hand-typed tabular data instead of read_csv + subset
ref = pd.DataFrame({
    "auc": [0.81, 0.83, 0.79, 0.88, 0.84, 0.77, 0.82, 0.86, 0.80, 0.85, 0.78, 0.87, 0.83, 0.81],
})

# randomness with no seed set -> non-reproducible
boot = np.random.choice(df["auc"].values, size=1000, replace=True)

breakpoint()  # debugger left in

# writes back to the source path -> overwrites raw data
df.to_csv("/Users/researcher/data/cohort.csv")

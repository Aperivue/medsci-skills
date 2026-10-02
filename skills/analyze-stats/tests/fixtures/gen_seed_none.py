"""
Analysis: synthetic BAD fixture -- seed calls that do not seed anything.
`np.random.seed(None)` re-seeds from OS entropy and `random_state=None` is the
unseeded default; neither makes the train/test split reproducible.
Date: 2026-01-01
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

np.random.seed(None)
df = pd.read_csv("cohort.csv")
train, test = train_test_split(df, test_size=0.3, random_state=None)
print(len(train), len(test), float(np.mean(train["auc"])))

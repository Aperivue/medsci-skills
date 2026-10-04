"""
Synthetic fixture: the same analysis with every API default stated.
Negative control for API_DEFAULT_STUDENT_T and API_DEFAULT_PENALIZED_OR.
"""
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind as tt
from sklearn.linear_model import LogisticRegression as LR

df = pd.read_csv("cohort.csv")
a = df.loc[df["group"] == 1, "age"]
b = df.loc[df["group"] == 0, "age"]
t, p = tt(a, b, equal_var=False)          # Welch, stated
t2, p2 = tt(a, b, equal_var=True)         # Student, stated: a choice, not a default

model = LR(C=np.inf, max_iter=1000)       # unpenalised (sklearn >= 1.8 spelling)
model.fit(df[["age", "bmi"]], df["event"])
odds_ratios = np.exp(model.coef_[0])
ridge = LR(penalty="l2", max_iter=1000)   # a stated penalty is a choice
ridge.fit(df[["age", "bmi"]], df["event"])
pd.Series(odds_ratios, index=["age", "bmi"]).to_csv("odds_ratios.csv")
print(f"t = {t:.2f}, P = {p:.3f}; {t2:.2f}, {p2:.3f}; {ridge.score(df[['age', 'bmi']], df['event']):.3f}")

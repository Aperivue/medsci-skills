"""
Synthetic fixture: two API defaults that differ from the skill's rules.
ttest_ind() without equal_var is Student's t; LogisticRegression() with neither
penalty nor C is L2-penalised, and its odds ratios are reported below.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression

df = pd.read_csv("cohort.csv")
a = df.loc[df["group"] == 1, "age"]
b = df.loc[df["group"] == 0, "age"]
t, p = stats.ttest_ind(a, b)

model = LogisticRegression(max_iter=1000)
model.fit(df[["age", "bmi"]], df["event"])
odds_ratios = np.exp(model.coef_[0])
pd.Series(odds_ratios, index=["age", "bmi"]).to_csv("odds_ratios.csv")
print(f"t = {t:.2f}, P = {p:.3f}")

"""
Synthetic fixture: statsmodels' ttest_ind, which takes usevar rather than equal_var.
Both calls are explicit Welch tests. Negative control for API_DEFAULT_STUDENT_T,
which checks only calls resolved to scipy.stats.
"""
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.weightstats import ttest_ind

df = pd.read_csv("cohort.csv")
a = df.loc[df["group"] == 1, "age"]
b = df.loc[df["group"] == 0, "age"]
print(ttest_ind(a, b, usevar="unequal"))
print(sm.stats.ttest_ind(a, b, usevar="unequal"))

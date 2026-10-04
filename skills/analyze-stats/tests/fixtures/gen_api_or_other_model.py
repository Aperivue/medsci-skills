"""
Synthetic fixture: odds ratios from an unpenalised statsmodels Logit, and a default
LogisticRegression used only for the AUC. No coef_ is exponentiated, so the odds
ratios are not tied to the sklearn model. Negative control for API_DEFAULT_PENALIZED_OR.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

df = pd.read_csv("cohort.csv")
res = smf.logit("event ~ age + bmi", data=df).fit()
odds_ratios = np.exp(res.params)
clf = LogisticRegression(max_iter=1000)
clf.fit(df[["age", "bmi"]], df["event"])
auc = roc_auc_score(df["event"], clf.predict_proba(df[["age", "bmi"]])[:, 1])
print(odds_ratios, f"apparent AUC = {auc:.3f}")

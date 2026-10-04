"""
Synthetic fixture: a default (penalised) LogisticRegression used only for
prediction, with no odds ratio anywhere. Negative control for API_DEFAULT_PENALIZED_OR.
"""
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

df = pd.read_csv("cohort.csv")
clf = LogisticRegression(max_iter=1000)
clf.fit(df[["age", "bmi"]], df["event"])
auc = roc_auc_score(df["event"], clf.predict_proba(df[["age", "bmi"]])[:, 1])
print(f"apparent AUC = {auc:.3f}")

#!/usr/bin/env bash
# Regression tests for the analyze-stats templates (v6 stats-lane fixes, ST-4 ... ST-34).
#
# Each check reproduces a defect that shipped: a template that crashed, reported a wrong
# number, or printed a conclusion regardless of the result. Reference values were computed
# with R (survey 4.5, MatchIt 4, sandwich, lme4, dcurves) on the fixtures generated below;
# the AS-2 cases (likert_summary, forest_plot, sample_size) record their R call inline.
# np.random.RandomState streams are frozen across numpy versions, so the fixtures are stable.
#
# Static assertions always run. The python runtime block needs exactly the packages the CI
# validate job installs (numpy, pandas, scipy, scikit-learn, matplotlib, statsmodels) and
# nothing else; the DCA checks need R + dcurves, which CI does not have. A missing
# dependency is reported on a loud "SKIPPED n runtime checks" line and never counted as a
# pass. The python block must exit 0 and report all PY_RUNTIME_CHECKS checks: counting only the
# PASS/FAIL lines it printed let a crash after the first PASS drop every later check silently.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T="$HERE/../references/templates"
PASS=0
FAIL=0
ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }
absent()  { grep -qE -- "$2" "$T/$1" && bad "$3" || ok "$3"; }
present() { grep -qE -- "$2" "$T/$1" && ok "$3" || bad "$3"; }

echo "--- static ---"
for f in regression table1_demographics repeated_measures propensity_score agreement_analysis \
         survey_weighted_analysis diagnostic_accuracy survival_analysis forest_plot likert_summary; do
  python3 -m py_compile "$T/$f.py" 2>/dev/null && ok "$f.py compiles" || bad "$f.py syntax error"
done
for f in regression table1_demographics repeated_measures propensity_score agreement_analysis \
         survey_weighted_analysis; do
  absent "$f.py" 'stats\.scipy\.' "ST-27 $f: no stats.scipy.__version__ (AttributeError on current scipy)"
done
absent regression.py '\.codes' "ST-5 regression: no Categorical(...).codes before dropna"
absent propensity_score.py '\.codes' "ST-5 propensity_score: no Categorical(...).codes before dropna"
present regression.py 'add_constant\(X, has_constant' "ST-6 regression: VIF computed with an intercept"
absent regression.py '[Hh]osmer.?[Ll]emeshow ?(test|P|:)|adequate calibration' "ST-7 regression: no Hosmer-Lemeshow / unconditional 'adequate calibration'"
absent survey_weighted_analysis.py 'freq_weights=' "ST-4 survey: no freq_weights (design-free SEs)"
present survey_weighted_analysis.py 'def design_vcov' "ST-4 survey: linearization variance with strata + PSU"
absent propensity_score.py 'freq_weights=|n_neighbors=ratio' "ST-9/16 PS: no freq_weights, no single-neighbour matching"
present propensity_score.py 'cov_type' "ST-9 PS: robust / cluster-robust SEs"
absent agreement_analysis.py 'DATA_TYPE = "auto"|Cicchetti' "ST-23 agreement: no auto data type, no Cicchetti bands"
present diagnostic_accuracy.py 'CLUSTER_COL' "ST-14 diagnostic: patient-level cluster CI option"
absent table1_demographics.py 'kstest' "ST-15 table1: no KS normality gate"
present table1_demographics.py 'equal_var=False' "ST-15 table1: Welch t-test"
present repeated_measures.py '"time_values"' "ST-33 repeated measures: actual visit times"
present repeated_measures.py '"gee_family"' "ST-33 repeated measures: GEE family configurable"
absent dca_plot.R 'as_probability += *model_cols|Using built-in example data|dpi <- if \(ext' "ST-20 dca: no recalibration, no silent example data, no dpi NULL"
present dca_plot.R 'net_intervention_avoided' "ST-20 dca: interventions avoided from dcurves"

echo "--- runtime (python) ---"
SKIPPED=0
PY_RUNTIME_CHECKS=23
if python3 -c "import numpy, pandas, scipy, sklearn, matplotlib, statsmodels" 2>/dev/null; then
  WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
  OUT="$(python3 - "$T" "$WORK" <<'PY' 2>&1
import contextlib, importlib.util, io, os, subprocess, sys, warnings
import matplotlib
matplotlib.use("Agg")
import numpy as np, pandas as pd
warnings.simplefilter("ignore")
T, WORK = sys.argv[1], sys.argv[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, f"{T}/{name}.py")
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    return m

def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)

def check(cond, msg):
    print(("PASS: " if cond else "FAIL: ") + msg)

close = lambda a, b, tol: abs(float(a) - b) < tol

# --- regression.py (ST-5, ST-6) ---
reg = load("regression")
r = np.random.RandomState(3); n = 500
d = pd.DataFrame(dict(age=r.normal(60, 10, n), bmi=r.normal(25, 4, n),
                      smoking=r.choice(["never", "former", "current"], n)))
X, cols = quiet(reg.encode_predictors, d, ["age", "bmi", "smoking"], ["smoking"],
                {"smoking": "never"})
check(sorted(cols["smoking"]) == ["smoking: current vs never", "smoking: former vs never"],
      "ST-5 regression: 3-level nominal -> 2 indicators vs the stated reference")
# the template drops incomplete rows BEFORE encoding: a missing category is not a level
src = open(f"{T}/regression.py").read()
check(src.index("df_complete = df[analysis_vars].dropna()") < src.index("model = run_logistic(df_complete"),
      "ST-5 regression: complete cases taken before the design matrix is built")
d_na = d.copy(); d_na.loc[::10, "smoking"] = np.nan
Xn, _ = quiet(reg.encode_predictors, d_na.dropna(), ["age", "bmi", "smoking"], ["smoking"], {})
check(len(Xn) == d_na["smoking"].notna().sum() and not Xn.isna().any().any(),
      "ST-5 regression: rows with a missing category are excluded, not coded")
check(reg.calculate_vif(X)["VIF"].max() < 1.5,
      "ST-6 regression: VIF of independent predictors with non-zero means is ~1")

# --- survey_weighted_analysis.py (ST-4): equals R survey::svyglm ---
r = np.random.RandomState(11); rows = []
for h in range(12):
    for c in range(3):
        u = r.normal(0, 0.4)
        for _ in range(25):
            x = r.binomial(1, 0.35); age = r.normal(50, 12); inc = r.randint(1, 5)
            y = r.binomial(1, 1 / (1 + np.exp(-(-1.2 + 0.4 * x + 0.02 * (age - 50) + 0.15 * (inc == 4) + u))))
            rows.append(dict(kstrata=h, psu=c, wt=r.uniform(200, 3000), y=y, x=x, age=age,
                             income=inc, sex=r.binomial(1, 0.5)))
d = pd.DataFrame(rows)
svy = load("survey_weighted_analysis")
design = {"w": d["wt"], "h": d["kstrata"].astype(str),
          "c": d["kstrata"].astype(str) + "|" + d["psu"].astype(str),
          "group_domain": pd.Series(True, index=d.index)}
full = pd.Series(True, index=d.index)
row = svy.svy_logistic(d, design, "y", "x", ["age", "income"], full, ["income"], {}).iloc[0]
# R: svyglm(y ~ x + age + factor(income), svydesign(~psu, strata = ~kstrata, weights = ~wt, nest = TRUE))
check(close(row.wOR, 1.702863, 1e-4) and close(row.CI_lower, 1.236736, 1e-4)
      and close(row.CI_upper, 2.344673, 1e-4) and close(row.P, 0.002487, 1e-5)
      and row.design_df == 19, "ST-4 survey: wOR, CI, P and design df equal svyglm")
dom = d["sex"] == 1
row = svy.svy_logistic(d, dict(design, group_domain=dom), "y", "x", ["age", "income"], dom,
                       ["income"], {}).iloc[0]
check(close(row.wOR, 1.601775, 1e-4) and close(row.CI_lower, 0.984197, 1e-4)
      and close(row.CI_upper, 2.606878, 1e-4) and close(row.P, 0.057199, 1e-5),
      "ST-4 survey: subgroup equals svyglm on subset(design, sex == 1)")

# --- propensity_score.py (ST-9, ST-16): equals MatchIt + sandwich ---
r = np.random.RandomState(5); n = 600
age = r.normal(60, 10, n); com = r.poisson(2, n); sex = np.where(r.rand(n) < 0.5, "F", "M")
t = r.binomial(1, 1 / (1 + np.exp(-(-2 + 0.05 * (age - 60) + 0.3 * com + 0.4 * (sex == "M")))))
y = 1.0 * t + 0.05 * (age - 60) + 0.5 * com + r.normal(0, 2, n)
d = pd.DataFrame(dict(treatment=t, outcome=y, age=age, sex=sex, comorbidity_score=com))
ps = load("propensity_score")
X, _ = quiet(ps.encode_covariates, d, ["age", "sex", "comorbidity_score"], ["sex"])
p = ps.estimate_ps(X, d["treatment"].values)
# R: matchit(..., method = "nearest", link = "linear.logit", caliper = 0.2, ratio = k);
#    lm(outcome ~ treatment, weights = weights) + sandwich::vcovCL(cluster = ~subclass)
for k, (nt, nc, md, se) in {1: (144, 144, 1.277883, 0.246138),
                            2: (144, 256, 1.280071, 0.228061)}.items():
    m = quiet(ps.ps_matching, d, p, "treatment", 0.2, k)
    est, lo, hi, _ = quiet(ps.weighted_outcome_analysis, m, "treatment", "outcome",
                           "continuous", m["match_weight"], cluster=m["subclass"])["mean difference"]
    check((m.treatment == 1).sum() == nt and (m.treatment == 0).sum() == nc
          and close(est, md, 1e-5) and close((hi - lo) / (2 * 1.959964), se, 1e-5),
          f"ST-16 PS: 1:{k} matched set and cluster-robust SE equal MatchIt + vcovCL")
w = np.where(d["treatment"] == 1, 1 / p, 1 / (1 - p))
est, lo, hi, _ = quiet(ps.weighted_outcome_analysis, d, "treatment", "outcome", "continuous",
                       w)["mean difference"]
check(close(est, 1.201293, 1e-5) and close((hi - lo) / (2 * 1.959964), 0.250183, 1e-5),
      "ST-9 PS: IPTW SE equals glm + sandwich::vcovHC(type = 'HC0')")

# --- agreement_analysis.py (ST-23) ---
ag = load("agreement_analysis"); ag.BOOTSTRAP_N = 200
check(ag.interpret_icc(0.848) == "good", "ST-23 agreement: Koo & Li band (0.848 -> good)")
r = np.random.RandomState(4); truth = r.choice([1, 2, 3], 120)
d = pd.DataFrame({f"r{i}": np.where(r.rand(120) < 0.8, truth, r.choice([1, 2, 3], 120))
                  for i in range(3)})
res = quiet(ag.analyze_categorical, d, ["r0", "r1", "r2"], WORK)
check(res[0]["Metric"] == "Fleiss' kappa" and res[0]["95% CI"].startswith("(0."),
      "ST-23 agreement: Fleiss' kappa carries a CI")

# --- diagnostic_accuracy.py (ST-13, ST-14) ---
dx_src = open(f"{T}/diagnostic_accuracy.py").read()
r = np.random.RandomState(8); rows = []
for pid in range(80):
    u = r.normal(0, 1.5)
    for _ in range(r.randint(1, 6)):
        yy = int(r.rand() < 0.5)
        rows.append(dict(patient_id=pid, ground_truth=yy,
                         model_score=1 / (1 + np.exp(-(-0.5 + 1.6 * yy + u * yy + r.normal(0, 0.7))))))
pd.DataFrame(rows).to_csv(f"{WORK}/dx.csv", index=False)
open(f"{WORK}/dx.py", "w").write(dx_src.replace('INPUT_FILE = "data.csv"', f'INPUT_FILE = "{WORK}/dx.csv"')
                                  .replace('OUTPUT_DIR = "."', f'OUTPUT_DIR = "{WORK}"'))
run = subprocess.run([sys.executable, f"{WORK}/dx.py"], capture_output=True, text=True)
check(run.returncode != 0 and "PRESPECIFIED" in run.stderr,
      "ST-13 diagnostic: no silent Youden cut-off when no prediction column is given")
dx = load("diagnostic_accuracy"); dd = pd.DataFrame(rows)
yt = dd["ground_truth"].values; yp = (dd["model_score"].values >= 0.5).astype(int)
wil = dx.compute_metrics(yt, yp)["Sensitivity"]
boot = dx.cluster_bootstrap_ci(yt, yp, None, dd["patient_id"].values, n_boot=500)["Sensitivity"]
check(boot[1] - boot[0] > wil[2] - wil[1],
      "ST-14 diagnostic: patient-level bootstrap CI wider than the row-level Wilson CI")

# --- table1_demographics.py (ST-15): Welch ANOVA equals R oneway.test ---
t1 = load("table1_demographics")
r = np.random.RandomState(8)
g = [r.normal(60, 12, 30), r.normal(56, 5, 90), r.normal(58, 8, 50)]
name, pval = t1.compare_continuous([pd.Series(x) for x in g], True)
check(name == "Welch ANOVA" and close(pval, 0.27669495, 1e-6),
      "ST-15 table1: Welch ANOVA P equals R oneway.test(var.equal = FALSE)")

# --- repeated_measures.py (ST-33): actual times; the LMM table builds ---
rm = load("repeated_measures")
r = np.random.RandomState(6); rows = []
for i in range(60):
    g = i % 2; b0 = r.normal(0, 2)
    yv = [50 + b0 + (0.5 + 0.3 * g) * wk + r.normal(0, 1.5) for wk in (0, 2, 6, 12)]
    rows.append(dict(subject_id=i, group=g, t0=yv[0], t1=yv[1], t2=yv[2], t3=yv[3]))
long = quiet(rm.wide_to_long, pd.DataFrame(rows), "subject_id", "group", ["t0", "t1", "t2", "t3"],
             "score", [0, 2, 6, 12])
res, tab = quiet(rm.run_lmm, long, "subject_id", "time", "score", "group", "intercept", [])
check(tab is not None and close(res.fe_params["time"], 0.482955, 1e-4)
      and close(res.fe_params["time:group"], 0.335885, 1e-4),
      "ST-33 repeated measures: slope per unit time equals lme4; results table builds")

# --- AS-2: known-answer cases for the templates no test exercised before ---
# Every reference value below was computed on 2026-10-04 with R 4.3.3 and the package
# named beside it; the call is recorded so the value can be recomputed.

# likert_summary.py: Mann-Whitney / Wilcoxon / item-rest correlation equal R stats::
lk = load("likert_summary")
r = np.random.RandomState(21); n = 60
grp = np.where(np.arange(n) < 32, "resident", "attending")
lat = r.normal(0, 1, n) + 0.6 * (grp == "attending")
def lk_item(noise): return np.clip(np.round(3 + lat + r.normal(0, noise, n)), 1, 5).astype(int)
lkd = pd.DataFrame(dict(group=grp, Q1=lk_item(0.8), Q2=lk_item(0.9), Q3=lk_item(1.0)))
lkd["Q4"] = 6 - lk_item(0.8)   # a reverse-worded item, not recoded
lkd["pre"] = lk_item(1.0); lkd["post"] = np.clip(lkd["pre"] + r.choice([-1, 0, 1, 1, 2], n), 1, 5)
g = quiet(lk.compare_groups, lkd, ["Q1"], "group").iloc[0]
# R: w <- wilcox.test(Q1[resident], Q1[attending], exact = FALSE, correct = TRUE)
#    -> W = 372.5, P = 0.2496238525; 1 - 2 * W / (32 * 28) = 0.1685268
check(g["U statistic"] == 372.5 and g["P value"] == 0.25 and g["r (effect size)"] == 0.169,
      "AS-2 likert: Mann-Whitney U, P and rank-biserial r equal R wilcox.test")
rest = lk.item_rest_correlations(lkd, ["Q1", "Q2", "Q3", "Q4"])
# R: cor(Q1, rowSums(d[, c("Q2","Q3","Q4")])) = 0.4432235359; same for Q4 = -0.5843952919
check(rest["Q1"] == 0.443 and rest["Q4"] == -0.584,
      "AS-2 likert: item-rest correlations equal R cor(item, rowSums(rest))")
pp = quiet(lk.prepost_comparison, lkd, ["pre"], ["post"]).iloc[0]
# R: wilcox.test(pre, post, paired = TRUE, exact = FALSE, correct = FALSE)
#    -> V = 238, P = 0.00260074389631
check(pp["W statistic"] == 238.0 and pp["P value"] == 0.003,
      "AS-2 likert: Wilcoxon signed-rank V and P equal R wilcox.test(paired = TRUE)")
same = pd.DataFrame(dict(group=["a"] * 20 + ["b"] * 20, Q1=list(range(1, 6)) * 8))
g0 = quiet(lk.compare_groups, same, ["Q1"], "group").iloc[0]
rc = quiet(lk.apply_reverse_coding, lkd, ["Q1", "Q2", "Q3", "Q4"], ["Q4"], 5)
check(g0["P value"] == 1.0 and g0["r (effect size)"] == 0.0
      and lk.item_rest_correlations(rc, ["Q1", "Q2", "Q3", "Q4"])["Q4"] > 0
      and quiet(lk.apply_reverse_coding, rc, ["Q4"], ["Q4"], 5)["Q4"].equals(lkd["Q4"]),
      "AS-2 likert: identical groups give P = 1, r = 0; reverse coding flips item-rest sign and is an involution")

# forest_plot.py: geometry of a plot drawn from a metafor fit
import matplotlib.pyplot as plt
fp = load("forest_plot")
# R: dat <- escalc("RR", ai = tpos, bi = tneg, ci = cpos, di = cneg, data = dat.bcg)
#    res <- rma(yi, vi, data = dat, method = "REML"); summary(dat, transf = exp); weights(res)
#    predict(res, transf = exp) -> 0.4894209368 (0.3440742934, 0.6961660838)   [metafor 4.4.0]
bcg = pd.DataFrame(
    [(0.4109386548, 0.1343015708, 1.2573983833, 5.059483079), (0.2048681542, 0.0862974496, 0.4863522707, 6.364679632),
     (0.2597402597, 0.0734425907, 0.9186086969, 4.436027763), (0.2365605236, 0.1792808941, 0.3121407979, 9.698746736),
     (0.8044895338, 0.5162931271, 1.2535580584, 8.868456287), (0.4556111448, 0.3871323353, 0.5362029889, 10.095738165),
     (0.1977210216, 0.0783565767, 0.4989192234, 6.027181703), (1.0120240481, 0.8945719776, 1.1448968888, 10.189438635),
     (0.6253663451, 0.3925762660, 0.9961964069, 8.743133132), (0.2537654653, 0.1494209435, 0.4309764740, 8.367607247),
     (0.7122268361, 0.5725136830, 0.8860348339, 9.925026663), (1.5619161996, 0.3736891112, 6.5283738311, 3.821629423),
     (0.9828350769, 0.5821374615, 1.6593413964, 8.402851535)],
    columns=["effect_size", "ci_lower", "ci_upper", "weight"])
bcg.insert(0, "study_label", [f"Trial {i + 1}" for i in range(len(bcg))])
captured = []
real_savefig = fp.plt.savefig
fp.plt.savefig = lambda *a, **k: captured.append(plt.gcf()) or real_savefig(*a, **k)
quiet(fp.make_forest_plot, bcg, 0.4894209368, 0.3440742934, 0.6961660838, 92.2, 0.3132, 0.0,
      effect_label="RR", output_path=f"{WORK}/forest")
fp.plt.savefig = real_savefig
fig = captured[0]
boxes = [a for a in fig.artists if type(a).__name__ == "FancyBboxPatch"]
diamond = [a for a in fig.artists if type(a).__name__ == "Polygon"][0]
cx = np.array([b.get_x() + b.get_width() / 2 for b in boxes]); bh = np.array([b.get_height() for b in boxes])
slope, icpt = np.polyfit(np.log(bcg["effect_size"]), cx, 1)
dx = sorted(diamond.get_xy()[:4, 0])
expect = icpt + slope * np.log([0.3440742934, 0.4894209368, 0.4894209368, 0.6961660838])
nulls = [a for a in fig.artists if type(a).__name__ == "Line2D" and a.get_linestyle() == "--"]
check(len(boxes) == 13 and slope > 0
      and np.allclose(cx, icpt + slope * np.log(bcg["effect_size"]), atol=1e-12)
      and np.allclose(dx, expect, atol=1e-12)
      and np.allclose(nulls[0].get_xdata()[0], icpt, atol=1e-12)
      and np.allclose((bh / bh.max()) ** 2, bcg["weight"] / bcg["weight"].max(), atol=1e-12)
      and os.path.getsize(f"{WORK}/forest.pdf") > 0 and os.path.getsize(f"{WORK}/forest.png") > 0,
      "AS-2 forest: RR on a log axis, null at 1, diamond at the metafor pooled CI, box area = metafor weight")
md = pd.DataFrame(dict(study_label=["a", "b"], effect_size=[-1.0, 0.5], ci_lower=[-2.0, -0.4], ci_upper=[0.0, 1.4]))
try:
    quiet(fp.make_forest_plot, md, -0.3, -1.1, 0.5, 0, 0, 1, effect_label="OR", output_path=f"{WORK}/bad")
    raised = False
except ValueError:
    raised = True
plt.close("all")
quiet(fp.make_forest_plot, md, -0.3, -1.1, 0.5, 0, 0, 1, effect_label="MD", output_path=f"{WORK}/md")
check(raised and os.path.getsize(f"{WORK}/md.png") > 0
      and list(fp.compute_box_size(pd.Series([1.0, 4.0, 9.0]), 3)) == [0.35 / 3, 0.35 * 2 / 3, 0.35],
      "AS-2 forest: non-positive limits refused on a ratio axis, drawn on a linear MD axis; box side ~ sqrt(weight)")

# sample_size.R: the template's closed-form sections, evaluated from its own source.
# CI has no R, so each `name <- expr` line is translated (^ -> **, qnorm -> norm.ppf, ...);
# a statement that needs anything else (pwr, functions, data frames) is left out.
import math, re
from scipy.stats import norm
def r_statements(path):
    out, buf = [], ""
    for line in open(path, encoding="utf-8"):
        code = line.split("#", 1)[0].rstrip()
        if not code.strip() and not buf:
            continue
        buf += " " + code.strip()
        if buf.count("(") == buf.count(")") and buf.count("{") == buf.count("}") \
                and not re.search(r"[-+*/^,]$", buf):
            out.append(buf.strip()); buf = ""
    return out
def r_eval(path, keep, override=None):
    env = {"qnorm": norm.ppf, "ceiling": math.ceil, "log": math.log, "exp": math.exp,
           "sqrt": math.sqrt, "max": max}
    env.update(override or {})
    for st in r_statements(path):
        m = re.match(r"^([A-Za-z_][\w.]*)\s*<-\s*(.+)$", st)
        if not m or "function" in st or m.group(1) in (override or {}):
            continue
        try:
            env[m.group(1)] = eval(m.group(2).replace("^", "**"), {"__builtins__": {}}, env)
        except Exception:
            continue
    return [env.get(k) for k in keep]
SS = f"{T}/sample_size.R"
# R: epiR::epi.ssdxsesp(test = 0.85, type = "se", Py = 0.3, epsilon = 0.05, error = "absolute",
#    nfractional = FALSE, conf.level = 0.95) -> 654; test = 0.90, type = "sp" -> 198;
#    test = 0.80 / 0.95, Py = 0.2, epsilon = 0.07 -> 628 / 47   [epiR 2.0.67]
alt = dict(sensitivity_expected=0.80, specificity_expected=0.95, prevalence=0.2, ci_half_width=0.07)
check(r_eval(SS, ["n_for_se", "n_for_sp", "n_total_diag"]) == [654, 198, 654]
      and r_eval(SS, ["n_for_se", "n_for_sp"], alt) == [628, 47],
      "AS-2 sample_size: diagnostic-accuracy N equals epiR::epi.ssdxsesp (two parameter sets)")
icc, mc, ev = r_eval(SS, ["n_icc", "n_mc", "n_events"])
check(None not in (icc, mc, ev)
      and r_eval(SS, ["n_icc"], dict(icc_expected=0.85))[0] < icc
      and r_eval(SS, ["n_mc"], dict(p10=0.20))[0] > mc
      and r_eval(SS, ["n_events"], dict(hr=0.80))[0] > ev
      and r_eval(SS, ["n_for_se"], dict(ci_half_width=0.10))[0] < 654,
      "AS-2 sample_size: N falls as the effect grows or the precision target loosens (ICC, McNemar, log-rank, Se)")

PY
)"
  RC=$?
  echo "$OUT" | grep -E "^(PASS|FAIL): " | while read -r line; do echo "  $line"; done
  echo "$OUT" | grep -E "^SKIPPED " | while read -r line; do echo "  $line"; done
  PASS=$((PASS + $(echo "$OUT" | grep -c '^PASS: ')))
  FAIL=$((FAIL + $(echo "$OUT" | grep -c '^FAIL: ')))
  INNER_SKIPPED=$(echo "$OUT" | sed -n 's/^SKIPPED \([0-9]*\) .*/\1/p' | awk '{s+=$1} END {print s+0}')
  SKIPPED=$((SKIPPED + INNER_SKIPPED))
  REPORTED=$(( $(echo "$OUT" | grep -cE '^(PASS|FAIL): ') + INNER_SKIPPED ))
  if [ "$RC" -ne 0 ]; then
    echo "$OUT" | tail -20; bad "runtime block exited $RC after $REPORTED of $PY_RUNTIME_CHECKS checks"
  elif [ "$REPORTED" -ne "$PY_RUNTIME_CHECKS" ]; then
    bad "runtime block reported $REPORTED of $PY_RUNTIME_CHECKS checks"
  fi
else
  echo "  SKIPPED $PY_RUNTIME_CHECKS runtime checks: numpy/pandas/scipy/sklearn/matplotlib/statsmodels missing"
  SKIPPED=$((SKIPPED + PY_RUNTIME_CHECKS))
fi

echo "--- runtime (R dcurves) ---"
if command -v Rscript >/dev/null 2>&1 && Rscript -e 'quit(status = !requireNamespace("dcurves", quietly = TRUE))' >/dev/null 2>&1; then
  RW="$(mktemp -d)"
  sed -e "s#input_file    = \"predictions.csv\"#input_file    = \"$RW/p.csv\"#" \
      -e "s#output_prefix = \"dca\"#output_prefix = \"$RW/dca\"#" "$T/dca_plot.R" > "$RW/dca.R"
  Rscript "$RW/dca.R" 2>&1 | grep -q "Input file .* not found" \
    && ok "ST-20 dca: missing input stops (no simulated fallback)" \
    || bad "ST-20 dca: missing input must stop, not switch to simulated data"
  Rscript -e 'n <- 400; y <- rep(c(1, 0, 0, 0), 100); s <- seq(0, 1, length.out = n)
    m1 <- ifelse(y == 1, 0.15 + 0.8 * s, 0.05 + 0.6 * rev(s)); m2 <- 0.1 + 0.5 * s
    write.csv(data.frame(event = y, model1 = pmin(m1, 0.99), model2 = m2), commandArgs(TRUE)[1], row.names = FALSE)' "$RW/p.csv" >/dev/null 2>&1
  Rscript "$RW/dca.R" >/dev/null 2>&1
  Rscript -e 'a <- commandArgs(TRUE); p <- read.csv(a[1]); r <- read.csv(a[2]); n <- nrow(p); ok <- TRUE
    for (t in c(0.1, 0.3)) { pos <- p$model1 >= t; nb <- (sum(pos & p$event == 1) - sum(pos & p$event == 0) * t / (1 - t)) / n
      all <- mean(p$event) - (1 - mean(p$event)) * t / (1 - t); nia <- (nb - all) / (t / (1 - t)) * 100
      got <- r$net_intervention_avoided[r$variable == "model1" & abs(r$threshold - t) < 1e-9]
      ok <- ok && length(got) == 1 && abs(got - nia) < 1e-6 }
    quit(status = !ok)' "$RW/p.csv" "$RW/dca_results.csv" >/dev/null 2>&1 \
    && ok "ST-20 dca: net interventions avoided = (NB_model - NB_all)/(pt/(1-pt)) x 100" \
    || bad "ST-20 dca: interventions avoided missing or wrong"
  [ -s "$RW/dca_dca.pdf" ] && [ -s "$RW/dca_dca.png" ] && ok "ST-20 dca: PDF and PNG written" || bad "ST-20 dca: figure not written"
  rm -rf "$RW"
else
  echo "  SKIPPED 3 runtime checks: Rscript/dcurves missing (ST-20 dca)"
  SKIPPED=$((SKIPPED + 3))
fi

echo "--- runtime (R sample_size) ---"
# The closed-form sections run in the python block above without R. This block runs the
# template itself and checks the two sections that call pwr, so it needs R + pwr + epiR,
# which CI does not have.
if command -v Rscript >/dev/null 2>&1 && Rscript -e 'quit(status = !all(sapply(c("pwr", "epiR"), requireNamespace, quietly = TRUE)))' >/dev/null 2>&1; then
  RW="$(mktemp -d)"
  (cd "$RW" && Rscript "$T/sample_size.R" >/dev/null 2>&1)
  # R 4.3.3, pwr 1.3.0: pwr.2p.test(h = ES.h(0.70, 0.55), sig.level = 0.05, power = 0.8)$n
  #   = 161.9349146 -> 162 per group; pwr.t.test(d = 0.5, sig.level = 0.05, power = 0.8,
  #   type = "two.sample")$n = 63.76561044 -> 64 per group; epiR 2.0.67 epi.ssdxsesp -> 654
  Rscript -e 'r <- read.csv(commandArgs(TRUE)[1]); g <- function(a, col) as.numeric(r[r$Analysis == a, col])
    quit(status = !(g("Two proportions (unpaired)", "N_per_group") == 162 && g("Independent t-test", "N_per_group") == 64
      && g("Diagnostic accuracy", "N_total") == 654))' "$RW/sample_size_results.csv" >/dev/null 2>&1 \
    && ok "AS-2 sample_size: template run gives pwr.2p.test 162, pwr.t.test 64, epiR 654" \
    || bad "AS-2 sample_size: template run does not reproduce pwr / epiR"
  rm -rf "$RW"
else
  echo "  SKIPPED 1 runtime check: Rscript/pwr/epiR missing (AS-2 sample_size pwr sections)"
  SKIPPED=$((SKIPPED + 1))
fi

echo ""
echo "test_stats_templates: $PASS passed, $FAIL failed, $SKIPPED runtime checks SKIPPED"
[ "$FAIL" -eq 0 ]

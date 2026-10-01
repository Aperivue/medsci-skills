#!/usr/bin/env bash
# Regression tests for the analyze-stats templates (v6 stats-lane fixes, ST-4 ... ST-34).
#
# Each check reproduces a defect that shipped: a template that crashed, reported a wrong
# number, or printed a conclusion regardless of the result. Reference values were computed
# with R (survey 4.5, MatchIt 4, sandwich, lme4, dcurves) on the fixtures generated below;
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
         survey_weighted_analysis diagnostic_accuracy survival_analysis; do
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
PY_RUNTIME_CHECKS=15
if python3 -c "import numpy, pandas, scipy, sklearn, matplotlib, statsmodels" 2>/dev/null; then
  WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
  OUT="$(python3 - "$T" "$WORK" <<'PY' 2>&1
import contextlib, importlib.util, io, subprocess, sys, warnings
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

echo ""
echo "test_stats_templates: $PASS passed, $FAIL failed, $SKIPPED runtime checks SKIPPED"
[ "$FAIL" -eq 0 ]

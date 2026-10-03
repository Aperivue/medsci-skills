#!/usr/bin/env python3
"""Every worked example in calc-sample-size reproduces the number its reference package returns.

The skill's reference files carry a **Check** next to each formula: one realistic input and the
value an established package (pwr, gsDesign, kappaSize, ICC.Sample.Size, presize, powerMediation,
TrialSize, TOSTER, epiR, statsmodels, pmsampsize, pmvalsampsize) or the method's own published
worked example gives for it. The code blocks are set to that input. This test executes the blocks
themselves -- the text an agent copies -- and compares what they compute with the recorded value.

Why the blocks and not a re-implementation: until v6 the log-rank block returned 62 events where
gsDesign returns 247, the kappa block 20 subjects where kappaSize returns 74, and the ANOVA block
474 where pwr returns 159. Each was internally consistent; none had ever been compared with a
package. A test that re-typed the formulas would have agreed with them.

For each case the test finds the block (by file, section heading and language) that assigns the
output variable, overrides the named inputs on their own assignment lines (or prepends them when the
block has none), runs it, and compares. A case's `needle`, when given, must appear in the section
text, so the Check line a reader sees and the number tested cannot drift apart. Every Python/R block
in the checked sections must be exercised by at least one case.

Python cases always run; a missing Python module is a FAILURE, not a skip (CI must run them).
R cases run when `Rscript` and the block's `library()` packages are available, and are SKIPPED
otherwise with the reason printed. `--require-r` turns every R skip into a failure (use it locally
before a release that touches these files).

Usage:
    test_worked_examples.py [--root DIR] [--require-r] [--only SUBSTR]
"""

from __future__ import annotations

import argparse
import contextlib
import io
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

FORMULAS = "skills/calc-sample-size/references/formulas.md"
PRED = "skills/calc-sample-size/references/prediction_model_sample_size.md"
MULTI = "skills/calc-sample-size/references/multi_model_comparison_sample_size.md"
SEGM = "skills/calc-sample-size/references/segmentation_metric_sample_size.md"
ACCEPT = "skills/calc-sample-size/references/segmentation_acceptability_sample_size.md"
TEMPLATE = "skills/analyze-stats/references/templates/sample_size.R"


@dataclass
class Case:
    file: str
    section: str          # prefix of the "## " heading that owns the block
    var: str              # variable the block assigns; locates the block and is compared
    expected: float | None  # None -> the block must stop with `error` in its message
    source: str           # where the expected value comes from
    inputs: dict = field(default_factory=dict)
    langs: tuple = ("python", "r")
    needle: str | None = None
    tol: float = 0.0      # 0 -> exact equality
    r_expr: str | None = None   # R expression to report (default: var)
    error: str | None = None    # expected error text when no N can reach the target


T = FORMULAS
CASES = [
    # Test 1 -- Buderer: specificity uses 1 - prevalence; N is the larger of the two.
    Case(T, "Test 1:", "n_total", 490, "epiR::epi.ssdxsesp(0.85, 0.85, Py=0.6, epsilon=0.05, 'absolute') total.n",
         needle="**N = 490**"),
    Case(T, "Test 1:", "n_se", 327, "epiR se.n"),
    Case(T, "Test 1:", "n_total", 654, "epiR::epi.ssdxsesp(test=0.85, type='se', Py=0.3, epsilon=0.05, error='absolute')",
         inputs={"prevalence": 0.30, "sp_expected": 0.90}),
    # Test 2 -- Walter test (k matters) and Bonett precision.
    Case(T, "Test 2:", "n_icc_test", 24, "ICC.Sample.Size::calculateIccSampleSize(0.75, 0.5, k=3, tails=1)",
         needle="**24 subjects**"),
    Case(T, "Test 2:", "n_icc_test", 36, "ICC.Sample.Size::calculateIccSampleSize(0.75, 0.5, k=2, tails=1)",
         inputs={"n_raters": 2}),
    Case(T, "Test 2:", "n_icc_prec", 20, "Bonett 2002 worked example 19.2; presize::prec_icc(0.85, 4, conf.width=0.2)",
         needle="**20 subjects**"),
    Case(T, "Test 2:", "n_icc_prec", 79, "presize::prec_icc(0.75, 2, conf.width=0.2) (includes +5*rho)",
         inputs={"icc_expected": 0.75, "n_raters": 2}),
    Case(T, "Test 2:", "n_icc_prec", 52, "presize::prec_icc(0.75, 3, conf.width=0.2)",
         inputs={"icc_expected": 0.75, "n_raters": 3}),
    # Test 3 -- Donner & Eliasziw goodness-of-fit; prevalence matters.
    Case(T, "Test 3:", "n_kappa", 74, "kappaSize::PowerBinary(0.4, 0.7, props=0.5, raters=2)$N = 73.26",
         needle="**74 subjects**"),
    Case(T, "Test 3:", "n_kappa", 107, "kappaSize::PowerBinary(0.4, 0.7, props=0.2, raters=2)$N = 106.89",
         inputs={"prevalence": 0.20}),
    Case(T, "Test 3:", "n_kappa", 39, "kappaSize::PowerBinary(0.4, 0.7, props=0.5, raters=3)$N = 38.37",
         inputs={"n_raters": 3}, langs=("r",)),
    # Tests 4-6 -- unchanged formulas, now with a recorded check.
    Case(T, "Test 4:", "n_per_group", 162, "pwr::pwr.2p.test(ES.h(0.7, 0.55), power=0.8) n = 161.93",
         needle="**162 per group"),
    Case(T, "Test 5:", "n_mc", 120, "TrialSize::McNemar.Test(0.05, 0.2, psai=2.5, paid=0.35) = 119.71",
         needle="**120 pairs**"),
    Case(T, "Test 6:", "n_per_group", 64, "pwr::pwr.t.test(d=0.5, power=0.8) n = 63.77",
         needle="**64 per group**"),
    # Test 7 -- Schoenfeld events with the allocation term; patients under accrual + dropout.
    Case(T, "Test 7:", "n_events", 247, "gsDesign::nEvents(hr=0.7, alpha=0.05, beta=0.2, sided=2) = 246.79",
         needle="**247 events**"),
    Case(T, "Test 7:", "n_events", 278, "gsDesign::nEvents(..., ratio=2) = 277.64",
         inputs={"p_alloc": 2 / 3}),
    Case(T, "Test 7:", "n_total", 508, "gsDesign::nSurv(..., method='Schoenfeld') n = 506.28 -> 254 + 254",
         needle="**254 per arm, 508 total**"),
    Case(T, "Test 7:", "n_total", 594, "gsDesign::nSurv(..., ratio=2, method='Schoenfeld') n = 593.65 -> 396 + 198",
         inputs={"p_alloc": 2 / 3}),
    # Test 7 -- the same study entered in years must give the same N (eta per time_unit, not per month).
    Case(T, "Test 7:", "n_total", 508, "same study as the 508 Check in years; eta = -log(0.95)/1 per year",
         inputs={"time_unit": "years", "median_ctrl": 2, "accrual_time": 1, "follow_up": 2}),
    Case(T, "Test 7:", "n_total", 606, "closed form + numerical integration, 20%/yr dropout, months",
         inputs={"annual_dropout": 0.20}),
    Case(T, "Test 7:", "n_total", 606, "same 20%/yr study in years (a per-month eta gave 490, ~71% power)",
         inputs={"time_unit": "years", "median_ctrl": 2, "accrual_time": 1, "follow_up": 2,
                 "annual_dropout": 0.20}),
    Case(T, "Test 7:", "n_total", None, "an unrecognised time unit stops the block",
         inputs={"time_unit": "days"}, error="not recognised"),
    # Test 8 -- statsmodels returns TOTAL N.
    Case(T, "Test 8:", "n_total", 159, "pwr::pwr.anova.test(k=3, f=0.25, power=0.8) n = 52.40 per group",
         needle="**53 per group, 159 total**"),
    # Test 9 -- Hsieh continuous vs binary predictor.
    Case(T, "Test 9:", "n_peduzzi", 500, "arithmetic: 10 x 10 / 0.20"),
    Case(T, "Test 9:", "n_hsieh_con", 103, "powerMediation::SSizeLogisticCon(0.2, 2)", needle="**103**"),
    Case(T, "Test 9:", "n_hsieh_bin", 398, "powerMediation::SSizeLogisticBin(0.1, 0.2, B=0.5)", needle="**398**"),
    Case(T, "Test 9:", "n_hsieh_bin", 575, "powerMediation::SSizeLogisticBin(0.1, 0.2, B=0.2)",
         inputs={"exposure_prev": 0.2}),
    Case(T, "Test 9:", "n_hsieh_bin", 424, "powerMediation::SSizeLogisticBin(0.1456832, 0.2543168, B=0.5)",
         inputs={"p_unexposed": 0.1456832, "p_exposed": 0.2543168}),
    # Test 10 -- directional NI; TOST joint power.
    Case(T, "Test 10:", "n_ni_prop", 76, "TrialSize::TwoSampleProportion.NIS(0.025, 0.2, 0.90, 0.85, 1, 0.05, -0.10) = 75.87",
         needle="**76 per group**"),
    Case(T, "Test 10:", "n_ni_prop", 201, "TrialSize::TwoSampleProportion.NIS(0.025, 0.2, 0.85, 0.85, 1, 0, -0.10) = 200.15",
         inputs={"p_new": 0.85}, needle="**201 per group**"),
    Case(T, "Test 10:", "n_ni_prop", 903, "TrialSize::TwoSampleProportion.NIS(0.025, 0.2, 0.80, 0.85, 1, -0.05, -0.10) = 902.62",
         inputs={"p_new": 0.80}),
    Case(T, "Test 10:", "n_ni_cont", 63, "TrialSize::TwoSampleMean.NIS(0.025, 0.2, 1, 1, 0, -0.5) = 62.79",
         needle="**63 per group**"),
    Case(T, "Test 10:", "n_ni_cont", None, "true_diff -1 lies inside H0 (<= -0.5): no N reaches 80% power",
         inputs={"true_diff": -1}, error="beyond the non-inferiority margin"),
    Case(T, "Test 10:", "n_ni_prop", None, "p_new 0.70 vs 0.85 lies inside H0 (<= -0.10): no N reaches 80% power",
         inputs={"p_new": 0.70}, error="beyond the non-inferiority margin"),
    Case(T, "Test 10:", "n_eq_cont", 70, "TOSTER::power_t_TOST(delta=0, sd=1, eqb=0.5, alpha=0.05, power=0.8) n = 69.20",
         needle="**70 per group**"),
    Case(T, "Test 10:", "n_eq_cont", 82, "TOSTER::power_t_TOST(delta=0.1, sd=1, eqb=0.5, ...) n = 81.44",
         inputs={"true_diff": 0.1}),
    Case(T, "Test 10:", "n_eq_cont", 4947, "TOSTER::power_t_TOST(delta=0.45, sd=1, eqb=0.5, ...) n = 4946.72 "
         "(the non-central t CDF returned NaN at n = 3073 and stopped the search there)",
         inputs={"true_diff": 0.45}),
    Case(T, "Test 10:", "n_eq_cont", None, "true_diff 0.6 lies outside +/-0.5: no N reaches 80% power",
         inputs={"true_diff": 0.6}, error="outside the equivalence margin"),
    Case(T, "Test 10:", "n_eq_prop", 219, "TrialSize::TwoSampleProportion.Equivalence(0.05, 0.2, 0.85, 0.85, 1, 0, 0.10) = 218.38",
         needle="**219 per group**"),
    # Test 11 -- arithmetic.
    Case(T, "Test 11:", "n_total", 320, "arithmetic: 8 x 10 / 0.25", needle="**320**"),
    Case(T, "Test 11:", "n_adj", 356, "arithmetic: 320 / 0.9"),
    # Tests 12-13 -- Riley (R only; the packages are the method).
    Case(PRED, "Development sample size", "dev_bin", 1556,
         "pmsampsize(type='b', cstatistic=0.78, parameters=30, prevalence=0.2) 1.1.3",
         langs=("r",), r_expr="dev_bin$sample_size", needle="**1556**"),
    Case(PRED, "Development sample size", "dev_surv", 5249,
         "pmsampsize(type='s', csrsquared=0.05, parameters=30, rate=0.08, timepoint=5, meanfup=4.2) 1.1.3",
         langs=("r",), r_expr="dev_surv$sample_size", needle="**5249**"),
    Case(PRED, "External-validation sample size", "val_bin", 2958,
         "pmvalsampsize(type='b', prevalence=0.2, cstatistic=0.78, lpnormal=c(-1.75, 1.22), cstatciwidth=0.1) 0.1.0",
         langs=("r",), r_expr="val_bin$sample_size", needle="**2958**"),
    # Tests 15-17 -- paired difference, precision, acceptability.
    Case(MULTI, "Metric-specific paired sizing", "n_pairs", 52,
         "pwr::pwr.t.test(d=0.4, power=0.8, type='paired') n = 51.01; statsmodels TTestPower",
         needle="**52 pairs**"),
    Case(MULTI, "Metric-specific paired sizing", "n_pairs_normal", 50, "normal approximation ((1.96+0.84)*0.05/0.02)^2 = 49.05"),
    Case(SEGM, "Precision sizing", "n_prec", 97, "(1.96 * 0.10 / 0.02)^2 = 96.04; presize::prec_mean (t) = 98.47",
         langs=("python",), needle="**97**"),
    Case(ACCEPT, "The endpoint is a proportion", "n_accept", 139,
         "presize::prec_prop(p=0.9, conf.width=0.1, method='wald') n = 138.29",
         langs=("python",), needle="**139 cases**"),
    Case(ACCEPT, "The endpoint is a proportion", "n_accept", 385,
         "presize::prec_prop(p=0.5, conf.width=0.1, method='wald') n = 384.15",
         inputs={"p_accept": 0.5}, langs=("python",)),
    Case(ACCEPT, "Bounding a catastrophic", "upper_bound", 0.009936,
         "binom.test(0, 300, alternative='less')$conf.int[2] = 0.009936",
         langs=("python",), tol=5e-6),
    Case(ACCEPT, "Ratings by several readers", "de_crossed", 6.95,
         "1 + (m-1)*rho_case + (n-1)*rho_reader; Monte Carlo 20,000 studies = 7.06 (MC SE 0.07)",
         langs=("python",), tol=1e-9, needle="**6.95**"),
]

# The whole analyze-stats template: run once, read its CSV.
TEMPLATE_EXPECT = [
    # (row Analysis, column, expected, source)
    ("Diagnostic accuracy", "N_total", 654, "epiR::epi.ssdxsesp(test=0.85, type='se', Py=0.3, epsilon=0.05, error='absolute')"),
    ("ICC agreement", "N_required", 36, "ICC.Sample.Size::calculateIccSampleSize(0.75, 0.5, k=2, tails=1)"),
    ("Kappa agreement", "N_required", 74, "kappaSize::PowerBinary(0.4, 0.7, props=0.5, raters=2)"),
    ("Log-rank test", "N_events", 170, "gsDesign::nEvents(hr=0.65, alpha=0.05, beta=0.2, sided=2) = 169.18"),
    ("Log-rank test", "N_total", 356, "gsDesign::nSurv(lambdaC=log(2)/24, hr=0.65, R=12, T=36, minfup=24, eta=-log(0.95)/12, Schoenfeld) n = 355.40 -> 178 + 178"),
]

FENCE = re.compile(r"^```(python|r)[ \t]*\n(.*?)^```", re.M | re.S)


def sections(text: str) -> dict[str, str]:
    out, head, buf = {}, None, []
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            if head is not None:
                out[head] = "".join(buf)
            head, buf = line[3:].strip(), []
        elif head is not None:
            buf.append(line)
    if head is not None:
        out[head] = "".join(buf)
    return out


def find_section(secs: dict[str, str], prefix: str) -> tuple[str, str]:
    hits = [(h, b) for h, b in secs.items() if h.startswith(prefix)]
    if len(hits) != 1:
        raise LookupError(f"{len(hits)} sections start with {prefix!r}")
    return hits[0]


def blocks(body: str, lang: str) -> list[str]:
    return [m.group(2) for m in FENCE.finditer(body) if m.group(1) == lang]


def assigns(block: str, var: str, lang: str) -> bool:
    op = r"<-" if lang == "r" else r"=(?!=)"
    return re.search(rf"^\s*{re.escape(var)}\s*{op}", block, re.M) is not None


def literal(v, lang: str) -> str:
    if isinstance(v, bool):
        return ("TRUE" if v else "FALSE") if lang == "r" else repr(v)
    return repr(v)


def override(block: str, inputs: dict, lang: str) -> str:
    op = "<-" if lang == "r" else "="
    pre = []
    for name, val in inputs.items():
        pat = re.compile(rf"^(\s*){re.escape(name)}\s*{re.escape(op)}.*$", re.M)
        new, n = pat.subn(lambda m: f"{m.group(1)}{name} {op} {literal(val, lang)}", block, count=1)
        if n:
            block = new
        else:
            pre.append(f"{name} {op} {literal(val, lang)}")
    return "\n".join(pre + [block])


def run_python(code: str, var: str) -> float:
    ns: dict = {"__name__": "__worked_example__"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(code, "<worked-example>", "exec"), ns)  # noqa: S102 - the repo's own code blocks
    if var not in ns:
        raise NameError(f"{var} is not defined after the block ran")
    return float(ns[var])


_R_PKG_CACHE: dict[str, bool] = {}


def r_missing(code: str) -> list[str]:
    pkgs = sorted(set(re.findall(r"^\s*library\(([\w.]+)\)", code, re.M)))
    need = [p for p in pkgs if p not in _R_PKG_CACHE]
    if need:
        vec = ", ".join(f'"{p}"' for p in need)
        out = subprocess.run(
            ["Rscript", "-e", f"x <- sapply(c({vec}), requireNamespace, quietly = TRUE); cat(paste(names(x), x))"],
            capture_output=True, text=True, timeout=120)
        for tok in re.findall(r"([\w.]+) (TRUE|FALSE)", out.stdout):
            _R_PKG_CACHE[tok[0]] = tok[1] == "TRUE"
    return [p for p in pkgs if not _R_PKG_CACHE.get(p, False)]


def run_r(code: str, expr: str, workdir: Path) -> float:
    script = workdir / "block.R"
    script.write_text(code + f'\ncat(sprintf("\\n__RESULT__=%.10g\\n", as.numeric({expr})))\n')
    out = subprocess.run(["Rscript", str(script)], capture_output=True, text=True, timeout=600, cwd=workdir)
    m = re.search(r"__RESULT__=(\S+)", out.stdout)
    if out.returncode != 0 or not m:
        raise RuntimeError(f"Rscript exit {out.returncode}: {(out.stderr or out.stdout).strip()[-400:]}")
    return float(m.group(1))


def close(got: float, want: float, tol: float) -> bool:
    return got == want if tol == 0 else math.isclose(got, want, abs_tol=tol)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--root", type=Path, default=REPO, help="tree to test (default: this checkout)")
    ap.add_argument("--require-r", action="store_true", help="an R case that cannot run is a failure")
    ap.add_argument("--only", default="", help="run cases whose file/section/var contains this")
    args = ap.parse_args()

    have_r = shutil.which("Rscript") is not None
    passed = failed = skipped = python_ran = 0
    skip_reasons: dict[str, int] = {}
    covered: set[tuple[str, str, str, int]] = set()
    texts: dict[str, str] = {}

    def fail(msg: str) -> None:
        nonlocal failed
        failed += 1
        print(f"  FAIL: {msg}")

    def skip(msg: str) -> None:
        nonlocal skipped, failed
        if args.require_r:
            fail(f"{msg} (--require-r)")
            return
        skipped += 1
        skip_reasons[msg] = skip_reasons.get(msg, 0) + 1

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for c in CASES:
            label = f"{Path(c.file).name} § {c.section} {c.var}"
            if args.only and args.only not in f"{c.file} {c.section} {c.var}":
                continue
            path = args.root / c.file
            if c.file not in texts:
                texts[c.file] = path.read_text(encoding="utf-8") if path.exists() else ""
            try:
                head, body = find_section(sections(texts[c.file]), c.section)
            except LookupError as e:
                fail(f"{label}: {e}")
                continue
            if c.needle and c.needle not in body:
                fail(f"{label}: the section's Check text does not contain {c.needle!r}")
            for lang in c.langs:
                tag = f"{label} [{lang}] {c.inputs or ''}".rstrip()
                bl = blocks(body, lang)
                idx = next((i for i, b in enumerate(bl) if assigns(b, c.var, lang)), None)
                if idx is None:
                    fail(f"{tag}: no {lang} block in '{head}' assigns {c.var}")
                    continue
                covered.add((c.file, head, lang, idx))
                code = override(bl[idx], c.inputs, lang)
                try:
                    if lang == "python":
                        python_ran += 1
                        got = run_python(code, c.var)
                    else:
                        if not have_r:
                            skip("Rscript not on PATH")
                            continue
                        missing = r_missing(code)
                        if missing:
                            skip(f"R package(s) not installed: {', '.join(missing)}")
                            continue
                        got = run_r(code, c.r_expr or c.var, work)
                except Exception as e:  # noqa: BLE001 - report any failure of the block itself
                    if c.error and c.error in str(e):
                        passed += 1
                        print(f"  PASS: {tag} stops: {c.error}")
                    else:
                        fail(f"{tag}: block raised {type(e).__name__}: {e}")
                    continue
                if c.error:
                    fail(f"{tag} = {got:g}, expected it to stop with {c.error!r} ({c.source})")
                elif close(got, c.expected, c.tol):
                    passed += 1
                    print(f"  PASS: {tag} = {got:g}")
                else:
                    fail(f"{tag} = {got:g}, expected {c.expected:g} ({c.source})")

        # Every code block in a checked section is exercised by at least one case.
        if not args.only:
            for file in sorted({c.file for c in CASES}):
                secs = sections(texts.get(file, ""))
                owned = {c.section for c in CASES if c.file == file}
                for head, body in secs.items():
                    if not any(head.startswith(p) for p in owned):
                        continue
                    for lang in ("python", "r"):
                        for i, _ in enumerate(blocks(body, lang)):
                            if (file, head, lang, i) not in covered:
                                fail(f"{Path(file).name} § {head}: {lang} block #{i + 1} has no worked-example case")

        # The analyze-stats sample_size.R template, run end to end.
        if not args.only or args.only in TEMPLATE:
            tpl = args.root / TEMPLATE
            if not have_r:
                skip("Rscript not on PATH")
            elif r_missing("library(pwr)\nlibrary(epiR)\n"):
                skip("R package(s) not installed: pwr/epiR (sample_size.R would try to install them)")
            else:
                out = subprocess.run(["Rscript", str(tpl)], capture_output=True, text=True, timeout=600, cwd=work)
                csv = work / "sample_size_results.csv"
                if out.returncode != 0 or not csv.exists():
                    fail(f"sample_size.R exit {out.returncode}: {out.stderr.strip()[-400:]}")
                else:
                    import csv as _csv
                    rows = {r["Analysis"]: r for r in _csv.DictReader(csv.open())}
                    for analysis, col, want, src in TEMPLATE_EXPECT:
                        raw = rows.get(analysis, {}).get(col)
                        try:
                            got = float(raw)
                        except (TypeError, ValueError):
                            fail(f"sample_size.R {analysis}/{col}: missing ({raw!r})")
                            continue
                        if got == want:
                            passed += 1
                            print(f"  PASS: sample_size.R {analysis}/{col} = {got:g}")
                        else:
                            fail(f"sample_size.R {analysis}/{col} = {got:g}, expected {want} ({src})")

    for why, n in skip_reasons.items():
        print(f"  SKIP x{n}: {why}")
    print(f"\ntest_worked_examples: {passed} passed, {failed} failed, {skipped} skipped")
    if python_ran == 0:
        print("  FAIL: no Python worked example ran")
        return 1
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

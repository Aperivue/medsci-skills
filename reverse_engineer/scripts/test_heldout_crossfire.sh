#!/usr/bin/env bash
# Self-test for the held-out measurement instrument and the development firewall that protects it.
#
# The real corpus is gitignored published papers, so CI can never run the real measurement. What CI
# CAN prove is that the instrument is honest about what it measured: that it withholds a
# false-positive rate it has no labels for, that it names a collapsed corpus instead of counting it,
# that a partial run cannot enter the trend series, and that a held-out source authorizes nothing.
#
# Network-free. Builds its own synthetic corpus in a temp dir.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$HERE/heldout_crossfire.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# The instrument needs a detector that reliably fires on a stub paper so the fire / worksheet /
# disposition paths are exercised. If this detector is ever renamed this test fails loudly, which
# is the intent: a test that silently stops exercising the fire path is worse than no test.
DET="check_disclosure_availability"

fail() { echo "FAIL: $*" >&2; exit 1; }

mkdir -p "$TMP/corpus"
cat > "$TMP/corpus/alpha_2024_ct.md" <<'EOF'
# Detection on CT
## Methods
Patients were split at the patient level; the reference standard was consensus of two readers.
## Results
Sensitivity was 0.88 (95% CI 0.83-0.92).
EOF
# A deliberate near-duplicate: same declared design profile as alpha. The instrument must call this
# one pattern measured twice, not two observations.
cp "$TMP/corpus/alpha_2024_ct.md" "$TMP/corpus/beta_2024_ct.md"

cat > "$TMP/manifest.json" <<'EOF'
{"schema_version": 1, "records": [
  {"record_id": "alpha_2024_ct", "split": "heldout", "frozen_at": "2026-07-25",
   "coverage": {"design": "retrospective_diagnostic", "modality": "ct"}},
  {"record_id": "beta_2024_ct", "split": "heldout", "frozen_at": "2026-07-25",
   "coverage": {"design": "retrospective_diagnostic", "modality": "ct"}}
]}
EOF

echo "== 1. measurement runs, withholds an unlabelled FP rate, names the collapse =="
OUT="$(python3 "$RUNNER" --corpus "$TMP/corpus" --manifest "$TMP/manifest.json" --only "$DET" \
        --worksheet "$TMP/ws.csv" --ledger "$TMP/ledger.jsonl" --out "$TMP/run.json" 2>&1)" \
  || fail "runner exited non-zero (it is an instrument and must never block)"

grep -q "FALSE-POSITIVE RATE: WITHHELD" <<<"$OUT" \
  || fail "printed a false-positive rate with zero labels — a fire on an accepted paper is not a FP"
grep -q "COLLAPSED: alpha_2024_ct, beta_2024_ct" <<<"$OUT" \
  || fail "did not flag two identical design profiles as a collapsed corpus"
grep -q "LEDGER SKIPPED" <<<"$OUT" \
  || fail "--only run was not kept out of the trend ledger"
[ ! -s "$TMP/ledger.jsonl" ] || fail "a partial (--only) run was written into the trend series"

python3 - "$TMP/run.json" <<'PY' || exit 1
import json, sys
d = json.load(open(sys.argv[1]))
assert d["n_papers"] == 2, d["n_papers"]
assert d["pairs_ran"] == 2, d["pairs_ran"]
assert d["pairs_fired"] == 2, "the fire path was not exercised: %r" % d["pairs_fired"]
assert d["false_positive_rate"] is None, "FP rate must be null without labels"
assert d["separation"]["distinct_profiles"] == 1, d["separation"]
assert d["separation"]["collapsed"], "collapse not recorded in the artifact"
v = {f["verdict"] for f in d["fires"]}
assert v and all(x and not set(x) <= set("=- ") for x in v), \
    "worksheet verdicts are separator rules, not labelable verdicts: %r" % v
# One exit carries several claims, and each must be labelable on its own merits: the pilot's
# systematic-review fire asserted a true omission AND a false one inside a single exit.
assert d["n_findings"] > d["pairs_fired"], \
    "findings not split out of fires: %r findings, %r fires" % (d["n_findings"], d["pairs_fired"])
assert all(f.get("code") for f in d["findings"]), "a finding with no code cannot be labelled"
# The bar is part of the measurement. A rate whose bar is not recorded is not reportable.
assert d["bar"] == "strict", d["bar"]
assert all(v["bar"] in ("strict", "default") for v in d["per_detector"].values())
# Every detector sits in exactly ONE status bucket. The old summary managed to report 33 run AND
# 10 skipped out of 42, by counting a truncated detector in both.
assert d["n_detectors_full"] + d["n_detectors_partial"] + d["n_detectors_never_ran"] \
    == len(d["per_detector"]), d
PY

echo "== 2. labelled dispositions produce a rate, at FINDING level =="
python3 - "$TMP/ws.csv" "$TMP/disp.csv" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
assert len(rows) >= 4, "expected finding-level rows (>=2 claims x 2 papers), got %r" % len(rows)
assert "code" in rows[0], "worksheet is not finding-level: %r" % list(rows[0])
# Same claims on both papers, labelled oppositely, so the rate is not degenerate either way.
for r in rows:
    r["disposition"] = "spurious" if r["paper"] == "alpha_2024_ct" else "real"
with open(sys.argv[2], "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["paper", "detector", "code", "severity", "verdict",
                                       "disposition", "note"])
    w.writeheader(); w.writerows(rows)
PY
python3 "$RUNNER" --corpus "$TMP/corpus" --manifest "$TMP/manifest.json" --only "$DET" \
    --dispositions "$TMP/disp.csv" 2>&1 | grep -q "FALSE-POSITIVE RATE: 0.500" \
  || fail "finding-level dispositions did not yield the expected half-spurious rate"

echo "== 2b. a pair-level label file (no code column) still labels every finding =="
python3 - "$TMP/ws.csv" "$TMP/disp_pairlevel.csv" <<'PY'
import csv, sys
seen, out = set(), []
for r in csv.DictReader(open(sys.argv[1])):
    if r["paper"] in seen:
        continue
    seen.add(r["paper"])
    out.append({"paper": r["paper"], "detector": r["detector"], "verdict": "", "note": "",
                "disposition": "spurious" if r["paper"] == "alpha_2024_ct" else "real"})
with open(sys.argv[2], "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["paper", "detector", "verdict", "disposition", "note"])
    w.writeheader(); w.writerows(out)
PY
python3 "$RUNNER" --corpus "$TMP/corpus" --manifest "$TMP/manifest.json" --only "$DET" \
    --dispositions "$TMP/disp_pairlevel.csv" 2>&1 | grep -q "coverage 100%" \
  || fail "a pre-findings (pair-level) label file no longer covers the findings it labelled"

echo "== 3. an unbacked paper is excluded, not silently measured =="
cp "$TMP/corpus/alpha_2024_ct.md" "$TMP/corpus/gamma_undeclared.md"
python3 "$RUNNER" --corpus "$TMP/corpus" --manifest "$TMP/manifest.json" --only "$DET" 2>&1 \
  | grep -q "EXCLUDED (no heldout manifest record): gamma_undeclared.md" \
  || fail "a paper with no heldout manifest record was not excluded and named"
rm "$TMP/corpus/gamma_undeclared.md"

echo "== 3b. a RELATIVE --corpus still reaches the detectors =="
# Detectors run with cwd inside a sandbox, so a relative corpus path resolves against a directory
# they do not share. The first real run was invoked exactly this way: every detector answered
# "manuscript not found", and the harness relabelled that as a missing-input skip — 34 of 42
# detectors silently unmeasured. Every synthetic fixture used absolute paths, so nothing caught it.
# This case runs from inside $TMP on purpose.
REL_OUT="$(cd "$TMP" && python3 "$RUNNER" --corpus ./corpus --only "$DET" 2>&1)" \
  || fail "relative --corpus made the runner exit non-zero"
grep -qE "pairs +: 2 " <<<"$REL_OUT" \
  || fail "relative --corpus ran 0 pairs — detectors were handed a path they cannot resolve"

echo "== 3c. the SEVERITY BAR: a detector that exits 0 on its own blocker must not read as clean =="
# Paid for on 2026-07-25. 32 of 42 manuscript detectors document exit 1 as conditional on --strict:
# without it they PRINT a Major finding and exit 0, and the first version of this instrument read
# only the exit code. Re-running the pilot corpus at both bars gave 5 fires vs 45, and seven
# detectors recorded as "observed clean" fired the moment they were allowed to speak.
# check_placeholders is the demonstration: it prints a warn-severity finding for a bare numeric
# citation and exits 0, and only escalates to exit 1 under --strict. Note what this fixture also
# shows — that the strict bar is not free. `--strict` means "gate Majors" in most detectors and
# "promote advisories" in some, so a published paper using Vancouver citations fires at the strict
# bar for a claim that is perfectly TRUE. That is why findings carry a severity tier and why the
# labelling rule is correctness, not usefulness.
mkdir -p "$TMP/bar"
cat > "$TMP/bar/paper_with_marker.md" <<'EOF'
# A study
## Methods
We enrolled patients consecutively, as described previously [1].
EOF
cat > "$TMP/bar_manifest.json" <<'EOF'
{"schema_version": 1, "records": [
  {"record_id": "paper_with_marker", "split": "heldout", "frozen_at": "2026-07-25",
   "coverage": {"design": "unspecified"}}
]}
EOF
python3 "$RUNNER" --corpus "$TMP/bar" --manifest "$TMP/bar_manifest.json" \
  --only check_placeholders --bar default --out "$TMP/bar_default.json" >/dev/null 2>&1 \
  || fail "runner exited non-zero on the bar fixture"
python3 "$RUNNER" --corpus "$TMP/bar" --manifest "$TMP/bar_manifest.json" \
  --only check_placeholders --bar strict --out "$TMP/bar_strict.json" >/dev/null 2>&1 \
  || fail "runner exited non-zero on the bar fixture"
python3 - "$TMP/bar_default.json" "$TMP/bar_strict.json" <<'PY' || exit 1
import json, sys
lo, hi = (json.load(open(p)) for p in sys.argv[1:3])
assert lo["pairs_fired"] == 0, "fixture no longer demonstrates the bar: %r" % lo["pairs_fired"]
assert hi["pairs_fired"] == 1, \
    "the strict bar did not surface a finding the default bar swallowed: %r" % hi["pairs_fired"]
assert hi["per_detector"]["check_placeholders"]["bar"] == "strict", hi["per_detector"]
PY

echo "== 3d. a per-paper skip must NOT abandon the rest of the corpus =="
# Also paid for on 2026-07-25. Exit 2 means both "you did not give me the flags I need" (about the
# DETECTOR) and "this paper has no section for me" (about the PAPER). The first version treated
# both as a detector-level skip and broke out of the paper loop, so check_credit_integrity was
# measured on 5 of 12 papers in FILENAME ORDER and the remaining 7 — holding three more fires —
# were never measured. The first paper here is the one that makes it exit 2, on purpose.
mkdir -p "$TMP/skip"
cat > "$TMP/skip/aaa_no_credit_section.md" <<'EOF'
# A study
## Methods
Patients were enrolled consecutively.
EOF
cat > "$TMP/skip/zzz_unresolvable_initials.md" <<'EOF'
# A study

Jane A. Doe, Robert B. Smith

## Author contributions
J.A.D.: Conceptualization; Methodology. R.B.S.: Writing – original draft. Q.Z.T.: Supervision.
EOF
cat > "$TMP/skip_manifest.json" <<'EOF'
{"schema_version": 1, "records": [
  {"record_id": "aaa_no_credit_section", "split": "heldout", "frozen_at": "2026-07-25",
   "coverage": {"design": "a"}},
  {"record_id": "zzz_unresolvable_initials", "split": "heldout", "frozen_at": "2026-07-25",
   "coverage": {"design": "b"}}
]}
EOF
python3 "$RUNNER" --corpus "$TMP/skip" --manifest "$TMP/skip_manifest.json" \
  --only check_credit_integrity --out "$TMP/skip.json" >/dev/null 2>&1 \
  || fail "runner exited non-zero on the truncation fixture"
python3 - "$TMP/skip.json" <<'PY' || exit 1
import json, sys
d = json.load(open(sys.argv[1]))
pd = d["per_detector"]["check_credit_integrity"]
assert pd["not_applicable"] == 1, "the self-declared skip was not classified per paper: %r" % pd
assert d["pairs_fired"] == 1, \
    "a skip on the FIRST paper swallowed the fire on the second: %r" % d["pairs_fired"]
assert pd["status"] == "partial", pd["status"]
assert pd["measured"] == 1, pd
assert d["pairs_unobserved"] == 1, d["pairs_unobserved"]
PY

echo "== 4. an empty corpus refuses to emit a rate =="
mkdir -p "$TMP/empty"
if python3 "$RUNNER" --corpus "$TMP/empty" --only "$DET" >/dev/null 2>&1; then
  fail "a corpus with zero papers produced a measurement instead of refusing"
fi

echo "== 5. development firewall: a held-out source authorizes nothing =="
python3 - "$HERE/distill.py" <<'PY' || exit 1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("distill", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
enums = m.load_schema_enums()

base = dict(record_id="x_2024", source_url="https://e.org/x", source_type="oa_article",
            license="CC-BY-4.0", license_url="https://creativecommons.org/licenses/by/4.0/",
            retrieved_at="2026-07-25", verbatim_allowed=False,
            public_reuse_policy="synthetic_only")

held = dict(base, split="heldout", frozen_at="2026-07-25")
ok, why = m.authorize(held, "synthetic")
assert not ok, "a held-out source authorized synthetic reuse — the measurement set can be trained on"
assert "HELD-OUT" in why, why
for mode in ("paraphrase", "verbatim"):
    assert not m.authorize(held, mode)[0], mode

# Negative fixture: the firewall must not block ordinary train-split work.
assert m.authorize(dict(base, split="train"), "synthetic")[0], "firewall blocked a train source"
assert m.authorize(base, "synthetic")[0], "firewall blocked a source with no split declared"

# A held-out claim without a freeze date is unverifiable and must not validate.
errs = m.validate_record(dict(base, split="heldout"), enums)
assert any("frozen_at" in e for e in errs), errs
assert not m.validate_record(held, enums), m.validate_record(held, enums)
assert any("split" in e for e in m.validate_record(dict(base, split="sometimes"), enums))
PY

echo "PASS: held-out instrument honest about labels, collapse, exclusions, trend; firewall closed."

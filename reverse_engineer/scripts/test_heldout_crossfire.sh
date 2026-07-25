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
PY

echo "== 2. labelled dispositions produce a rate =="
python3 - "$TMP/ws.csv" "$TMP/disp.csv" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
assert len(rows) == 2, rows
for r, d in zip(rows, ["spurious", "real"]):
    r["disposition"] = d
with open(sys.argv[2], "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["paper", "detector", "verdict", "disposition", "note"])
    w.writeheader(); w.writerows(rows)
PY
python3 "$RUNNER" --corpus "$TMP/corpus" --manifest "$TMP/manifest.json" --only "$DET" \
    --dispositions "$TMP/disp.csv" 2>&1 | grep -q "FALSE-POSITIVE RATE: 0.500" \
  || fail "labelled dispositions did not yield the expected 1 spurious / 2 decided rate"

echo "== 3. an unbacked paper is excluded, not silently measured =="
cp "$TMP/corpus/alpha_2024_ct.md" "$TMP/corpus/gamma_undeclared.md"
python3 "$RUNNER" --corpus "$TMP/corpus" --manifest "$TMP/manifest.json" --only "$DET" 2>&1 \
  | grep -q "EXCLUDED (no heldout manifest record): gamma_undeclared.md" \
  || fail "a paper with no heldout manifest record was not excluded and named"
rm "$TMP/corpus/gamma_undeclared.md"

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

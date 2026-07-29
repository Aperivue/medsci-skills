#!/usr/bin/env bash
# Regression test: an INFERRED denominator must earn its use.
#
# The most common table in clinical research is a Table 1 of independent binary characteristics with
# N stated in the CAPTION. It declares no column `n = N` and has no Total row, so the checker fell
# through to summing the column's counts — 79 + 53 + 40 + 26 = 198 for a study of 132 — and then
# accused all four correct cells of bad arithmetic, each with a specific wrong replacement
# percentage, at MAJOR, exit 1 under --strict. A gate that reds a correct submission and tells the
# author to change a right number to a wrong one is worse than one that stays quiet.
#
# Gating on `is_partition` is NOT the fix and this test pins that: that flag is derived from the
# printed percentages summing to ~100, so a partition containing a wrong percentage stops looking
# like a partition and the check would go silent on the very error it exists to catch. The rule is
# instead that an inferred denominator reconciling NOTHING is the wrong denominator, while a
# denominator the author DECLARED is never second-guessed.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
D="$REPO_ROOT/skills/self-review/scripts/check_table_percentages.py"
WORK="$(mktemp -d -t table_percent_test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-50s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-50s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

rc_of() {  # rc_of <file> -> exit code, no pipe between the command and $?
  python3 "$D" --manuscript "$WORK/$1" --strict > "$WORK/$1.out" 2>&1
  echo $?
}
majors() { grep -c '^\[MAJOR\]' "$WORK/$1.out" || true; }
has_info() { grep -q 'PERCENT_DENOM_UNKNOWN' "$WORK/$1.out" && echo yes || echo no; }

# 1. The real-world false positive: caption N, independent binary rows, every percentage correct.
cat > "$WORK/caption_n.md" <<'EOF'
## Results

**Table 1.** Baseline characteristics of the 132 enrolled patients.

| Characteristic | Value |
|---|---|
| Male sex | 79 (59.8%) |
| Hypertension | 53 (40.2%) |
| Diabetes | 40 (30.3%) |
| Current smoker | 26 (19.7%) |
EOF

# 2. A genuine partition with one wrong percentage. The count-sum IS the denominator here and
#    reconciles 2 of 3 rows, so the wrong one must still be caught.
cat > "$WORK/partition_bad.md" <<'EOF'
## Results

**Table 2.** Tumour stage distribution.

| Stage | n (%) |
|---|---|
| I | 40 (99.0%) |
| II | 30 (30.0%) |
| III | 30 (30.0%) |
EOF

# 3. A correct partition: silent.
cat > "$WORK/partition_ok.md" <<'EOF'
## Results

**Table 3.** Tumour stage distribution.

| Stage | n (%) |
|---|---|
| I | 40 (40.0%) |
| II | 30 (30.0%) |
| III | 30 (30.0%) |
EOF

# 4. A DECLARED denominator that the arithmetic contradicts. Never second-guessed.
cat > "$WORK/declared_bad.md" <<'EOF'
## Results

**Table 4.** Characteristics.

| Characteristic | Value (n = 132) |
|---|---|
| Male sex | 79 (75.0%) |
EOF

echo "==== the false positive this fixes ===="
ck "caption-N Table 1: exit 0"            0   "$(rc_of caption_n.md)"
ck "caption-N Table 1: zero MAJOR"        0   "$(majors caption_n.md)"
ck "caption-N Table 1: says why (INFO)"   yes "$(has_info caption_n.md)"

echo "==== NEGATIVE CONTROLS — the check must still bite ===="
ck "partition with a wrong %: exit 1"     1   "$(rc_of partition_bad.md)"
ck "partition with a wrong %: 1 MAJOR"    1   "$(majors partition_bad.md)"
ck "declared n= contradicted: exit 1"     1   "$(rc_of declared_bad.md)"
ck "declared n= contradicted: 1 MAJOR"    1   "$(majors declared_bad.md)"
ck "declared n= is never downgraded"      no  "$(has_info declared_bad.md)"

echo "==== a correct partition stays silent ===="
ck "correct partition: exit 0"            0   "$(rc_of partition_ok.md)"
ck "correct partition: no findings at all" 0  "$(majors partition_ok.md)"
ck "correct partition: no INFO either"    no  "$(has_info partition_ok.md)"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || { for f in caption_n partition_bad declared_bad partition_ok; do
    echo "--- $f"; cat "$WORK/$f.md.out"; done; exit 1; }
echo "OK: an inferred denominator must reconcile something; a declared one is taken at its word."

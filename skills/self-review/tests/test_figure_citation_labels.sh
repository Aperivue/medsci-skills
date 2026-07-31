#!/usr/bin/env bash
# Regression test: the summary line must name the defect it found, and a document-level fact must be
# stated once.
#
# `check_figure_citation` emits five verdicts, only two of which are orphans. Its summary line
# counted by SEVERITY and printed the result as a KIND:
#
#     REVIEW: 3 orphan float(s).
#
# — on the repository's own `demo/01_wisconsin_bc`, where the orphan count is zero and all three
# findings were FIGURE_NOT_EMBEDDED. A reader is told to go looking for uncited floats that do not
# exist.
#
# And FIGURE_NOT_EMBEDDED was emitted once per caption while its condition is document-level
# (`not IMG_LINK_RE.search(text)` — true or false for the whole file, never per figure). Three
# figures produced three claims of one fact; across the three demo manuscripts, 8 claims for 3
# documents, inflating every count downstream that treats a claim as a finding.
#
# Evidence for this fix comes from `demo/` only. `_corpus/heldout/` was not read — see CLAUDE.md.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
D="$REPO_ROOT/skills/self-review/scripts/check_figure_citation.py"
WORK="$(mktemp -d -t figcite_test.XXXXXX)"
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

# --- fixtures ------------------------------------------------------------------------------------
# Captioned and cited, but the manuscript embeds no image at all.
cat > "$WORK/not_embedded.md" <<'EOF'
## Results

Enrolment is shown in Figure 1, survival in Figure 2 and calibration in Figure 3.

**Figure 1.** Study flow diagram.

**Figure 2.** Kaplan-Meier survival curves.

**Figure 3.** Calibration plot.
EOF

# A genuine orphan: Figure 2 is captioned and never cited. An image IS embedded, so the
# not-embedded branch stays silent and the orphan branch is the only thing left.
cat > "$WORK/orphan.md" <<'EOF'
## Results

Enrolment is shown in Figure 1.

**Figure 1.** Study flow diagram.

![flow](figures/flow.png)

**Figure 2.** A figure nobody mentions.
EOF

# Clean: captioned, cited, embedded.
cat > "$WORK/clean.md" <<'EOF'
## Results

Enrolment is shown in Figure 1.

**Figure 1.** Study flow diagram.

![flow](figures/flow.png)
EOF

summary_line() { python3 "$D" --manuscript "$WORK/$1" 2>/dev/null | tail -1; }
jq_field() {  # jq_field <fixture> <summary key>
  python3 "$D" --manuscript "$WORK/$1" --out "$WORK/$1.json" --quiet >/dev/null 2>&1
  python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['summary'][sys.argv[2]])" \
    "$WORK/$1.json" "$2"
}

echo "==== the summary line must not report orphans that are not there ===="
ck "no 'orphan' in the not-embedded summary" no \
   "$(summary_line not_embedded.md | grep -qi orphan && echo yes || echo no)"
ck "it names what it did find" yes \
   "$(summary_line not_embedded.md | grep -qi 'no image embedded' && echo yes || echo no)"
ck "n_orphan is 0"        0 "$(jq_field not_embedded.md n_orphan)"
ck "n_not_embedded is 1"  1 "$(jq_field not_embedded.md n_not_embedded)"

echo "==== a document-level fact is stated once, and names every figure ===="
ck "3 captioned figures -> 1 claim" 1 "$(jq_field not_embedded.md n_claims)"
for n in 1 2 3; do
  ck "  claim names Figure $n" yes \
     "$(python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
print('yes' if 'Figure $n' in d['claims'][0]['detail'] else 'no')" "$WORK/not_embedded.md.json")"
done

echo "==== NEGATIVE CONTROLS — a real orphan is still an orphan ===="
ck "orphan fixture: n_orphan is 1"          1 "$(jq_field orphan.md n_orphan)"
ck "orphan fixture: summary says 'orphan'"  yes \
   "$(summary_line orphan.md | grep -qi 'orphan float' && echo yes || echo no)"
ck "orphan fixture: not_embedded is 0"      0 "$(jq_field orphan.md n_not_embedded)"
ck "clean manuscript: no claims"            0 "$(jq_field clean.md n_claims)"
ck "clean manuscript: says OK"              yes \
   "$(summary_line clean.md | grep -q '^OK:' && echo yes || echo no)"

echo "==== the documented exit contract is real: Major IS reachable ===="
python3 "$D" --manuscript "$WORK/not_embedded.md" --require-embedded --strict >/dev/null 2>&1
ck "--require-embedded --strict exits 1"    1 "$?"
python3 "$D" --manuscript "$WORK/not_embedded.md" --strict >/dev/null 2>&1
ck "without --require-embedded it exits 0"  0 "$?"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: the summary names the defect it found, and one fact is stated once."

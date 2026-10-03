#!/usr/bin/env bash
# Regression test for the STROBE flow cascade-closure check (make-figures).
# Synthetic, PII-free YAML fixtures modelled on a real cohort-figure defect:
#   imbalanced -> 10,000 - 500 = 9,500, but the analysis box says 9,470 (off by 30)
#   balanced   -> the same cascade closing exactly (9,500)
#   branching  -> a landmark-subset leaf with no exclusion between it and its parent, which
#                 must NOT be read as an unbalanced cascade step (low-false-positive guard)
# The helper (_strobe_cascade.py) is checked directly (no python-pptx needed); the
# build_strobe_template.py --strict-cascade integration is checked only when pptx is present.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHK="$HERE/../scripts/_strobe_cascade.py"
BUILD="$HERE/../scripts/build_strobe_template.py"
FX="$HERE/fixtures"
fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %s\n' "$1"; else printf '  FAIL  %s (want %s got %s)\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }

[ -f "$CHK" ] || { echo "ENV-ERR: helper missing" >&2; exit 2; }

# (1) imbalanced cascade -> exit 1 under --strict, and the message names the offending link.
out="$(python3 "$CHK" --config "$FX/strobe_cascade_imbalanced.yaml" --strict 2>&1)"; rc=$?
ck "imbalanced exits 1 under --strict" 1 "$rc"
printf '%s\n' "$out" | grep -q 'CASCADE_IMBALANCE' && ck "imbalanced reports CASCADE_IMBALANCE" yes yes || ck "imbalanced reports CASCADE_IMBALANCE" yes no
printf '%s\n' "$out" | grep -q "off by -30" && ck "imbalanced names the -30 offset" yes yes || ck "imbalanced names the -30 offset" yes no

# (2) balanced cascade -> exit 0, no imbalance.
python3 "$CHK" --config "$FX/strobe_cascade_balanced.yaml" --strict >/dev/null 2>&1; ck "balanced exits 0" 0 "$?"

# (3) branching leaf -> exit 0 (the 4,200 subset is not a cascade step off the 5,000 parent).
out3="$(python3 "$CHK" --config "$FX/strobe_cascade_branching.yaml" --strict 2>&1)"; ck "branching leaf exits 0 (no false positive)" 0 "$?"
printf '%s\n' "$out3" | grep -q 'CASCADE_IMBALANCE' && { echo "  FAIL  branching leaf falsely flagged" >&2; fail=$((fail+1)); } || printf '  PASS  branching leaf not flagged\n'

# (4) build integration (only if python-pptx is installed): --strict-cascade refuses the
#     imbalanced config and builds the balanced one.
if python3 -c "import pptx" 2>/dev/null; then
  tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
  python3 "$BUILD" --config "$FX/strobe_cascade_imbalanced.yaml" --out "$tmp/x.pptx" --strict-cascade >/dev/null 2>&1
  ck "build --strict-cascade refuses the imbalanced config" 1 "$?"
  python3 "$BUILD" --config "$FX/strobe_cascade_balanced.yaml" --out "$tmp/ok.pptx" --strict-cascade >/dev/null 2>&1
  ck "build --strict-cascade builds the balanced config" 0 "$?"
  [ -f "$tmp/ok.pptx" ] && ck "balanced build wrote the pptx" yes yes || ck "balanced build wrote the pptx" yes no
else
  echo "  SKIP  build integration (python-pptx not installed)"
fi

# (5) generate_flow_diagram.R nodes/edges schema (dashed edge = exclusion) is recognised but NOT
#     evaluated: an evaluation was tried and flagged correct diagrams (strobe_split: 10,000 - 500 =
#     9,500, 9,500 - 300 = 9,200 = 4,000 + 5,200; stard_branch: 1,000 - 20 = 980, 980 - 30 = 950 =
#     400 + 550). Every nodes/edges config, balanced or not, must report NOT_ASSESSED, never
#     CASCADE_IMBALANCE, and exit 0 even under --strict (the exit code origin/main gave it).
for cfg in "$FX"/flow_graph_*.yaml "$HERE"/../references/exemplar_diagrams/*/template_input.yaml; do
  name="$(basename "$(dirname "$cfg")")/$(basename "$cfg")"
  out5="$(python3 "$CHK" --config "$cfg" --strict 2>&1)"; rc=$?
  ck "$name: nodes/edges exits 0 under --strict" 0 "$rc"
  printf '%s\n' "$out5" | grep -q '^NOT_ASSESSED: nodes/edges schema' && ck "$name: reported NOT_ASSESSED" yes yes || ck "$name: reported NOT_ASSESSED" yes no
  printf '%s\n' "$out5" | grep -q 'CASCADE_IMBALANCE' && ck "$name: no CASCADE_IMBALANCE" no yes || ck "$name: no CASCADE_IMBALANCE" no no
done
for f in strobe_split stard_branch; do
  [ -f "$FX/flow_graph_$f.yaml" ] && ck "must-not-flag fixture $f present" yes yes || ck "must-not-flag fixture $f present" yes no
done

# (6) A check that could not run is never an OK: unrecognised schema -> exit 2 (with or without
#     --strict).
python3 "$CHK" --config "$FX/figure1_flow.yaml" >/dev/null 2>&1; ck "unrecognised schema exits 2" 2 "$?"

echo "fail=$fail"; [ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"

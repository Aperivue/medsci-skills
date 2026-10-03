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

# (5) generate_flow_diagram.R nodes/edges schema (dashed edge = exclusion). Before this check
#     existed the helper printed OK for every such config without reading it.
out5="$(python3 "$CHK" --config "$FX/flow_graph_imbalanced.yaml" --strict 2>&1)"; rc=$?
ck "nodes/edges imbalanced exits 1 under --strict" 1 "$rc"
printf '%s\n' "$out5" | grep -q '9,470' && ck "nodes/edges imbalance names the 9,470 box" yes yes || ck "nodes/edges imbalance names the 9,470 box" yes no
python3 "$CHK" --config "$FX/flow_graph_child_attached_imbalanced.yaml" --strict >/dev/null 2>&1
ck "exclusion beside the produced box: imbalance exits 1" 1 "$?"
python3 "$CHK" --config "$FX/flow_graph_balanced.yaml" --strict >/dev/null 2>&1; ck "nodes/edges balanced exits 0" 0 "$?"
python3 "$CHK" --config "$FX/flow_graph_child_attached.yaml" --strict >/dev/null 2>&1
ck "exclusion beside the produced box + branch side note exits 0 (no false positive)" 0 "$?"
for t in strobe consort prisma stard; do
  out6="$(python3 "$CHK" --config "$HERE/../references/exemplar_diagrams/$t/template_input.yaml" --strict 2>&1)"; rc=$?
  ck "$t exemplar template closes (exit 0)" 0 "$rc"
  printf '%s\n' "$out6" | grep -q 'nodes/edges schema' && ck "$t exemplar actually checked" yes yes || ck "$t exemplar actually checked" yes no
done

# (5b) Exclusion box total. A box listing reasons with no total of its own must not have its
#      first sub-count read as the total (reviewer counter-example: 1,000 - 60 - 40 = 900 closes,
#      but reading 60 as the total reported 940 != 900). The total is unknown, so the link is
#      skipped: never CASCADE_IMBALANCE, and NOT CHECKED (exit 2) under --strict.
for f in excl_no_total excl_inline_reasons; do
  out7="$(python3 "$CHK" --config "$FX/flow_graph_$f.yaml" --strict 2>&1)"; rc=$?
  ck "$f: total unknown, not flagged (exit 2 = not checked)" 2 "$rc"
  printf '%s\n' "$out7" | grep -q 'CASCADE_IMBALANCE' && ck "$f: no CASCADE_IMBALANCE" no yes || ck "$f: no CASCADE_IMBALANCE" no no
  python3 "$CHK" --config "$FX/flow_graph_$f.yaml" >/dev/null 2>&1; ck "$f: report-only exits 0" 0 "$?"
done
python3 "$CHK" --config "$FX/flow_graph_excl_total_first.yaml" --strict >/dev/null 2>&1
ck "total stated first, then reasons: closes (exit 0)" 0 "$?"
out8="$(python3 "$CHK" --config "$FX/flow_graph_excl_total_first_imbalanced.yaml" --strict 2>&1)"; rc=$?
ck "total stated first, imbalanced: exit 1" 1 "$rc"
printf '%s\n' "$out8" | grep -q "1,000 - 100 = 900 but the next box 'b' says 880" && ck "imbalance reads the stated total 100" yes yes || ck "imbalance reads the stated total 100" yes no

# (5c) Every box on the link follows the same total rule, not only the exclusion box. A source
#      or next box that lists its parts with no stated total (PRISMA 2020 identification box,
#      sub-cohorts) has an unknown total: the link is NOT_ASSESSED, reported, and never a
#      CASCADE_IMBALANCE. All of these close; main cleared them and they must stay unflagged.
for f in prisma2020_ident sources_first_line next_subcohorts next_two_counts excl_beside_cohort; do
  out9="$(python3 "$CHK" --config "$FX/flow_graph_$f.yaml" --strict 2>&1)"; rc=$?
  ck "$f: not flagged (exit 2 = not checked)" 2 "$rc"
  printf '%s\n' "$out9" | grep -q 'CASCADE_IMBALANCE' && ck "$f: no CASCADE_IMBALANCE" no yes || ck "$f: no CASCADE_IMBALANCE" no no
  printf '%s\n' "$out9" | grep -q '^NOT_ASSESSED: ' && ck "$f: link reported NOT_ASSESSED" yes yes || ck "$f: link reported NOT_ASSESSED" yes no
  python3 "$CHK" --config "$FX/flow_graph_$f.yaml" >/dev/null 2>&1; ck "$f: report-only exits 0" 0 "$?"
done
# A stated total (a count alone on the first or last line that equals the sum of the others)
# is read, so the link is still evaluated: closes -> 0, does not close -> 1 naming the total.
python3 "$CHK" --config "$FX/flow_graph_ident_total_last.yaml" --strict >/dev/null 2>&1
ck "source box with total on its last line: closes (exit 0)" 0 "$?"
for f in ident_total_last_imbalanced ident_total_first_imbalanced; do
  out10="$(python3 "$CHK" --config "$FX/flow_graph_$f.yaml" --strict 2>&1)"; rc=$?
  ck "$f: exit 1" 1 "$rc"
  printf '%s\n' "$out10" | grep -q "'ident' 2,000 - 300 = 1,700 but the next box 'screened' says 1,650" \
    && ck "$f: reads the stated total 2,000" yes yes || ck "$f: reads the stated total 2,000" yes no
done
# The PRISMA exemplar's last step ("included" lists 28 and 24) is reported, not evaluated.
python3 "$CHK" --config "$HERE/../references/exemplar_diagrams/prisma/template_input.yaml" 2>&1 \
  | grep -q "^NOT_ASSESSED: .*'ft_assessed'" && ck "prisma exemplar: two-count box link NOT_ASSESSED" yes yes \
  || ck "prisma exemplar: two-count box link NOT_ASSESSED" yes no

# (6) A check that could not run is never an OK: unrecognised schema -> exit 2 (with or without
#     --strict); no evaluable exclusion link -> exit 2 under --strict.
python3 "$CHK" --config "$FX/figure1_flow.yaml" >/dev/null 2>&1; ck "unrecognised schema exits 2" 2 "$?"
python3 "$CHK" --config "$FX/flow_graph_no_exclusion.yaml" --strict >/dev/null 2>&1; ck "no exclusion link exits 2 under --strict" 2 "$?"
python3 "$CHK" --config "$FX/flow_graph_no_exclusion.yaml" >/dev/null 2>&1; ck "no exclusion link report-only exits 0" 0 "$?"

echo "fail=$fail"; [ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"

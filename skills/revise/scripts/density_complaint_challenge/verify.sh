#!/usr/bin/env bash
# Deterministic verifier for the density-complaint challenge card.
#
# The bug this gate exists to catch is not hypothetical. A DTA meta-analysis was told by four
# reviewers that it was too dense; the revision answered each comment point-by-point and came back
# 613 words LONGER, every named term higher than before. It took three rounds to do what the
# reviewers asked in round one, because point-by-point response rewards adding text and "too long"
# is the one comment adding text cannot answer.
#
# So the fixtures reproduce that exact arithmetic:
#   v_prev       -> what the reviewers saw
#   v20_longer   -> answered point-by-point, body got LONGER   -> DENSITY_COMPLAINT_UNADDRESSED
#   v21_shorter  -> actually cut, body got SHORTER             -> OK
#
# And the half that keeps the gate honest: a decision letter with NO density complaint must stay
# silent no matter what the word count did — the gate is not a "shorter is always better" nag.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_density_complaint.py"
FIX="$HERE/fixture"

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-52s exit=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-52s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }

# 1) the revision that got LONGER under a density complaint -> fires
python3 "$DET" --comments "$FIX/decision_letter.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v20_longer.md" --strict >/dev/null 2>&1
ck "point-by-point revision got longer -> UNADDRESSED" 1 "$?"

# ...and it must NAME the verdict, not merely exit nonzero
python3 "$DET" --comments "$FIX/decision_letter.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v20_longer.md" 2>&1 | grep -q "DENSITY_COMPLAINT_UNADDRESSED" \
  && ck "the verdict token is printed" 0 0 || ck "the verdict token is printed" 0 1

# 2) the revision that actually CUT -> silent
python3 "$DET" --comments "$FIX/decision_letter.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v21_shorter.md" --strict >/dev/null 2>&1
ck "revision got shorter -> OK" 0 "$?"

# 3) NEGATIVE: a decision letter with no density complaint -> silent even if it got longer
cat > "$FIX/_no_complaint.md" <<'EOF'
Reviewer 1: Please add a sensitivity analysis and report the calibration slope.
Reviewer 2: The methods are sound. Add one sentence on generalizability.
EOF
python3 "$DET" --comments "$FIX/_no_complaint.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v20_longer.md" --strict >/dev/null 2>&1
ck "no density complaint -> not a shorter-is-better nag" 0 "$?"
rm -f "$FIX/_no_complaint.md"

# 4) the JSON report carries the arithmetic a downstream consumer needs
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
python3 "$DET" --comments "$FIX/decision_letter.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v20_longer.md" --out "$TMP/d.json" >/dev/null 2>&1
python3 - "$TMP/d.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["verdict"] == "DENSITY_COMPLAINT_UNADDRESSED", d["verdict"]
assert d["delta_words"] > 0 and d["density_complaints"], d
print("  PASS  JSON report has verdict + delta + complaints")
PY

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1

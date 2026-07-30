#!/usr/bin/env bash
# Regression test: the page-number exemption must cover the forms decks actually use — starting with
# the one this repo's own generator emits.
#
# `is_page_number` was `re.fullmatch(r"\d{1,3}", ...)`. Its docstring says a bare page number "earns
# its place — someone in Q&A says 'go back to 12'", and then it exempted literally nothing else. So
# `2 / 57` — the string `references/generate_pptx_templates.py::_slidenum` writes onto every slide it
# builds — was classified as chrome and flagged, under a remediation line reading "Keep the page
# number". The detector was flagging the output of its own scaffolding.
#
# The exemption stays a FULL match on purpose. A shape whose entire text is a page number is
# furniture the audience uses; a shape that merely contains a number ("Confidential — p. 4") is
# ordinary chrome and must stay flagged.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
S="$REPO_ROOT/skills/present-paper/scripts/check_slide_tells.py"
GEN="$REPO_ROOT/skills/present-paper/references/generate_pptx_templates.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-46s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-46s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

isnum() {
  python3 - "$S" "$1" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("st", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["st"] = m
spec.loader.exec_module(m)
print("yes" if m.is_page_number(sys.argv[2]) else "no")
PY
}

echo "==== the forms a deck writes a page number in ===="
for t in "12" "12." "2 / 57" "2/57" "12 | 57" "12 of 57" "p. 12" "pg 12" "Page 12" \
         "Slide 4" "Slide 4 of 20" "- 12 -"; do
  ck "exempt: '$t'" yes "$(isnum "$t")"
done

echo "==== NEGATIVE CONTROLS — real chrome must stay chrome ===="
for t in "Confidential" "Draft — do not circulate" "Asan Medical Center" "2026-07-30" \
         "Study 3 results" "Confidential — p. 4" "Background" "1234" "v2.1"; do
  ck "chrome: '$t'" no "$(isnum "$t")"
done

echo "==== the repo's own generator must not produce a flagged shape ===="
# Read the format string out of the generator rather than restating it, so this assertion breaks if
# the generator's page-number format ever changes without the detector following.
fmt="$(python3 - "$GEN" <<'PY'
import re, sys
src = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"f'\{n\}\s*(.*?)\s*\{total\}'", src)
sys.stdout.write(m.group(1) if m else "MISSING")
PY
)"
ck "generator's separator found in source" "/" "$fmt"
ck "generator's own output is exempt" yes "$(isnum "3 $fmt 12")"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: a page number in any ordinary form is furniture; everything else is still chrome."

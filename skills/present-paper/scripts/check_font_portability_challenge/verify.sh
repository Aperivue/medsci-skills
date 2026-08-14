#!/usr/bin/env bash
# Deterministic verifier for the font-portability challenge card.
#
# The claim: a deck can name a font that does not exist on the machine it will be shown on, and
# nothing about the file is wrong — the substitution is silent, and it happens on the screen.
#
# Three things have to hold together, and the third is the one that keeps the check alive:
#   a deck naming macOS-only fonts FIRES
#   a deck naming cross-platform fonts is SILENT      (or everyone's deck is "broken")
#   a deck that EMBEDS the macOS fonts is SILENT      (or the check punishes its own fix)
#
# No network. python-pptx builds the fixtures; the detector is stdlib-only.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_font_portability.py"

FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
python3 "$HERE/make_fixtures.py" "$FIX" >/dev/null

fail=0
pass() { echo "PASS  $1"; }
bad()  { echo "FAIL  $1"; fail=1; }

out_mac="$(python3 "$DET" "$FIX/mac_fonts.pptx" || true)"

if grep -q FONT_NOT_PORTABLE <<<"$out_mac"; then
  pass "a deck built in Apple SD Gothic Neo is caught before it reaches the venue"
else
  bad "macOS-only body font passed"
  echo "$out_mac"
fi

# Naming the font is not enough. A report that says "some fonts are not portable" sends the author
# looking; the count and the name are what make it a two-minute fix.
if grep -q "Apple SD Gothic Neo" <<<"$out_mac" && grep -q "Menlo" <<<"$out_mac"; then
  pass "...and it names both offenders rather than reporting a bare count"
else
  bad "the report did not name the fonts"
fi

if grep -qE "Apple SD Gothic Neo.*[0-9]+ reference" <<<"$out_mac"; then
  pass "...with a reference count, so a body font reads differently from a stray code run"
else
  bad "no per-font reference count in the report"
fi

if python3 "$DET" "$FIX/portable.pptx" | grep -q '^OK:'; then
  pass "Inter / Noto Sans Mono are left alone (a blocklist, not an allowlist)"
else
  bad "a cross-platform deck was flagged — this check would be switched off within a week"
  python3 "$DET" "$FIX/portable.pptx"
fi

if python3 "$DET" "$FIX/embedded.pptx" | grep -q '^OK:'; then
  pass "embedding the fonts clears it — the check does not punish its own fix"
else
  bad "a deck that EMBEDDED its macOS fonts was still flagged"
  python3 "$DET" "$FIX/embedded.pptx"
fi

# The inherited-slot rule, in the direction that can be faked.
#
# portable.pptx passing proves an inherited Windows-only default is ignored when the deck has no
# Korean in it. That alone is also what you would see if inherited defaults were ignored ALWAYS --
# a rule with no teeth passes the same test. korean_text.pptx is the same stock template with the
# same theme and Korean on the slides, and it has to fire.
if python3 "$DET" "$FIX/korean_text.pptx" | grep -q FONT_NOT_PORTABLE; then
  pass "a Korean deck inheriting the template's Windows-only Korean face DOES fire"
else
  bad "an inherited default never fires — the rule is 'ignore inherited fonts' wearing a costume"
  python3 "$DET" "$FIX/korean_text.pptx" --list-fonts
fi

# Exit codes: deck detectors report on stdout and exit 0; --strict is their verdict.
if python3 "$DET" "$FIX/mac_fonts.pptx" >/dev/null 2>&1; then
  pass "exits 0 without --strict (a report, not a build failure)"
else
  bad "exited non-zero without --strict"
fi

if python3 "$DET" "$FIX/mac_fonts.pptx" --strict >/dev/null 2>&1; then
  bad "--strict returned 0 on a non-portable deck"
else
  pass "--strict exits non-zero, so a build can gate on it"
fi

python3 "$DET" "$FIX/mac_fonts.pptx" --json "$FIX/o.json" >/dev/null
python3 - "$FIX/o.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["detector"] == "check_font_portability", d.get("detector")
assert d["findings"] and all(f["detector"] == "check_font_portability" for f in d["findings"])
PY
pass "qc JSON self-identifies"

[ "$fail" -eq 0 ] || exit 1
echo "----"
echo "font-portability challenge: all checks passed"

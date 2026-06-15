#!/usr/bin/env bash
# Regression test for the scientific-symbol + CJK glyph-coverage scanner (G43).
# Synthetic, PII-free fixtures: a doc with risky glyphs (arrow →, ±, ≤, κ, CJK,
# ★) that xelatex would silently drop under a default Latin font, and a plain
# ASCII doc. Stdlib-only (python3); fonttools optional (not required here).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/scan_glyph_coverage.py"
RISKY="$HERE/fixtures/glyph_risky.md"
PLAIN="$HERE/fixtures/glyph_plain.md"
OUT="$(mktemp -t glyph_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_class() { python3 -c "
import json; d=json.load(open('$OUT')); assert '$1' in d['classes'], '$1 missing'"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) risky doc -> exit 1 under --strict (risky glyphs present, unverified font)
python3 "$SCRIPT" "$RISKY" --json "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (risky glyphs, no font)" test "$?" -eq 1
check "arrows class detected"        has_class arrows
check "math_operators class detected" has_class math_operators
check "cjk class detected"           has_class cjk

# (2) plain ASCII doc -> exit 0, no classes
python3 "$SCRIPT" "$PLAIN" --json "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 on plain ASCII" test "$?" -eq 0
check "no risky classes on plain doc" python3 -c "
import json; d=json.load(open('$OUT')); assert d['classes']=={}, d['classes']"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"

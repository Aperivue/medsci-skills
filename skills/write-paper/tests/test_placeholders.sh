#!/usr/bin/env bash
# Test scripts/check_placeholders.py — the A5 placeholder/marker gate.
# Synthetic, PII-free fixtures: a manuscript with one of each marker type, a clean
# manuscript that exercises the code-fence and References-section guards, a warn-only
# manuscript (bare [N] outside references), and a missing file. Stdlib-only.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_placeholders.py"
PASS=0
FAIL=0
ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- fixtures ---
# dirty: one of each blocker type + bare numeric cites in the body
cat > "$WORK/dirty.md" <<'EOF'
# Introduction

Our method follows prior work [@NEW:competing-risk-model].

We used [version] of the model via the [channel] interface.

TODO: rewrite this. See FIXME below; values still XXX.

Data are at https://example.com/data and doi.org/XXXX, link here [URL].

This cites a source [4] in Vancouver style [5-7].

## References

[1] Smith J, et al. A real paper. 2020.
[2] Doe A. Another paper. 2021.
EOF

# clean: code-fence guard + legit DOI + numbered reference list (no body markers)
cat > "$WORK/clean.md" <<'EOF'
# Methods

We analyzed the cohort using a competing-risk model.

```python
# TODO: inside a code fence, must be ignored
url = "https://example.com/ignored"
ref = [1]  # ignored
EOF
printf '```\n' >> "$WORK/clean.md"
cat >> "$WORK/clean.md" <<'EOF'

Full data are at https://doi.org/10.1038/s41591-024-00001-2.

## References

[1] Smith J, et al. A real paper. N Engl J Med. 2020.
[2] Doe A. Another paper. Lancet. 2021.
EOF

# warn-only: a bare [N] in the body, no blockers
cat > "$WORK/warn.md" <<'EOF'
# Body
This cites a source [3] in Vancouver style.
EOF

run() { python3 "$SCRIPT" "$@" 2>/dev/null; }

# 1. dirty manuscript fails with exit 1
run --manuscript "$WORK/dirty.md" --quiet
[ $? -eq 1 ] && ok "dirty manuscript fails (exit 1)" || bad "dirty manuscript should fail"

# 2. JSON reports all five finding types and submission_safe=false
run --manuscript "$WORK/dirty.md" --out "$WORK/dirty.json" --quiet
python3 -c "
import json,sys
d=json.load(open('$WORK/dirty.json'))
types={f['type'] for f in d['findings']}
need={'new_marker','ai_disclosure_placeholder','generic_todo','template_url','bare_numeric_cite'}
sys.exit(0 if need <= types and d['submission_safe'] is False and d['summary']['blocker']>=5 else 1)
" && ok "JSON: all five finding types + submission_safe false" || bad "JSON findings incomplete"

# 3. clean manuscript passes (code-fence + references guards work)
run --manuscript "$WORK/clean.md" --quiet
[ $? -eq 0 ] && ok "clean manuscript passes (guards work)" || bad "clean manuscript should pass"

# 3b. clean manuscript has zero findings (no leakage from code fence / refs)
run --manuscript "$WORK/clean.md" --out "$WORK/clean.json" --quiet
python3 -c "
import json,sys
d=json.load(open('$WORK/clean.json'))
sys.exit(0 if not d['findings'] and d['submission_safe'] is True else 1)
" && ok "clean manuscript: zero findings" || bad "clean manuscript should have no findings"

# 4. warn-only: passes by default, fails under --strict
run --manuscript "$WORK/warn.md" --quiet
[ $? -eq 0 ] && ok "warn-only passes by default" || bad "warn-only should pass by default"
run --manuscript "$WORK/warn.md" --strict --quiet
[ $? -eq 1 ] && ok "warn-only fails under --strict" || bad "warn-only should fail under --strict"

# 5. missing file -> exit 2
run --manuscript "$WORK/nope.md" --quiet
[ $? -eq 2 ] && ok "missing file exits 2" || bad "missing file should exit 2"

echo ""
echo "test_placeholders: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

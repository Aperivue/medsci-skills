#!/usr/bin/env bash
# Self-test for scripts/check_frontmatter_schema.py.
# (1) the real skills/ tree must pass; (2) each spec violation must be caught.
# Synthetic fixtures are generated in a temp dir — nothing is committed.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
GATE="$REPO/scripts/check_frontmatter_schema.py"
[[ -f "$GATE" ]] || { echo "ENV-ERR: gate missing: $GATE" >&2; exit 2; }

fail=0
pass() { printf '  PASS  %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fail=$((fail+1)); }

echo "test_frontmatter_schema:"

# 1. Real tree passes (exit 0).
if python3 "$GATE" --root "$REPO/skills" >/dev/null 2>&1; then
  pass "real skills/ tree conforms (exit 0)"
else
  bad "real skills/ tree unexpectedly failed the gate"
fi

# Helper: write a one-skill fixture dir and assert the gate's exit code.
expect() {  # $1=label  $2=expected_rc  $3=frontmatter-body(+blank+body)
  local label="$1" want="$2" content="$3"
  local td; td="$(mktemp -d)"
  mkdir -p "$td/s"
  printf '%s' "$content" > "$td/s/SKILL.md"
  python3 "$GATE" --root "$td" >/dev/null 2>&1; local rc=$?
  if [[ "$rc" -eq "$want" ]]; then pass "$label (exit $rc)"; else bad "$label (got $rc, want $want)"; fi
  rm -rf "$td"
}

GOOD='---
name: good-skill
description: A valid skill. Does a thing and another thing for medical manuscripts.
---

body
'
expect "valid frontmatter accepted"        0 "$GOOD"

# invalid YAML: inline description with a colon-space mapping ambiguity
expect "invalid YAML (colon-space) caught" 1 '---
name: bad-yaml
description: Does things. Commands: init, run.
---

body
'

# name too long (> 64)
LONGNAME=$(printf 'a%.0s' {1..70})
expect "name >64 chars caught"             1 "---
name: $LONGNAME
description: ok description here for the test.
---

body
"

# name not lowercase-hyphen
expect "uppercase name caught"             1 '---
name: Bad_Name
description: ok description here for the test.
---

body
'

# reserved token in name
expect "reserved token in name caught"     1 '---
name: claude-helper
description: ok description here for the test.
---

body
'

# angle bracket in description value
expect "angle bracket in description caught" 1 '---
name: angle-skill
description: Use this when the count is < 10 items in the set.
---

body
'

# empty description
expect "empty description caught"          1 '---
name: empty-desc
description:
---

body
'

if [[ $fail -eq 0 ]]; then echo "  OK"; exit 0; else echo "  $fail check(s) failed"; exit 1; fi

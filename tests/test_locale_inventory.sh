#!/usr/bin/env bash
# Test scripts/check_locale_inventory.py — the locale-inventory coverage gate.
# Uses synthetic, PII-free fixtures via --skills-dir / --inventory. No repo files touched.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check_locale_inventory.py"
PASS=0
FAIL=0

ok()   { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Synthetic skills tree: one Korean-bearing file, one English-only file.
mkdir -p "$WORK/skills/alpha" "$WORK/skills/beta"
printf 'description: sample\n비식별화 샘플 텍스트\n' > "$WORK/skills/alpha/SKILL.md"   # Hangul -> matched
printf 'description: english only\nno korean here\n'   > "$WORK/skills/beta/SKILL.md"    # not matched

run() { python3 "$SCRIPT" --skills-dir "$WORK/skills" --inventory "$1" "${@:2}"; }

# 1. Korean file listed -> OK (exit 0)
cat > "$WORK/inv_ok.md" <<'EOF'
# Inventory
| skills/alpha/SKILL.md | A | locale sample |
EOF
run "$WORK/inv_ok.md" >/dev/null 2>&1
[ $? -eq 0 ] && ok "listed Korean file -> exit 0" || bad "listed Korean file should pass"

# 2. Korean file NOT listed -> missing -> FAIL (exit 1)
cat > "$WORK/inv_missing.md" <<'EOF'
# Inventory
(no rows)
EOF
run "$WORK/inv_missing.md" >/dev/null 2>&1
[ $? -eq 1 ] && ok "missing Korean file -> exit 1" || bad "missing Korean file should fail"

# 3. Stale row (lists an English-only file that has no Korean) -> warn, exit 0 by default
cat > "$WORK/inv_stale.md" <<'EOF'
# Inventory
| skills/alpha/SKILL.md | A | locale sample |
| skills/beta/SKILL.md | B | stale row (beta has no Korean) |
EOF
run "$WORK/inv_stale.md" >/dev/null 2>&1
[ $? -eq 0 ] && ok "stale row -> warn, exit 0 (default)" || bad "stale row should not fail by default"

# 4. Stale row under --strict -> FAIL (exit 1)
run "$WORK/inv_stale.md" --strict >/dev/null 2>&1
[ $? -eq 1 ] && ok "stale row --strict -> exit 1" || bad "stale row should fail under --strict"

# 5. JSON output is valid and reports the missing file
cat > "$WORK/inv_missing2.md" <<'EOF'
# Inventory
EOF
out="$(run "$WORK/inv_missing2.md" --json 2>/dev/null)"
echo "$out" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d['missing']==['skills/alpha/SKILL.md'] and d['ok'] is False else 1)" \
  && ok "JSON reports missing file + ok:false" || bad "JSON summary incorrect"

echo ""
echo "test_locale_inventory: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

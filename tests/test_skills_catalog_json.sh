#!/usr/bin/env bash
# Test scripts/gen_skills_catalog_json.py — the storefront catalog generator/gate.
# Uses synthetic, PII-free fixtures via --skills-dir / --out. Also asserts the
# committed metadata/skills_catalog.json is in sync (the CI gate it backs).
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/gen_skills_catalog_json.py"
PASS=0
FAIL=0

ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mk_skill() {  # name owner_domain layer
  local d="$WORK/skills/$1"
  mkdir -p "$d"
  printf -- '---\nname: %s\ndescription: A synthetic %s skill for testing. Second sentence ignored.\ntriggers: a, b\ntools: Read\nmodel: sonnet\n---\nbody\n' "$1" "$1" > "$d/SKILL.md"
  printf 'schema_version: 2\nname: %s\nlayer: %s\nowner_domain: %s\nmaturity: official\n' "$1" "$3" "$2" > "$d/skill.yml"
}

# --- 1. happy path: a mapped owner_domain generates + round-trips on --check ---
rm -rf "$WORK/skills"
mk_skill alpha statistical_analysis B
mk_skill beta  reporting_compliance A
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/cat.json" >/dev/null 2>&1
if [ $? -eq 0 ] && [ -f "$WORK/cat.json" ]; then ok "generates catalog for mapped domains"; else bad "generate failed"; fi

python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/cat.json" --check >/dev/null 2>&1
[ $? -eq 0 ] && ok "--check round-trips on fresh output" || bad "--check should pass right after generate"

python3 -c "
import json,sys
d=json.load(open('$WORK/cat.json'))
slugs={s['slug'] for s in d['skills']}
cats={s['category'] for s in d['skills']}
sys.exit(0 if d['skill_count']==2 and slugs=={'alpha','beta'}
         and cats=={'analysis_figures','review_compliance'}
         and d['skills'][0]['description'].endswith('.') else 1)
" && ok "JSON shape: count + slugs + category mapping + 1-sentence desc" || bad "JSON shape wrong"

# --- 2. drift: editing the file makes --check fail ---
printf '{"tampered":true}\n' > "$WORK/cat.json"
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/cat.json" --check >/dev/null 2>&1
[ $? -eq 1 ] && ok "--check detects drift (exit 1)" || bad "--check should fail on drift"

# --- 3. fail-loud: an UNMAPPED owner_domain aborts generation ---
mk_skill gamma totally_new_domain D
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/cat2.json" >/dev/null 2>&1
[ $? -eq 1 ] && ok "unmapped owner_domain aborts (exit 1)" || bad "unmapped owner_domain must fail loud"

# --- 4. the committed repo catalog is in sync (the actual CI gate) ---
python3 "$SCRIPT" --check >/dev/null 2>&1
[ $? -eq 0 ] && ok "committed metadata/skills_catalog.json in sync" || bad "repo catalog drifted — run the generator"

echo ""
echo "test_skills_catalog_json: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

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
  printf -- '---\nname: %s\ndescription: A synthetic %s skill for testing. Second sentence ignored.\nmodel: sonnet\nmetadata:\n  triggers: "a, b"\n---\nbody\n' "$1" "$1" > "$d/SKILL.md"
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

# --- 3b. v6 compatibility aliases: listed apart, never counted; a malformed stub fails loud ---
rm -rf "$WORK/skills"
mk_skill alpha statistical_analysis B
mk_skill beta  reporting_compliance A
printf 'aliases:\n  - old-alpha\n' >> "$WORK/skills/alpha/skill.yml"
mk_alias() {  # alias target
  mkdir -p "$WORK/skills/$1"
  printf -- '---\nname: %s\ndescription: Renamed to /%s in v6 (removed in v7).\ndisable-model-invocation: true\n---\nRun /%s.\n' "$1" "$2" "$2" > "$WORK/skills/$1/SKILL.md"
}
mk_alias old-alpha alpha
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/cat_a.json" >/dev/null 2>&1
python3 -c "
import json,sys
d=json.load(open('$WORK/cat_a.json'))
sys.exit(0 if d['skill_count']==2 and d['alias_count']==1
         and {s['slug'] for s in d['skills']}=={'alpha','beta'}
         and d['aliases']==[{'slug':'old-alpha','target':'alpha','category':'analysis_figures'}]
         and all('old-alpha' not in c['slugs'] for c in d['categories']) else 1)
" && ok "alias listed apart (skill_count excludes it; category follows its target)" || bad "alias handling wrong"

mkdir -p "$WORK/skills/old-alpha/scripts" && printf 'print(1)\n' > "$WORK/skills/old-alpha/scripts/check_x.py"
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/cat_b.json" >/dev/null 2>&1
[ $? -eq 1 ] && ok "a stub that ships a script aborts (exit 1)" || bad "stub with a script must fail loud"
rm -rf "$WORK/skills/old-alpha/scripts"

mk_alias old-beta beta   # beta's skill.yml does not declare it
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/cat_c.json" >/dev/null 2>&1
[ $? -eq 1 ] && ok "a stub its target does not declare under aliases: aborts (exit 1)" || bad "undeclared alias must fail loud"
rm -rf "$WORK/skills/old-beta"

mk_alias old-gone gone   # redirect to a skill that does not exist
python3 "$SCRIPT" --skills-dir "$WORK/skills" --out "$WORK/cat_d.json" >/dev/null 2>&1
[ $? -eq 1 ] && ok "a stub redirecting to a missing skill aborts (exit 1)" || bad "dangling alias must fail loud"
rm -rf "$WORK/skills/old-gone"

# --- 4. the committed repo catalog is in sync (the actual CI gate) ---
python3 "$SCRIPT" --check >/dev/null 2>&1
[ $? -eq 0 ] && ok "committed metadata/skills_catalog.json in sync" || bad "repo catalog drifted — run the generator"

echo ""
echo "test_skills_catalog_json: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

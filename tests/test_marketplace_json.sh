#!/usr/bin/env bash
# Test scripts/gen_marketplace_json.py — the plugin-marketplace generator/gate.
# Uses synthetic catalog fixtures via --catalog / --out. Also asserts the committed
# .claude-plugin/marketplace.json is in sync AND structurally covers every skill.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/gen_marketplace_json.py"
PASS=0
FAIL=0

ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- 1. happy path: a mapped-category catalog generates + round-trips on --check ---
cat > "$WORK/cat.json" <<'JSON'
{
  "skill_count": 3,
  "categories": [
    {"key": "analysis_figures", "label": "Analysis & Figures", "slugs": ["beta", "alpha"]},
    {"key": "review_compliance", "label": "Review & Compliance", "slugs": ["gamma"]}
  ],
  "skills": []
}
JSON
python3 "$SCRIPT" --catalog "$WORK/cat.json" --out "$WORK/mk.json" >/dev/null 2>&1
if [ $? -eq 0 ] && [ -f "$WORK/mk.json" ]; then ok "generates marketplace for mapped categories"; else bad "generate failed"; fi

python3 "$SCRIPT" --catalog "$WORK/cat.json" --out "$WORK/mk.json" --check >/dev/null 2>&1
[ $? -eq 0 ] && ok "--check round-trips on fresh output" || bad "--check should pass right after generate"

python3 -c "
import json,sys
d=json.load(open('$WORK/mk.json'))
names=[p['name'] for p in d['plugins']]
analysis=next((p for p in d['plugins'] if p['name']=='medsci-analysis'), None)
ok = (d['name']=='medsci-skills'
      and names==['medsci-analysis','medsci-review']          # catalog order preserved
      and analysis is not None
      and analysis['source']=='./' and analysis['strict'] is False
      and analysis['skills']==['./skills/alpha','./skills/beta']  # slugs sorted
      and 'version' not in d
      and all('version' not in p for p in d['plugins']))
sys.exit(0 if ok else 1)
" && ok "JSON shape: name + plugin order + source/strict + sorted skills + no version" || bad "JSON shape wrong"

# --- 2. drift: editing the file makes --check fail ---
printf '{"tampered":true}\n' > "$WORK/mk.json"
python3 "$SCRIPT" --catalog "$WORK/cat.json" --out "$WORK/mk.json" --check >/dev/null 2>&1
[ $? -eq 1 ] && ok "--check detects drift (exit 1)" || bad "--check should fail on drift"

# --- 3. fail-loud: an UNMAPPED category aborts generation ---
cat > "$WORK/cat_bad.json" <<'JSON'
{
  "skill_count": 1,
  "categories": [
    {"key": "totally_new_category", "label": "New", "slugs": ["delta"]}
  ],
  "skills": []
}
JSON
python3 "$SCRIPT" --catalog "$WORK/cat_bad.json" --out "$WORK/mk2.json" >/dev/null 2>&1
[ $? -eq 1 ] && ok "unmapped category aborts (exit 1)" || bad "unmapped category must fail loud"

# --- 4. the committed marketplace is in sync (the actual CI gate) ---
python3 "$SCRIPT" --check >/dev/null 2>&1
[ $? -eq 0 ] && ok "committed .claude-plugin/marketplace.json in sync" || bad "repo marketplace drifted — run the generator"

# --- 5. structural coverage of the committed file vs real skills/ + catalog ---
python3 -c "
import json,sys
from pathlib import Path
root=Path('$REPO_ROOT')
mk=json.load(open(root/'.claude-plugin'/'marketplace.json'))
cat=json.load(open(root/'metadata'/'skills_catalog.json'))
errs=[]
# marketplace identity + 8 plugins
if mk.get('name')!='medsci-skills': errs.append('name != medsci-skills')
if len(mk['plugins'])!=len(cat['categories']):
    errs.append('plugin count != category count')
# plugin names kebab-case + unique
names=[p['name'] for p in mk['plugins']]
import re
for n in names:
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', n): errs.append(f'name not kebab-case: {n}')
if len(set(names))!=len(names): errs.append('duplicate plugin names')
# every skills path is ./skills/<slug> whose dir exists with SKILL.md
seen=[]
for p in mk['plugins']:
    for s in p['skills']:
        if not s.startswith('./skills/'): errs.append(f'bad path: {s}'); continue
        slug=s[len('./skills/'):]
        if not (root/'skills'/slug/'SKILL.md').is_file(): errs.append(f'missing SKILL.md: {slug}')
        seen.append(slug)
# union == all catalog slugs, each exactly once
catalog_slugs=sorted(sk['slug'] for sk in cat['skills'])
if sorted(seen)!=catalog_slugs: errs.append('skills union != catalog slugs')
if len(seen)!=len(set(seen)): errs.append('a skill appears in >1 plugin')
if len(seen)!=cat['skill_count']: errs.append(f'covered {len(seen)} != skill_count {cat[\"skill_count\"]}')
if errs:
    print('\n'.join(errs)); sys.exit(1)
sys.exit(0)
" && ok "committed file covers every skill exactly once (paths exist)" || bad "structural coverage failed"

echo ""
echo "test_marketplace_json: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

#!/usr/bin/env bash
# Test scripts/sync_hero_skill.py — the hero-skill standalone-mirror generator.
# Build-only (staging) mode; never pushes. Asserts the generated standalone tree
# has every expected artifact and a valid single-skill marketplace.json.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/sync_hero_skill.py"
PASS=0
FAIL=0

ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Build the first hero skill listed in metadata/hero_skills.json into staging.
SKILL="$(python3 -c "import json; print(json.load(open('$REPO_ROOT/metadata/hero_skills.json'))['hero_skills'][0]['skill'])")"
STAGE="$WORK/stage"
python3 "$SCRIPT" --skill "$SKILL" --staging-dir "$STAGE" >/dev/null 2>&1
[ $? -eq 0 ] && ok "builds standalone tree for '$SKILL'" || bad "build failed"

# --- expected files present ---
for f in "skills/$SKILL/SKILL.md" ".claude-plugin/marketplace.json" "README.md" "LICENSE" \
         "CITATION.cff" "installers/install.py" ".github/workflows/validate.yml"; do
  [ -f "$STAGE/$f" ] && ok "present: $f" || bad "missing: $f"
done

# --- marketplace.json shape: single plugin, skill path resolves, no version ---
python3 -c "
import json,sys
from pathlib import Path
mk=json.load(open('$STAGE/.claude-plugin/marketplace.json'))
plugins=mk['plugins']
ok = (len(plugins)==1
      and plugins[0]['source']=='./' and plugins[0]['strict'] is False
      and plugins[0]['skills']==['./skills/$SKILL']
      and (Path('$STAGE')/'skills'/'$SKILL'/'SKILL.md').is_file()
      and 'version' not in mk and 'version' not in plugins[0])
sys.exit(0 if ok else 1)
" && ok "marketplace.json: single plugin + resolvable skill + no version" || bad "marketplace.json shape wrong"

# --- README carries the backlink to the canonical suite ---
grep -q "Aperivue/medsci-skills" "$STAGE/README.md" && ok "README backlinks to medsci-skills" || bad "README missing backlink"
grep -qi "generated mirror" "$STAGE/README.md" && ok "README states it is a generated mirror" || bad "README missing mirror notice"

# --- CITATION.cff has author + standalone repo url (author read from canonical) ---
grep -q "repository-code: \"https://github.com/" "$STAGE/CITATION.cff" \
  && grep -q "given-names:" "$STAGE/CITATION.cff" \
  && ok "CITATION.cff has author + standalone repo url" || bad "CITATION.cff incomplete"

# --- generated installer self-test runs ---
python3 "$STAGE/installers/install.py" --self-test >/dev/null 2>&1
[ $? -eq 0 ] && ok "generated installer --self-test passes" || bad "installer self-test failed"

echo ""
echo "test_sync_hero_skill: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

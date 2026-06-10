#!/usr/bin/env bash
# Test scripts/sync_hero_skill.py — the hero-skill standalone-mirror generator.
# Build-only (staging) mode; never pushes. For EVERY hero skill in
# metadata/hero_skills.json, asserts the generated standalone tree has every
# expected artifact and a valid single-skill marketplace.json.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/sync_hero_skill.py"
PASS=0
FAIL=0

ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

SKILLS="$(python3 -c "import json; print(' '.join(e['skill'] for e in json.load(open('$REPO_ROOT/metadata/hero_skills.json'))['hero_skills']))")"
[ -n "$SKILLS" ] && ok "hero_skills.json lists at least one hero skill" || bad "no hero skills listed"

for SKILL in $SKILLS; do
  echo "--- $SKILL ---"
  STAGE="$WORK/$SKILL"
  python3 "$SCRIPT" --skill "$SKILL" --staging-dir "$STAGE" >/dev/null 2>&1
  [ $? -eq 0 ] && ok "$SKILL: builds standalone tree" || { bad "$SKILL: build failed"; continue; }

  for f in "skills/$SKILL/SKILL.md" ".claude-plugin/marketplace.json" "README.md" "LICENSE" \
           "CITATION.cff" "installers/install.py" ".github/workflows/validate.yml"; do
    [ -f "$STAGE/$f" ] && ok "$SKILL: present $f" || bad "$SKILL: missing $f"
  done

  STAGE="$STAGE" SKILL="$SKILL" python3 -c "
import json,os,sys
from pathlib import Path
stage=os.environ['STAGE']; skill=os.environ['SKILL']
mk=json.load(open(f'{stage}/.claude-plugin/marketplace.json'))
p=mk['plugins']
ok=(len(p)==1 and p[0]['source']=='./' and p[0]['strict'] is False
    and p[0]['skills']==[f'./skills/{skill}']
    and (Path(stage)/'skills'/skill/'SKILL.md').is_file()
    and 'version' not in mk and 'version' not in p[0])
sys.exit(0 if ok else 1)
" && ok "$SKILL: marketplace single plugin + resolvable skill + no version" || bad "$SKILL: marketplace shape wrong"

  grep -q "Aperivue/medsci-skills" "$STAGE/README.md" && ok "$SKILL: README backlinks to medsci-skills" || bad "$SKILL: README missing backlink"
  grep -qi "generated mirror" "$STAGE/README.md" && ok "$SKILL: README states generated mirror" || bad "$SKILL: README missing mirror notice"
  grep -q "given-names:" "$STAGE/CITATION.cff" && ok "$SKILL: CITATION has author (read from canonical)" || bad "$SKILL: CITATION missing author"

  # third-party license carve-out must propagate when the skill bundles references/LICENSES.md
  if [ -f "$REPO_ROOT/skills/$SKILL/references/LICENSES.md" ]; then
    grep -qi "Third-Party" "$STAGE/LICENSE" && ok "$SKILL: LICENSE carries third-party carve-out" || bad "$SKILL: LICENSE dropped third-party carve-out"
  fi

  python3 "$STAGE/installers/install.py" --self-test >/dev/null 2>&1
  [ $? -eq 0 ] && ok "$SKILL: generated installer --self-test passes" || bad "$SKILL: installer self-test failed"
done

echo ""
echo "test_sync_hero_skill: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

#!/usr/bin/env bash
# validate_skills.sh — Lint all medsci-skills for required structure
# Run from repo root: bash scripts/validate_skills.sh

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
PASS=0
WARN=0
FAIL=0
TOTAL=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}PASS${NC} $1"; ((PASS++)); }
warn() { echo -e "  ${YELLOW}WARN${NC} $1"; ((WARN++)); }
fail() { echo -e "  ${RED}FAIL${NC} $1"; ((FAIL++)); }

echo "========================================="
echo " MedSci Skills Validator"
echo "========================================="
echo ""

for skill_dir in "$SKILLS_DIR"/*/; do
  skill_name=$(basename "$skill_dir")
  skill_file="$skill_dir/SKILL.md"

  if [ ! -f "$skill_file" ]; then
    fail "$skill_name: SKILL.md not found"
    continue
  fi

  ((TOTAL++))
  echo "[$skill_name]"
  lines=$(wc -l < "$skill_file")

  # 1. Frontmatter: required fields
  has_name=$(head -20 "$skill_file" | grep -c "^name:" || true)
  has_desc=$(head -20 "$skill_file" | grep -c "^description:" || true)
  has_triggers=$(head -20 "$skill_file" | grep -c "^triggers:" || true)
  has_tools=$(head -20 "$skill_file" | grep -c "^tools:" || true)
  has_model=$(head -20 "$skill_file" | grep -c "^model:" || true)

  if [ "$has_name" -ge 1 ] && [ "$has_desc" -ge 1 ] && [ "$has_triggers" -ge 1 ] && [ "$has_tools" -ge 1 ] && [ "$has_model" -ge 1 ]; then
    pass "Frontmatter (all 5 fields)"
  else
    missing=""
    [ "$has_name" -eq 0 ] && missing="$missing name"
    [ "$has_desc" -eq 0 ] && missing="$missing description"
    [ "$has_triggers" -eq 0 ] && missing="$missing triggers"
    [ "$has_tools" -eq 0 ] && missing="$missing tools"
    [ "$has_model" -eq 0 ] && missing="$missing model"
    fail "Frontmatter missing:$missing"
  fi

  # 2. Anti-Hallucination section
  if grep -qi "anti.hallucination\|Anti-Hallucination" "$skill_file"; then
    pass "Anti-Hallucination section"
  else
    fail "Anti-Hallucination section MISSING"
  fi

  # 3. Quality gates (look for "Gate" or "user approval" or "user review")
  gate_count=$(grep -ci "gate\|user approval\|user review\|user confirms\|present.*user" "$skill_file" || true)
  if [ "$gate_count" -ge 3 ]; then
    pass "Quality gates ($gate_count references)"
  elif [ "$gate_count" -ge 1 ]; then
    warn "Quality gates ($gate_count — recommend 3+)"
  else
    warn "Quality gates (0 found)"
  fi

  # 4. Line count tier
  if [ "$lines" -ge 300 ]; then
    pass "Size: $lines lines (HIGH tier)"
  elif [ "$lines" -ge 150 ]; then
    pass "Size: $lines lines (MID tier)"
  else
    warn "Size: $lines lines (THIN tier — consider expanding)"
  fi

  # 5. Reference file integrity
  ref_count=0
  ref_missing=0
  while IFS= read -r ref_line; do
    ref_path=$(echo "$ref_line" | grep -oE '\$\{SKILL_DIR\}/references/[^ `*),]+' | head -1 | sed "s|\${SKILL_DIR}|${skill_dir%/}|" | sed 's/[`\*]//g' || true)
    if [ -n "$ref_path" ]; then
      ((ref_count++))
      if [ ! -f "$ref_path" ] && [ ! -d "$ref_path" ]; then
        # Try without trailing characters
        clean_path=$(echo "$ref_path" | sed 's/[,;]$//')
        if [ ! -f "$clean_path" ] && [ ! -d "$clean_path" ]; then
          ((ref_missing++))
        fi
      fi
    fi
  done < <(grep 'SKILL_DIR.*references' "$skill_file" || true)

  if [ "$ref_count" -eq 0 ]; then
    pass "References: none declared"
  elif [ "$ref_missing" -eq 0 ]; then
    pass "References: $ref_count declared, all found"
  else
    fail "References: $ref_missing of $ref_count missing"
  fi

  # ---------------- Content Integrity (v2 lints) ----------------
  # Scope: SKILL.md + references/**/*.md only (shipped prose).
  # Excluded (meta-docs): TODO_*.md, HANDOFF.md, and scripts/yaml files.

  integrity_files=()
  [ -f "$skill_file" ] && integrity_files+=("$skill_file")
  if [ -d "${skill_dir}references" ]; then
    while IFS= read -r -d '' f; do
      # Skip meta-docs (HANDOFF, TODO_*) inside references/
      base=$(basename "$f")
      case "$base" in
        HANDOFF.md|TODO_*.md) continue ;;
      esac
      integrity_files+=("$f")
    done < <(find "${skill_dir}references" -type f -name "*.md" -print0 2>/dev/null)
  fi

  # 6. Personal precedent leak (blocklist of project-specific identifiers)
  precedent_hits=0
  precedent_patterns='CBCT Ablation MA|Du 2023|FD Occlusion AI SR|FD Occlusion|Paper ①|Paper ②|Paper ③'
  for f in "${integrity_files[@]}"; do
    if grep -qE "$precedent_patterns" "$f"; then
      hit=$(grep -nE "$precedent_patterns" "$f" | head -1)
      rel="${f#$REPO_ROOT/}"
      fail "Personal precedent in $rel: $hit"
      ((precedent_hits++))
    fi
  done
  [ "$precedent_hits" -eq 0 ] && pass "Precedent blocklist (no project-specific identifiers)"

  # 7. Absolute path leak (/Users/eugene/)
  path_hits=0
  for f in "${integrity_files[@]}"; do
    if grep -qE '/Users/eugene/' "$f"; then
      hit=$(grep -nE '/Users/eugene/' "$f" | head -1)
      rel="${f#$REPO_ROOT/}"
      fail "Absolute path in $rel: $hit"
      ((path_hits++))
    fi
  done
  [ "$path_hits" -eq 0 ] && pass "Absolute paths (no /Users/eugene/ leak)"

  # 8. Dated precedent blockquote (lines starting with '> ' containing YYYY-MM-DD)
  # Allow-list: meta headers like "Last updated:", "Created:", "Updated:".
  blockdate_hits=0
  for f in "${integrity_files[@]}"; do
    matched=$(grep -nE '^>.*20[2-3][0-9]-[0-1][0-9]-[0-3][0-9]' "$f" \
      | grep -vE '^[0-9]+:> *(Last updated|Created|Updated|Date):' || true)
    if [ -n "$matched" ]; then
      rel="${f#$REPO_ROOT/}"
      first=$(echo "$matched" | head -1)
      fail "Dated precedent blockquote in $rel: $first"
      ((blockdate_hits++))
    fi
  done
  [ "$blockdate_hits" -eq 0 ] && pass "Blockquote dates (no dated precedents)"

  # 9. Korean prose outside code blocks in SKILL.md
  # Allow-list: Communication Rules section, trigger/example tables (lines starting with '|').
  korean_lines=$(python3 - "$skill_file" <<'PY'
import re, sys
path = sys.argv[1]
hangul = re.compile(r'[\uac00-\ud7a3\u3131-\u318e]')
in_code = False
in_comm = False
in_frontmatter = False
frontmatter_closed = False
hits = []
with open(path, encoding='utf-8') as fh:
    for i, line in enumerate(fh, 1):
        s = line.rstrip('\n')
        # Frontmatter: first --- opens, second --- closes
        if s.strip() == '---':
            if not frontmatter_closed and i == 1:
                in_frontmatter = True
                continue
            if in_frontmatter:
                in_frontmatter = False
                frontmatter_closed = True
                continue
        if in_frontmatter:
            continue
        if s.startswith('```'):
            in_code = not in_code
            continue
        if re.match(r'^##\s+Communication Rules', s):
            in_comm = True
            continue
        if re.match(r'^##\s+', s) and 'Communication Rules' not in s:
            in_comm = False
        if in_code or in_comm:
            continue
        stripped = s.lstrip()
        if stripped.startswith('|'):
            continue
        if stripped.startswith('>'):  # blockquote examples (user prompts, dialogue)
            continue
        if hangul.search(s):
            hits.append(f"{i}: {s[:80]}")
for h in hits:
    print(h)
PY
)

  if [ -z "$korean_lines" ]; then
    pass "Korean prose (none outside code/tables/Communication Rules)"
  else
    count=$(echo "$korean_lines" | wc -l | tr -d ' ')
    first=$(echo "$korean_lines" | head -1)
    # WARN-only: Korean-native SKILL.md migration is a separate translation task.
    # Precedent/path/blockquote rules (6-8) remain FAIL to block regressions.
    warn "Korean prose in SKILL.md: $count line(s), first $first"
  fi

  echo ""
done

echo "========================================="
echo " Summary"
echo "========================================="
echo -e " Skills checked: ${TOTAL}"
echo -e " ${GREEN}PASS${NC}: ${PASS}"
echo -e " ${YELLOW}WARN${NC}: ${WARN}"
echo -e " ${RED}FAIL${NC}: ${FAIL}"
echo ""

python3 "$REPO_ROOT/scripts/validate_skill_contracts.py"
contract_status=$?
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — fix $FAIL issue(s) before release"
  exit 1
elif [ "$contract_status" -ne 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — skill contract validation failed"
  exit 1
else
  echo -e "${GREEN}ALL CHECKS PASSED${NC}"
  exit 0
fi

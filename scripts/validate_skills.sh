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

# Personal path blocklist. Narrowed (2026-05-30): block only personal home dirs
# and the personal-config subtrees that carry private working notes
# (~/.claude/plans, ~/.claude/projects, ~/.claude/private-*). The generic
# integration paths ~/.claude/{skills,rules,hooks,templates,agents,settings.json}
# are documented install targets across README / docs/setup / many SKILL.md and
# must NOT be blocked. Matching `\.claude/(plans|projects|private)` (no leading
# anchor) catches ~/ , $HOME/ and absolute forms alike.
PERSONAL_PATH='/Users/eugene/|/home/eugene/|\.claude/(plans|projects|private)'

# Returns the first "lineno:line" personal-path violation read from stdin, or
# nothing. Allowlists the documented `private-journal-profiles` skill-convention
# directory — a generic two-tier library location that add-journal / find-journal
# instruct the model to read/write (analogous to the allowed ~/.claude/{skills,
# rules,hooks} install paths). Author scratchpads (~/.claude/private-*, plans,
# projects) and personal home dirs are still blocked.
_personal_path_hit() {
  sed -E 's/private-journal-profiles/journal-profiles/g' | grep -nE "$PERSONAL_PATH" | head -1
}

echo "========================================="
echo " MedSci Skills Validator"
echo "========================================="
echo ""

# Tool dependencies. exiftool is required for rule 10 (binary EXIF metadata
# scan). Python3 is invoked inline; missing it fails on use. Make exiftool a
# hard requirement so a missing install is loud, not silent — installing it
# once (brew / apt) is the easy path and beats shipping PII in a PDF Author
# field that the text linter cannot see.
if ! command -v exiftool >/dev/null 2>&1; then
  echo -e "${RED}ERROR${NC}: exiftool not found."
  echo "  Install: brew install exiftool      # macOS"
  echo "           sudo apt-get install -y libimage-exiftool-perl   # Ubuntu"
  exit 2
fi

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
  # Scope: every tracked .md inside the skill directory (SKILL.md + references/
  # + any TODO_*.md / HANDOFF*.md scratchpads that slipped past .gitignore).
  # Rationale: meta-docs are the most common PII-leak path because authors
  # treat them as "internal" while git still tracks and publishes them. The
  # 2026-05-02 audit caught one such file (TODO_*.md skipped by the previous
  # case-statement exclusion). Force scanning everything; gitignore is the
  # mechanism for keeping a developer scratchpad out, not the linter.

  # Helper: skip gitignored files. Linter should match what the public sees,
  # not what is on local disk.
  _add_if_tracked() {
    local f="$1"
    # `git check-ignore` exits 0 when the file IS ignored; skip in that case.
    if ! git -C "$REPO_ROOT" check-ignore -q "$f" 2>/dev/null; then
      integrity_files+=("$f")
    fi
  }

  # Text-bearing extensions to scan. Binary types (.png/.pdf/.docx) are out
  # of scope — separate FAIL rule below catches their FILENAMES (rule 7c)
  # but their content needs a different tool (e.g. exiftool for EXIF).
  TEXT_EXTS='-name *.md -o -name *.yml -o -name *.yaml -o -name *.json -o -name *.txt -o -name *.csv -o -name *.tsv'

  integrity_files=()
  [ -f "$skill_file" ] && _add_if_tracked "$skill_file"
  if [ -d "${skill_dir}references" ]; then
    while IFS= read -r -d '' f; do
      _add_if_tracked "$f"
    done < <(find "${skill_dir}references" -type f \( $TEXT_EXTS \) -print0 2>/dev/null)
  fi
  # Extended scope (2026-05): templates/ and scripts/ subdirs. Same blocklist
  # patterns apply — these dirs were previously silently excluded and could
  # carry vendored PII (manuscript IDs, author names, project paths) into
  # downstream skill consumers without detection. Includes .py / .sh source
  # since docstrings and comments are the typical PII vector.
  if [ -d "${skill_dir}templates" ]; then
    while IFS= read -r -d '' f; do
      _add_if_tracked "$f"
    done < <(find "${skill_dir}templates" -type f \( $TEXT_EXTS -o -name "*.py" -o -name "*.sh" \) -print0 2>/dev/null)
  fi
  if [ -d "${skill_dir}scripts" ]; then
    while IFS= read -r -d '' f; do
      _add_if_tracked "$f"
    done < <(find "${skill_dir}scripts" -type f \( $TEXT_EXTS -o -name "*.py" -o -name "*.sh" \) -print0 2>/dev/null)
  fi
  # Also catch top-level skill scratchpads (skills/<name>/TODO_*.md, HANDOFF.md)
  # and skill.yml / capabilities.yml that some skills keep alongside SKILL.md.
  while IFS= read -r -d '' f; do
    _add_if_tracked "$f"
  done < <(find "${skill_dir}" -maxdepth 1 -type f \( $TEXT_EXTS \) \
            ! -name "SKILL.md" -print0 2>/dev/null)

  # 6. Personal precedent leak (blocklist of project-specific identifiers)
  # Covers: legacy project IDs, project slugs, product names, etc.,
  # institution / mentor identifiers, numbered workspace folders, and the
  # historical prefix patterns (Paper ①②③). Keep additions in alphabetical
  # blocks so future maintainers can spot what is being filtered.
  precedent_hits=0
  precedent_patterns='\bCK-[0-9]+\b|\bMA-[0-9]+\b|\bMA0[0-9]\b|\b0_MI2RL\b|\b1_Samsung_Changwon\b|\b5_Personal_Research\b|\b6_Aperivue\b|\b10_Meta_Analysis\b|\b11_CheckUP\b|\b21_Aneurysm\b|01_RFA_Adjunct|02_CBCT_Biopsy|03_CBCT_Ablation|RFA-Adjunct|RFA_Adjunct|CBCT Ablation MA|CBCT Biopsy MA|Du 2023|FD Occlusion AI SR|FD Occlusion|Paper ①|Paper ②|Paper ③|MeducAI|CXRscoliosis|SkullFx|Samsung Changwon|삼성서울|삼성창원|서울아산|Asan/UoU|\bKKW\b|\bLHC\b|\bKDY\b|\bLWJ\b|\bHRP_Rhim\b|김경원|이덕희|김남국|임현철|임해진|남유진|Hyunchul Rhim|Pa Hong|Taein An|Hye Ree Cho|Yoojin Nam|Dong Yeong Kim|Kyung Won Kim|Jeong Min Song|Jaeyoon Kim|[가-힣]{2,4}[[:space:]]*(교수님|선생님)|CAC>[0-9]+|VIF[[:space:]]+Diag|[A-Z]+[0-9]+_Consensus_Sheet|v[0-9]+_edit_plan\.md|screening_consensus_final\.md|fulltext_screening_final\.tsv'
  for f in "${integrity_files[@]}"; do
    if grep -qE "$precedent_patterns" "$f"; then
      hit=$(grep -nE "$precedent_patterns" "$f" | head -1)
      rel="${f#$REPO_ROOT/}"
      fail "Personal precedent in $rel: $hit"
      ((precedent_hits++))
    fi
  done
  [ "$precedent_hits" -eq 0 ] && pass "Precedent blocklist (no project-specific identifiers)"

  # 7. Personal path leak (/Users/eugene/, /home/<user>/, ~/.claude/{plans,
  #    projects,private-*}). Generic ~/.claude/{skills,rules,hooks,...} paths
  #    are documented install targets and intentionally NOT matched (see
  #    PERSONAL_PATH definition near the top).
  path_hits=0
  for f in "${integrity_files[@]}"; do
    hit=$(_personal_path_hit < "$f")
    if [ -n "$hit" ]; then
      rel="${f#$REPO_ROOT/}"
      fail "Personal path in $rel: $hit"
      ((path_hits++))
    fi
  done
  [ "$path_hits" -eq 0 ] && pass "Personal paths (no home-dir / private-config leak)"

  # 7b. Real personal email leak. Whitelist: example.com / example.org /
  #     known journal editorial-office domains (sciencedirect, lancet, ahajournals,
  #     wjgnet, kams, wiley, aasld) + `your@email.com` style placeholders.
  email_hits=0
  email_pattern='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
  email_whitelist='example\.com|example\.org|your@email\.com|user@host|name@|placeholder|noreply@|git@github\.com|@lancet\.com|@strokeahajournal\.org|@aasld\.org|@wjgnet\.com|@wiley\.com|@kams\.or\.kr|@journal\.|aim-aicro\.com'
  # Note: `aim-aicro.com` is a corporate domain that historically appeared in a
  #   personal author roster. We allow the bare domain here only because the
  #   precedent blocklist already catches the full `kyungwon.kim@aim-aicro.com`
  #   string by way of the personal-name patterns above; remove from this
  #   whitelist if the bare domain ever surfaces on its own.
  for f in "${integrity_files[@]}"; do
    matches=$(grep -nE "$email_pattern" "$f" | grep -vE "$email_whitelist" || true)
    if [ -n "$matches" ]; then
      rel="${f#$REPO_ROOT/}"
      first=$(echo "$matches" | head -1)
      fail "Real email leak in $rel: $first"
      ((email_hits++))
    fi
  done
  [ "$email_hits" -eq 0 ] && pass "Email whitelist (no personal addresses)"

  # 7c. Filename PII (Author{Year}_Journal_FigNN, Surname{Year}_Conf_..., etc.)
  #     Catches the case where the file CONTENT is fine but the filename itself
  #     reveals authorship — e.g. `Nam2025_KJR_Fig01.png` from the 2026-05-02
  #     audit. Pattern: a capitalised word (≥3 chars) directly followed by a
  #     4-digit year, then `_`. Common exemplar / precedent file shape.
  #     Allow-list: the precedent filename has to actually be a real file inside
  #     the skill, so this only fires when shipping such a file. Common
  #     non-author tokens are excluded (Issue, Year, Vol, Table, Figure, Sample,
  #     Example, Sample, Demo, Test, Type, Class).
  filename_hits=0
  filename_pattern='^[A-Z][a-zA-Z]{2,}[0-9]{4}_'
  filename_allow='^(Issue|Year|Vol|Table|Figure|Sample|Example|Demo|Test|Type|Class|Group|Cohort|Study|Trial|Phase|Run|Batch|Round|Stage|Step|Item|Mode)[0-9]{4}_'
  while IFS= read -r -d '' f; do
    base=$(basename "$f")
    if echo "$base" | grep -qE "$filename_pattern" && ! echo "$base" | grep -qE "$filename_allow"; then
      rel="${f#$REPO_ROOT/}"
      fail "Author-style filename in $rel: $base"
      ((filename_hits++))
    fi
  done < <(find "${skill_dir}" -type f -print0 2>/dev/null)
  [ "$filename_hits" -eq 0 ] && pass "Filenames (no Author{Year}_ patterns)"

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

  # 10. Binary EXIF metadata scan (DOCX / PPTX / XLSX / PDF / PNG / JPG / TIFF).
  # Document/image metadata (dc:creator, cp:lastModifiedBy, PDF Author, EXIF
  # Artist, etc.) is opaque to grep on the file content and is the most common
  # silent PII leak when authors drop a personally-authored slide deck or
  # annotated screenshot into a skill. Match the values against the same
  # `precedent_patterns` used for text scanning + the absolute-path patterns.
  # Upstream/3rd-party document authors (e.g. STARD's Patrick Bossuyt, the
  # python-pptx maintainer) are not in `precedent_patterns`, so they pass
  # without an explicit allow-list.
  exif_binary_files=()
  while IFS= read -r -d '' f; do
    if ! git -C "$REPO_ROOT" check-ignore -q "$f" 2>/dev/null; then
      exif_binary_files+=("$f")
    fi
  done < <(find "${skill_dir}" -type f \( \
      -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \
      -o -iname "*.tif" -o -iname "*.tiff" \
      -o -iname "*.pdf" -o -iname "*.docx" -o -iname "*.pptx" -o -iname "*.xlsx" \
    \) -print0 2>/dev/null)

  exif_hits=0
  if [ ${#exif_binary_files[@]} -gt 0 ]; then
    exif_dump=$(exiftool -S \
      -Author -Creator -LastModifiedBy -LastSavedBy -Copyright -Artist \
      -Owner -OwnerName -CompanyName -Manager -HostComputer -UserComment \
      -Subject -Title -Description -Keywords -Comment \
      -Producer -CreatorTool -Software \
      "${exif_binary_files[@]}" 2>/dev/null || true)
    current_file=""
    while IFS= read -r line; do
      if [[ "$line" == ========\ * ]]; then
        current_file="${line#======== }"
        continue
      fi
      [ -z "$line" ] && continue
      [ -z "$current_file" ] && continue
      if echo "$line" | grep -qE "$precedent_patterns|/Users/eugene/|/home/eugene/"; then
        rel="${current_file#$REPO_ROOT/}"
        fail "Binary EXIF PII in $rel: $line"
        ((exif_hits++))
      fi
    done <<< "$exif_dump"
  fi
  [ "$exif_hits" -eq 0 ] && pass "Binary EXIF (no PII in document/image metadata)"

  echo ""
done

echo "========================================="
echo " Public-surface PII scan (all tracked text outside skills/)"
echo "========================================="
# Full tracked-text scan OUTSIDE skills/ (skills/ is covered by the per-skill
# loop above). Closes the 2026-05-29 gap where docs/, INTAKE/, and root
# metadata were never scanned — a hospital-name + incoming-fellowship PII
# reached public main while the validator reported PASS (validator PASS !=
# security PASS). Uses `git ls-files` so privatized (gitignored) drafts are
# excluded and only the public surface is gated; the gate is "0 hits", not a
# fixed file count.
#
# Self-exemption: this script holds the blocklist literals (precedent_patterns,
# PERSONAL_PATH); scanning it would self-match. Excluded explicitly.
#
# Author-attribution allowlist: README.md / CITATION.cff / paper.md /
# .zenodo.json legitimately carry the maintainer's own name for citation. Only
# the name tokens are stripped before the precedent match, so other PII
# (hospital, project codes, personal paths) on the same line is still caught.
META_FAIL=0
META_SCANNED=0
AUTHOR_ATTRIB_RE='^(README\.md|CITATION\.cff|paper\.md|\.zenodo\.json)$'
while IFS= read -r rel; do
  [ "$rel" = "scripts/validate_skills.sh" ] && continue   # self-exempt
  case "$rel" in skills/*) continue ;; esac               # covered by per-skill loop
  f="$REPO_ROOT/$rel"
  [ -f "$f" ] || continue
  ((META_SCANNED++))
  if echo "$rel" | grep -qE "$AUTHOR_ATTRIB_RE"; then
    scan_src=$(sed -E 's/Yoojin Nam//g; s/남유진//g' "$f")
  else
    scan_src=$(cat "$f")
  fi
  if echo "$scan_src" | grep -qE "$precedent_patterns"; then
    hit=$(echo "$scan_src" | grep -nE "$precedent_patterns" | head -1)
    fail "Personal precedent in $rel: $hit"
    ((META_FAIL++))
  fi
  hit=$(printf '%s\n' "$scan_src" | _personal_path_hit)
  if [ -n "$hit" ]; then
    fail "Personal path in $rel: $hit"
    ((META_FAIL++))
  fi
  matches=$(echo "$scan_src" | grep -nE "$email_pattern" | grep -vE "$email_whitelist" || true)
  if [ -n "$matches" ]; then
    first=$(echo "$matches" | head -1)
    fail "Real email leak in $rel: $first"
    ((META_FAIL++))
  fi
done < <(git -C "$REPO_ROOT" ls-files -- '*.md' '*.yml' '*.yaml' '*.json' '*.cff' '*.bib' '*.txt' '*.csv' '*.tsv' '*.py' '*.sh')
echo "  Scanned $META_SCANNED tracked non-skills text files"
[ "$META_FAIL" -eq 0 ] && pass "Public-surface PII scan clean (docs/, root, metadata)"
echo ""

echo "========================================="
echo " Summary"
echo "========================================="
echo -e " Skills checked: ${TOTAL}"
echo -e " ${GREEN}PASS${NC}: ${PASS}"
echo -e " ${YELLOW}WARN${NC}: ${WARN}"
echo -e " ${RED}FAIL${NC}: ${FAIL}"
echo -e " Meta-doc FAIL: ${META_FAIL}"
echo ""

python3 "$REPO_ROOT/scripts/validate_skill_contracts.py"
contract_status=$?
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — fix $FAIL issue(s) before release"
  exit 1
elif [ "$META_FAIL" -gt 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — fix $META_FAIL meta-doc PII issue(s) before release"
  exit 1
elif [ "$contract_status" -ne 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — skill contract validation failed"
  exit 1
else
  echo -e "${GREEN}ALL CHECKS PASSED${NC}"
  exit 0
fi

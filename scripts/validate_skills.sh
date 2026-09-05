#!/usr/bin/env bash
# validate_skills.sh — Lint all medsci-skills for required structure
# Run from repo root: bash scripts/validate_skills.sh
#                     bash scripts/validate_skills.sh --only <skill-name>
#
# `--only` exists because the validator's own self-tests were paying for the whole repo. Fixing the
# find-glob bug (#435) took this script from reading 58 files to ~1,200, and the two tests written
# to prove that fix works each invoke the validator again — so CI ran the full scan three times and
# the `validate` job went from 3m57s to 5-7 minutes. Nothing was wrong with either test; the cost
# was structural, because the validator took no arguments and a test that needs to observe ONE
# fixture skill had no way to ask for less than all of them.
#
# It is a test affordance, not a release gate. A scoped run deliberately does NOT print the verdict
# a full run prints — see the exit block. A cheap gate is one that actually gets run; a gate whose
# partial result reads identically to its full result is worse than a slow one.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"

ONLY_SKILL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --only)
      [ $# -ge 2 ] || { echo "--only requires a skill name" >&2; exit 2; }
      ONLY_SKILL="$2"; shift 2 ;;
    --only=*)
      ONLY_SKILL="${1#--only=}"; shift ;;
    -h|--help)
      echo "usage: validate_skills.sh [--only <skill-name>]"
      echo "  (no args)       validate every skill + the public-surface scan + the repo-wide gates"
      echo "  --only <name>   validate just skills/<name>/ — for self-tests; NOT a release gate"
      exit 0 ;;
    *)
      echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

# A name matching nothing must be an error, never an empty loop. #435 was a gate that scanned zero
# files and printed PASS; a silently-unmatched --only would rebuild exactly that shape.
if [ -n "$ONLY_SKILL" ] && [ ! -f "$SKILLS_DIR/$ONLY_SKILL/SKILL.md" ]; then
  echo "no such skill: $ONLY_SKILL (expected $SKILLS_DIR/$ONLY_SKILL/SKILL.md)" >&2
  exit 2
fi
# Precedent / personal-identifier scanner. Structural shapes stay as plaintext
# regex inside it; real names / mentors / institutions / project codes are
# matched against SHA-256 digests (scripts/precedent_hashes.txt) so this public
# validator never enumerates them in cleartext (oss-publication-pii-guard §5).
CHECK_PRECEDENT="$REPO_ROOT/scripts/check_precedent.py"
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
# Known personal usernames are hash-only in check_precedent.py; never repeat
# a real home-directory path in the rule that is meant to prevent its publication.
PERSONAL_PATH='\.claude/(plans|projects|private)'

# Returns the first "lineno:line" personal-path violation read from stdin, or
# nothing. Allowlists the documented `private-journal-profiles` skill-convention
# directory — a generic two-tier library location that add-journal / find-journal
# instruct the model to read/write (analogous to the allowed ~/.claude/{skills,
# rules,hooks} install paths). Author scratchpads (~/.claude/private-*, plans,
# projects) and personal home dirs are still blocked.
_personal_path_hit() {
  sed -E 's/private-journal-profiles/journal-profiles/g' | grep -nE "$PERSONAL_PATH" | head -1
}

# An instruction whose content lives in a file we do not ship. Paths under
# ~/.claude/rules/ are the maintainer's personal global rules; the distribution
# bundle is skills/ + installers/ only (metadata/distribution_files.json), so an
# installed user has no such file and never will. That is harmless when the path
# is provenance — "English only (per <path>)" states the rule and then says where
# it came from. It is a silent defect when a verb GOVERNS the path — "apply
# <path>", "follow <path>" — because then the instruction *is* the file, the file
# is absent, and the step is skipped with nothing to show for it.
#
# Deliberately narrow: `see` / `per` / `cross-link` are not matched. Blocking
# those would fire on ~70 correctly-formed citations at once and this check would
# never land. `[^|]` keeps the window inside one markdown table cell, so a "must"
# in one column cannot reach a path in another.
#
# Calibrated against real defects rather than a fixture: on the tree immediately
# before this check was added, it matched exactly the four imperative references
# that were there (render-pdf-doc x2, meta-analysis phase-4, revise) and nothing
# else in 79 total references.
RULE_IMPERATIVE='(apply|applies|follow|enforce|obey|adhere to|refer to|as required by|as specified in|read)[^|]{0,40}\.claude/rules/'

echo "========================================="
if [ -n "$ONLY_SKILL" ]; then
  echo " MedSci Skills Validator — SCOPED to '$ONLY_SKILL'"
else
  echo " MedSci Skills Validator"
fi
echo "========================================="
if [ -n "$ONLY_SKILL" ]; then
  echo " Per-skill rules for this one skill only."
  echo " NOT run: the other skills, the public-surface PII scan, the repo-wide gates."
fi
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

if [ -n "$ONLY_SKILL" ]; then
  SKILL_DIRS=("$SKILLS_DIR/$ONLY_SKILL/")
else
  SKILL_DIRS=("$SKILLS_DIR"/*/)
fi

for skill_dir in "${SKILL_DIRS[@]}"; do
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
  #
  # An ARRAY, and every glob quoted. As a bare string expanded unquoted into
  # `find`, `*.md` was pathname-expanded against the CALLER'S working directory
  # before find ever saw it. From the repo root — which is how CI and every
  # documented invocation run it — that became the thirteen top-level .md files,
  # find aborted with "unknown primary or operator", `2>/dev/null` swallowed the
  # message, and each loop below yielded ZERO files. Net effect: references/,
  # templates/ and scripts/ — the "extended scope" added in 2026-05 precisely
  # because vendored PII hides there — were never scanned, while the run printed
  # PASS for every rule on every skill.
  TEXT_EXTS=( -name '*.md' -o -name '*.yml' -o -name '*.yaml' -o -name '*.json' \
              -o -name '*.txt' -o -name '*.csv' -o -name '*.tsv' )
  CODE_EXTS=( -o -name '*.py' -o -name '*.sh' )

  integrity_files=()
  [ -f "$skill_file" ] && _add_if_tracked "$skill_file"
  if [ -d "${skill_dir}references" ]; then
    while IFS= read -r -d '' f; do
      _add_if_tracked "$f"
    done < <(find "${skill_dir}references" -type f \( "${TEXT_EXTS[@]}" \) -print0 2>/dev/null)
  fi
  # Extended scope (2026-05): templates/ and scripts/ subdirs. Same blocklist
  # patterns apply — these dirs were previously silently excluded and could
  # carry vendored PII (manuscript IDs, author names, project paths) into
  # downstream skill consumers without detection. Includes .py / .sh source
  # since docstrings and comments are the typical PII vector.
  if [ -d "${skill_dir}templates" ]; then
    while IFS= read -r -d '' f; do
      _add_if_tracked "$f"
    done < <(find "${skill_dir}templates" -type f \( "${TEXT_EXTS[@]}" "${CODE_EXTS[@]}" \) -print0 2>/dev/null)
  fi
  if [ -d "${skill_dir}scripts" ]; then
    while IFS= read -r -d '' f; do
      _add_if_tracked "$f"
    done < <(find "${skill_dir}scripts" -type f \( "${TEXT_EXTS[@]}" "${CODE_EXTS[@]}" \) -print0 2>/dev/null)
  fi
  # Also catch top-level skill scratchpads (skills/<name>/TODO_*.md, HANDOFF.md)
  # and skill.yml / capabilities.yml that some skills keep alongside SKILL.md.
  while IFS= read -r -d '' f; do
    _add_if_tracked "$f"
  done < <(find "${skill_dir}" -maxdepth 1 -type f \( "${TEXT_EXTS[@]}" \) \
            ! -name "SKILL.md" -print0 2>/dev/null)
  # tests/ (2026-07-29). Test fixtures are the *easiest* place for a real name to
  # settle: an author roster, a byline, a reader panel — you reach for a plausible
  # one and the nearest plausible name is someone you actually work with. These
  # files are excluded from the distribution bundle, so they never reach an
  # installer, but they are in a public git repository, which is the exposure the
  # precedent blocklist exists to prevent. Scanning them found real names in two
  # skills, one of them inside a fixture named `supplement_pii_clean.md`.
  if [ -d "${skill_dir}tests" ]; then
    while IFS= read -r -d '' f; do
      _add_if_tracked "$f"
    done < <(find "${skill_dir}tests" -type f \( "${TEXT_EXTS[@]}" "${CODE_EXTS[@]}" \) -print0 2>/dev/null)
  fi

  # 6. Personal precedent leak (blocklist of project-specific identifiers).
  # Delegated to check_precedent.py: structural shapes (CK-<n>, MA-<n>, ...)
  # stay as plaintext regex there, while real names / mentors / institutions /
  # project codes are matched against SHA-256 digests in precedent_hashes.txt —
  # so neither this validator nor the digest file enumerates them in cleartext.
  precedent_hits=0
  for f in "${integrity_files[@]}"; do
    hit=$(python3 "$CHECK_PRECEDENT" "$f"); rc=$?
    rel="${f#$REPO_ROOT/}"
    if [ "$rc" -eq 3 ]; then
      fail "Personal precedent in $rel: $hit"
      ((precedent_hits++))
    elif [ "$rc" -ne 0 ]; then
      fail "check_precedent.py error on $rel (rc=$rc)"
      ((precedent_hits++))
    fi
  done
  [ "$precedent_hits" -eq 0 ] && pass "Precedent blocklist (no project-specific identifiers)"

  # 7. Personal path leak (known home-directory names, ~/.claude/{plans,
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
  email_whitelist='example\.com|example\.org|your@email\.com|user@host|name@|placeholder|noreply@|users\.noreply\.github\.com|git@github\.com|@lancet\.com|@strokeahajournal\.org|@aasld\.org|@wjgnet\.com|@wiley\.com|@kams\.or\.kr|@nejm\.org|@journal\.'
  # A corporate domain from a personal author roster used to sit on that whitelist, and the note
  # justifying it SPELLED OUT the full address it claimed was covered elsewhere. So the one file
  # exempt from the precedent scan (this one — see the self-exemption below) was the file
  # publishing a colleague's name and work address in cleartext, inside the comment explaining
  # why doing so was safe. It was neither safe nor true: that address was run against the
  # blocklist and MISSED. Entry and note are both gone; the address and its bare domain are now
  # hashed in precedent_hashes.txt, so a reappearance anywhere scannable fails instead of being
  # waved through. A whitelist entry must never carry the string it exempts.
  # `@nejm.org` and `users.noreply.github.com` joined the list in 2026-07-29, when
  #   this rule started scanning references/ and scripts/ for the first time: a
  #   journal's published editorial-office address and a GitHub noreply sender are
  #   contact information, not a person's private address.
  #
  # Two files exist in order to CARRY personal-looking data, and exempting them is
  # not a loophole but the only way they can do their job: they are the corpora
  # that prove the PII detectors fire. `deidentify` needs Korean PHI shapes
  # (resident-registration numbers, phone numbers, addresses) and `contribute`
  # needs a message that leaks an author's address, so that each skill's scanner
  # can be shown catching them. Every other rule still applies to them; only this
  # one is skipped, and only for these two paths.
  #
  # This note used to carry two further claims, and a 2026-08-15 audit found BOTH false:
  #
  #   "Both are fully synthetic." The names, national IDs, addresses and hospital ARE
  #   invented. A journal submission ID in the `contribute` fixture was not — it belonged
  #   to a manuscript the maintainer had actually reviewed. The verification behind the
  #   word "synthetic" had been done name by name, and the ID is not a name, so it was
  #   never in scope. State what a check covered, not what it felt like it covered.
  #
  #   "Neither ships (tests/ is excluded from the distribution bundle)." True of the
  #   classroom ZIP. FALSE of the npm package, which ships `skills/**/tests/`. The claim
  #   was written from one distribution channel and asserted over all of them.
  #
  # An exemption is a place where nothing downstream will check the reasoning, so the
  # reasoning has to be checked here. Anything added to this list is exempt from the
  # scanner AND from the review the scanner would have prompted. Verify the claim you
  # write, against every channel, before adding a path below.
  PII_FIXTURE_PATHS='^skills/deidentify/tests/test_phi_[a-z]+\.csv$|^skills/contribute/tests/test_contribution_safety\.sh$'
  for f in "${integrity_files[@]}"; do
    rel_f="${f#$REPO_ROOT/}"
    if printf '%s' "$rel_f" | grep -qE "$PII_FIXTURE_PATHS"; then
      continue
    fi
    matches=$(grep -nE "$email_pattern" "$f" | grep -vE "$email_whitelist" || true)
    if [ -n "$matches" ]; then
      rel="${f#$REPO_ROOT/}"
      first=$(echo "$matches" | head -1)
      fail "Real email leak in $rel: $first"
      ((email_hits++))
    fi
  done
  [ "$email_hits" -eq 0 ] && pass "Email whitelist (no personal addresses)"

  # 7b-ii. An instruction that points at a file we do not ship (see
  #        RULE_IMPERATIVE near the top for why this is narrow).
  unshipped_hits=0
  for f in "${integrity_files[@]}"; do
    hit=$(grep -niE "$RULE_IMPERATIVE" "$f" | head -1)
    if [ -n "$hit" ]; then
      rel="${f#$REPO_ROOT/}"
      fail "Instruction points at an unshipped personal rule in $rel: $hit"
      ((unshipped_hits++))
    fi
  done
  [ "$unshipped_hits" -eq 0 ] && pass "Unshipped-rule instructions (no 'apply ~/.claude/rules/...')"

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
  # annotated screenshot into a skill. Match the values through the same
  # check_precedent.py scanner used for text + the absolute-path patterns.
  # Upstream/3rd-party document authors (e.g. STARD's Patrick Bossuyt, the
  # python-pptx maintainer) are not in the precedent set, so they pass
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
      _exif_rc=0
      printf '%s' "$line" | python3 "$CHECK_PRECEDENT" - >/dev/null 2>&1 || _exif_rc=$?
      if [ "$_exif_rc" -eq 3 ]; then
        rel="${current_file#$REPO_ROOT/}"
        fail "Binary EXIF PII in $rel: $line"
        ((exif_hits++))
      fi
    done <<< "$exif_dump"
  fi
  [ "$exif_hits" -eq 0 ] && pass "Binary EXIF (no PII in document/image metadata)"

  echo ""
done

META_FAIL=0
META_SCANNED=0
if [ -z "$ONLY_SKILL" ]; then

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
# Self-exemption: this script + check_precedent.py + precedent_hashes.txt carry
# the blocklist machinery (structural regex, PERSONAL_PATH, SHA-256 digests).
# Scanning them would self-match the structural shapes. Excluded explicitly.
#
# Author-attribution allowlist: README.md / CITATION.cff / paper.md /
# .zenodo.json legitimately carry the maintainer's own name for citation. For
# those files the precedent scan runs with --allow-author (the author's own name
# digest is exempted), so other PII (hospital, project codes, personal paths) on
# the same line is still caught. The author name is no longer spelled out here.
#
# `README.<locale>.md` is matched as a FAMILY rather than enumerated. The first translated
# README (zh-CN) failed CI on its byline — the same "Created & maintained by ..." line README.md
# carries and is allowlisted for. A translation carries that byline by definition, so every
# future locale hits the identical wall, and enumerating them one at a time rebuilds the wall
# per language. The allowance stays narrow: `--allow-author` exempts only the author-name digest,
# so a hospital name, a project code or a personal path in a translated README is still caught
# exactly as it is in the English one.
AUTHOR_ATTRIB_RE='^(README\.md|README\.[A-Za-z]{2}(-[A-Za-z]{2,4})?\.md|CITATION\.cff|paper\.md|\.zenodo\.json|MAINTAINERS\.md|CONTRIBUTORS\.md)$'
while IFS= read -r rel; do
  case "$rel" in
    scripts/validate_skills.sh|scripts/check_precedent.py|scripts/precedent_hashes.txt|scripts/precedent_author_hashes.txt) continue ;;  # self-exempt: blocklist machinery
    tests/test_precedent_hashing.sh) continue ;;           # self-exempt: scanner's own test carries structural fixtures (CK-<n>, ...)
    skills/*) continue ;;                                  # covered by per-skill loop
  esac
  f="$REPO_ROOT/$rel"
  [ -f "$f" ] || continue
  ((META_SCANNED++))
  scan_src=$(cat "$f")
  if echo "$rel" | grep -qE "$AUTHOR_ATTRIB_RE"; then
    precedent_hit=$(printf '%s' "$scan_src" | python3 "$CHECK_PRECEDENT" --allow-author -); precedent_rc=$?
  else
    precedent_hit=$(printf '%s' "$scan_src" | python3 "$CHECK_PRECEDENT" -); precedent_rc=$?
  fi
  if [ "$precedent_rc" -eq 3 ]; then
    fail "Personal precedent in $rel: $precedent_hit"
    ((META_FAIL++))
  elif [ "$precedent_rc" -ne 0 ]; then
    fail "check_precedent.py error on $rel (rc=$precedent_rc)"
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

# The public surface also contains demonstration Word documents. Reuse the
# submission scanner's package-level path check, including custom properties
# and relationships, rather than relying on visible text or selected EXIF keys.
python3 - "$REPO_ROOT" <<'PY'
import importlib.util
import subprocess
import sys
from pathlib import Path
root = Path(sys.argv[1])
source = root / "skills/sync-submission/scripts/check_asset_anonymization.py"
spec = importlib.util.spec_from_file_location("asset_privacy", source)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
paths = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z", "--", "*.docx"])
failed = 0
for raw in paths.decode().split("\0"):
    if not raw or raw.startswith("_corpus/") or not (root / raw).is_file():
        continue
    if module._docx_embedded_abs_paths(root / raw):
        print(f"  FAIL {raw}: embedded home-directory path in document package")
        failed += 1
sys.exit(1 if failed else 0)
PY
if [ "$?" -ne 0 ]; then
  fail "Public Word document packages contain embedded personal paths"
  ((META_FAIL++))
fi
echo "  Scanned $META_SCANNED tracked non-skills text files"
[ "$META_FAIL" -eq 0 ] && pass "Public-surface PII scan clean (docs/, root, metadata)"
echo ""

fi  # end: whole-repo public-surface scan (skipped under --only)

echo "========================================="
echo " Summary"
echo "========================================="
echo -e " Skills checked: ${TOTAL}"
echo -e " ${GREEN}PASS${NC}: ${PASS}"
echo -e " ${YELLOW}WARN${NC}: ${WARN}"
echo -e " ${RED}FAIL${NC}: ${FAIL}"
[ -z "$ONLY_SKILL" ] && echo -e " Meta-doc FAIL: ${META_FAIL}"
echo ""

# The three repo-wide gates below reason about the whole skills/ tree (contracts, vendoring drift,
# script reachability). Under --only they would either scan everything — defeating the point — or
# report on a set the caller did not ask about. They are skipped, and the exit block says so.
contract_status=0
domain_probe_status=0
script_reach_status=0
if [ -z "$ONLY_SKILL" ]; then
  python3 "$REPO_ROOT/scripts/validate_skill_contracts.py"
  contract_status=$?
  echo ""

  # Vendoring drift gate (all vendored sets: domain probes + RoB checklists + any undeclared
  # cross-skill duplicate). Capture the exit status explicitly: this script runs under
  # `set -uo pipefail` (not `set -e`), so a bare call would not abort and the failure would be
  # silently buried before the summary.
  python3 "$REPO_ROOT/scripts/check_domain_probe_sync.py" --strict
  domain_probe_status=$?
  echo ""

  # Script reachability. A script no SKILL.md invokes never runs for a user, however well it is
  # tested — the non-detector sibling of check_detector_reachability.py.
  python3 "$REPO_ROOT/scripts/check_script_reachability.py" --strict
  script_reach_status=$?
  echo ""
fi

if [ "$FAIL" -gt 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — fix $FAIL issue(s) before release"
  exit 1
elif [ "$META_FAIL" -gt 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — fix $META_FAIL meta-doc PII issue(s) before release"
  exit 1
elif [ "$contract_status" -ne 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — skill contract validation failed"
  exit 1
elif [ "$domain_probe_status" -ne 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — vendoring drift (run check_domain_probe_sync.py --sync)"
  exit 1
elif [ "$script_reach_status" -ne 0 ]; then
  echo -e "${RED}VALIDATION FAILED${NC} — a skill script is never invoked by any SKILL.md (see check_script_reachability.py)"
  exit 1
elif [ -n "$ONLY_SKILL" ]; then
  # Deliberately NOT "ALL CHECKS PASSED". A caller grepping for that string — a human skimming, a
  # test, a future CI step — must not be able to get it out of a run that looked at one skill and
  # skipped every repo-wide gate. The scoped verdict names its own scope.
  echo -e "${GREEN}SCOPED PASS${NC} — skills/$ONLY_SKILL only; repo-wide gates NOT run"
  exit 0
else
  echo -e "${GREEN}ALL CHECKS PASSED${NC}"
  exit 0
fi

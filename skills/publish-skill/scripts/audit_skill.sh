#!/usr/bin/env bash
# audit_skill.sh -- PII / hardcoded-path / metadata scanner for a single
# Claude Code skill. Standalone wrapper that mirrors the per-skill checks
# in `medsci-skills/scripts/validate_skills.sh` so a personal skill can be
# audited the same way before being moved into a public repo.
#
# Usage:
#   audit_skill.sh <skill_directory> [extra_patterns]
#
# Arguments:
#   skill_directory  Path to a single skill (must contain SKILL.md).
#   extra_patterns   Optional `grep -E` alternation pattern of names /
#                    institutions / collaborator handles to add. Example:
#                      "jane doe|MIT Medical|@gmail\.com"
#
# Exit codes:
#   0  Clean -- no findings
#   1  Findings detected -- review required before publication
#   2  Usage error
#
# Coverage parity with medsci-skills/scripts/validate_skills.sh:
#   rule 6  Personal precedent (text)            yes
#   rule 7  Absolute path leak                   yes
#   rule 7b Real personal email                  yes
#   rule 7c Author{Year}_ filename pattern       yes
#   rule 8  Blockquote dated precedent           yes
#   rule 10 Binary EXIF metadata (DOCX/PDF/PNG)  yes (skipped silently if
#                                                exiftool not installed)
#
# False-positive guard: text scans use `grep --binary-files=without-match`
# so compiled `.pyc`, raster `.png` byte-stream collisions, and `git` pack
# files do not count as matches. `__pycache__/` is also explicitly skipped.

set -u

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    cat >&2 <<USAGE
Usage: audit_skill.sh <skill_directory> [extra_patterns]

Examples:
  audit_skill.sh ~/.claude/skills/my-skill
  audit_skill.sh ./skills/my-skill "jane doe|Stanford|@gmail\.com"
USAGE
    exit 2
fi

SKILL_DIR="$1"
EXTRA_PATTERNS="${2:-}"

if [ ! -d "$SKILL_DIR" ]; then
    echo "Error: directory not found: $SKILL_DIR" >&2
    exit 2
fi

# Resolve to absolute path so the report shows useful locations.
SKILL_DIR="$(cd "$SKILL_DIR" && pwd)"

FOUND=0
TOTAL=0

# Color output only when stdout is a TTY.
if [ -t 1 ]; then
    RED=$'\033[0;31m'
    GRN=$'\033[0;32m'
    YEL=$'\033[1;33m'
    NC=$'\033[0m'
else
    RED=""; GRN=""; YEL=""; NC=""
fi

# Files to exclude from text scans. Binary scan handles its own subset.
TEXT_EXCLUDES=(
    --exclude-dir=.git
    --exclude-dir=__pycache__
    --exclude-dir=.pytest_cache
    --exclude-dir=.mypy_cache
    --exclude-dir=node_modules
    --exclude=audit_skill.sh
    --exclude=pii-patterns.md
    --exclude="*.pyc"
)

# ---------------------------------------------------------------------
# Helper: scan a category of grep -E pattern over text files only.
# `--binary-files=without-match` keeps random byte sequences inside .png
# / .pdf / .docx / .pyc from triggering false positives.
# ---------------------------------------------------------------------
scan_text() {
    local category="$1"
    local pattern="$2"
    local whitelist="${3:-}"   # optional grep -E pattern; matches removed before counting
    local results
    results=$(grep -rinE --binary-files=without-match \
        "${TEXT_EXCLUDES[@]}" \
        "$pattern" "$SKILL_DIR" 2>/dev/null || true)
    if [ -n "$whitelist" ] && [ -n "$results" ]; then
        results=$(printf '%s\n' "$results" | grep -vE "$whitelist" || true)
    fi

    if [ -n "$results" ]; then
        local count
        count=$(printf '%s\n' "$results" | wc -l | tr -d ' ')
        TOTAL=$((TOTAL + count))
        FOUND=1
        echo
        echo "${RED}## $category${NC} ($count match(es))"
        printf '%s\n' "$results" | sed 's/^/  /'
    fi
}

# ---------------------------------------------------------------------
# Helper: filename pattern check. Catches the case where file CONTENT is
# fine but the filename itself reveals authorship (e.g. Nam2025_KJR_Fig01.png).
# Mirrors validate_skills.sh rule 7c.
# ---------------------------------------------------------------------
scan_filenames() {
    local category="Author-style filenames (Surname{Year}_)"
    local pattern='^[A-Z][a-zA-Z]{2,}[0-9]{4}_'
    local allow='^(Issue|Year|Vol|Table|Figure|Sample|Example|Demo|Test|Type|Class|Group|Cohort|Study|Trial|Phase|Run|Batch|Round|Stage|Step|Item|Mode)[0-9]{4}_'
    local hits=""
    while IFS= read -r -d '' f; do
        local base
        base=$(basename "$f")
        if [[ "$base" =~ $pattern ]] && ! [[ "$base" =~ $allow ]]; then
            hits="${hits}${f}"$'\n'
        fi
    done < <(find "$SKILL_DIR" -type f \
        -not -path '*/.git/*' \
        -not -path '*/__pycache__/*' \
        -print0 2>/dev/null)

    if [ -n "$hits" ]; then
        local count
        count=$(printf '%s' "$hits" | grep -c '^' || true)
        TOTAL=$((TOTAL + count))
        FOUND=1
        echo
        echo "${RED}## $category${NC} ($count match(es))"
        printf '%s' "$hits" | sed 's/^/  /'
    fi
}

# ---------------------------------------------------------------------
# Helper: optional EXIF scan via exiftool. Skipped silently if exiftool is
# not installed (publish-skill users are not expected to have it). When
# present, mirrors validate_skills.sh rule 10.
# ---------------------------------------------------------------------
scan_exif() {
    if ! command -v exiftool >/dev/null 2>&1; then
        echo "${YEL}## Binary EXIF metadata${NC} skipped (exiftool not installed)"
        echo "  Install: brew install exiftool   # macOS"
        echo "           sudo apt-get install -y libimage-exiftool-perl   # Ubuntu"
        return 0
    fi

    local binary_files=()
    while IFS= read -r -d '' f; do
        binary_files+=("$f")
    done < <(find "$SKILL_DIR" -type f \
        \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \
        -o -iname "*.tif" -o -iname "*.tiff" \
        -o -iname "*.pdf" -o -iname "*.docx" -o -iname "*.pptx" -o -iname "*.xlsx" \) \
        -print0 2>/dev/null)

    if [ ${#binary_files[@]} -eq 0 ]; then
        return 0
    fi

    local pii_pattern='/Users/[a-zA-Z]|/home/[a-zA-Z]'
    if [ -n "$EXTRA_PATTERNS" ]; then
        pii_pattern="${pii_pattern}|${EXTRA_PATTERNS}"
    fi

    local exif_dump
    exif_dump=$(exiftool -S \
        -Author -Creator -LastModifiedBy -LastSavedBy -Copyright -Artist \
        -Owner -OwnerName -CompanyName -Manager -HostComputer -UserComment \
        -Subject -Title -Description -Keywords -Comment \
        -Producer -CreatorTool -Software \
        "${binary_files[@]}" 2>/dev/null || true)

    # exiftool only prints `======== <file>` headers when given multiple files.
    # Pre-prime current_file so single-file mode still attributes hits correctly.
    local current_file="${binary_files[0]}"
    local hits=""
    while IFS= read -r line; do
        if [[ "$line" == ========\ * ]]; then
            current_file="${line#======== }"
            continue
        fi
        [ -z "$line" ] && continue
        [ -z "$current_file" ] && continue
        if echo "$line" | grep -qE "$pii_pattern"; then
            hits="${hits}${current_file}: ${line}"$'\n'
        fi
    done <<< "$exif_dump"

    if [ -n "$hits" ]; then
        local count
        count=$(printf '%s' "$hits" | grep -c '^' || true)
        TOTAL=$((TOTAL + count))
        FOUND=1
        echo
        echo "${RED}## Binary EXIF metadata${NC} ($count match(es))"
        printf '%s' "$hits" | sed 's/^/  /'
    fi
}

echo "=========================================="
echo "PII Audit: $SKILL_DIR"
echo "=========================================="

# --- Universal text categories -----------------------------------------

# rule 7: hardcoded user-home / project paths.
scan_text "Hardcoded Paths" \
    '/Users/[a-zA-Z]|/home/[a-zA-Z]|~/Documents|~/Desktop|~/Downloads|~/Projects'

# rule 7b: real personal email addresses. The whitelist matches common
# placeholder / example / RFC-reserved domains so the script does not
# flag legitimate documentation samples.
EMAIL_WHITELIST='example\.com|example\.org|example\.net|your@email|user@host|noreply@|placeholder|<your-email>|<email>'
scan_text "Email Addresses" \
    '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' \
    "$EMAIL_WHITELIST"

# Internal infrastructure leakage.
scan_text "IP Addresses / Internal URLs" \
    '\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b|https?://[a-z0-9-]+\.(internal|local|corp)'

# rule 6: institutional references. `\b` word boundaries replace the
# `(?<!...)` lookbehind that the original grep -E silently failed on.
scan_text "Institutional References" \
    '\b(SNUH|AMC|SMC|KAIST|SNU|ASAN|MGH|UCSF)\b|Mayo Clinic|Johns Hopkins|Samsung Medical|Severance|Asan Medical'

# rule 6 cont.: titled academic roles with adjacent surname.
scan_text "Academic Roles with Names" \
    'professor [A-Z][a-z]+|Prof\. [A-Z]|Dr\. [A-Z][a-z]+|PGY[0-9]|[가-힣]{2,4}[[:space:]]*(교수님|선생님|박사님)'

# Language-default hardcoding.
scan_text "Language Hardcoding" \
    'in Korean|한국어로|Korean language|communicate in Korean|in Japanese|in Chinese'

# Frequent-collision city names.
scan_text "Location Specifics" \
    '\b(Seoul|Busan|Daegu|Tokyo|Beijing|Shanghai|Boston|Stanford)\b|서울|부산|울산|창원|대구|대전'

# rule 8: dated precedent inside blockquote (`> 2026-04-26 ...`).
# Allow-list: meta headers like "Last updated:", "Created:", "Updated:",
# "Date:" — these are routine version stamps, not internal review timeline.
scan_text "Blockquote Dated Precedent" \
    '^>.*20[2-9][0-9]-[0-1][0-9]-[0-3][0-9]' \
    '> *(Last updated|Created|Updated|Date|Version|Released):'

# rule 7c filename pattern.
scan_filenames

# rule 10 EXIF scan (optional).
scan_exif

# --- User-supplied identifiers ----------------------------------------
if [ -n "$EXTRA_PATTERNS" ]; then
    scan_text "User-Specified Patterns" "$EXTRA_PATTERNS"
fi

# --- Summary -----------------------------------------------------------
echo
echo "=========================================="
if [ "$FOUND" -eq 0 ]; then
    echo "${GRN}RESULT: CLEAN (0 findings)${NC}"
    echo "=========================================="
    exit 0
else
    echo "${RED}RESULT: $TOTAL FINDING(S) DETECTED${NC}"
    echo "Review and fix all findings before publishing."
    echo "=========================================="
    exit 1
fi

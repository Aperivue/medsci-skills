#!/usr/bin/env bash
# audit_skill.sh -- PII / hardcoded-path / metadata scanner for a single
# Claude Code skill. Standalone wrapper that mirrors the per-skill checks
# in `medsci-skills/scripts/validate_skills.sh` so a personal skill can be
# audited the same way before being moved into a public repo.
#
# Usage:
#   audit_skill.sh [--strict] <skill_directory> [extra_patterns]
#
# Arguments:
#   skill_directory  Path to a single skill (must contain SKILL.md).
#   extra_patterns   Optional `grep -E` alternation pattern of names /
#                    institutions / collaborator handles to add. Example:
#                      "jane doe|MIT Medical|@gmail\.com"
#                    Matched case-insensitively, in text and in EXIF fields.
#   --strict         Treat a check that could not run as a failure (exit 3).
#
# Exit codes:
#   0  Clean -- no findings (without --strict, a check that could not run
#      is reported as INCOMPLETE on the RESULT line but still exits 0)
#   1  Findings detected -- review required before publication
#   2  Usage error, an invalid extra_patterns regex, or a scan whose grep
#      failed (an error is never reported as CLEAN)
#   3  --strict only: no findings, but a check could not run (binary files
#      present and exiftool not installed)
#
# Coverage parity with medsci-skills/scripts/validate_skills.sh:
#   rule 6  Personal precedent (text)            yes
#   rule 7  Absolute path leak                   yes
#   rule 7b Real personal email                  yes
#   rule 7c Author{Year}_ filename pattern       yes
#   rule 8  Blockquote dated precedent           yes
#   rule 10 Binary EXIF metadata (DOCX/PDF/PNG)  yes (reported as INCOMPLETE
#                                                if exiftool is not installed)
#
# False-positive guard: text scans use `grep --binary-files=without-match`
# so compiled `.pyc`, raster `.png` byte-stream collisions, and `git` pack
# files do not count as matches. `__pycache__/` is also explicitly skipped.

set -u

STRICT=0
ARGS=()
for a in "$@"; do
    if [ "$a" = "--strict" ]; then
        STRICT=1
    else
        ARGS+=("$a")
    fi
done
set -- ${ARGS[@]+"${ARGS[@]}"}

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    cat >&2 <<USAGE
Usage: audit_skill.sh [--strict] <skill_directory> [extra_patterns]

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

# Reject an extra_patterns regex grep cannot compile. Scanning with it would
# fail on every file and the user's own name check would silently go inert.
if [ -n "$EXTRA_PATTERNS" ]; then
    grep -E -- "$EXTRA_PATTERNS" </dev/null >/dev/null 2>&1
    if [ $? -eq 2 ]; then
        echo "Error: extra_patterns is not a valid grep -E regex: $EXTRA_PATTERNS" >&2
        exit 2
    fi
fi

# Resolve to absolute path so the report shows useful locations.
SKILL_DIR="$(cd "$SKILL_DIR" && pwd)"

FOUND=0
TOTAL=0
ERRORS=0       # a grep that failed (rc 2): the category was not evaluated
INCOMPLETE=""  # checks that could not run, e.g. EXIF without exiftool

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
    local byte_locale="${4:-}" # "byte": run grep under LC_ALL=C (pattern holds raw UTF-8 bytes)
    local results rc errfile
    errfile=$(mktemp)
    if [ "$byte_locale" = "byte" ]; then
        results=$(LC_ALL=C grep -rinE --binary-files=without-match \
            "${TEXT_EXCLUDES[@]}" \
            -- "$pattern" "$SKILL_DIR" 2>"$errfile")
    else
        results=$(grep -rinE --binary-files=without-match \
            "${TEXT_EXCLUDES[@]}" \
            -- "$pattern" "$SKILL_DIR" 2>"$errfile")
    fi
    rc=$?
    if [ "$rc" -ge 2 ]; then
        # grep could not evaluate this category (bad regex, unreadable file).
        # Never let that read as "no matches".
        ERRORS=1
        echo
        echo "${RED}## $category${NC} ERROR: grep failed (rc=$rc); category not fully evaluated"
        sed 's/^/  /' "$errfile" | head -5
    fi
    rm -f "$errfile"
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
# Helper: optional EXIF scan via exiftool. If binary files are present and
# exiftool is not installed, the check is recorded as INCOMPLETE (exit 3
# under --strict) rather than reported as clean. When present, mirrors
# validate_skills.sh rule 10, plus the email and (case-insensitive) user
# patterns used by the text scans.
# ---------------------------------------------------------------------
scan_exif() {
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

    if ! command -v exiftool >/dev/null 2>&1; then
        echo "${YEL}## Binary EXIF metadata${NC} NOT CHECKED (exiftool not installed; ${#binary_files[@]} binary file(s) unscanned)"
        echo "  Install: brew install exiftool   # macOS"
        echo "           sudo apt-get install -y libimage-exiftool-perl   # Ubuntu"
        INCOMPLETE="${INCOMPLETE}EXIF metadata of ${#binary_files[@]} binary file(s) (exiftool not installed); "
        return 0
    fi

    local pii_pattern='/Users/[a-zA-Z]|/home/[a-zA-Z]'

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
        local hit=0
        if printf '%s\n' "$line" | grep -qE -- "$pii_pattern"; then
            hit=1
        elif printf '%s\n' "$line" | grep -E -- "$EMAIL_PATTERN" \
                | grep -qvE -- "$EMAIL_WHITELIST"; then
            hit=1
        elif [ -n "$EXTRA_PATTERNS" ] \
                && printf '%s\n' "$line" | grep -qiE -- "$EXTRA_PATTERNS"; then
            hit=1
        fi
        if [ "$hit" -eq 1 ]; then
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

# Shared by the text scan and the EXIF scan.
EMAIL_PATTERN='[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
EMAIL_WHITELIST='example\.com|example\.org|example\.net|your@email|user@host|noreply@|placeholder|<your-email>|<email>'

# Hangul syllable block U+AC00..U+D7A3 spelled as UTF-8 byte sequences, so the
# class needs no locale collation ([가-힣] makes GNU grep fail with "Invalid
# collation character" under C.UTF-8, and never matches under C/POSIX).
# Used only with scan_text's "byte" mode (LC_ALL=C).
HANGUL_SYL=$'(\xEA[\xB0-\xBF][\x80-\xBF]|[\xEB\xEC][\x80-\xBF][\x80-\xBF]|\xED[\x80-\x9D][\x80-\xBF]|\xED\x9E[\x80-\xA3])'

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
scan_text "Email Addresses" \
    "$EMAIL_PATTERN" \
    "$EMAIL_WHITELIST"

# Internal infrastructure leakage.
scan_text "IP Addresses / Internal URLs" \
    '\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b|https?://[a-z0-9-]+\.(internal|local|corp)'

# rule 6: institutional references. `\b` word boundaries replace the
# `(?<!...)` lookbehind that the original grep -E silently failed on.
scan_text "Institutional References" \
    '\b(SNUH|AMC|SMC|KAIST|SNU|ASAN|MGH|UCSF)\b|Mayo Clinic|Johns Hopkins|Samsung Medical|Severance|Asan Medical'

# rule 6 cont.: titled academic roles with adjacent surname.
# Run in byte mode: the Hangul class is spelled as UTF-8 bytes (HANGUL_SYL). The old
# `[가-힣]` range made grep exit 2 under UTF-8 locales, which silently disabled this whole
# category (English branches included); under C/POSIX it degraded to a byte set that in
# effect still required the 님 suffix. The 님 stays required here: without it the name slot
# swallows job descriptions (`지도 교수`), and scripts/check_precedent.py suppresses those with
# a lookahead stoplist that grep -E cannot express. Known limit: a bare third-person
# `<name> 교수` is not caught by this script (check_precedent.py does catch it).
scan_text "Academic Roles with Names" \
    "professor [A-Z][a-z]+|Prof\\. [A-Z]|Dr\\. [A-Z][a-z]+|PGY[0-9]|${HANGUL_SYL}{2,4}[[:space:]]*(교수|선생|박사|원장)님" \
    "" byte

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
if [ "$ERRORS" -ne 0 ]; then
    echo "${RED}RESULT: ERROR -- at least one check could not run ($TOTAL finding(s) among the checks that did)${NC}"
    echo "=========================================="
    exit 2
elif [ "$FOUND" -eq 0 ] && [ -n "$INCOMPLETE" ]; then
    echo "${YEL}RESULT: INCOMPLETE (0 findings; not checked: ${INCOMPLETE%; })${NC}"
    echo "=========================================="
    if [ "$STRICT" -eq 1 ]; then
        exit 3
    fi
    exit 0
elif [ "$FOUND" -eq 0 ]; then
    echo "${GRN}RESULT: CLEAN (0 findings)${NC}"
    echo "=========================================="
    exit 0
else
    echo "${RED}RESULT: $TOTAL FINDING(S) DETECTED${NC}"
    echo "Review and fix all findings before publishing."
    echo "=========================================="
    exit 1
fi

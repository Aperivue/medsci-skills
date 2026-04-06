#!/bin/sh
# audit_skill.sh -- PII and hardcoded-path scanner for Claude Code skills
# Usage: audit_skill.sh <skill_directory> [extra_patterns]
#
# Arguments:
#   skill_directory   Path to the skill directory to audit
#   extra_patterns    Optional pipe-separated additional grep patterns
#                     e.g., "john|doe|MIT Medical"
#
# Exit codes:
#   0  Clean -- no PII findings
#   1  Findings detected -- review required
#   2  Usage error

set -e

if [ -z "$1" ]; then
    echo "Usage: audit_skill.sh <skill_directory> [extra_patterns]"
    echo ""
    echo "Example:"
    echo "  audit_skill.sh ~/.claude/skills/my-skill"
    echo "  audit_skill.sh ./skills/my-skill \"jane|doe|Stanford\""
    exit 2
fi

SKILL_DIR="$1"
EXTRA_PATTERNS="${2:-}"

if [ ! -d "$SKILL_DIR" ]; then
    echo "Error: Directory not found: $SKILL_DIR"
    exit 2
fi

FOUND=0
TOTAL=0

# --- Helper ---
scan_category() {
    category="$1"
    pattern="$2"

    results=$(grep -rinE "$pattern" "$SKILL_DIR" 2>/dev/null | grep -v "\.git/" | grep -v "audit_skill.sh" | grep -v "pii-patterns.md" || true)

    if [ -n "$results" ]; then
        count=$(echo "$results" | wc -l | tr -d ' ')
        TOTAL=$((TOTAL + count))
        FOUND=1
        echo ""
        echo "## $category ($count match(es))"
        echo "$results" | while IFS= read -r line; do
            echo "  $line"
        done
    fi
}

echo "=========================================="
echo "PII Audit: $SKILL_DIR"
echo "=========================================="

# --- Category scans ---

scan_category "Hardcoded Paths" \
    "/Users/[a-zA-Z]|/home/[a-zA-Z]|~/Documents|~/Desktop|~/Downloads|~/Projects"

scan_category "Email Addresses" \
    "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

scan_category "IP Addresses / Internal URLs" \
    "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+|https?://[a-z]+\.(internal|local|corp)"

scan_category "Institutional References" \
    "SNUH|(?<![a-zA-Z])AMC(?![a-zA-Z])|(?<![a-zA-Z])SMC(?![a-zA-Z])|KAIST|(?<![a-zA-Z])SNU(?![a-zA-Z])|ASAN|Mayo Clinic|Johns Hopkins|(?<![a-zA-Z])MGH(?![a-zA-Z])"

scan_category "Academic Roles with Names" \
    "professor [A-Z][a-z]+|Prof\. [A-Z]|Dr\. [A-Z][a-z]+|PGY[0-9]"

scan_category "Language Hardcoding" \
    "in Korean|한국어로|Korean language|communicate in Korean|in Japanese|in Chinese"

scan_category "Location Specifics" \
    "Seoul|Busan|Tokyo|Beijing|서울|부산|울산|창원"

# --- User-provided extra patterns ---
if [ -n "$EXTRA_PATTERNS" ]; then
    scan_category "User-Specified Patterns" "$EXTRA_PATTERNS"
fi

# --- Summary ---
echo ""
echo "=========================================="
if [ "$FOUND" -eq 0 ]; then
    echo "RESULT: CLEAN (0 findings)"
    echo "=========================================="
    exit 0
else
    echo "RESULT: $TOTAL FINDING(S) DETECTED"
    echo "Review and fix all findings before publishing."
    echo "=========================================="
    exit 1
fi

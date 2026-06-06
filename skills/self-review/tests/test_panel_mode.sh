#!/usr/bin/env bash
# Structural + PII regression tests for self-review --panel mode (Phase 2.6).
# Pure file checks — no agent invocation. Run from anywhere.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILL="$REPO_ROOT/skills/self-review/SKILL.md"
TEMPLATE="$REPO_ROOT/skills/self-review/references/panel_review_template.md"
PROBE_DIR="$REPO_ROOT/skills/self-review/references/domain-probes"

fail=0
ran=0
check() {
    local label="$1"; shift
    ran=$((ran + 1))
    if "$@" >/dev/null 2>&1; then
        printf '  PASS  %s\n' "$label"
    else
        printf '  FAIL  %s\n' "$label"
        fail=$((fail + 1))
    fi
}

[[ -f "$SKILL" ]] || { echo "ENV-ERR: SKILL.md missing" >&2; exit 2; }

# 1. Panel section + flag present.
check "Phase 2.6 panel section present"       grep -qE '^### Phase 2\.6: Multi-Agent Panel Review' "$SKILL"
check "--panel flag documented in Optional Flags" grep -qE '^- `--panel`:' "$SKILL"
check "default stays single-pass (off by default)" grep -qi 'off by default' "$SKILL"
check "--fix x --panel guard documented"       grep -qi 'Do \*\*not\*\* combine with `--fix`' "$SKILL"

# 2. Reviewer-set mapping names all four domain-probe modules.
for m in survival_prognostic sr_ma radiomics narrative_review; do
    check "reviewer-set table references $m module" grep -qE "domain-probes/$m\.md" "$SKILL"
done

# 3. Template exists and carries the schema fields + skeletons.
check "panel_review_template.md exists"         test -f "$TEMPLATE"
check "template references skill-dir path in SKILL.md" grep -qE 'references/panel_review_template\.md' "$SKILL"
check "template has reviewer schema fields"     grep -qE '"severity": "Fatal \| Fixable"' "$TEMPLATE"
check "template has editor synthesis skeleton"  grep -qi 'Editor synthesis prompt skeleton' "$TEMPLATE"

# 4. Vendored probe modules each reviewer loads exist.
for m in survival_prognostic sr_ma radiomics narrative_review; do
    check "vendored module present: $m.md"      test -f "$PROBE_DIR/$m.md"
done

# 5. PoC-content-leak scan on the PoC-derived template.
#    The authoritative PII gate for names / mentors / institutions / project
#    codes is scripts/check_precedent.py (SHA-256 hashed, run repo-wide by
#    validate_skills.sh). Do NOT duplicate those identifiers in cleartext here —
#    that would re-introduce the very PII as a public string (self-doxxing,
#    oss-publication-pii-guard §5). This check is belt-and-suspenders for the
#    non-identifying content markers of the source PoC manuscript (a personal
#    path, the study disease term, the cohort N) that would signal the template
#    was not fully generalized. POSIX-safe (no \b).
POC_MARKERS='/Users/|/home/|emphysema|41,?291'
ran=$((ran + 1))
if grep -nEi "$POC_MARKERS" "$TEMPLATE"; then
    printf '  FAIL  PoC-content-leak scan (panel_review_template.md)\n'
    fail=$((fail + 1))
else
    printf '  PASS  PoC-content-leak scan (panel_review_template.md)\n'
fi

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]

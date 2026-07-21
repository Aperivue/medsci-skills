#!/usr/bin/env bash
# Self-test for scripts/verify_checklist_fidelity.py — a bundled checklist must match the official
# instrument it claims to be.
#
# Issue #352: the file labelled "TRIPOD+AI 2024" was actually TRIPOD 2015 + separately-numbered `-AI`
# additions — wrong section sequence, non-canonical identifiers, no Open Science, no PPI. Nothing
# caught it: check_checklist_exists only checks the file is present, check_framework_naming only
# checks it names its base. So this gate regresses the exact defect from the issue and demands it
# fail, and holds the gate silent on the corrected file.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
G="$REPO_ROOT/skills/check-reporting/scripts/verify_checklist_fidelity.py"

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-52s exit=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-52s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }

# 1) the live repo's corrected TRIPOD+AI file passes
python3 "$G" --strict >/dev/null 2>&1
ck "live repo: TRIPOD+AI matches the official 27/52 inventory" 0 "$?"

# 2) REGRESSION — point the gate at a fixture tree carrying the #352 defect (TRIPOD 2015 + -AI items,
#    no Open Science / PPI, non-canonical identifiers, no DOI). It must fail.
FIX="$(mktemp -d)"; trap 'rm -rf "$FIX"' EXIT
mkdir -p "$FIX/skills/check-reporting/references/checklists"
cat > "$FIX/skills/check-reporting/references/checklists/TRIPOD_AI.md" <<'MD'
# TRIPOD+AI Checklist
Version: TRIPOD+AI 2024

## Checklist Items

Items marked with **(AI)** are specific to the AI extension. All other items are from TRIPOD 2015.

### Title and Abstract
| # | Item | Description |
|---|------|-------------|
| 1 | Title | Identify the study. |
| 1-AI | Title (AI) | Identify AI/ML methods. |
| 2 | Abstract | Provide a summary. |

### Methods
| # | Item | Description |
|---|------|-------------|
| 10-AI-a | Model architecture (AI) | Describe the architecture. |

### Discussion
| # | Item | Description |
|---|------|-------------|
| 18 | Limitations | Discuss limitations. |
| 20 | Implications | Discuss clinical use. |

## MedSci supplemental
MD
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "REGRESSION: the #352 defect (2015 + -AI, no 18/19) fails" 1 "$?"

# ...and the message must name the specific defects, not just exit nonzero
OUT="$(python3 "$G" --root "$FIX" 2>&1)"
echo "$OUT" | grep -q "Open science"          && ck "names the missing Open science section" 0 0 || ck "names the missing Open science section" 0 1
echo "$OUT" | grep -q "non-canonical"          && ck "names the non-canonical -AI identifiers" 0 0 || ck "names the non-canonical -AI identifiers" 0 1
echo "$OUT" | grep -q "10.1136/bmj-2023-078378" && ck "names the missing source DOI marker"    0 0 || ck "names the missing source DOI marker"    0 1

# 3) NEGATIVE — a corrected copy in the fixture tree passes (proves it is not always-fail)
cp "$REPO_ROOT/skills/check-reporting/references/checklists/TRIPOD_AI.md" \
   "$FIX/skills/check-reporting/references/checklists/TRIPOD_AI.md"
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "NEGATIVE: the corrected file passes in a fixture tree too" 0 "$?"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1

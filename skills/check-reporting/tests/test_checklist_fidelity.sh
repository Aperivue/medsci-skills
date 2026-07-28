#!/usr/bin/env bash
# Self-test for scripts/verify_checklist_fidelity.py — a bundled checklist must match the official
# instrument it claims to be.
#
# Issue #352: the file labelled "TRIPOD+AI 2024" was actually TRIPOD 2015 + separately-numbered `-AI`
# additions — wrong section sequence, non-canonical identifiers, no Open Science, no PPI. Nothing
# caught it: check_checklist_exists only checks the file is present, check_framework_naming only
# checks it names its base.
#
# The same fidelity audit (2026-07-21) found two more of the same class:
#   - CLEAR: invented a 7-topical-domain taxonomy (item 1 = "Study hypothesis"); official CLEAR is
#     numbered by manuscript section (item 1 = Title, item 44 = baseline demographics), non-essential
#     items are 53 and 58 (the file said 17 and 57).
#   - MI-CLEAR-LLM: labelled "Version 2025" but carried the 2024 SIX-item body; official 2025 has EIGHT
#     item categories (Access mode, Input data type, Adaptation strategy promoted to first-class items).
#
# This gate regresses all three defects and demands they fail, and holds the gate silent on the
# corrected files.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
G="$REPO_ROOT/skills/check-reporting/scripts/verify_checklist_fidelity.py"
CK_DIR="skills/check-reporting/references/checklists"

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-56s exit=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-56s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }

# Seed a fixture tree with the LIVE (corrected) copies of every checklist the gate knows about, so a
# regression can then overwrite exactly one file with a defect and isolate the failure to it.
seed() {
  local dir="$1"
  mkdir -p "$dir/$CK_DIR"
  cp "$REPO_ROOT/$CK_DIR/TRIPOD_AI.md"    "$dir/$CK_DIR/"
  cp "$REPO_ROOT/$CK_DIR/CLEAR.md"        "$dir/$CK_DIR/"
  cp "$REPO_ROOT/$CK_DIR/MI_CLEAR_LLM.md" "$dir/$CK_DIR/"
  cp "$REPO_ROOT/$CK_DIR/GATHER.md"       "$dir/$CK_DIR/"
}

# 1) the live repo's corrected files pass
python3 "$G" --strict >/dev/null 2>&1
ck "live repo: all bundled checklists match their official inventory" 0 "$?"

FIX="$(mktemp -d)"; trap 'rm -rf "$FIX"' EXIT

# 2) REGRESSION — the #352 TRIPOD+AI defect (TRIPOD 2015 + -AI items, no Open Science / PPI, no DOI)
seed "$FIX"
cat > "$FIX/$CK_DIR/TRIPOD_AI.md" <<'MD'
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
ck "REGRESSION #352: TRIPOD 2015 + -AI (no 18/19) fails" 1 "$?"
OUT="$(python3 "$G" --root "$FIX" 2>&1)"
echo "$OUT" | grep -q "Open science"            && ck "  names the missing Open science section"   0 0 || ck "  names the missing Open science section"   0 1
echo "$OUT" | grep -q "TRIPOD_AI.md.*forbidden" && ck "  names the non-canonical -AI identifiers"   0 0 || ck "  names the non-canonical -AI identifiers"   0 1
echo "$OUT" | grep -q "10.1136/bmj-2023-078378" && ck "  names the missing source DOI marker"       0 0 || ck "  names the missing source DOI marker"       0 1

# 3) REGRESSION — CLEAR regrouped into topical "domains" (item 1 = Study hypothesis), no manuscript
#    sections, no radiomic-title marker. The real bundled defect found on 2026-07-21.
seed "$FIX"
cat > "$FIX/$CK_DIR/CLEAR.md" <<'MD'
# CLEAR Checklist
Version: CLEAR 2023
Source: https://doi.org/10.1186/s13244-023-01415-8

## Checklist Items (58 items)

### Domain 1: Study Design (Items 1-8)
| # | Item | Description |
|---|------|-------------|
| 1 | Study hypothesis | State the study hypothesis. |
| 2 | Study design | Describe the study design. |

### Domain 5: Modeling (Items 35-44)
| # | Item | Description |
|---|------|-------------|
| 44 | Temporal validation | Report temporal validation. |

## Notes for assessors
Items 17 and 57 are aspirational.
MD
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "REGRESSION CLEAR: topical-domain regrouping fails" 1 "$?"
OUT="$(python3 "$G" --root "$FIX" 2>&1)"
echo "$OUT" | grep -q "CLEAR.md.*forbidden"          && ck "  names the invented Domain grouping"      0 0 || ck "  names the invented Domain grouping"      0 1
echo "$OUT" | grep -q "### Title"                     && ck "  names the missing Title section"          0 0 || ck "  names the missing Title section"          0 1
echo "$OUT" | grep -q "specifying the radiomic"       && ck "  names the missing item-1 (Title) marker"  0 0 || ck "  names the missing item-1 (Title) marker"  0 1

# 4) REGRESSION — MI-CLEAR-LLM labelled 2025 but carrying the 2024 six-item body (no numbered item
#    table, and none of the three items promoted to first-class in 2025).
seed "$FIX"
cat > "$FIX/$CK_DIR/MI_CLEAR_LLM.md" <<'MD'
# MI-CLEAR-LLM Checklist
**Version:** 2025 (expanded from 2024 original)
**Source:** https://kjronline.org/DOIx.php?id=10.3348/kjr.2025.1522

## Checklist Items

## Item 1 — LLM Identification and Specifications
## Item 2 — Stochasticity Handling
## Item 3 — Full Prompt Text
## Item 4 — Prompt Execution Details
## Item 5 — Prompt Testing and Optimization
## Item 6 — Test Data Independence

## Notes for assessors
| Category | Items |
|----------|-------|
| **TOTAL** | **6** |
MD
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "REGRESSION MI-CLEAR-LLM: 2024 body under a 2025 label fails" 1 "$?"
OUT="$(python3 "$G" --root "$FIX" 2>&1)"
echo "$OUT" | grep -q "expected 1..8"                 && ck "  names the missing 8-item inventory"       0 0 || ck "  names the missing 8-item inventory"       0 1
echo "$OUT" | grep -q "### 2. Access mode"            && ck "  names the missing 2025 Access-mode item"  0 0 || ck "  names the missing 2025 Access-mode item"  0 1

# 5) NEGATIVE — a fully corrected fixture tree passes (proves the gate is not always-fail)
seed "$FIX"
python3 "$G" --root "$FIX" --strict >/dev/null 2>&1
ck "NEGATIVE: a corrected fixture tree passes" 0 "$?"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1

#!/usr/bin/env bash
# pre_submission_gate.sh — manage-refs four-stage pre-submission orchestration.
#
# Chains the existing scripts in the order required before a manuscript DOCX
# leaves the project. Each stage delegates to the canonical script under
# /manage-refs or /verify-refs — this wrapper does NOT reimplement any check.
#
# Stages (run in order; first failure aborts the chain):
#   1. check_citation_keys.py  — markdown [@bibkey] ↔ refs.bib key matching
#   2. verify_refs.py --strict — refs.bib ↔ PubMed/CrossRef entry verification
#   3. render_pandoc.sh        — (only when --docx is not provided) render DOCX
#   4. check_xref.py --strict  — manuscript ↔ rendered DOCX cross-reference QC
#                                (optionally with --allow-separate-attachments)
#
# Usage:
#   pre_submission_gate.sh --md MD --bib BIB [--docx DOCX] [--journal CSL]
#                          [--allow-separate-attachments] [--qc-dir DIR]
#
# Exit codes:
#   0 — all stages PASS; qc/pre_submission_gate.json contains submission_safe:true
#   1 — at least one stage FAIL; qc/pre_submission_gate.json contains submission_safe:false
#   2 — usage / missing-input error
#
# The script writes qc/pre_submission_gate.json with one record per stage
# (status, exit_code, stderr_excerpt) plus a top-level submission_safe boolean.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_REFS_DIR="${SCRIPT_DIR}/../../verify-refs/scripts"

usage() {
  cat >&2 <<'EOF'
Usage: pre_submission_gate.sh --md MD --bib BIB [options]

Required:
  --md PATH                   Manuscript markdown SSOT
  --bib PATH                  BibTeX bibliography

Optional:
  --docx PATH                 Pre-built DOCX. If omitted, render via render_pandoc.sh.
  --journal CSL_KEY           Journal CSL key (default: vancouver)
  --allow-separate-attachments
                              Forwarded to check_xref.py; downgrades MISSING_DOCX
                              from FAIL to WARN.
  --qc-dir PATH               Output artifact directory (default: qc/)
  -h, --help                  Show this help

Outputs:
  <qc-dir>/pre_submission_gate.json   summary
  <qc-dir>/reference_audit.json       verify_refs output
  <qc-dir>/xref_audit.json            check_xref output

Exit: 0 = pass, 1 = fail, 2 = bad input.
EOF
  exit 2
}

MD=""
BIB=""
DOCX=""
JOURNAL="vancouver"
ALLOW_SEPARATE_ATTACHMENTS=0
QC_DIR="qc"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --md)       MD="$2"; shift 2 ;;
    --bib)      BIB="$2"; shift 2 ;;
    --docx)     DOCX="$2"; shift 2 ;;
    --journal)  JOURNAL="$2"; shift 2 ;;
    --allow-separate-attachments)
                ALLOW_SEPARATE_ATTACHMENTS=1; shift ;;
    --qc-dir)   QC_DIR="$2"; shift 2 ;;
    -h|--help)  usage ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      ;;
  esac
done

[[ -z "$MD"  ]] && { echo "ERROR: --md is required" >&2;  usage; }
[[ -z "$BIB" ]] && { echo "ERROR: --bib is required" >&2; usage; }
[[ -f "$MD"  ]] || { echo "ERROR: markdown not found: $MD" >&2; exit 2; }
[[ -f "$BIB" ]] || { echo "ERROR: refs.bib not found: $BIB" >&2; exit 2; }

mkdir -p "$QC_DIR"

ARTIFACT="$QC_DIR/pre_submission_gate.json"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Stage helpers ---------------------------------------------------------------

declare -a STAGE_NAMES=()
declare -a STAGE_STATUSES=()
declare -a STAGE_EXITS=()
declare -a STAGE_NOTES=()

record_stage() {
  local name="$1" status="$2" exit_code="$3" note="$4"
  STAGE_NAMES+=("$name")
  STAGE_STATUSES+=("$status")
  STAGE_EXITS+=("$exit_code")
  STAGE_NOTES+=("$note")
}

write_artifact() {
  local safe="$1"
  python3 - "$ARTIFACT" "$TIMESTAMP" "$safe" \
    "${STAGE_NAMES[@]}" "::sep::" \
    "${STAGE_STATUSES[@]}" "::sep::" \
    "${STAGE_EXITS[@]}" "::sep::" \
    "${STAGE_NOTES[@]}" <<'PY'
import json, sys
out_path, ts, safe = sys.argv[1], sys.argv[2], sys.argv[3] == "true"
rest = sys.argv[4:]

def split_groups(values, sep="::sep::"):
    groups = []
    cur = []
    for v in values:
        if v == sep:
            groups.append(cur); cur = []
        else:
            cur.append(v)
    groups.append(cur)
    return groups

names, statuses, exits, notes = split_groups(rest)
gates = [
    {"stage": n, "status": s, "exit_code": int(e), "note": no}
    for n, s, e, no in zip(names, statuses, exits, notes)
]
payload = {
    "version": "1.0",
    "timestamp": ts,
    "submission_safe": safe,
    "gates": gates,
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)
PY
}

abort_with_failure() {
  write_artifact "false"
  echo "[pre_submission_gate] FAIL (artifact: $ARTIFACT)" >&2
  exit 1
}

# Stage 1: citation keys ------------------------------------------------------

echo "[pre_submission_gate] stage 1/4: check_citation_keys.py"
STAGE1_LOG="$(mktemp)"
if python3 "$SCRIPT_DIR/check_citation_keys.py" "$MD" "$BIB" > "$STAGE1_LOG" 2>&1; then
  record_stage "check_citation_keys" "PASS" 0 "$(tail -n 1 "$STAGE1_LOG")"
  cat "$STAGE1_LOG"
else
  rc=$?
  record_stage "check_citation_keys" "FAIL" "$rc" "$(tail -n 5 "$STAGE1_LOG" | tr '\n' '; ')"
  cat "$STAGE1_LOG"
  rm -f "$STAGE1_LOG"
  abort_with_failure
fi
rm -f "$STAGE1_LOG"

# Stage 2: verify_refs.py against refs.bib ------------------------------------

echo "[pre_submission_gate] stage 2/4: verify_refs.py --strict"
PROJECT_ROOT="$(dirname "$QC_DIR")"
[[ -z "$PROJECT_ROOT" || "$PROJECT_ROOT" == "." ]] && PROJECT_ROOT="$(pwd)"
STAGE2_LOG="$(mktemp)"
if python3 "$VERIFY_REFS_DIR/verify_refs.py" "$BIB" \
     --project-root "$PROJECT_ROOT" --strict > "$STAGE2_LOG" 2>&1; then
  record_stage "verify_refs" "PASS" 0 "$(grep -E '^\[verify-refs\]|"counts"' "$STAGE2_LOG" | tail -n 1)"
  cat "$STAGE2_LOG"
else
  rc=$?
  record_stage "verify_refs" "FAIL" "$rc" "$(tail -n 5 "$STAGE2_LOG" | tr '\n' '; ')"
  cat "$STAGE2_LOG"
  rm -f "$STAGE2_LOG"
  abort_with_failure
fi
rm -f "$STAGE2_LOG"

# Stage 3: render DOCX if missing --------------------------------------------

if [[ -z "$DOCX" ]]; then
  echo "[pre_submission_gate] stage 3/4: render_pandoc.sh -j $JOURNAL"
  DERIVED_DOCX="${MD%.md}.docx"
  STAGE3_LOG="$(mktemp)"
  if bash "$SCRIPT_DIR/render_pandoc.sh" -j "$JOURNAL" -i "$MD" -b "$BIB" -o "$DERIVED_DOCX" \
       > "$STAGE3_LOG" 2>&1; then
    DOCX="$DERIVED_DOCX"
    record_stage "render_pandoc" "PASS" 0 "rendered $DERIVED_DOCX"
    cat "$STAGE3_LOG"
  else
    rc=$?
    record_stage "render_pandoc" "FAIL" "$rc" "$(tail -n 5 "$STAGE3_LOG" | tr '\n' '; ')"
    cat "$STAGE3_LOG"
    rm -f "$STAGE3_LOG"
    abort_with_failure
  fi
  rm -f "$STAGE3_LOG"
else
  echo "[pre_submission_gate] stage 3/4: skipped (pre-built DOCX: $DOCX)"
  record_stage "render_pandoc" "SKIPPED" 0 "pre-built DOCX supplied"
fi

[[ -f "$DOCX" ]] || { echo "ERROR: DOCX not found after stage 3: $DOCX" >&2; abort_with_failure; }

# Stage 4: check_xref.py ------------------------------------------------------

echo "[pre_submission_gate] stage 4/4: check_xref.py --strict"
XREF_OUT="$QC_DIR/xref_audit.json"
STAGE4_ARGS=(--md "$MD" --docx "$DOCX" --out "$XREF_OUT" --strict)
if [[ "$ALLOW_SEPARATE_ATTACHMENTS" == "1" ]]; then
  STAGE4_ARGS+=(--allow-separate-attachments)
fi
STAGE4_LOG="$(mktemp)"
if python3 "$SCRIPT_DIR/check_xref.py" "${STAGE4_ARGS[@]}" > "$STAGE4_LOG" 2>&1; then
  record_stage "check_xref" "PASS" 0 "$(grep -E 'wrote|WARN|SUBMISSION' "$STAGE4_LOG" | tr '\n' '; ')"
  cat "$STAGE4_LOG"
else
  rc=$?
  record_stage "check_xref" "FAIL" "$rc" "$(grep -E 'BLOCKED|wrote' "$STAGE4_LOG" | tr '\n' '; ')"
  cat "$STAGE4_LOG"
  rm -f "$STAGE4_LOG"
  abort_with_failure
fi
rm -f "$STAGE4_LOG"

# All stages passed -----------------------------------------------------------

write_artifact "true"
echo "[pre_submission_gate] PASS (artifact: $ARTIFACT)"
exit 0

#!/usr/bin/env bash
# verify-refs CLI wrapper — thin shell in front of verify_refs.py for use by
# the pre-submission hook and ad-hoc manual runs.
#
# Usage:   verify_cli.sh <manuscript.docx|.md|.bib|.txt|.tsv> [--offline]
# Exit:    0 = submission-safe (no FABRICATED/MISMATCH)
#          1 = FABRICATED or MISMATCH found -> hook should block
#          2 = input missing / usage error
#          3 = no references detected (unusual; treated as non-blocking)
#
# Project root resolution: the first ancestor directory containing a
# `submission/` sibling, else the manuscript's parent directory. Output
# artifacts are written under `<project_root>/references/` and
# `<project_root>/qc/` per the skill's output contract.

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: verify_cli.sh <manuscript> [--offline]" >&2
  exit 2
fi

MANUSCRIPT="$1"; shift || true
EXTRA_ARGS=()
if [ $# -gt 0 ]; then
  EXTRA_ARGS=("$@")
fi

if [ ! -f "$MANUSCRIPT" ]; then
  echo "Not found: $MANUSCRIPT" >&2
  exit 2
fi

ABS="$(cd "$(dirname "$MANUSCRIPT")" && pwd)/$(basename "$MANUSCRIPT")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve project root: nearest ancestor whose path contains /submission/,
# otherwise the manuscript's parent directory.
PROJECT_ROOT=""
dir="$(dirname "$ABS")"
while [ "$dir" != "/" ] && [ -n "$dir" ]; do
  case "$dir" in
    */submission|*/submission/*)
      PROJECT_ROOT="${dir%/submission*}/submission/$(basename "$(dirname "$dir")")"
      [ -d "$PROJECT_ROOT" ] || PROJECT_ROOT="$dir"
      break
      ;;
  esac
  dir="$(dirname "$dir")"
done
if [ -z "$PROJECT_ROOT" ]; then
  PROJECT_ROOT="$(dirname "$ABS")"
fi

set +e
python3 "$SCRIPT_DIR/verify_refs.py" "$ABS" --project-root "$PROJECT_ROOT" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
EXIT_CODE=$?
set -e

AUDIT="$PROJECT_ROOT/qc/reference_audit.json"
echo "[verify-refs] exit=$EXIT_CODE; audit=$AUDIT" >&2
exit "$EXIT_CODE"

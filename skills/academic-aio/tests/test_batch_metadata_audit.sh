#!/usr/bin/env bash
# Regression test for academic-aio/scripts/batch_metadata_audit.py.
# Builds synthetic repos / HF cards (no committed data) and asserts: a clean
# repo reports no issues (exit 0), a repo missing README/CITATION/LICENSE fails
# under --fail-on-issue (exit 1), and an HF card carrying a PHI-shaped string is
# flagged. Stdlib-only (json/re), network-free, ASCII-only.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/batch_metadata_audit.py"
TMP="$(mktemp -d -t aio_audit_XXXX)"
trap 'rm -rf "$TMP"' EXIT

fail=0
check_exit() { local label="$1" want="$2"; shift 2
    "$@" >/dev/null 2>&1; local got=$?
    if [[ "$got" -eq "$want" ]]; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s (exit %s, want %s)\n' "$label" "$got" "$want"; fail=$((fail+1)); fi
}
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: batch_metadata_audit.py missing" >&2; exit 2; }

# --- Clean repo: README (DOI + citation + quickstart), CITATION.cff, LICENSE ---
CLEAN="$TMP/clean_repo"; mkdir -p "$CLEAN"
cat > "$CLEAN/README.md" <<'MD'
# Synthetic Tool
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.0000000-blue)](https://doi.org/10.5281/zenodo.0000000)
## Installation
pip install synthetic-tool
## How to cite
See CITATION.cff.
MD
cat > "$CLEAN/CITATION.cff" <<'CFF'
cff-version: 1.2.0
title: Synthetic Tool
version: 1.0.0
authors:
  - family-names: Kim
    given-names: Alice
    orcid: https://orcid.org/0000-0002-1825-0097
CFF
echo "MIT License" > "$CLEAN/LICENSE"
check_exit "clean repo -> exit 0 (no issues, --fail-on-issue)" 0 \
    python3 "$SCRIPT" "$CLEAN" --fail-on-issue

# --- Broken repo: directory exists but empty (all three artifacts missing) ---
BROKEN="$TMP/broken_repo"; mkdir -p "$BROKEN"
check_exit "repo missing README/CITATION/LICENSE -> exit 1" 1 \
    python3 "$SCRIPT" "$BROKEN" --fail-on-issue
# Without --fail-on-issue the same audit still exits 0 (report-only).
check_exit "report-only mode -> exit 0 even with issues" 0 \
    python3 "$SCRIPT" "$BROKEN"

# --- HF card with a PHI-shaped string (KR resident registration number) ---
CARD="$TMP/model_card.md"
cat > "$CARD" <<'MD'
---
license: mit
library_name: transformers
tags:
  - medical
---
# Model
## Intended use
Research only.
## Training data
Synthetic records, e.g. subject 900101-1234567 was excluded.
## Evaluation
AUC reported.
## Limitations
Small sample.
## Ethical considerations
De-identified.
MD
JSON_OUT="$TMP/report.json"
python3 "$SCRIPT" --hf-card "$CARD" --output "$JSON_OUT" >/dev/null 2>&1
check "HF card report written" test -s "$JSON_OUT"
check "PHI pattern flagged in HF card" python3 -c "
import json
d=json.load(open('$JSON_OUT'))
issues=' '.join(d['hf_cards'][0]['issues'])
assert 'PHI' in issues, d['hf_cards'][0]['issues']"
check_exit "HF card with PHI -> exit 1 under --fail-on-issue" 1 \
    python3 "$SCRIPT" --hf-card "$CARD" --fail-on-issue

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"

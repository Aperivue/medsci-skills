#!/usr/bin/env bash
# Phase 1C hook regression — validates verify-refs-guard.sh mode resolution.
# Covers: MODE env override, auto-detect via SSOT.yaml + qc/migration_complete,
# BYPASS env, project marker detection.

set -u

HOOK="$HOME/.claude/hooks/verify-refs-guard.sh"
if [ ! -x "$HOOK" ]; then
  echo "SKIP: $HOOK missing — Phase 1C hook not installed."
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
check() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-44s mode=%s\n' "$label" "$actual"
    pass=$((pass+1))
  else
    printf '  FAIL  %-44s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail+1))
  fi
}

# Source the hook to access resolve_mode() without running the full pipeline.
# The hook reads stdin when run as main; sourcing skips the `cat` until invoked.
# We isolate resolve_mode by extracting it via a subshell that defines the
# required surroundings.
SNIPPET="$TMP/mode_fns.sh"
sed -n '/^project_root_for/,/^}/p; /^resolve_mode/,/^}/p' "$HOOK" > "$SNIPPET"

extract_mode() {
  local file="$1"
  bash -c '
    set -u
    source "$1"
    resolve_mode "$2"
  ' _ "$SNIPPET" "$file"
}

# Fixture 1: non-SSOT project (has project.yaml but no SSOT.yaml)
mkdir -p "$TMP/legacy/submission/draft/manuscript"
touch "$TMP/legacy/project.yaml"
legacy_file="$TMP/legacy/submission/draft/manuscript/x.docx"
touch "$legacy_file"

# Fixture 2: SSOT project w/ migration_complete
mkdir -p "$TMP/ssot/submission/draft/manuscript" "$TMP/ssot/qc"
touch "$TMP/ssot/SSOT.yaml" "$TMP/ssot/qc/migration_complete"
ssot_file="$TMP/ssot/submission/draft/manuscript/x.docx"
touch "$ssot_file"

# Fixture 3: SSOT.yaml only (no migration_complete marker)
mkdir -p "$TMP/half/submission/draft/manuscript"
touch "$TMP/half/SSOT.yaml"
half_file="$TMP/half/submission/draft/manuscript/x.docx"
touch "$half_file"

echo "Phase 1C hook mode-resolution regression"
check "auto: legacy project → warn"         warn    "$(extract_mode "$legacy_file")"
check "auto: ssot + migration_complete → enforce" enforce "$(extract_mode "$ssot_file")"
check "auto: ssot without marker → warn"    warn    "$(extract_mode "$half_file")"
check "MODE=off override"                   off     "$(MEDSCI_VERIFY_REFS_MODE=off extract_mode "$ssot_file")"
check "MODE=warn override on ssot"          warn    "$(MEDSCI_VERIFY_REFS_MODE=warn extract_mode "$ssot_file")"
check "MODE=enforce override on legacy"     enforce "$(MEDSCI_VERIFY_REFS_MODE=enforce extract_mode "$legacy_file")"
check "BYPASS=1 on ssot → bypass"           bypass  "$(MEDSCI_VERIFY_REFS_BYPASS=1 extract_mode "$ssot_file")"
check "BYPASS precedence over MODE=enforce" bypass  "$(MEDSCI_VERIFY_REFS_BYPASS=1 MEDSCI_VERIFY_REFS_MODE=enforce extract_mode "$ssot_file")"

echo
echo "Summary: $pass passed, $fail failed."
[ "$fail" -eq 0 ]

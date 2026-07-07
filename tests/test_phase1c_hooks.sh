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
echo "Phase 1C hook end-to-end (FABRICATED → block in enforce mode)"

# Build a clone of the hook with the verify_cli path replaced by a stub so the
# test does not depend on network or on the real verify_refs.py behavior.
HOOK_CLONE="$TMP/verify-refs-guard.sh"
STUB_CLI="$TMP/stub_verify_cli.sh"
cat > "$STUB_CLI" <<'STUB'
#!/usr/bin/env bash
# Simulate verify_cli.sh rc=1 (FABRICATED) and write an audit hint to stderr.
echo '{"total": 1, "fabricated": 1}' > /tmp/verify-refs-guard.stdout
echo "[verify-refs] exit=1; audit=/tmp/ssot_smoke/qc/reference_audit.json" >&2
exit 1
STUB
chmod +x "$STUB_CLI"

# Escape for sed
STUB_ESCAPED="$(printf '%s' "$STUB_CLI" | sed 's:[\/&]:\\&:g')"
sed "s:^CLI=.*:CLI=\"$STUB_ESCAPED\":" "$HOOK" > "$HOOK_CLONE"
chmod +x "$HOOK_CLONE"

# SSOT project w/ migration_complete + a gated submission path
mkdir -p "$TMP/e2e/submission/draft/manuscript" "$TMP/e2e/qc"
touch "$TMP/e2e/SSOT.yaml" "$TMP/e2e/qc/migration_complete"
MS="$TMP/e2e/submission/draft/manuscript/test.md"
echo "# stub manuscript with [@fab_doi_2026]" > "$MS"

# Build PostToolUse JSON payload
PAYLOAD="$(printf '{"tool_input":{"file_path":"%s"}}' "$MS")"

set +e
OUT="$(printf '%s' "$PAYLOAD" | MEDSCI_VERIFY_REFS_MODE=auto bash "$HOOK_CLONE" 2>"$TMP/e2e.stderr")"
rc=$?
set -e

# Assertions
e2e_pass=0; e2e_fail=0
e2e_check() {
  local label="$1" cond="$2"
  if [ "$cond" = "ok" ]; then
    printf '  PASS  %s\n' "$label"; e2e_pass=$((e2e_pass+1))
  else
    printf '  FAIL  %s\n' "$label"; e2e_fail=$((e2e_fail+1))
  fi
}

if [ "$rc" -eq 2 ]; then e2e_check "hook exits 2 (block)" ok; else e2e_check "hook exits 2 (block) (got rc=$rc)" no; fi
if echo "$OUT" | grep -q '"decision"[[:space:]]*:[[:space:]]*"block"'; then
  e2e_check "stdout has decision=block" ok
else
  e2e_check "stdout has decision=block" no
fi
if echo "$OUT" | grep -q 'FABRICATED'; then
  e2e_check "reason mentions FABRICATED" ok
else
  e2e_check "reason mentions FABRICATED" no
fi

# Bypass should convert the same payload to approve.
set +e
OUT2="$(printf '%s' "$PAYLOAD" | MEDSCI_VERIFY_REFS_BYPASS=1 bash "$HOOK_CLONE" 2>/dev/null)"
rc2=$?
set -e
if [ "$rc2" -eq 0 ] && echo "$OUT2" | grep -q '"continue"[[:space:]]*:[[:space:]]*true'; then
  e2e_check "BYPASS=1 → approve (continue:true, rc=0)" ok
else
  e2e_check "BYPASS=1 → approve (got rc=$rc2)" no
fi

# Issue #14: an outgoing/ mentor-circulation draft is WARN-ONLY — a FABRICATED
# reference must NOT block even under MODE=enforce (the new patterns downgrade
# enforce -> warn), yet it must still be gated (the hook runs verify_cli).
mkdir -p "$TMP/e2e/8_Review_Comments/Prof_X/outgoing"
OG="$TMP/e2e/8_Review_Comments/Prof_X/outgoing/reply.docx"
echo "# reply with [@fab_doi_2026]" > "$OG"
PAYLOAD_OG="$(printf '{"tool_input":{"file_path":"%s"}}' "$OG")"
set +e
OUT_OG="$(printf '%s' "$PAYLOAD_OG" | MEDSCI_VERIFY_REFS_MODE=enforce bash "$HOOK_CLONE" 2>/dev/null)"
rc_og=$?
set -e
if [ "$rc_og" -ne 2 ] && echo "$OUT_OG" | grep -q '"continue"[[:space:]]*:[[:space:]]*true'; then
  e2e_check "#14 outgoing/ FABRICATED in enforce -> warn, not block" ok
else
  e2e_check "#14 outgoing/ FABRICATED -> warn (got rc=$rc_og)" no
fi

pass=$((pass + e2e_pass))
fail=$((fail + e2e_fail))

echo
echo "Summary: $pass passed, $fail failed."
[ "$fail" -eq 0 ]

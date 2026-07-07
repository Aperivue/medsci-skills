#!/usr/bin/env bash
# Regression test for scripts/validate_capabilities.py — the registry-consistency
# gate (issue #15). Confirms a clean fixture passes and each drift class fails
# under --strict, and that the live repo is clean.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V="$REPO_ROOT/scripts/validate_capabilities.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-52s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# --- helper: build a minimal fixture root at $1 with a clean registry ---
make_clean() {
  local r="$1"
  mkdir -p "$r/skills/alpha" "$r/skills/beta"
  cat > "$r/capabilities.yml" <<'YAML'
schema_version: 2
domains:
  shared_domain:
    owner: alpha
    overlaps:
      - beta
    rule: Alpha owns it; beta overlaps.
umbrellas:
  bundle:
    - - shared_domain
    - "A one-domain umbrella."
YAML
  printf 'schema_version: 2\nname: alpha\nowner_domain: shared_domain\n' > "$r/skills/alpha/skill.yml"
  printf 'schema_version: 2\nname: beta\nowner_domain: shared_domain\n' > "$r/skills/beta/skill.yml"
}

# 1) clean fixture -> exit 0 (--strict)
CLEAN="$TMP/clean"; make_clean "$CLEAN"
python3 "$V" --root "$CLEAN" --strict > /dev/null 2>&1
ck "clean registry passes (--strict)" 0 "$?"

# 2) malformed skill.yml (unquoted embedded colon) -> exit 1
BADYAML="$TMP/badyaml"; make_clean "$BADYAML"
printf 'schema_version: 2\nname: beta\nowner_domain: shared_domain\nnote: enforce redact_internal: true here\n' \
  > "$BADYAML/skills/beta/skill.yml"
python3 "$V" --root "$BADYAML" --strict > /dev/null 2>&1
ck "malformed skill.yml fails (--strict)" 1 "$?"

# 3) owner ⇄ skill disagreement (owner's owner_domain != domain) -> exit 1
BADOWNER="$TMP/badowner"; make_clean "$BADOWNER"
printf 'schema_version: 2\nname: alpha\nowner_domain: something_else\n' > "$BADOWNER/skills/alpha/skill.yml"
python3 "$V" --root "$BADOWNER" --strict > /dev/null 2>&1
ck "owner/owner_domain mismatch fails (--strict)" 1 "$?"

# 4) a skill claims a declared domain but is not owner/overlap -> exit 1
BADCLAIM="$TMP/badclaim"; make_clean "$BADCLAIM"
mkdir -p "$BADCLAIM/skills/gamma"
printf 'schema_version: 2\nname: gamma\nowner_domain: shared_domain\n' > "$BADCLAIM/skills/gamma/skill.yml"
python3 "$V" --root "$BADCLAIM" --strict > /dev/null 2>&1
ck "unlisted claimant of declared domain fails (--strict)" 1 "$?"

# 5) umbrella references an undeclared domain -> exit 1
BADUMB="$TMP/badumb"; make_clean "$BADUMB"
cat > "$BADUMB/capabilities.yml" <<'YAML'
schema_version: 2
domains:
  shared_domain:
    owner: alpha
    overlaps:
      - beta
    rule: Alpha owns it.
umbrellas:
  bundle:
    - - shared_domain
      - ghost_domain
    - "References a domain that does not exist."
YAML
python3 "$V" --root "$BADUMB" --strict > /dev/null 2>&1
ck "umbrella -> undeclared domain fails (--strict)" 1 "$?"

# 6) drift tolerated without --strict -> exit 0
python3 "$V" --root "$BADCLAIM" > /dev/null 2>&1
ck "drift tolerated without --strict" 0 "$?"

# 7) the live repo registry must be clean (the CI invariant)
python3 "$V" --strict > /dev/null 2>&1
ck "live repo registry clean (--strict)" 0 "$?"

echo "----"
echo "test_capabilities_validator: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

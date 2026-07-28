#!/usr/bin/env bash
# Regression test for the "instruction points at an unshipped personal rule" check
# in scripts/validate_skills.sh.
#
# Why the check exists: the distribution bundle is skills/ + installers/ only
# (metadata/distribution_files.json). A shipped skill that says "apply
# ~/.claude/rules/numerical-safety.md" is telling an installed reader to open a
# file that exists on exactly one machine on earth. Nothing errors — the step is
# simply skipped, and the skill looks like it enforced something it did not. Four
# such instructions shipped for months; the repo's own 2026-07-11 audit had
# already named the class.
#
# Why this drives the whole validator rather than grepping the pattern: a regex
# that matches in isolation says nothing about whether validate_skills.sh is
# wired to run it. And why one run rather than one per case: the validator
# reports the offending FILE, so a single pass over a fixture skill whose
# references/ holds both shapes proves the positives are named AND the negatives
# are not — a stronger assertion than an exit code, at a fifth of the runtime.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Unique per run: a fixed fixture path means two concurrent invocations delete
# each other's files mid-scan, and every assertion then fails for a reason that
# has nothing to do with the gate.
FIXTURE_DIR="$REPO_ROOT/skills/zz-ruleref-fixture-$$"
VERDICT="Instruction points at an unshipped personal rule"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-60s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-60s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

cleanup() { rm -rf "$FIXTURE_DIR"; }
trap cleanup EXIT
cleanup
mkdir -p "$FIXTURE_DIR/references"

cat > "$FIXTURE_DIR/SKILL.md" <<'EOF'
---
name: zz-ruleref-fixture
description: Throwaway fixture created and deleted by tests/test_personal_rule_refs.sh.
triggers: none
tools: Read
model: inherit
---

# Fixture

Created and removed inside a single test run. If you are reading this on disk, a test crashed.

## Anti-Hallucination

- This skill is a test fixture and produces nothing.
EOF

# --- POSITIVES: a verb governs the path, so the instruction IS the missing file ---

# The exact line that shipped in render-pdf-doc/SKILL.md.
cat > "$FIXTURE_DIR/references/pos-apply.md" <<'EOF'
- Numerical content in tables: apply `~/.claude/rules/numerical-safety.md`. Read from CSV.
EOF

# A second verb, so the check is not a one-verb special case.
cat > "$FIXTURE_DIR/references/pos-follow.md" <<'EOF'
- Before circulating, follow `~/.claude/rules/senior-mentor-circulation.md`.
EOF

# --- NEGATIVES: the rule is in the sentence; the path only says where it came from ---

# Blocking this shape would fire on ~70 correctly-written citations at once, and
# the check would never land.
cat > "$FIXTURE_DIR/references/neg-provenance.md" <<'EOF'
- **Body language**: English only (per `~/.claude/rules/academic-lecture-style.md`).
EOF

# The disclosure note every affected skill now carries. It quotes the path shape
# on purpose; a check that fired here would make the fix unwritable.
cat > "$FIXTURE_DIR/references/neg-disclosure.md" <<'EOF'
Some passages in this skill cite a path of the form `~/.claude/rules/<name>.md`. They are not
shipped with this skill and appear only as provenance for where a convention came from.
EOF

# An imperative and a path in different table cells. `[^|]` in the pattern is what
# keeps them apart; without it the check fires on any long row containing both.
cat > "$FIXTURE_DIR/references/neg-table-cell.md" <<'EOF'
| Step | Rule | Source |
|---|---|---|
| 3 | Numbers must come from the CSV | `~/.claude/rules/numerical-safety.md` |
EOF

OUT="$(bash "$REPO_ROOT/scripts/validate_skills.sh" 2>&1)"
FLAGGED="$(printf '%s\n' "$OUT" | grep "$VERDICT" || true)"

FIXTURE_NAME="$(basename "$FIXTURE_DIR")"
named() { printf '%s\n' "$FLAGGED" | grep -q "$FIXTURE_NAME/references/$1"; }

named 'pos-apply.md';      ck "an 'apply <personal rule path>' instruction is caught"        0 "$?"
named 'pos-follow.md';     ck "a 'follow <personal rule path>' instruction is caught"        0 "$?"
named 'neg-provenance.md'; ck "a '(per <path>)' provenance citation is left alone"           1 "$?"
named 'neg-disclosure.md'; ck "the 'not shipped' disclosure note does not self-trip"         1 "$?"
named 'neg-table-cell.md'; ck "an imperative in another table cell does not reach the path"  1 "$?"

# The check must be reachable at all: if validate_skills.sh ever stops emitting
# this verdict, every assertion above still "passes" by never matching.
[ -n "$FLAGGED" ]
ck "the validator emitted the verdict at all (the check is wired)" 0 "$?"

cleanup

echo "----"
echo "test_personal_rule_refs: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Regression test: validate_skills.sh must actually READ every directory it claims
# to scan.
#
# The defect this exists to stop: TEXT_EXTS was a bare string expanded unquoted
# into `find`, so `*.md` was pathname-expanded against the CALLER'S working
# directory before find saw it. Run from the repo root — which is how CI and every
# documented invocation run it — that became the thirteen top-level .md files,
# find aborted with "unknown primary or operator", and `2>/dev/null` swallowed the
# message. references/, templates/ and scripts/ yielded ZERO files. The validator
# printed PASS for every rule on every skill while scanning nothing but SKILL.md,
# and it had been doing so since the "extended scope" was added in 2026-05. A
# fixture carrying a home-directory path and a personal email under references/
# came back clean.
#
# So this test does not ask whether the validator passes. It plants the one string
# the personal-path rule exists to catch in every scanned location and asserts the
# validator NAMES EACH FILE. A scope regression makes a location silently drop out
# of the output, which is exactly what nobody noticed for two months.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Unique per run: two concurrent invocations sharing one fixture path made each
# trap delete the other's files mid-scan, and every assertion then failed for a
# reason that had nothing to do with the validator.
FIXTURE_DIR="$REPO_ROOT/skills/zz-scope-fixture-$$"
# Use a synthetic username and a disposable digest set. A regression test must
# not reconstruct the real identifier that the public scanner keeps hash-only.
LEAK="/Users/syntheticperson/workspace/private/notes.md"
SCOPE_HASHES="$(mktemp)"
cp "$REPO_ROOT/scripts/precedent_hashes.txt" "$SCOPE_HASHES"
printf '%s' syntheticperson | shasum -a 256 | cut -d' ' -f1 >> "$SCOPE_HASHES"
export PRECEDENT_HASH_FILE="$SCOPE_HASHES"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-56s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-56s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

cleanup() { rm -rf "$FIXTURE_DIR"; }
trap 'cleanup; rm -f "$SCOPE_HASHES"' EXIT
cleanup
mkdir -p "$FIXTURE_DIR"/{references,templates,scripts,tests}

cat > "$FIXTURE_DIR/SKILL.md" <<'EOF'
---
name: zz-scope-fixture
description: Throwaway fixture created and deleted by tests/test_validator_scope.sh.
triggers: none
tools: Read
model: inherit
---

# Fixture

Created and removed inside a single test run. If you are reading this on disk, a test crashed.

## Anti-Hallucination

- This skill is a test fixture and produces nothing.
EOF

# One planted leak per scanned location, each in a file type that location holds.
printf -- '- Source note: %s\n'            "$LEAK" > "$FIXTURE_DIR/references/note.md"
printf -- '<!-- draft path: %s -->\n'      "$LEAK" > "$FIXTURE_DIR/templates/starter.md"
printf -- '# path: %s\n'                   "$LEAK" > "$FIXTURE_DIR/scripts/helper.py"
printf -- '# fixture path: %s\n'           "$LEAK" > "$FIXTURE_DIR/tests/test_thing.sh"
printf -- 'note: "%s"\n'                   "$LEAK" > "$FIXTURE_DIR/skill.yml"
# ...and one the linter is SUPPOSED to skip: skills/**/TODO_*.md is gitignored, and
# the rule is that this scan matches what the public sees, not what is on disk.
printf -- '- scratch: %s\n'                "$LEAK" > "$FIXTURE_DIR/TODO_scratch.md"

FIXTURE_NAME="$(basename "$FIXTURE_DIR")"
# Scoped to the fixture. Every assertion below is about locations INSIDE one skill, so the other
# 57 and the whole-repo scan were pure cost — this test alone was ~90 s of CI, and it runs on every
# push. `--only` errors out on a name it cannot find, so a typo here fails loudly rather than
# validating nothing and letting `[ -n "$FLAGGED" ]` be the only thing standing.
OUT="$(bash "$REPO_ROOT/scripts/validate_skills.sh" --only "$FIXTURE_NAME" 2>&1)"
FLAGGED="$(printf '%s\n' "$OUT" | grep -E 'Personal (path|precedent) in' || true)"
seen() { printf '%s\n' "$FLAGGED" | grep -q "$FIXTURE_NAME/$1"; }

seen 'references/note.md';    ck "references/ is scanned"                    0 "$?"
seen 'templates/starter.md';  ck "templates/ is scanned"                     0 "$?"
seen 'scripts/helper.py';     ck "scripts/ is scanned"                       0 "$?"
seen 'tests/test_thing.sh';   ck "tests/ is scanned"                         0 "$?"
seen 'skill.yml';             ck "a skill-root sidecar file is scanned"      0 "$?"
seen 'TODO_scratch.md';       ck "a gitignored scratchpad is NOT scanned"     1 "$?"

# Guard against the assertions above passing vacuously: if the rule ever stops
# emitting this verdict, every `seen` call fails to match and the suite would
# still look meaningful only because we assert exit 0 on each. Assert the rule
# spoke at all.
[ -n "$FLAGGED" ]
ck "the personal-path rule emitted a verdict at all"                         0 "$?"

cleanup

echo "----"
echo "test_validator_scope: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Self-test for scripts/check_skill_discovery.py.
#
# The gate exists because a file can BE a fixture and LOOK LIKE a skill at the same time.
# `gh skill` keys on a directory literally named `skills` at any depth, so a frozen
# regression fixture at tests/fixtures/<x>/skills/<name>/SKILL.md is published as a real
# skill called <name>. That is how tests/fixtures/phase_budget/skills/self-review/SKILL.md
# failed `gh skill publish --dry-run` for the entire repository on 2026-07-24.
#
# So the test has to prove two things, and the second is the one that matters:
#
#   1. the gate is SILENT on the fixed tree (no false positives -> nobody switches it off), and
#   2. the gate FAILS on the real defect restored (a SKILL.md under a nested `skills/`).
#      A test that only proves "passes on clean input" proves nothing: a gate that never
#      fires passes that test too.
#
# It also pins the property that makes the fix legible: the SAME file, moved out of a
# directory named `skills`, must go silent. Otherwise the gate would be telling contributors
# to delete fixtures rather than rename their parent directory.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DET="$ROOT/scripts/check_skill_discovery.py"

pass=0
fail() { echo "FAIL: $1" >&2; exit 1; }

# ---------------------------------------------------------------- 1. live repo is silent
python3 "$DET" --strict >/dev/null 2>&1 \
  || fail "the live repo must be clean (run: python3 scripts/check_skill_discovery.py)"
pass=$((pass + 1))

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

# A frontmatter-less body, exactly what a frozen defect fixture looks like.
fixture_body() {
  echo "# Frozen fixture — the REAL defect, pinned so the gate stays regressed."
  echo
  echo "### Phase 2: Systematic Check"
}

# ----------------------------------- NEGATIVE FIXTURE 1: canonical skills the gate must not flag
mkdir -p "$tmp/clean/skills/self-review"
{
  echo "---"
  echo "name: self-review"
  echo "description: Pre-submission self-review."
  echo "---"
  echo "# Self Review"
} > "$tmp/clean/skills/self-review/SKILL.md"

python3 "$DET" --root "$tmp/clean" --strict >/dev/null 2>&1 \
  || fail "NEGATIVE: the gate fired on a canonical skills/<name>/SKILL.md"
pass=$((pass + 1))

# --------------------------- NEGATIVE FIXTURE 2: a fixture parked OUTSIDE any `skills/` dir
mkdir -p "$tmp/clean/tests/fixtures/phase_budget/real_defect/self-review"
fixture_body > "$tmp/clean/tests/fixtures/phase_budget/real_defect/self-review/SKILL.md"

python3 "$DET" --root "$tmp/clean" --strict >/dev/null 2>&1 \
  || fail "NEGATIVE: the gate fired on a fixture already moved out of a 'skills' directory"
pass=$((pass + 1))

# ------------------------------- REGRESSION: the REAL defect shape. The gate must FAIL on it.
# Same file, same content, one directory renamed back to `skills`. This is the only difference
# between the shipped bug and the fix, so it is the only thing the gate may key on.
mkdir -p "$tmp/broken/skills/self-review"
{ echo "---"; echo "name: self-review"; echo "description: real."; echo "---"; } \
  > "$tmp/broken/skills/self-review/SKILL.md"
mkdir -p "$tmp/broken/tests/fixtures/phase_budget/skills/self-review"
fixture_body > "$tmp/broken/tests/fixtures/phase_budget/skills/self-review/SKILL.md"

if python3 "$DET" --root "$tmp/broken" --strict >/dev/null 2>&1; then
  fail "REGRESSION: a SKILL.md under a nested 'skills/' did NOT fail the gate"
fi
pass=$((pass + 1))

# ------------------------------------------- the verdict names the skill it would collide with
out="$(python3 "$DET" --root "$tmp/broken" --json 2>/dev/null)"
echo "$out" | grep -q '"verdict": "SKILL_DISCOVERY_COLLISION"' \
  || fail "JSON verdict missing SKILL_DISCOVERY_COLLISION"
echo "$out" | grep -q '"skill_name_it_would_claim": "self-review"' \
  || fail "the verdict must name the skill the fixture would be published as"
pass=$((pass + 1))

# ----------------------------------------- the message must teach the fix, not just the failure
python3 "$DET" --root "$tmp/broken" 2>/dev/null | grep -qi "rename" \
  || fail "the message must tell the contributor to rename the directory, not delete the fixture"
pass=$((pass + 1))

# ------------- REGRESSION: the gate must read the WORKING TREE, not the git index.
# The first draft of this gate used `git ls-files`. `gh skill publish` reads the working tree,
# so a plain `mv` of the fixture back into `skills/` left the index untouched and the gate
# reported OK on the exact defect it was written for. Pin the difference: commit the fixture at
# its safe path, then move it on disk only. A gate that reads the index passes this and is wrong.
if command -v git >/dev/null 2>&1; then
  repo="$tmp/indexed"
  mkdir -p "$repo/skills/real-skill" "$repo/tests/fixtures/x/real_defect/self-review"
  { echo "---"; echo "name: real-skill"; echo "description: real."; echo "---"; } \
    > "$repo/skills/real-skill/SKILL.md"
  fixture_body > "$repo/tests/fixtures/x/real_defect/self-review/SKILL.md"
  (
    cd "$repo"
    git init -q .
    git config user.email t@example.com && git config user.name t
    git add -A && git commit -qm "fixture at its safe path"
  ) >/dev/null 2>&1

  # on disk only -- the index still says real_defect/
  mv "$repo/tests/fixtures/x/real_defect" "$repo/tests/fixtures/x/skills"

  if python3 "$DET" --root "$repo" --strict >/dev/null 2>&1; then
    fail "REGRESSION: the gate read the git index, not the working tree that gh skill reads"
  fi
  pass=$((pass + 1))
fi

echo "PASS: gh-skill discovery gate — $pass checks."
echo "  live repo silent - canonical silent - moved fixture silent -"
echo "  nested skills/ FAILS - verdict names the collision - message teaches the fix -"
echo "  reads the working tree, not the git index."

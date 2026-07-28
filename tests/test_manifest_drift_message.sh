#!/usr/bin/env bash
# The manifest gate must fail a first-time contributor USEFULLY.
#
# On 2026-07-13 a stranger's first pull request — five nephrology journal profiles, the exact thing
# our "good first issue" asked for — went red with:
#
#     DISTRIBUTION_MANIFEST_DRIFT: metadata/distribution_files.json out of date — run
#     python3 scripts/gen_distribution_manifest.py
#
# He had added ten shipped files, so the hashed inventory no longer matched. Nothing was wrong with
# his work. But CONTRIBUTING invites people to contribute **through the browser, with no git and no
# terminal** — and someone who accepts that invitation cannot run a Python script. We told them to do
# the one thing we had just promised they would never have to do.
#
# This test reproduces that exact situation: add a shipped file, do not touch metadata/, and demand
# that the failure (a) still fails — the gate protects the updater and must stay strict — and (b)
# names the file, and (c) tells a browser contributor that a maintainer will handle it.
#
# It asserts on the MESSAGE, because the message was the defect.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"; rm -f "$ROOT/skills/find-journal/references/journal_profiles/__ci_probe__.md"' EXIT

pass=0
fail=0
ck() {
  if [ "$2" = "$3" ]; then
    printf '  PASS  %s\n' "$1"; pass=$((pass + 1))
  else
    printf '  FAIL  %s (expected=%s actual=%s)\n' "$1" "$2" "$3"; fail=$((fail + 1))
  fi
}
has() {  # has <label> <pattern>
  if grep -qi -- "$2" "$TMP/out"; then
    printf '  PASS  %s\n' "$1"; pass=$((pass + 1))
  else
    printf '  FAIL  %s (missing: %s)\n' "$1" "$2"; fail=$((fail + 1))
  fi
}

# Sanity: the tree is in sync before we disturb it, or this test proves nothing.
python3 "$ROOT/scripts/gen_distribution_manifest.py" --check >/dev/null 2>&1
ck "the repo starts in sync (otherwise this test is meaningless)" 0 "$?"

# Reproduce the trap: a new shipped file, exactly as a good-first-issue contributor would add it.
PROBE="$ROOT/skills/find-journal/references/journal_profiles/__ci_probe__.md"
printf '# CI probe\n\nA synthetic profile, added and removed by this test.\n' > "$PROBE"

python3 "$ROOT/scripts/gen_distribution_manifest.py" --check > "$TMP/out" 2>&1
ck "adding a shipped file still FAILS the gate (it guards the updater)" 1 "$?"

has "...names the file that moved"                 "__ci_probe__.md"
has "...says how many files were added"            "1 file(s) added"
has "...gives the command to refresh it"           "gen_distribution_manifest.py"
has "...tells browser contributors it is not on them" "maintainer will refresh"
has "...says this is not a rejection"              "not a rejection"

# And the gate must go green again once the manifest is refreshed — otherwise the advice we just
# printed would be a lie.
rm -f "$PROBE"
python3 "$ROOT/scripts/gen_distribution_manifest.py" --check >/dev/null 2>&1
ck "removing the file restores sync (the advice is true)" 0 "$?"

echo "----"
echo "test_manifest_drift_message: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

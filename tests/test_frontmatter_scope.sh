#!/usr/bin/env bash
# Regression test for scripts/check_frontmatter_scope.py.
#
# The gate exists because a pandoc manuscript opens with a `---`-fenced YAML block that
# projects fill with real sentences — `status:` notes, `changelog:` entries — and every
# `--manuscript` detector's hand-rolled body extractor filters `#`, `|`, `>`, `!`, list
# markers and code fences, none of which a YAML block matches. Three shipped detectors
# fired on it, one of them returning a P0 (`PRIMARY_REASSIGNED`) because a changelog said
# the primary endpoint had been changed — a Major that fires harder the more openly a
# project records its own history.
#
# The fix existed the whole time (`_frontmatter.py`); nothing made the gap visible, so it
# reached 4 of 41 detectors over months. So what this suite pins is not the fix but the
# VISIBILITY: a new detector cannot join silently, and an entry cannot rot on the list
# after its detector is fixed.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
G="$REPO_ROOT/scripts/check_frontmatter_scope.py"
PROBE="$REPO_ROOT/skills/self-review/scripts/check_zz_frontmatter_probe_$$.py"
LISTED="$REPO_ROOT/skills/self-review/scripts/check_paren_spans.py"
BACKUP="$(mktemp)"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-58s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-58s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

cleanup() {
  rm -f "$PROBE"
  # cp, never `git checkout -- <file>`: that reverts to HEAD and would destroy any
  # uncommitted work on this file, which has cost this repo a session before.
  [ -s "$BACKUP" ] && cp "$BACKUP" "$LISTED"
  rm -f "$BACKUP"
}
trap cleanup EXIT
cp "$LISTED" "$BACKUP"

# Never pipe between the gate and $? — a pipeline's status is the LAST command's, and
# reading `head`'s 0 as the gate's verdict is a mistake this repo has made more than once.
run() { python3 "$G" --strict > /dev/null 2>&1; echo $?; }

# 1) The tree as committed must be clean, or the gate cannot land.
ck "the repository as committed passes" 0 "$(run)"

# 2) A NEW --manuscript detector that strips nothing must fail. No grace period: the
#    allowlist is a record of what was already there, not a door.
cat > "$PROBE" <<'PY'
#!/usr/bin/env python3
"""Throwaway probe created and deleted by tests/test_frontmatter_scope.sh."""
import argparse
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", required=True)
    ap.parse_args()
    return 0
PY
ck "a new unlisted --manuscript detector FAILS" 1 "$(run)"

# 3) ...and passes as soon as it strips.
printf 'from _frontmatter import strip_frontmatter\n' >> "$PROBE"
ck "...and passes once it strips front matter" 0 "$(run)"
rm -f "$PROBE"

# 4) An entry that has been fixed must be REMOVED from the list, not left to rot. A stale
#    allowlist overstates the debt and quietly re-permits a regression on that file.
printf 'from _frontmatter import strip_frontmatter\n' | cat - "$LISTED" > "$LISTED.tmp" && mv "$LISTED.tmp" "$LISTED"
ck "a listed detector that now strips is reported STALE" 1 "$(run)"
python3 "$G" --strict 2>&1 | grep -q "STALE ALLOWLIST"
ck "...and the stale entry is named" 0 "$?"
cp "$BACKUP" "$LISTED"

# 5) Transitive stripping counts. check_aphorism_density and check_rhetorical_density strip
#    through _prose.py; a gate that could not see one level of same-directory import would
#    call those two debt, which is inventing work rather than finding it.
python3 "$G" 2>&1 | grep -qE 'strip front matter: [6-9]|strip front matter: [1-9][0-9]'
ck "same-directory helper imports are resolved (not counted as debt)" 0 "$?"

# 6) The advisory path must not be silently green: without --strict it still reports.
rm -f "$PROBE"; cat > "$PROBE" <<'PY'
import argparse
argparse.ArgumentParser().add_argument("--manuscript")
PY
python3 "$G" 2>&1 | grep -q "FRONTMATTER_SCOPE"
ck "without --strict the violation is still printed" 0 "$?"
python3 "$G" > /dev/null 2>&1
ck "...but does not fail the build" 0 "$?"

cleanup

echo "----"
echo "test_frontmatter_scope: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

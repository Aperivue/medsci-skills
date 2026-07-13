#!/usr/bin/env bash
# Regression test for scripts/check_release_cadence.py.
#
# The gate exists because this repository cut 42 releases in 37 days — a median gap of zero days,
# three of them on one afternoon. That did not merely look untidy: it destroyed the project's own
# adoption signal, because every release attracts a handful of automated asset downloads, so
# `release_downloads` grew with the number of RELEASES rather than the number of users. The
# cumulative total doubled while per-release downloads collapsed from 32 to 5 — and the cumulative
# total was about to be cited as evidence of adoption.
#
# So the gate must (a) block a too-soon release, (b) let a genuine hotfix straight through, and
# (c) stay silent when no release is being prepared, which is almost every commit.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
G="$REPO_ROOT/scripts/check_release_cadence.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-54s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-54s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# A throwaway repo, so the test never depends on this project's own tag history.
REPO="$TMP/repo"
mkdir -p "$REPO/scripts"
cp "$G" "$REPO/scripts/"
cd "$REPO"
git init -q .
git config user.email t@t.t
git config user.name t

write_release() {   # $1 version   $2 changelog body
  printf 'cff-version: 1.2.0\nversion: "%s"\n' "$1" > CITATION.cff
  printf '# Changelog\n\n## [Unreleased]\n\n## [%s] - 2026-07-13\n%s\n' "$1" "$2" > CHANGELOG.md
}

# --- a released state: the tag and CITATION.cff agree -----------------------------------------
write_release "1.0.0" "
### Added

- The first thing.
"
git add -A > /dev/null && git commit -qm v1
GIT_COMMITTER_DATE="2026-07-13T12:00:00" git tag -a v1.0.0 -m v1.0.0

# 1) no release pending -> silent, and this is the case on almost every commit
python3 scripts/check_release_cadence.py --strict > /dev/null 2>&1
ck "no release pending -> passes (the common case)" 0 "$?"

# 2) a release cut the same day as the last one -> blocked
write_release "1.1.0" "
### Added

- Something new.
"
python3 scripts/check_release_cadence.py --strict > /dev/null 2>&1
ck "a release 0 days after the last one is blocked" 1 "$?"

OUT="$(python3 scripts/check_release_cadence.py 2>&1)"
echo "$OUT" | grep -q "Hotfix"
ck "...and the message shows the way out (a hotfix)" 0 "$?"

# 3) a genuine hotfix goes out immediately — something is broken in the wild
write_release "1.0.1" "
**Hotfix:** the installer crashes on Windows and nobody can install.

### Fixed

- The crash.
"
python3 scripts/check_release_cadence.py --strict > /dev/null 2>&1
ck "a declared hotfix ships immediately" 0 "$?"

# 4) a docs-only release is not a release
write_release "1.1.0" "
### Docs

- Fixed a typo.
"
python3 scripts/check_release_cadence.py --strict > /dev/null 2>&1
ck "a docs-only release is refused" 1 "$?"

# 5) ...and it is still refused even when enough time HAS passed: the objection is that nobody
#    would notice, not that it is too soon.
GIT_COMMITTER_DATE="2026-06-01T12:00:00" git tag -a v0.9.0 -m old > /dev/null 2>&1 || true
python3 scripts/check_release_cadence.py 2>&1 | grep -q "nothing a user would notice"
ck "the docs-only objection is substance, not timing" 0 "$?"

# 6) a version with no changelog section at all
printf 'cff-version: 1.2.0\nversion: "2.0.0"\n' > CITATION.cff
printf '# Changelog\n\n## [Unreleased]\n' > CHANGELOG.md
python3 scripts/check_release_cadence.py --strict > /dev/null 2>&1
ck "a release with no changelog section is refused" 1 "$?"

# 7) after enough time, a substantive release passes
write_release "1.1.0" "
### Added

- Something a user would notice.
"
python3 scripts/check_release_cadence.py --strict --min-days 0 > /dev/null 2>&1
ck "enough time + real content -> passes" 0 "$?"

echo "----"
echo "test_release_cadence: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

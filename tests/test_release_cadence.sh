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
#
# Every fixture date below is derived from TODAY, never written as a literal. The gate measures
# `date.today() - <tag creatordate>`, so a hard-coded tag date does not describe a fixed gap — it
# describes a gap that grows by one day per day. This test previously pinned its tag to
# 2026-07-13 and asserted that a release cut "0 days later" is blocked; that assertion was true
# for fourteen days and then quietly became false, and the suite went red on 2026-07-27 for a
# reason that had nothing to do with the gate. A fixture may only encode a DURATION.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
G="$REPO_ROOT/scripts/check_release_cadence.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Dates relative to now. python3 rather than `date -d` / `date -v`, which disagree across
# GNU and BSD and would make this test pass on CI and fail on a maintainer's laptop.
days_ago() { python3 -c "import datetime,sys;print((datetime.date.today()-datetime.timedelta(days=int(sys.argv[1]))).isoformat())" "$1"; }
TODAY="$(days_ago 0)"
LONG_AGO="$(days_ago 60)"

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
  printf '# Changelog\n\n## [Unreleased]\n\n## [%s] - %s\n%s\n' "$1" "$TODAY" "$2" > CHANGELOG.md
}

# --- a released state: the tag and CITATION.cff agree -----------------------------------------
write_release "1.0.0" "
### Added

- The first thing.
"
git add -A > /dev/null && git commit -qm v1
GIT_COMMITTER_DATE="${TODAY}T12:00:00" git tag -a v1.0.0 -m v1.0.0

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
GIT_COMMITTER_DATE="${LONG_AGO}T12:00:00" git tag -a v0.9.0 -m old > /dev/null 2>&1 || true
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

# 8) the second exemption: a release cut so an external artifact can cite an exact version.
#    A measurement study reporting "N detectors, false-positive rate X" has to name what it
#    measured, and a git SHA is a worse coordinate than a release for anyone reproducing it — so
#    waiting would not improve the thing the waiting period protects.
write_release "1.1.0" "
**Pinned reference:** the held-out validation study must report the exact version it measured.

### Added

- Something a user would notice.
"
python3 scripts/check_release_cadence.py --strict > /dev/null 2>&1
ck "a declared pinned reference ships early" 0 "$?"

OUT="$(python3 scripts/check_release_cadence.py 2>&1)"
echo "$OUT" | grep -q "PINNED REFERENCE declared: the held-out validation study"
ck "...and the reason is printed, so an unjustified use is visible in the log" 0 "$?"

# 9) the exemption waives the WAIT, not the SUBSTANCE. A version worth citing is a version worth
#    updating to, so it cannot be used to ship a docs-only release early.
write_release "1.1.0" "
**Pinned reference:** a paper needs to cite this.

### Docs

- Fixed a typo.
"
python3 scripts/check_release_cadence.py --strict > /dev/null 2>&1
ck "a pinned reference does not excuse an empty release" 1 "$?"

# 10) and the blocked message names it as a way out, so nobody has to guess or mislabel a hotfix
write_release "1.1.0" "
### Added

- Something new.
"
python3 scripts/check_release_cadence.py 2>&1 | grep -q "Pinned reference"
ck "the blocked message offers the pin, not only the hotfix" 0 "$?"

echo "----"
echo "test_release_cadence: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

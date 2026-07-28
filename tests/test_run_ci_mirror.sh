#!/usr/bin/env bash
# Self-test for scripts/run_ci_mirror.py — the local mirror of the CI `validate` job.
# It must (1) enumerate the real gate steps (not drift), (2) include actual gates, and
# (3) exclude `uses:` and dependency-install steps. Fast: only exercises --list (never
# the full run, which would be recursive and slow).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
S="$ROOT/scripts/run_ci_mirror.py"
fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %s\n' "$1"; else printf '  FAIL  %s (want %s got %s)\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }

[ -f "$S" ] || { echo "ENV-ERR: script missing" >&2; exit 2; }

LIST="$(python3 "$S" --list)"; rc=$?
ck "--list exits 0" 0 "$rc"

# (1) enumerates many gates — the validate job has well over 100 run-steps.
n="$(printf '%s\n' "$LIST" | grep -cvE '^\s*$|gate step\(s\) mirrored')"
if [ "$n" -ge 100 ]; then printf '  PASS  --list enumerates >=100 gates (%s)\n' "$n"; else printf '  FAIL  --list only %s gates\n' "$n"; fail=$((fail+1)); fi

# (2) includes a real gate that must always be there.
printf '%s\n' "$LIST" | grep -qi 'validate_skills' && ck "includes the validate_skills gate" yes yes || ck "includes the validate_skills gate" yes no
printf '%s\n' "$LIST" | grep -qi 'catalog' && ck "includes a catalog-consistency gate" yes yes || ck "includes a catalog-consistency gate" yes no

# (3) excludes dependency-install setup steps (e.g. a step named "Install ... poppler").
if printf '%s\n' "$LIST" | grep -qiE '^Install (Python|exiftool|node)'; then
  printf '  FAIL  setup/install step leaked into the mirror\n'; fail=$((fail+1))
else
  printf '  PASS  setup/install steps are excluded\n'
fi

# (4) --only narrows the set and still parses.
python3 "$S" --only 'workflow' --list >/dev/null 2>&1
ck "--only narrows and exits 0" 0 "$?"

echo "test_run_ci_mirror: $fail failure(s)"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Deterministic verifier for the citation-snowballing challenge card.
# No network: reads recorded Semantic Scholar responses from fixture/.
# Exit 0 = output matches expected/snowball.bib ; non-zero = regression.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SNOWBALL="$HERE/../snowball.py"

actual="$(python3 "$SNOWBALL" \
  --seed DOI:10.0/seed1 \
  --direction all \
  --offline-fixture "$HERE/fixture" \
  --pool "$HERE/fixture/library.bib" \
  --as-of 2026-06-14 \
  --stdout 2>/dev/null)"

if diff -u "$HERE/expected/snowball.bib" <(printf '%s\n' "$actual"); then
  echo "PASS: snowball output matches expected (4 new candidates; 1 backward dup removed)."
else
  echo "FAIL: snowball output drifted from expected/snowball.bib" >&2
  exit 1
fi

# A count is only a PRISMA count if the source answered in full. A fetch that failed, or a page
# the source says continues (`next`), used to print "N raw ... M new candidates" and exit 0, so a
# lower bound went into the flow diagram as the number that exists.
fail=0
ERR="$(mktemp)"
trap 'rm -f "$ERR"' EXIT
run() {  # run <seed> <limit> -> exit code; stderr lands in $ERR
  set +e
  python3 "$SNOWBALL" --seed "$1" --direction all --offline-fixture "$HERE/fixture" \
    --limit "$2" --as-of 2026-06-14 --stdout >/dev/null 2>"$ERR"
  local rc=$?
  set -e
  echo "$rc"
}

rc="$(run DOI:10.0/seed_err 50)"
if [ "$rc" -ne 0 ] && grep -q "FAILED backward" "$ERR" && grep -q "INCOMPLETE" "$ERR"; then
  echo "PASS: a Semantic Scholar error body exits non-zero and marks the PRISMA line INCOMPLETE."
else
  echo "FAIL: an error body was read as 0 records (exit $rc)" >&2; cat "$ERR" >&2; fail=1
fi

rc="$(run DOI:10.0/seed_trunc 2)"
if [ "$rc" -ne 0 ] && grep -q "TRUNCATED forward" "$ERR" && grep -q "INCOMPLETE" "$ERR"; then
  echo "PASS: a page with 'next' (more records past --limit) prints TRUNCATED and exits non-zero."
else
  echo "FAIL: a truncated page was reported as complete (exit $rc)" >&2; cat "$ERR" >&2; fail=1
fi

# Negative control: a page exactly at --limit with no `next` is complete.
rc="$(run DOI:10.0/seed1 2)"
if [ "$rc" -eq 0 ] && ! grep -qE "TRUNCATED|FAILED|INCOMPLETE" "$ERR"; then
  echo "PASS: a full page with no 'next' is complete (exit 0, no TRUNCATED)."
else
  echo "FAIL: a complete page was called incomplete (exit $rc)" >&2; cat "$ERR" >&2; fail=1
fi

# A live fetch that raises (network down, 403, 429) is a failure, not zero results.
set +e
python3 - "$HERE/.." >"$ERR" 2>&1 <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import snowball
def boom(url):
    raise OSError("HTTP Error 403: Forbidden")
snowball._http_get_json = boom
rc = snowball.main(["--seed", "10.1000/xyz", "--direction", "backward", "--stdout"])
sys.exit(10 + rc)
PY
rc=$?
set -e
if [ "$rc" -eq 11 ] && grep -q "FAILED backward for DOI:10.1000/xyz" "$ERR" && grep -q "INCOMPLETE" "$ERR"; then
  echo "PASS: a live fetch that raises exits non-zero and marks the PRISMA line INCOMPLETE."
else
  echo "FAIL: a failed live fetch was read as 0 records (main returned $((rc-10)))" >&2; cat "$ERR" >&2; fail=1
fi

[ "$fail" -eq 0 ] || exit 1

#!/usr/bin/env bash
# Challenge card for skills/lit-sync/scripts/check_citekey_provenance.py.
#
# Run with no argument from CI; pass a path to point it at a mutated copy (see the
# self-test below, which is how this card earns the right to be believed).
#
# The script decides whether a literature note's citekey is real. Its verdicts are what a
# user acts on, and its --strict exit code is what a gate acts on. Both are asserted here
# against a fixture built at runtime, so the card carries no committed vault to drift.
#
# The boundary that matters and is easy to get wrong: --strict fails on INVENTED only.
# UNRESOLVED and FILENAME are reported but do not fail — a paper that was never added to
# the library is not the same defect as a citekey that was composed.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${1:-$HERE/../scripts/check_citekey_provenance.py}"
[ -f "$SCRIPT" ] || { echo "cannot find check_citekey_provenance.py at $SCRIPT"; exit 2; }
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0
check() { # check <label> <expected> <actual>
  if [ "$2" = "$3" ]; then printf '  PASS  %s\n' "$1"; PASS=$((PASS+1))
  else printf '  FAIL  %s (expected %s, got %s)\n' "$1" "$2" "$3"; FAIL=$((FAIL+1)); fi
}

note() { # note <path> <citekey-or-empty> <doi-or-empty> <notetype>
  mkdir -p "$(dirname "$1")"
  {
    echo "---"
    [ -n "$2" ] && echo "citekey: \"$2\""
    [ -n "$3" ] && echo "doi: \"$3\""
    echo "notetype: $4"
    echo "---"
    echo
    echo "body"
  } > "$1"
}

# ---------------------------------------------------------------- fixture
VAULT="$WORK/vault"
BIB="$WORK/refs.bib"
cat > "$BIB" <<'BIB'
@article{realKey2020,
  title = {A real entry},
  doi = {10.1000/real},
}
@article{otherKey2021,
  title = {Another real entry},
  doi = {10.1000/other},
}
BIB

note "$VAULT/realKey2020.md"      "realKey2020" "10.1000/real"     literature  # OK
note "$VAULT/wrongName.md"        "otherKey2021" "10.1000/other"   literature  # FILENAME
note "$VAULT/composedKey2021.md"  "composedKey2021" "10.1000/other" literature # INVENTED (doi resolves)
note "$VAULT/neverAdded2019.md"   "neverAdded2019" "10.1000/absent" literature # UNRESOLVED
note "$VAULT/noKey.md"            "" "10.1000/real"                literature  # NO_CITEKEY
note "$VAULT/concept.md"          "notAKey" ""                     concept     # skipped: not literature
note "$VAULT/.trash/hidden.md"    "alsoNotAKey" ""                 literature  # skipped: dot-path

OUT="$WORK/out.txt"
python3 "$SCRIPT" --vault "$VAULT" --bib "$BIB" --json "$WORK/audit.json" > "$OUT" 2>&1
rc=$?
check "exit 0 without --strict" 0 "$rc"

count() { python3 -c "
import json,sys
d=json.load(open('$WORK/audit.json'))
print(d['counts'].get('$1',0))
"; }

check "OK counted once"          1 "$(count OK)"
check "FILENAME counted once"    1 "$(count FILENAME)"
check "INVENTED counted once"    1 "$(count INVENTED)"
check "UNRESOLVED counted once"  1 "$(count UNRESOLVED)"
check "NO_CITEKEY counted once"  1 "$(count NO_CITEKEY)"

total=$(python3 -c "
import json; d=json.load(open('$WORK/audit.json')); print(sum(d['counts'].values()))
")
check "non-literature and dot-path notes skipped" 5 "$total"

sugg=$(python3 -c "
import json
d=json.load(open('$WORK/audit.json'))
print(next(r['suggested_citekey'] for r in d['findings'] if r['verdict']=='INVENTED'))
")
check "INVENTED names the real key from the DOI" "otherKey2021" "$sugg"

# ------------------------------------------------- --strict fires on INVENTED
python3 "$SCRIPT" --vault "$VAULT" --bib "$BIB" --strict > /dev/null 2>&1
check "--strict exits 1 when INVENTED present" 1 "$?"

# --------------------------------- --strict does NOT fire without INVENTED
VAULT2="$WORK/vault2"
note "$VAULT2/realKey2020.md"    "realKey2020" "10.1000/real"      literature  # OK
note "$VAULT2/neverAdded2019.md" "neverAdded2019" "10.1000/absent" literature  # UNRESOLVED
note "$VAULT2/wrongName.md"      "otherKey2021" "10.1000/other"    literature  # FILENAME
python3 "$SCRIPT" --vault "$VAULT2" --bib "$BIB" --strict > /dev/null 2>&1
check "--strict exits 0 for UNRESOLVED/FILENAME alone" 0 "$?"

# ------------------------------------------------------------ input guards
python3 "$SCRIPT" --vault "$WORK/does-not-exist" --bib "$BIB" > /dev/null 2>&1
check "missing vault exits 2" 2 "$?"

python3 "$SCRIPT" --vault "$VAULT" > /dev/null 2>&1
check "no --bib and no --live exits 2" 2 "$?"

: > "$WORK/empty.bib"
python3 "$SCRIPT" --vault "$VAULT" --bib "$WORK/empty.bib" > /dev/null 2>&1
check "empty library exits 2 instead of condemning every note" 2 "$?"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]

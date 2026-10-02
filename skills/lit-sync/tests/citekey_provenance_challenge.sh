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
# The boundary that matters and is easy to get wrong: --strict fails on INVENTED, MISMATCH
# and UNPARSED only (and exits 2 when no literature note was found at all).
# UNRESOLVED and FILENAME are reported but do not fail — a paper not found in the library
# is not the same defect as a citekey that was composed.
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

note() { # note <path> <citekey-or-empty> <doi-or-empty> <notetype> [pmid]
  mkdir -p "$(dirname "$1")"
  {
    echo "---"
    [ -n "$2" ] && echo "citekey: \"$2\""
    [ -n "$3" ] && echo "doi: \"$3\""
    [ -n "${5:-}" ] && echo "pmid: \"$5\""
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

# ------------------------- a key is a label, not an identity (keys repeat; some are URLs)
# Content-negotiated BibTeX mints Author_Year keys, so one key can sit on two different
# papers; arXiv entries can arrive keyed by a URL. A note carrying such a key used to read
# OK, which is how two different papers' notes nearly got merged on a shared key. And a
# note with no DOI used to be called "never added", which led to re-importing papers the
# library already held. Every row below was a wrong verdict before this block existed.
VAULT3="$WORK/vault3"
BIB3="$WORK/refs3.bib"
cat > "$BIB3" <<'BIB'
@article{Doe_2025,
  title = {First synthetic paper},
  doi = {10.0000/example.1},
}
@article{Doe_2025,
  title = {Second synthetic paper, same minted key},
  doi = {10.0000/example.2},
}
@article{https://doi.org/10.0000/example.3,
  title = {A URL-keyed synthetic preprint},
  doi = {10.0000/example.3},
}
@article{uniqueKey2024,
  title = {A synthetic paper found by PMID only},
  pmid = {90000001},
}
BIB
note "$VAULT3/Doe_2025.md"      "Doe_2025" "10.0000/example.1"                    literature  # AMBIGUOUS
note "$VAULT3/urlKey.md"        "https://doi.org/10.0000/example.3" "10.0000/example.3" literature  # UNUSABLE
note "$VAULT3/noIds2019.md"     "noIds2019" ""                                    literature  # NO_IDENTIFIER
note "$VAULT3/composed2024.md"  "composed2024" "" literature 90000001                          # INVENTED via PMID
note "$VAULT3/DoeComposed.md"   "DoeComposed" "10.0000/example.2"                 literature  # INVENTED, key withheld
note "$VAULT3/absent2020.md"    "absent2020" "" literature 90000009                           # UNRESOLVED
python3 "$SCRIPT" --vault "$VAULT3" --bib "$BIB3" --json "$WORK/audit3.json" > /dev/null 2>&1
verdict_of() { python3 -c "
import json,sys
d=json.load(open('$WORK/audit3.json'))
print(next((r['verdict'] for r in d['findings'] if r['file'].endswith('/$1')), 'OK'))
"; }
suggestion_of() { python3 -c "
import json
d=json.load(open('$WORK/audit3.json'))
print(next((r['suggested_citekey'] or '(none)') for r in d['findings'] if r['file'].endswith('/$1')))
"; }
check "a key on two library entries is AMBIGUOUS, not OK"  AMBIGUOUS     "$(verdict_of Doe_2025.md)"
check "a URL key is UNUSABLE"                              UNUSABLE      "$(verdict_of urlKey.md)"
check "no DOI and no PMID is NO_IDENTIFIER, not 'never added'" NO_IDENTIFIER "$(verdict_of noIds2019.md)"
check "a PMID finds the real key when the DOI is missing"  INVENTED      "$(verdict_of composed2024.md)"
check "the PMID lookup names the real key"                 uniqueKey2024 "$(suggestion_of composed2024.md)"
check "an ambiguous real key is never suggested"           "(none)"      "$(suggestion_of DoeComposed.md)"
check "a PMID absent from the library stays UNRESOLVED"    UNRESOLVED    "$(verdict_of absent2020.md)"

# the same entry seen in a snapshot AND a second export is one entry, not a duplicate
python3 "$SCRIPT" --vault "$VAULT" --bib "$BIB" "$BIB" --json "$WORK/audit_twice.json" > /dev/null 2>&1
twice=$(python3 -c "
import json; print(json.load(open('$WORK/audit_twice.json'))['counts'].get('AMBIGUOUS', 0))
")
check "one library passed twice does not make every key AMBIGUOUS" 0 "$twice"

# ------------------- a real key on the wrong paper (a composed key that collided)
# The note's DOI is paper A, but the key it carries is the library's key for paper B. The
# key exists, so it used to read OK and pass --strict; [@key] then cites the wrong paper.
VAULT4="$WORK/vault4"
note "$VAULT4/otherKey2021.md" "otherKey2021" "10.1000/real"  literature   # MISMATCH
python3 "$SCRIPT" --vault "$VAULT4" --bib "$BIB" --json "$WORK/audit4.json" > /dev/null 2>&1
v4=$(python3 -c "
import json; d=json.load(open('$WORK/audit4.json'))
print(','.join(r['verdict']+':'+r['suggested_citekey'] for r in d['findings']) or 'OK')
")
check "a real key whose library DOI differs is MISMATCH, naming the DOI's key" "MISMATCH:realKey2020" "$v4"
python3 "$SCRIPT" --vault "$VAULT4" --bib "$BIB" --strict > /dev/null 2>&1
check "--strict exits 1 on MISMATCH" 1 "$?"
# negative controls: same DOI spelled differently, and a note or entry without a DOI
VAULT5="$WORK/vault5"
BIB5="$WORK/refs5.bib"
printf '@article{noDoiKey2022,\n  title = {An entry without a DOI},\n}\n' > "$BIB5"
note "$VAULT5/realKey2020.md"   "realKey2020"   "https://doi.org/10.1000/REAL" literature  # OK
note "$VAULT5/otherKey2021.md"  "otherKey2021"  ""                             literature  # OK (no DOI on note)
note "$VAULT5/noDoiKey2022.md"  "noDoiKey2022"  "10.1000/whatever"             literature  # OK (entry has no DOI)
python3 "$SCRIPT" --vault "$VAULT5" --bib "$BIB" "$BIB5" --strict --json "$WORK/audit5.json" > /dev/null 2>&1
check "--strict exits 0 when every key's DOI agrees or is absent" 0 "$?"
check "matching or missing DOIs stay OK" 3 "$(python3 -c "
import json; print(json.load(open('$WORK/audit5.json'))['counts']['OK'])
")"

# negative controls: the right key, with the same paper's DOI spelled differently from the
# library (single-quoted YAML, a bare or www. resolver host, a double-braced or \_-escaped
# .bib DOI). None of these DOIs is another key's library DOI, so none may read MISMATCH.
VAULT12="$WORK/vault12"
BIB12="$WORK/refs12.bib"
mkdir -p "$VAULT12/www"
printf '@article{bracedKey2022,\n  doi = {{10.1000/braced}},\n}\n@article{escKey2022,\n  doi = {10.1000/under\\_score},\n}\n' > "$BIB12"
fm() { printf -- '---\ncitekey: "%s"\ndoi: %s\nnotetype: literature\n---\nbody\n' "$2" "$3" > "$VAULT12/$1.md"; }
fm realKey2020      realKey2020   "'10.1000/real'"
fm otherKey2021     otherKey2021  '"doi.org/10.1000/other"'
fm www/realKey2020  realKey2020   '"https://www.doi.org/10.1000/real"'
fm bracedKey2022    bracedKey2022 '"10.1000/braced"'
fm escKey2022       escKey2022    '"10.1000/under_score"'
python3 "$SCRIPT" --vault "$VAULT12" --bib "$BIB" "$BIB12" --strict --json "$WORK/audit12.json" > /dev/null 2>&1
check "a DOI spelled differently from the library never raises MISMATCH (--strict exits 0)" 0 "$?"
check "all five spelling-drift notes stay OK" 5 "$(python3 -c "
import json; print(json.load(open('$WORK/audit12.json'))['counts']['OK'])
")"
# ...while a single-quoted note DOI that IS another key's library DOI is still MISMATCH
VAULT13="$WORK/vault13"
mkdir -p "$VAULT13"
printf -- "---\ncitekey: \"otherKey2021\"\ndoi: \"https://doi.org/10.1000/REAL\"\nnotetype: literature\n---\nbody\n" > "$VAULT13/otherKey2021.md"
python3 "$SCRIPT" --vault "$VAULT13" --bib "$BIB" --strict > /dev/null 2>&1
check "a resolver-prefixed DOI of another key is still MISMATCH (--strict exits 1)" 1 "$?"

# ------------- notes the scan used to skip silently (zero checked, --strict green)
# A vault reached through ../ or kept under a dot-folder had every note treated as hidden;
# a note saved with a UTF-8 BOM, or with frontmatter past 4000 characters, was not read.
HIDDEN="$WORK/.dotparent/vault6"
note "$HIDDEN/composedKey2021.md" "composedKey2021" "10.1000/other" literature  # INVENTED
python3 "$SCRIPT" --vault "$HIDDEN" --bib "$BIB" --strict > /dev/null 2>&1
check "a vault under a dot-folder is scanned (--strict exits 1)" 1 "$?"
mkdir -p "$WORK/sib"
( cd "$WORK/sib" && python3 "$SCRIPT" --vault ../vault4 --bib "$BIB" --strict > /dev/null 2>&1 )
check "a vault given as ../path is scanned (--strict exits 1)" 1 "$?"
VAULT7="$WORK/vault7"
mkdir -p "$VAULT7"
printf '\xef\xbb\xbf---\ncitekey: "composedKey2021"\ndoi: "10.1000/other"\nnotetype: literature\n---\nbody\n' \
  > "$VAULT7/composedKey2021.md"
python3 "$SCRIPT" --vault "$VAULT7" --bib "$BIB" --strict > /dev/null 2>&1
check "a note starting with a UTF-8 BOM is read (--strict exits 1)" 1 "$?"
VAULT8="$WORK/vault8"
mkdir -p "$VAULT8"
{ echo "---"; echo 'citekey: "composedKey2021"'; printf 'abstract: "%s"\n' "$(printf 'x%.0s' $(seq 1 4100))"
  echo 'doi: "10.1000/other"'; echo "notetype: literature"; echo "---"; echo body; } > "$VAULT8/composedKey2021.md"
python3 "$SCRIPT" --vault "$VAULT8" --bib "$BIB" --strict > /dev/null 2>&1
check "a note with frontmatter past 4000 chars is read (--strict exits 1)" 1 "$?"
VAULT9="$WORK/vault9"
mkdir -p "$VAULT9"
printf -- '---\ncitekey: "composedKey2021"\nnotetype: literature\n\nbody, fence never closed\n' > "$VAULT9/unclosed.md"
python3 "$SCRIPT" --vault "$VAULT9" --bib "$BIB" --strict --json "$WORK/audit9.json" > /dev/null 2>&1
check "an unclosed literature frontmatter is UNPARSED and fails --strict" 1 "$?"
check "UNPARSED counted once" 1 "$(python3 -c "
import json; print(json.load(open('$WORK/audit9.json'))['counts']['UNPARSED'])
")"
# negative controls: a hidden folder INSIDE the vault is still skipped, and a vault with
# no literature note passes without --strict but cannot pass under it
VAULT10="$WORK/vault10"
note "$VAULT10/realKey2020.md"      "realKey2020" "10.1000/real" literature  # OK
note "$VAULT10/.trash/composed.md"  "composedKey2021" "10.1000/other" literature  # skipped
printf -- '---\ntitle: x\n\nnot a literature note, fence never closed\n' > "$VAULT10/draft.md"
python3 "$SCRIPT" --vault "$VAULT10" --bib "$BIB" --strict > /dev/null 2>&1
check "dot-folders inside the vault and unclosed non-literature notes stay skipped" 0 "$?"
VAULT11="$WORK/vault11"
note "$VAULT11/concept.md" "notAKey" "" concept
python3 "$SCRIPT" --vault "$VAULT11" --bib "$BIB" > /dev/null 2>&1
check "no literature note: exit 0 without --strict" 0 "$?"
python3 "$SCRIPT" --vault "$VAULT11" --bib "$BIB" --strict > /dev/null 2>&1
check "no literature note: --strict exits 2 (nothing was checked)" 2 "$?"

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

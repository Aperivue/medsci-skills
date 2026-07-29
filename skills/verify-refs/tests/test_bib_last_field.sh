#!/usr/bin/env bash
# Regression test: a BibTeX field that is the entry's LAST one must still be read.
#
# BibTeX makes the comma after an entry's final field optional. Both the `doi` and `title` regexes
# required one, so any entry ending in `doi = {...}` produced `record.doi == ""` — and an empty DOI
# skips the CrossRef check outright and drops the record onto the soft-flagged OpenAlex title path,
# where the full-author cross-check is DISABLED. The anti-fabrication check this skill exists for was
# silently off for exactly those references. All three DOIs in the repo's own shipped fixture
# `tests/fixtures/corporate_author.bib` were being dropped this way.
#
# `title` had the identical defect with a different remedy: it cannot take an optional comma, because
# a non-greedy match would then stop at the inner `}` of a brace-protected group and return
# "A multisociety {Delphi". Both fields are now read by counting braces.
#
# Network-free: every assertion is against the parser.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/verify-refs/scripts/verify_refs.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-46s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-46s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

field() {  # field <which> <bib-body>
  python3 - "$V" "$1" "$2" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["vr"] = m
spec.loader.exec_module(m)
recs = m.parse_bib(sys.argv[3])
r = recs[0]
print(r.doi if sys.argv[2] == "doi" else r.title_guess)
PY
}

DOI_LAST='@article{k,
  author = {Smith, John},
  title  = {A title},
  doi    = {10.1000/xyz789}
}'
TITLE_LAST='@article{k,
  author = {Smith, John},
  doi    = {10.1000/xyz789},
  title  = {A plain title}
}'
BRACED='@article{k,
  author = {Smith, John},
  title  = {A multisociety {Delphi} consensus statement},
  doi    = {10.1000/xyz789}
}'
BRACED_LAST='@article{k,
  author = {Smith, John},
  doi    = {10.1000/xyz789},
  title  = {A multisociety {Delphi} consensus statement}
}'
QUOTED='@article{k,
  author = {Smith, John},
  title  = "A quoted title",
  doi    = {10.1000/xyz789}
}'
NO_DOI='@article{k,
  author = {Smith, John},
  title  = {A title}
}'
# doi genuinely mid-entry, with a trailing comma: the form that already worked and must keep working.
DOI_MID='@article{k,
  author = {Smith, John},
  doi    = {10.1000/xyz789},
  year   = {2024}
}'

echo "==== the last field is still a field ===="
ck "doi last"                     "10.1000/xyz789"  "$(field doi "$DOI_LAST")"
ck "doi mid-entry, trailing comma" "10.1000/xyz789" "$(field doi "$DOI_MID")"
ck "title last"                   "A plain title"   "$(field title "$TITLE_LAST")"

echo "==== brace-protected groups are not truncated (either position) ===="
ck "braced title, comma after"    "A multisociety {Delphi} consensus statement" "$(field title "$BRACED")"
ck "braced title, last field"     "A multisociety {Delphi} consensus statement" "$(field title "$BRACED_LAST")"
ck "quote-delimited title"        "A quoted title"  "$(field title "$QUOTED")"

echo "==== NEGATIVE CONTROLS — absent stays absent ===="
ck "no doi field: empty, not invented"  ""  "$(field doi "$NO_DOI")"
ck "title still read when doi absent"   "A title"  "$(field title "$NO_DOI")"

echo "==== the shipped fixture that was silently DOI-less ===="
n_empty="$(python3 - "$V" "$REPO_ROOT/skills/verify-refs/tests/fixtures/corporate_author.bib" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["vr"] = m
spec.loader.exec_module(m)
recs = m.parse_bib(open(sys.argv[2], encoding="utf-8").read())
print(sum(1 for r in recs if not r.doi))
PY
)"
ck "entries with no parsed DOI"   0  "$n_empty"

echo "==== duplicate detection needs the DOI it was not getting ===="
dup="$(python3 - "$V" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["vr"] = m
spec.loader.exec_module(m)
bib = """@article{a,
  author = {Smith, John},
  title  = {First},
  doi    = {10.1000/same}
}

@article{b,
  author = {Doe, Jane},
  title  = {Second},
  doi    = {10.1000/same}
}
"""
print(len(m.detect_duplicates(m.parse_bib(bib))))
PY
)"
ck "two DOI-last entries sharing a DOI"  1  "$dup"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: the last field parses, brace groups survive, and an absent DOI stays absent."

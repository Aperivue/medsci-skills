#!/usr/bin/env bash
# Regression test: fill_journal_abbrev.py must survive its own first entry.
#
# `parse_entries` returned the Match objects from `re.finditer`, while every caller treats the result
# as the entry TEXT. So the first line of work —
#
#     key = re.match(r"@\w+\{([^,]+),", b).group(1)
#
# — raised `TypeError: expected string or bytes-like object, got 're.Match'`, on the FIRST entry, for
# every input. The script had never run. Meanwhile `check_csl_render.py` names it to the user as the
# remedy when a journal spec needs `shortjournal`, and `manage-refs/SKILL.md` lists it in the tool
# table. A tool that cannot start is worse than a missing one: it is advertised.
#
# The second defect only becomes visible once the first is fixed. `field()` required a trailing comma
# after the value, and BibTeX makes that comma optional on an entry's LAST field — which `doi` very
# often is. The DOI would have come back None, no PMID lookup would happen, and the run would report
# "0/1 entries" while exiting 0. Same defect class as the reference parser fixed in #445.
#
# Network-free: asserts the parsing contract, never PubMed.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
F="$REPO_ROOT/skills/manage-refs/scripts/fill_journal_abbrev.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-52s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

probe() {  # probe <mode> -> one line of output
  python3 - "$F" "$1" <<'PY'
import importlib.util, re, sys
spec = importlib.util.spec_from_file_location("fja", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["fja"] = m
spec.loader.exec_module(m)
mode = sys.argv[2]

DOI_LAST = """@article{Rinella2023,
\tauthor = {Rinella, Mary E.},
\tjournal = {Hepatology},
\tyear = {2023},
\tdoi = {10.1097/HEP.0000000000000520}
}
"""
DOI_MID = """@article{Smith2023,
\tauthor = {Smith, John},
\tdoi = {10.1000/xyz789},
\tjournal = {Radiology},
\tyear = {2023}
}
"""
NO_DOI = """@article{Doe2023,
\tauthor = {Doe, Jane},
\tjournal = {Radiology},
\tyear = {2023}
}
"""
TWO = DOI_LAST + "\n" + DOI_MID

if mode == "type":
    print(type(m.parse_entries(DOI_LAST)[0]).__name__)
elif mode == "caller":
    # exactly what main() does first; this is where it used to raise TypeError
    try:
        b = m.parse_entries(DOI_LAST)[0]
        print(re.match(r"@\w+\{([^,]+),", b).group(1).strip())
    except TypeError as e:
        print(f"TypeError: {e}")
elif mode == "count":
    print(len(m.parse_entries(TWO)))
elif mode == "doi_last":
    print(m.field(m.parse_entries(DOI_LAST)[0], "doi") or "None")
elif mode == "doi_mid":
    print(m.field(m.parse_entries(DOI_MID)[0], "doi") or "None")
elif mode == "doi_absent":
    print(m.field(m.parse_entries(NO_DOI)[0], "doi") or "None")
elif mode == "journal_mid":
    print(m.field(m.parse_entries(DOI_MID)[0], "journal") or "None")
PY
}

echo "==== the script must survive its own first entry ===="
ck "parse_entries yields text, not Match"  str        "$(probe type)"
ck "the caller's first line does not raise" Rinella2023 "$(probe caller)"
ck "two entries parse as two"              2          "$(probe count)"

echo "==== a value in the LAST field is still a value ===="
ck "doi as the entry's last field"  "10.1097/HEP.0000000000000520" "$(probe doi_last)"
ck "doi mid-entry, trailing comma"  "10.1000/xyz789"               "$(probe doi_mid)"
ck "journal mid-entry"              "Radiology"                    "$(probe journal_mid)"

echo "==== NEGATIVE CONTROL — absent stays absent ===="
ck "no doi field: None, not invented" None "$(probe doi_absent)"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: the tool starts, reads its last field, and does not invent a DOI it was not given."

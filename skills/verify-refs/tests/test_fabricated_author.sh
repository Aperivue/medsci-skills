#!/usr/bin/env bash
# Regression test for verify-refs fabricated-author detection (network-free).
#
# author_cross_check() is the sole decision surface behind an AUTHOR MISMATCH status
# (family-by-family + author-count). It is the repo's most trust-critical citation
# check: a real AI-assembled bib once registered 7 of 10 fabricated co-author names
# with a correct first author + DOI, and only the family/count cross-check catches
# that. This test locks the logic so a refactor cannot silently drop the MISMATCH
# path. Stdlib-only, no network (the pure function is tested in isolation, so no
# PubMed/CrossRef/OpenAlex call is made).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$HERE/../scripts"
[[ -f "$SCRIPTS/verify_refs.py" ]] || { echo "ENV-ERR: verify_refs.py missing" >&2; exit 2; }

python3 - "$SCRIPTS" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from verify_refs import author_cross_check

fails = 0
def check(label, cond):
    global fails
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        fails += 1

# 1. Clean list — cited == actual — no mismatch.
m, n = author_cross_check(["Liu", "Chen", "Wang"], ["Liu", "Chen", "Wang"], 3, 3)
check("clean list -> no mismatch", m == [])

# 2. Fabricated co-authors — correct first author + count, wrong #2..#N families.
m, n = author_cross_check(["Liu", "Ingram", "Xue"], ["Liu", "Chen", "Wang"], 3, 3)
check("fabricated co-authors -> 2 family mismatches",
      len(m) == 2 and "#2 family" in m[0] and "#3 family" in m[1])

# 3. Extra cited author beyond the source list.
m, n = author_cross_check(["Liu", "Chen", "Ghost"], ["Liu", "Chen"], 3, 2)
check("extra cited author -> flagged", any("extra cited='Ghost'" in x for x in m))

# 4. Author-count mismatch (not truncated) -> AUTHOR COUNT flag.
m, n = author_cross_check(["Liu"], ["Liu", "Chen", "Wang"], 1, 3)
check("count mismatch -> AUTHOR COUNT flag", any("AUTHOR COUNT" in x for x in m))

# 5. Intentional CSL et-al truncation (cited < actual, marker set) -> note, NOT mismatch.
m, n = author_cross_check(["Liu"], ["Liu", "Chen", "Wang"], 1, 3, audit_truncated=True)
check("audit_truncated -> note not mismatch",
      m == [] and any("intentional truncate" in x for x in n))

# 6. Corporate/collective author -> exempt (must never fire MISMATCH).
m, n = author_cross_check(["Ghost"], ["KDIGO Working Group"], 1, 1, corporate=True)
check("corporate author -> exempt", m == [])

# 7. OpenAlex-soft list -> exempt from strict positional check.
m, n = author_cross_check(["Liu", "Ingram"], ["Liu", "Chen"], 2, 2, soft=True)
check("soft (OpenAlex) list -> exempt", m == [])

# 8. First-author degrade (no cited list; first_author_guess mismatches source).
m, n = author_cross_check([], ["Chen", "Wang"], 0, 2, first_author_guess="Liu")
check("first-author degrade -> #1 mismatch", any("#1 family" in x for x in m))

# 9. First-author degrade clean (first_author_guess matches source).
m, n = author_cross_check([], ["Liu", "Wang"], 0, 2, first_author_guess="Liu")
check("first-author degrade clean -> no mismatch", m == [])

print(f"\nfails={fails}")
sys.exit(1 if fails else 0)
PY
rc=$?
echo
[[ $rc -eq 0 ]] && echo "ALL PASS" || echo "FAILURES"
exit $rc

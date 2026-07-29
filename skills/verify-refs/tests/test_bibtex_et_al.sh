#!/usr/bin/env bash
# Regression test: the BibTeX `and others` sentinel is a declared truncation, not a mismatch.
#
# `and others` is BibTeX's own et-al.: Zotero, Mendeley, JabRef and a hand-written .bib all
# emit it for a list the author chose not to type out, and BibTeX and CSL both render it as
# "et al." verify_refs parsed it (it already dropped the literal family "others" from the
# cited list) but did not treat it as a declaration, so `cited=6 vs source=53` became
# AUTHOR MISMATCH — the render-aborting verdict — on the reference class clinical
# manuscripts cite most: multisociety guidelines and consortium papers.
#
# The escape hatch that did exist, `_audit_truncated = N`, is a field this toolkit invented.
# No reference manager writes it. So the universal way to declare a truncation failed and the
# private way succeeded, which is the wrong way round.
#
# The repo's own fixture proved the cost: skills/manage-refs/tests/fixtures/pre_submission_gate
# uses `and others`, and its Test 2 invariant broke when the author cross-check landed
# (v1.3.0, #41, 2026-05-31) and stayed broken because that fixture is not wired into CI.
#
# Network-free by construction: every assertion below is against the parser and the
# cross-check function, never against PubMed or CrossRef.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/verify-refs/scripts/verify_refs.py"

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

run() {
  python3 - "$V" "$@" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
m = importlib.util.module_from_spec(spec)
# @dataclass resolves cls.__module__ through sys.modules; register before exec.
sys.modules["vr"] = m
spec.loader.exec_module(m)
mode = sys.argv[2]

if mode == "sentinel":
    print("true" if m.has_bibtex_et_al(sys.argv[3]) else "false")

elif mode == "parsed_truncated":
    bib = (
        "@article{k,\n  author = {%s},\n  title = {T},\n  year = {2023},\n"
        "  doi = {10.1/x}\n}\n" % sys.argv[3]
    )
    rec = m.parse_bib(bib)[0]
    print("true" if rec.audit_truncated else "false")

elif mode == "xcheck":
    # cited families | source families | cited_n | actual_n | truncated
    cited = [s for s in sys.argv[3].split(",") if s]
    actual = [s for s in sys.argv[4].split(",") if s]
    mism, _notes = m.author_cross_check(
        cited, actual, int(sys.argv[5]), int(sys.argv[6]),
        corporate=False, soft=False,
        audit_truncated=(sys.argv[7] == "1"), first_author_guess="",
    )
    print("MISMATCH" if mism else "OK")
PY
}

echo "==== the sentinel is recognised only where BibTeX defines it ===="
ck "trailing 'and others'"          true  "$(run sentinel 'Rinella, M and Lazarus, J and others')"
ck "case-insensitive"               true  "$(run sentinel 'Rinella, M and Others')"
ck "no sentinel"                    false "$(run sentinel 'Rinella, M and Lazarus, J')"
ck "surname Others mid-list"        false "$(run sentinel 'Others, A B and Rinella, M')"
ck "empty field"                    false "$(run sentinel '')"

echo "==== the parser records it as a declared truncation ===="
ck "and others sets audit_truncated"   true  "$(run parsed_truncated 'Rinella, M and Lazarus, J and others')"
ck "plain list does not"               false "$(run parsed_truncated 'Rinella, M and Lazarus, J')"

echo "==== NEGATIVE CONTROLS — the check must still bite ===="
# 2 cited of 53 real authors, truncation declared: a count gap alone is not a finding.
ck "declared truncation, families agree" OK \
   "$(run xcheck 'Rinella,Lazarus' 'Rinella,Lazarus,Ratziu' 2 53 1)"
# Same declaration, but a cited family does not match the source: still a mismatch.
ck "declared truncation, wrong family"  MISMATCH \
   "$(run xcheck 'Rinella,Fabricated' 'Rinella,Lazarus,Ratziu' 2 53 1)"
# Same declaration, but MORE cited authors than the source has: invention, never intentional.
ck "declared truncation, extra author"  MISMATCH \
   "$(run xcheck 'Rinella,Lazarus,Ratziu,Ghost' 'Rinella,Lazarus,Ratziu' 4 3 1)"
# No declaration at all: a silent short list is exactly what the count check exists for.
ck "undeclared truncation still fires"  MISMATCH \
   "$(run xcheck 'Rinella,Lazarus' 'Rinella,Lazarus,Ratziu' 2 53 0)"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: \`and others\` is a declaration, and declaring it does not buy silence on invention."

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
# The third defect sat in the WRITE step, which nothing tested. The insertion pattern only knew tab
# indentation, so on a two-space bib it never found the journal field and appended `shortjournal`
# after the entry's last field; when that field had no trailing comma (BibTeX does not need one), the
# result was `doi = {...}\n\tshortjournal = {...},` and pandoc refused the whole file ("unexpected
# 's'"), so on a two-space bib nearly every addition broke it. The write-path section below
# runs main() end to end with the lookups pinned, and asserts the exact output text, that pandoc reads
# it, that a second run changes nothing, and that a failed lookup is reported, not passed over.
#
# Network-free: PubMed and CrossRef are replaced by fixed answers.
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

echo "==== WRITE PATH — main() end to end, lookups pinned ===="
# One Python run checks every case and prints one PASS/FAIL line each; the last line is the count.
write_out="$(python3 - "$F" <<'PY'
import contextlib, importlib.util, io, json, os, shutil, subprocess, sys, tempfile

spec = importlib.util.spec_from_file_location("fja_w", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["fja_w"] = m
spec.loader.exec_module(m)

PMID = {"10.1234/a": "111", "10.1234/b": "222"}
NLM = {"111": "Synth Rep", "222": "J Synth Methods"}
CROSSREF = {"10.1234/c": "J. Synth. Softw."}
REAL_PMIDS_SUMMARY = m.pmids_summary
m.doi_to_pmid = lambda doi: PMID.get(doi)
m.pmids_summary = lambda pmids: {p: {"source": NLM.get(p)} for p in pmids}
m.crossref_short_title = lambda doi: CROSSREF.get(doi)
m.time.sleep = lambda s: None
PANDOC = shutil.which("pandoc")
work = tempfile.mkdtemp()
results = []

def run(text, same_file=False):
    src = os.path.join(work, "in.bib")
    dst = src if same_file else os.path.join(work, "out.bib")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(text)
    if os.path.exists(dst) and not same_file:
        os.remove(dst)
    sys.argv = ["fill_journal_abbrev.py", "--bib", src, "--out", dst]
    buf, code = io.StringIO(), 0
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            m.main()
        except SystemExit as e:
            code = e.code or 0
    out = open(dst, encoding="utf-8").read() if os.path.exists(dst) else None
    return out, code, buf.getvalue()

def pandoc_short(text):
    """{key: container-title-short} as pandoc reads the bib, or an error string."""
    path = os.path.join(work, "check.bib")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    p = subprocess.run([PANDOC, path, "-f", "biblatex", "-t", "csljson"], capture_output=True, text=True)
    if p.returncode != 0:
        return "pandoc exit %d: %s" % (p.returncode, p.stderr.strip()[:120])
    return {e["id"]: e.get("container-title-short") for e in json.loads(p.stdout)}

def case(label, text, expected, short=None):
    """expected: the exact output text; short: {key: abbreviation} pandoc must read back."""
    try:
        out, code, log = run(text)
        problems = []
        if out != expected:
            problems.append("output differs: %r" % (out,))
        if code != 0:
            problems.append("exit %s" % code)
        if PANDOC and short is not None and out is not None:
            got = pandoc_short(out)
            if got != short and not (isinstance(got, dict) and all(got.get(k) == v for k, v in short.items())):
                problems.append("pandoc read %r" % (got,))
        if out is not None:  # a second run must change nothing
            again, _, _ = run(out)
            if again != out:
                problems.append("second run changed the file")
    except Exception as e:  # an interface the tool lacks is a failure, not a crash of the test
        problems = ["%s: %s" % (type(e).__name__, e)]
    results.append(("PASS  " if not problems else "FAIL  ") + label + ("" if not problems else "  -- " + "; ".join(problems)))

A = "@article{alpha2020,\n  author = {Alpha, Ada},\n  journal = {Synthetic Reports},\n  year = {2020},\n  doi = {10.1234/a}\n}\n"
case("two-space indent, doi last without comma", A,
     A.replace("  journal = {Synthetic Reports},\n", "  journal = {Synthetic Reports},\n  shortjournal = {Synth Rep},\n"),
     {"alpha2020": "Synth Rep"})

B = "@article{beta2021,\n  author = {Beta, Boris},\n  doi = {10.1234/b},\n  journal = {Journal of Synthetic Methods}\n}\n"
case("journal is the last field, no comma", B,
     B.replace("{Journal of Synthetic Methods}\n}", "{Journal of Synthetic Methods},\n  shortjournal = {J Synth Methods}\n}"),
     {"beta2021": "J Synth Methods"})

C = '@article{gamma2022,\n  author = {Gamma, Grace},\n  journal = "Synthetic Reports",\n  doi = "10.1234/a"\n}\n'
case("quoted journal and doi", C,
     C.replace('"Synthetic Reports",\n', '"Synthetic Reports",\n  shortjournal = {Synth Rep},\n'),
     {"gamma2022": "Synth Rep"})

D = "@article{delta2023, author = {Delta, Dan}, journal = {Synthetic Reports}, doi = {10.1234/a}}\n"
case("one-line entry", D,
     D.replace("{Synthetic Reports},", "{Synthetic Reports}, shortjournal = {Synth Rep},"),
     {"delta2023": "Synth Rep"})

E = "@article{eps2024,\n  journal = {Synthetic Reports},\n  shortjournal = {},\n  doi = {10.1234/a}\n}\n"
case("empty shortjournal is filled in place", E, E.replace("shortjournal = {}", "shortjournal = {Synth Rep}"),
     {"eps2024": "Synth Rep"})

F = "@article{zeta2025,\n  journal = {Synthetic Reports},\n  shortjournal = {Synthetic Rep},\n  doi = {10.1234/a}\n}\n"
case("non-empty shortjournal is kept as written", F, F, {"zeta2025": "Synthetic Rep"})

G = "@article{eta2026,\n\tjournal = {Synthetic Reports},\n\tdoi = {10.1234/a}\n}\n"
case("tab indent is kept", G, G.replace("{Synthetic Reports},\n", "{Synthetic Reports},\n\tshortjournal = {Synth Rep},\n"),
     {"eta2026": "Synth Rep"})

H = "@article{theta2027,\n  journal = {Journal of Synthetic Software},\n  doi = {10.1234/c}\n}\n"
case("CrossRef fallback when PubMed has no record", H,
     H.replace("Software},\n", "Software},\n  shortjournal = {J. Synth. Softw.},\n"), {"theta2027": "J. Synth. Softw."})
try:
    _, _, log = run(H)
    results.append(("PASS  " if "CrossRef" in log and "check" in log else "FAIL  ") + "a CrossRef value is reported as such")
except Exception as e:
    results.append("FAIL  a CrossRef value is reported as such  -- %s" % e)

I = "@article{iota2028,\n  journal = {Synthetic Reports},\n  year = {2028}\n}\n"
case("NEGATIVE: no PMID or DOI -> unchanged", I, I)

# A bare number is a BibTeX literal: `pmid = 111` is a PMID, not a missing one.
K = "@article{kappa2029,\n  journal = {Synthetic Reports},\n  pmid = 111\n}\n"
case("bare numeric pmid is read", K, K.replace("{Synthetic Reports},\n", "{Synthetic Reports},\n  shortjournal = {Synth Rep},\n"),
     {"kappa2029": "Synth Rep"})

# A `%` line outside any entry is a comment, as pandoc reads it: `% @article{old,` starts no entry.
L = "% @article{old,\n" + A
case("a commented-out entry start is a comment", L,
     L.replace("  journal = {Synthetic Reports},\n", "  journal = {Synthetic Reports},\n  shortjournal = {Synth Rep},\n"),
     {"alpha2020": "Synth Rep"})

# Fields with no comma between them: never write a file pandoc cannot read.
try:
    nocomma = "@article{mu2031, journal = {Synthetic Reports} pmid = {111}}\n"
    out, code, log = run(nocomma)
    ok = (code == 2 and out is None) or (out == nocomma and "mu2031" in log and "not parsed" in log)
    results.append(("PASS  " if ok else "FAIL  ") + "fields without a comma -> refused or left unchanged, never broken further"
                   + ("" if ok else "  -- exit %s, out %r" % (code, out)))
except Exception as e:
    results.append("FAIL  fields without a comma  -- %s: %s" % (type(e).__name__, e))

# An entry with unbalanced braces swallows every entry after it: stop, name it, write nothing.
try:
    broken = A + "@article{lambda2030, journal = {Synthetic Reports}, pmid = {111}\n" + B
    out, code, log = run(broken)
    ok = code == 2 and out is None and "lambda2030" in log and "unbalanced" in log
    results.append(("PASS  " if ok else "FAIL  ") + "unbalanced braces -> exit 2, entry named, nothing written"
                   + ("" if ok else "  -- exit %s, wrote %s" % (code, out is not None)))
except Exception as e:
    results.append("FAIL  unbalanced braces -> exit 2  -- %s: %s" % (type(e).__name__, e))

# NCBI can report a failure inside a 200 reply ({"error": ...}); that is no answer, not "no record".
real_get = m._get
try:
    m.pmids_summary = REAL_PMIDS_SUMMARY
    m._get = lambda url: '{"error": "API rate limit exceeded"}'
    out, code, log = run(K)
    ok = code == 1 and out == K and "LOOKUP FAILED" in log
    results.append(("PASS  " if ok else "FAIL  ") + "an error reply from PubMed is a failed lookup"
                   + ("" if ok else "  -- exit %s, log %r" % (code, log[-160:])))
except Exception as e:
    results.append("FAIL  an error reply from PubMed is a failed lookup  -- %s: %s" % (type(e).__name__, e))
finally:
    m._get = real_get
    m.pmids_summary = lambda pmids: {p: {"source": NLM.get(p)} for p in pmids}

# A lookup that could not be made is not "no record": exit 1, entry unchanged, named.
try:
    def down(doi):
        raise m.LookupFailed("network down")
    m.doi_to_pmid = down
    out, code, log = run(A)
    ok = code == 1 and out == A and "alpha2020" in log and "LOOKUP FAILED" in log
    results.append(("PASS  " if ok else "FAIL  ") + "failed lookup -> exit 1, entry unchanged and named"
                   + ("" if ok else "  -- exit %s, out %r" % (code, out)))
except Exception as e:
    results.append("FAIL  failed lookup -> exit 1  -- %s: %s" % (type(e).__name__, e))
finally:
    m.doi_to_pmid = lambda doi: PMID.get(doi)

# A Better BibTeX-managed file is regenerated by Zotero: refuse to edit it in place.
try:
    bbt = "% refs.bib managed by /lit-sync via Zotero Better BibTeX. Do not hand-edit.\n" + A
    out, code, _ = run(bbt, same_file=True)
    ok = code == 2 and out == bbt
    results.append(("PASS  " if ok else "FAIL  ") + "a /lit-sync-managed bib is not edited in place"
                   + ("" if ok else "  -- exit %s" % code))
except Exception as e:
    results.append("FAIL  a /lit-sync-managed bib is not edited in place  -- %s: %s" % (type(e).__name__, e))

if not PANDOC:
    results.append("SKIP  pandoc read-back (pandoc unavailable)")
print("\n".join(results))
print("FAILED=%d" % sum(r.startswith("FAIL") for r in results))
PY
)"
printf '%s\n' "$write_out" | grep -v '^FAILED=' | sed 's/^/  /'
wfail="$(printf '%s\n' "$write_out" | sed -n 's/^FAILED=//p')"
wpass="$(printf '%s\n' "$write_out" | grep -c '^PASS')"
pass=$((pass + wpass))
if [ -z "$wfail" ]; then
  printf '  FAIL  write-path probe did not finish\n'
  fail=$((fail + 1))
else
  fail=$((fail + wfail))
fi

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: the tool starts, reads its last field, does not invent a DOI, and writes a bib pandoc can read."

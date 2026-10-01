#!/usr/bin/env bash
# Regression test: a DOI that is registered nowhere makes the reference FABRICATED.
#
# Every CrossRef failure used to be UNVERIFIED, so a made-up DOI could never come out
# FABRICATED, and submission_safe (which tolerates UNVERIFIED) stayed true for a fabricated
# reference. CrossRef's 404 alone proves nothing — it is one of several DOI registration
# agencies — so after a CrossRef 404 the doi.org handle API, which resolves across all of them,
# decides: HTTP 404 + responseCode 100 is FABRICATED, or MISMATCH when a title search still finds
# the work (a real paper cited with a wrong DOI); a DOI registered elsewhere (a DataCite one) or
# a failed lookup stays UNVERIFIED, and the title search can still earn it OK.
#
# Cases: not registered + no title match (FABRICATED, audit not submission-safe); not registered
# + title match (MISMATCH); registered with another agency (never FABRICATED or MISMATCH, and an
# index can still confirm it); doi.org failing (network, 5xx, unexpected JSON); CrossRef itself
# unreachable (doi.org is not consulted); a placeholder that is not a DOI; and a legacy SICI DOI
# extracted whole from text.
# Network-free: http_fetch and http_json are monkeypatched.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/verify_refs.py"

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 - "$SCRIPT" <<'PY'
import importlib.util, json, sys, tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
vr = importlib.util.module_from_spec(spec)
sys.modules["vr"] = vr  # dataclass resolution needs the module registered (py3.14)
spec.loader.exec_module(vr)

fail = 0
def check(label, cond):
    global fail
    if cond:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}")
        fail += 1

NOT_FOUND = (404, {"responseCode": 100, "handle": "x"})
REGISTERED = (200, {"responseCode": 1, "handle": "x", "values": []})
NETWORK_DOWN = (None, None)
CROSSREF_404 = (404, None)                      # CrossRef answers 404 with a plain-text body

REAL_TITLE = "A synthetic stand-in title for a record that the stubbed index really holds"
FAKE_TITLE = "Synthetic invented deep learning prediction of imaginary outcomes in fictional cohorts"

calls = []
def route(crossref, handle, openalex_doi=None, pubmed_title=None):
    """Stub both HTTP helpers from one URL table; `calls` records every URL asked for."""
    def fetch(url, timeout):
        calls.append(url)
        if "api.crossref.org" in url:
            return crossref
        if "doi.org/api/handles/" in url:
            return handle(url) if callable(handle) else handle
        if "api.openalex.org/works/https://doi.org/" in url:
            return (200, openalex_doi) if openalex_doi else (404, None)
        if "api.openalex.org" in url:
            return (200, {"results": []})
        if "esearch.fcgi" in url:
            return (200, {"esearchresult": {"idlist": ["90000001"] if pubmed_title else []}})
        if "esummary.fcgi" in url:
            return (200, {"result": {"90000001": {"title": pubmed_title}}})
        return (None, None)
    def json_only(url, timeout):
        status, data = fetch(url, timeout)
        return data if status == 200 else None
    vr.http_fetch, vr.http_json = fetch, json_only

def record(doi, title=FAKE_TITLE):
    return vr.RefRecord(ref_id="synthetic2024", raw="@article{synthetic2024, ...}",
                        title_guess=title, title_from_field=True,  # a BibTeX title, as parse_bib sets it
                        doi=doi, cited_authors=["Nobody"], cited_author_count=1)

def run(rec, use_openalex=True):
    calls.clear()
    return vr.verify_record(rec, offline=False, timeout=5, use_openalex=use_openalex)

# 1. Not registered anywhere -> FABRICATED, and the audit is not submission-safe.
route(CROSSREF_404, NOT_FOUND)
st, ev, _ = vr.verify_crossref("10.0000/synthetic.0001", 5)
check("CrossRef 404 + handle not found -> FABRICATED", st == "FABRICATED")
out = run(record("10.0000/synthetic.0001"))
check("made-up DOI + made-up title -> FABRICATED", out.status == "FABRICATED")
check("evidence: DOI does not exist in any registry", "does not exist in any registry" in out.evidence)
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    bib = td / "refs.bib"
    bib.write_text("@article{synthetic2024,\n  title = {%s},\n  doi = {10.0000/synthetic.0001}\n}\n"
                   % FAKE_TITLE, encoding="utf-8")
    recs = [vr.verify_record(r, offline=False, timeout=5, use_openalex=True)
            for r in vr.parse_bib(bib.read_text(encoding="utf-8"))]
    vr.write_outputs(recs, td, bib, vr.detect_duplicates(recs))
    audit = json.loads((td / "qc" / "reference_audit.json").read_text(encoding="utf-8"))
check("audit: submission_safe is false", audit["submission_safe"] is False)

# 2. Registered with another agency (a DataCite-style DOI CrossRef does not hold): never FABRICATED
#    or MISMATCH. With no title match it is UNVERIFIED; an index that holds it makes it OK.
route(CROSSREF_404, REGISTERED)
out = run(record("10.5281/zenodo.0000001"))
check("DataCite-style DOI, no title match -> UNVERIFIED", out.status == "UNVERIFIED")
check("evidence says registered with another agency", "registered with another agency" in out.evidence)
route(CROSSREF_404, REGISTERED, openalex_doi={"id": "https://openalex.org/W1", "title": FAKE_TITLE})
out = run(record("10.5281/zenodo.0000001"))
check("DataCite-style DOI, OpenAlex holds it -> OK", out.status == "OK")
route(CROSSREF_404, REGISTERED, pubmed_title=REAL_TITLE + ".")
out = run(record("10.5281/zenodo.0000001", title=REAL_TITLE), use_openalex=False)
check("DataCite-style DOI, PubMed title match -> OK (not MISMATCH)", out.status == "OK")

# 3. doi.org fails after a CrossRef 404 (network, 5xx, 404 without responseCode 100,
#    unexpected JSON) -> UNVERIFIED, even when nothing else finds the work.
for label, handle in (("network error", NETWORK_DOWN), ("HTTP 500", (500, None)),
                      ("404 without responseCode", (404, None)),
                      ("unexpected JSON", (200, {"responseCode": 2})), ("JSON list", (200, []))):
    route(CROSSREF_404, handle)
    out = run(record("10.0000/synthetic.0001"))
    check(f"handle lookup {label} -> UNVERIFIED", out.status == "UNVERIFIED")

# 4. CrossRef unreachable (no 404) -> doi.org is not consulted, UNVERIFIED.
route(NETWORK_DOWN, NOT_FOUND)
out = run(record("10.0000/synthetic.0001"))
check("CrossRef network error -> UNVERIFIED", out.status == "UNVERIFIED")
check("CrossRef network error -> doi.org not called",
      not any("doi.org/api/handles/" in u for u in calls))

# 5. A made-up DOI on a title the index really holds -> MISMATCH (wrong DOI for the title).
route(CROSSREF_404, NOT_FOUND, pubmed_title=REAL_TITLE + ".")
out = run(record("10.0000/synthetic.0001", title=REAL_TITLE))
check("made-up DOI + real title -> MISMATCH", out.status == "MISMATCH")
check("MISMATCH evidence: DOI exists nowhere, title matches the PMID",
      "does not exist in any registry" in out.evidence and "PMID=90000001" in out.evidence)
check("MISMATCH note names the wrong identifier", out.note.startswith("wrong identifier"))

# 6. A placeholder in the DOI field is not a DOI -> never FABRICATED, doi.org not called.
route(CROSSREF_404, NOT_FOUND)
out = run(record("n/a"))
check("placeholder DOI -> UNVERIFIED", out.status == "UNVERIFIED")
check("placeholder DOI -> doi.org not called", not any("doi.org/api/handles/" in u for u in calls))

# 7. The DOI a text reference carries is extracted whole, angle brackets included (a cut
#    legacy SICI DOI is registered nowhere and would read as FABRICATED).
sici = "10.1002/(SICI)1097-0258(19980430)17:8<857::AID-SIM777>3.0.CO;2-E"
recs = vr.parse_reference_lines(
    "References\n1. Doe J. A synthetic reference with a legacy DOI. Stat Med. 1998. doi:" + sici + "\n"
    "2. Roe R. Another synthetic reference. J Synth Med. 2020. doi:10.0000/synthetic.0002\n")
check("SICI DOI extracted whole from text", recs[0].doi == sici.lower())
check("ordinary DOI still extracted", recs[1].doi == "10.0000/synthetic.0002")

# 8. A trailing "/" is legal in a DOI. The handle lookup strips it for normalization, so the
#    form the reference actually cites is looked up too: FABRICATED only when every form is
#    registered nowhere, any registered form means registered, any failed lookup UNVERIFIED.
def by_form(slashed, stripped):
    return lambda url: slashed if url.endswith("/") else stripped
recs = vr.parse_bib("@article{synthetic2024,\n  title = {%s},\n  doi = {10.0000/synthetic.dataset/}\n}\n"
                    % FAKE_TITLE)
check("bib keeps the trailing slash of a DOI", recs[0].doi == "10.0000/synthetic.dataset/")
route(CROSSREF_404, by_form(REGISTERED, NOT_FOUND))
out = run(recs[0])
check("slashed form registered, stripped form not -> not FABRICATED", out.status == "UNVERIFIED")
check("both forms looked up",
      sum("doi.org/api/handles/" in u for u in calls) == 2)
route(CROSSREF_404, by_form(NOT_FOUND, NOT_FOUND))
out = run(recs[0])
check("neither form registered -> FABRICATED", out.status == "FABRICATED")
route(CROSSREF_404, by_form(NETWORK_DOWN, NOT_FOUND))
out = run(recs[0])
check("slashed form lookup fails, stripped not registered -> UNVERIFIED", out.status == "UNVERIFIED")
route(CROSSREF_404, NOT_FOUND)
out = run(record("10.0000/synthetic.0001"))
check("DOI without a trailing slash -> one lookup",
      sum("doi.org/api/handles/" in u for u in calls) == 1)

# 9. A legacy SICI DOI can end in a "#" check character (Crossref's own documented example).
#    It is extracted whole, and because SICI extraction from text is fragile, a SICI DOI that
#    doi.org does not know is UNVERIFIED rather than FABRICATED.
sici_hash = "10.1002/(SICI)1521-3951(199911)216:1<135::AID-PSSB135>3.0.CO;2-#"
recs = vr.parse_reference_lines(
    "References\n1. Doe J. A synthetic reference with a legacy DOI. Phys Status Solidi. 1999. doi:"
    + sici_hash + "\n2. Roe R. Another synthetic reference. J Synth Med. 2020. "
    "doi:10.0000/synthetic.0002#section\n")
check("SICI DOI ending in '#' extracted whole", recs[0].doi == sici_hash.lower())
check("'#' after an ordinary DOI is not taken in", recs[1].doi == "10.0000/synthetic.0002")
route(CROSSREF_404, NOT_FOUND)
out = run(record(sici_hash.lower()))
check("SICI DOI not found at doi.org -> UNVERIFIED, not FABRICATED", out.status == "UNVERIFIED")
check("evidence names the legacy SICI caveat", "legacy SICI DOI" in out.evidence)

print(f"fail={fail}")
print("ALL PASS" if fail == 0 else f"FAILURES: {fail}")
sys.exit(fail)
PY

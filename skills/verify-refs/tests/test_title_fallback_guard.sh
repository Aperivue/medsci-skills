#!/usr/bin/env bash
# Regression test: the PubMed title-only fallback must not pass a reference on a search hit alone.
#
# esearch matches the words of a title, not the title, so a made-up title still returns PMIDs. The
# fallback used to return OK on any hit, which let a reference whose DOI lookup failed and whose
# title was fabricated finish OK with submission_safe and fully_verified both true. The OpenAlex
# title search already had a similarity guard for exactly this case; the PubMed fallback now
# fetches the candidates' titles and applies the same one.
#
# The DOI lookup is made unreachable here so the title search is the only evidence (a DOI that is
# registered nowhere is FABRICATED; test_doi_not_registered.sh covers that). Cases: the fabricated
# title ends UNVERIFIED (never OK, never FABRICATED: a search miss is a coverage gap, not proof);
# the positive control, a title PubMed really holds, still ends OK; and a failed candidate fetch is
# UNVERIFIED. A title match is OK only when the matched record's authors were compared with the
# cited ones and agree (case 7). Network-free: http_json and http_fetch are monkeypatched.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/verify_refs.py"

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 - "$SCRIPT" <<'PY'
import importlib.util, sys

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

FAKE_TITLE = "Synthetic invented deep learning prediction of imaginary outcomes in fictional cohorts"
REAL_TITLE = "A synthetic stand-in title for a record that the stubbed index really holds"

IDS = {"esearchresult": {"idlist": ["90000001", "90000002", "90000003"]}}
UNRELATED = {"result": {"uids": ["90000001", "90000002", "90000003"],
    "90000001": {"title": "Prediction of outcomes after an unrelated procedure in adults."},
    "90000002": {"title": "Deep learning in a different imaging task: a cohort study."},
    "90000003": {"title": "Imaginary numbers in signal processing."}}}
# PubMed style: trailing period, one candidate is the cited work.
HOLDS_IT = {"result": {"uids": ["90000001", "90000002", "90000003"],
    "90000001": {"title": "Prediction of outcomes after an unrelated procedure in adults."},
    "90000002": {"title": REAL_TITLE + ".",
                 "authors": [{"name": "Nobody A", "authtype": "Author"},
                             {"name": "Noone B", "authtype": "Author"}]},
    "90000003": {"title": "Imaginary numbers in signal processing."}}}

def make_http(summary):
    def _http(url, timeout):
        if "api.crossref.org" in url:
            return None                 # DOI lookup unreachable
        if "api.openalex.org" in url:
            return {"results": []}      # OpenAlex has nothing either
        if "esearch.fcgi" in url:
            return IDS                  # esearch always finds *something*
        if "esummary.fcgi" in url:
            return summary
        return None
    return _http

def use(http):
    """Route both HTTP helpers through one stub; a None answer is an unreachable host."""
    def fetch(url, timeout):
        data = http(url, timeout)
        return (None, None) if data is None else (200, data)
    vr.http_json, vr.http_fetch = http, fetch

def fake_record(title):
    return vr.RefRecord(
        ref_id="synthetic2024", raw="@article{synthetic2024, ...}", title_guess=title,
        doi="10.0000/synthetic.0001", cited_authors=["Nobody", "Noone"], cited_author_count=2)

# 1. DOI lookup unavailable + fabricated title, candidates unrelated -> UNVERIFIED.
use(make_http(UNRELATED))
out = vr.verify_record(fake_record(FAKE_TITLE), offline=False, timeout=5, use_openalex=True)
check("fabricated title is not OK", out.status != "OK")
check("fabricated title is UNVERIFIED (a search miss is not FABRICATED)",
      out.status == "UNVERIFIED")
check("evidence says no confident PubMed title match",
      "no confident pubmed title match" in out.evidence.lower())

# 2. Same through --no-openalex: the PubMed fallback is the only title check left.
use(make_http(UNRELATED))
out = vr.verify_record(fake_record(FAKE_TITLE), offline=False, timeout=5, use_openalex=False)
check("fabricated title is UNVERIFIED without OpenAlex", out.status == "UNVERIFIED")

# 3. Positive control: a title PubMed holds still earns OK, and names the matched PMID.
use(make_http(HOLDS_IT))
st, ev, fams = vr.verify_pubmed_title(REAL_TITLE, 5)
check("title PubMed holds -> OK", st == "OK" and "PMID=90000002" in ev)
out = vr.verify_record(fake_record(REAL_TITLE), offline=False, timeout=5, use_openalex=True)
check("record with a title PubMed holds -> OK", out.status == "OK")

# 4. The candidate titles cannot be fetched -> UNVERIFIED, not OK.
use(make_http(None))
st, ev, fams = vr.verify_pubmed_title(REAL_TITLE, 5)
check("candidate fetch failure -> UNVERIFIED", st == "UNVERIFIED")

# 5. The audit written for the fabricated reference is not fully verified.
use(make_http(UNRELATED))
import json, tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    bib = td / "refs.bib"
    bib.write_text("@article{synthetic2024,\n  title = {%s},\n  doi = {10.0000/synthetic.0001}\n}\n"
                   % FAKE_TITLE, encoding="utf-8")
    recs = [vr.verify_record(r, offline=False, timeout=5, use_openalex=True)
            for r in vr.parse_bib(bib.read_text(encoding="utf-8"))]
    vr.write_outputs(recs, td, bib, vr.detect_duplicates(recs))
    audit = json.loads((td / "qc" / "reference_audit.json").read_text(encoding="utf-8"))
check("audit: fully_verified is false", audit["fully_verified"] is False)
check("audit: manual reference check required", audit["requires_manual_reference_check"] is True)

# 6. Short tokens that carry meaning count. Dropping every token of <=2 characters made a
#    title ending "CT" identical to the same title ending "MR"; only connective stopwords and
#    stray single letters are ignored now.
CT_TITLE = "Deep learning prediction of lung cancer in CT"
check("'... in CT' vs '... in MR' is below the match threshold",
      vr._title_similarity(CT_TITLE, "Deep learning prediction of lung cancer in MR.") < vr.TITLE_MATCH_MIN)
check("'type 2' vs 'type 1' is not an exact match",
      vr._title_similarity("Outcomes in type 2 diabetes", "Outcomes in type 1 diabetes") < 1.0)
check("stopwords and case still ignored",
      vr._title_similarity("The role of AI in CT triage", "Role of ai for CT triage.") == 1.0)
MR_ONLY = {"result": {"uids": ["90000004"],
    "90000004": {"title": "Deep learning prediction of lung cancer in MR."}}}
def mr_http(url, timeout):
    if "esearch.fcgi" in url:
        return {"esearchresult": {"idlist": ["90000004"]}}
    if "esummary.fcgi" in url:
        return MR_ONLY
    if "api.openalex.org" in url:
        return {"results": []}
    return None
use(mr_http)
out = vr.verify_record(fake_record(CT_TITLE), offline=False, timeout=5, use_openalex=True)
check("CT title matched only by an MR record -> UNVERIFIED, not OK", out.status == "UNVERIFIED")

# 7. A title-only match says a work with that title exists, not that the cited authors wrote it.
#    It used to return OK with an empty author list, so the author cross-check never ran and a
#    reference with invented authors ended OK. The Jaccard guard also tolerates one substituted
#    token once a title has nine or more content tokens, so "hepatitis B" matches "hepatitis C".
HEP_B = ("Long term outcomes of antiviral therapy in chronic hepatitis B patients "
         "enrolled in a multicentre prospective registry cohort")
HEP_C = HEP_B.replace("hepatitis B", "hepatitis C")
check("one substituted token in a long title passes the similarity guard (the gap this closes)",
      vr._title_similarity(HEP_B, HEP_C) >= vr.TITLE_MATCH_MIN)
def one_hit(title, authors):
    item = {"title": title + "."}
    if authors is not None:
        item["authors"] = [{"name": a, "authtype": "Author"} for a in authors]
    def _http(url, timeout):
        if "esearch.fcgi" in url:
            return {"esearchresult": {"idlist": ["90000005"]}}
        if "esummary.fcgi" in url:
            return {"result": {"uids": ["90000005"], "90000005": item}}
        if "api.openalex.org" in url:
            return {"results": []}
        return None
    return _http
def no_id_record(title, authors):
    return vr.RefRecord(ref_id="synthetic2024", raw="@article{synthetic2024, ...}",
                        title_guess=title, title_from_field=True,
                        cited_authors=list(authors), cited_author_count=len(authors))

use(one_hit(HEP_C, ["Realname JK", "Truename L"]))
out = vr.verify_record(no_id_record(HEP_B, ["Fakeauthor", "Nobody"]), offline=False, timeout=5)
check("title match + invented authors -> not OK", out.status != "OK")
check("title match + invented authors -> UNVERIFIED (the matched work may be another one)",
      out.status == "UNVERIFIED" and out.note.startswith("title_only"))
use(one_hit(HEP_B, None))
out = vr.verify_record(no_id_record(HEP_B, ["Fakeauthor", "Nobody"]), offline=False, timeout=5)
check("title match whose record has no author list -> UNVERIFIED",
      out.status == "UNVERIFIED" and "could not be compared" in out.note)
use(one_hit(HEP_B, ["Realname JK", "Truename L"]))
out = vr.verify_record(no_id_record(HEP_B, []), offline=False, timeout=5)
check("title match with no cited authors to compare -> UNVERIFIED", out.status == "UNVERIFIED")
# Negative control: the same title match with agreeing authors is still OK.
out = vr.verify_record(no_id_record(HEP_B, ["Realname", "Truename"]), offline=False, timeout=5)
check("title match + agreeing authors -> OK", out.status == "OK" and not out.note)
st, ev, fams = vr.verify_pubmed_title(HEP_B, 5)
check("verify_pubmed_title returns the matched record's family names",
      st == "OK" and fams == ["Realname", "Truename"])

print(f"fail={fail}")
print("ALL PASS" if fail == 0 else f"FAILURES: {fail}")
sys.exit(fail)
PY

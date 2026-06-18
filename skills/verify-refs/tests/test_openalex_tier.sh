#!/usr/bin/env bash
# Regression test for the OpenAlex tertiary index (conference proceedings / non-DOI
# / non-biomedical recovery). Network-free: monkeypatches http_json so no live API
# is called. Motivation: NeurIPS/ICLR/ACL citations common in medical-AI papers fall
# through PubMed (not biomedical) and CrossRef (spotty proceedings) — OpenAlex is the
# free analogue of a journal portal's second index (e.g. Scopus). Stdlib-only.
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

# --- _title_similarity ----------------------------------------------------------
t = "Reflexion: Language agents with verbal reinforcement learning"
check("title sim exact == 1.0", abs(vr._title_similarity(t, t) - 1.0) < 1e-9)
check("title sim unrelated < 0.3",
      vr._title_similarity(t, "A meta-analysis of CT screening for lung cancer") < 0.3)
check("title sim empty == 0.0", vr._title_similarity("", t) == 0.0)

# --- _openalex_families ---------------------------------------------------------
work = {"authorships": [
    {"author": {"display_name": "Aman Madaan"}},
    {"author": {"display_name": "Niket Tandon"}},
    {"author": {"display_name": "Madaan A"}},   # trailing-initials form
]}
fams = vr._openalex_families(work)
check("families last-token parse", fams[:2] == ["Madaan", "Tandon"])
check("families strip trailing initials", fams[2] == "Madaan")

# --- verify_openalex via monkeypatched http_json --------------------------------
DOI_WORK = {"id": "https://openalex.org/W1",
            "title": "Self-Refine: Iterative refinement with self-feedback",
            "publication_year": 2023,
            "authorships": [{"author": {"display_name": "Aman Madaan"}}]}
TITLE_HIT = {"results": [
    {"title": "Reflexion: Language agents with verbal reinforcement learning",
     "publication_year": 2023,
     "authorships": [{"author": {"display_name": "Noah Shinn"}},
                     {"author": {"display_name": "Federico Cassano"}}]},
    {"title": "Some unrelated paper about kidneys", "authorships": []},
]}
TITLE_MISS = {"results": [
    {"title": "Completely different work on radiology", "authorships": []}]}

def make_http(mapping):
    def _http(url, timeout):
        for needle, payload in mapping.items():
            if needle in url:
                return payload
        return None
    return _http

# (a) DOI resolve
vr.http_json = make_http({"api.openalex.org/works/https://doi.org/": DOI_WORK})
st, ev, fams = vr.verify_openalex("10.5555/self-refine", "", 5)
check("openalex DOI resolve OK", st == "OK" and fams == ["Madaan"] and "via doi" in ev)

# (b) title.search with strong similarity → OK
vr.http_json = make_http({"api.openalex.org/works?": TITLE_HIT})
st, ev, fams = vr.verify_openalex(
    "", "Reflexion: Language agents with verbal reinforcement learning", 5)
check("openalex title hit OK", st == "OK" and fams[0] == "Shinn" and "via title" in ev)

# (c) title with no close match → UNVERIFIED (fabrication guard)
vr.http_json = make_http({"api.openalex.org/works?": TITLE_MISS})
st, ev, fams = vr.verify_openalex(
    "", "Reflexion: Language agents with verbal reinforcement learning", 5)
check("openalex weak-title rejected (UNVERIFIED)", st == "UNVERIFIED" and fams == [])

# (d) no DOI, no title, no match → UNVERIFIED, never FABRICATED
vr.http_json = make_http({})
st, ev, fams = vr.verify_openalex("", "", 5)
check("openalex empty never FABRICATED", st == "UNVERIFIED")

# --- integration through verify_record ------------------------------------------
# A conference paper: no PMID, no DOI, title only. OpenAlex resolves it and the
# cited first author matches → status OK, source includes openalex.
vr.http_json = make_http({"api.openalex.org/works?": TITLE_HIT})
rec = vr.RefRecord(
    ref_id="reflexion2023",
    raw="Shinn N, Cassano F, et al. Reflexion: Language agents with verbal reinforcement learning. NeurIPS 2023.",
    title_guess="Reflexion: Language agents with verbal reinforcement learning",
    cited_authors=["Shinn", "Cassano"],
    first_author_guess="Shinn",
)
out = vr.verify_record(rec, offline=False, timeout=5, use_openalex=True)
check("verify_record conference OK via openalex",
      out.status == "OK" and "openalex" in out.evidence)

# Same record with a fabricated first author → MISMATCH from OpenAlex authors.
vr.http_json = make_http({"api.openalex.org/works?": TITLE_HIT})
rec_bad = vr.RefRecord(
    ref_id="reflexion_bad",
    raw="Ebrahimi A, et al. Reflexion: Language agents with verbal reinforcement learning. NeurIPS 2023.",
    title_guess="Reflexion: Language agents with verbal reinforcement learning",
    cited_authors=["Ebrahimi", "Cassano"],
    first_author_guess="Ebrahimi",
)
out_bad = vr.verify_record(rec_bad, offline=False, timeout=5, use_openalex=True)
check("verify_record catches first-author hallucination via openalex",
      out_bad.status == "MISMATCH" and "AUTHOR MISMATCH" in out_bad.evidence)

# --no-openalex equivalent: use_openalex=False leaves a no-identifier record UNVERIFIED.
vr.http_json = make_http({"api.openalex.org/works?": TITLE_HIT})
rec_off = vr.RefRecord(
    ref_id="reflexion_off",
    raw="Reflexion NeurIPS 2023.",
    title_guess="Reflexion: Language agents with verbal reinforcement learning",
    cited_authors=["Shinn"],
    first_author_guess="Shinn",
)
out_off = vr.verify_record(rec_off, offline=False, timeout=5, use_openalex=False)
check("use_openalex=False skips OpenAlex (no openalex source)",
      "openalex" not in out_off.evidence)

print(f"fail={fail}")
print("ALL PASS" if fail == 0 else f"FAILURES: {fail}")
sys.exit(fail)
PY

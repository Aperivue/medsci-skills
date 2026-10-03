#!/usr/bin/env bash
# Regression test for the trajectory-archetype classifier (author-strategy).
#
# Name-free synthetic fixtures only. Covers:
#   A) pure-function scoring: per-archetype labels/scores/confidence, the score formula
#      (computable-only denominator), negative-suppression, evidence shapes
#      (evidence_pmids vs evidence_summary), max_confidence cap, composite, A5 flag,
#      insufficient-evidence paths.
#   B) CLI + manifest gate: approved corpus classifies; pending and tampered (hash
#      mismatch) manifests hard-fail.
#   C) stdlib pubmed_parse target-author attribution: a co-author's ORCID is never
#      borrowed; ORCID is authoritative; surname-alone collision -> unknown.
#   D) rubric .md <-> .yaml sync via render_archetype_doc.py --check.
#   E) a supplied ORCID/initials that contradicts every same-surname author -> unknown,
#      no namesake metadata; compatible (abbreviated) initials still attribute.
#   F) venue-impact tier is never inferred from a journal name; no high-tier rate.
#   G) A3 'AI-pivot hybrid' needs AI papers and a clinical foundation before them.
#
# Requires PyYAML (a declared dependency, present in CI); part F also needs pandas and
# matplotlib (both installed in CI; seaborn is stubbed if absent). No Biopython needed.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SKILL_DIR="$(cd "$HERE/.." && pwd)"
export FIXTURES="$HERE/fixtures"
export RUBRIC="$SKILL_DIR/references/trajectory_archetypes.yaml"
export PYTHONPATH="$SKILL_DIR${PYTHONPATH:+:$PYTHONPATH}"

fail=0
check_rc() { local label="$1"; local rc="$2"
    if [ "$rc" -eq 0 ]; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

python3 -c "import yaml" 2>/dev/null || { echo "ENV-ERR: PyYAML missing" >&2; exit 2; }
[ -f "$SKILL_DIR/classify_archetypes.py" ] || { echo "ENV-ERR: classify_archetypes.py missing" >&2; exit 2; }

# ---------------------------------------------------------------------------
# Part A — pure-function scoring
# ---------------------------------------------------------------------------
python3 <<'PY'
import os, pathlib
import classify_archetypes as C
rub, _ = C.load_rubric(pathlib.Path(os.environ["RUBRIC"]))

def rec(pmid, title, year, n_authors, pos, st, topic="Other"):
    return {"pmid": str(pmid), "title": title, "abstract": "", "year": str(year),
            "n_authors": str(n_authors), "author_position": pos, "study_type": st, "topic": topic}

# --- A1 infrastructure builder (8) ---
a1 = [
    rec(1, "A benchmark dataset for cardiac segmentation", 2014, 4, "first", "Other", "Radiology/Imaging"),
    rec(2, "An open dataset and challenge for organ detection", 2015, 5, "first", "Other", "Radiology/Imaging"),
    rec(3, "An ontology for radiology reporting", 2016, 3, "last", "Other", "Radiology/Imaging"),
    rec(4, "A lexicon and schema for structured findings", 2017, 4, "first", "Other", "Radiology/Imaging"),
    rec(5, "A benchmark for image registration", 2018, 6, "first", "Other", "Radiology/Imaging"),
    rec(6, "A terminology and common data element catalogue", 2019, 5, "last", "Other", "Radiology/Imaging"),
    rec(7, "An overview of imaging informatics", 2020, 2, "first", "Other", "Radiology/Imaging"),
    rec(8, "Basic principles a primer and general review", 2021, 2, "first", "Other", "Radiology/Imaging"),
]
r = C.score_archetypes(a1, rub)["archetypes"]["A1"]
assert r["surfaced"] and r["score"] == 1.0 and r["confidence"] == "high", r
assert r["evidence_pmids"], "A1 must carry per-paper evidence PMIDs"

# --- A4 SR/MA engine (8); also exercises evidence_summary + denominator exclusion ---
a4 = [
    rec(11, "Systematic review and meta-analysis of statin therapy", 2018, 6, "first", "SR/MA", "Cardiovascular"),
    rec(12, "Meta-analysis of screening for colorectal cancer", 2019, 5, "first", "SR/MA", "Oncology"),
    rec(13, "Systematic review of dementia biomarkers", 2019, 4, "last", "SR/MA", "Neurological"),
    rec(14, "Meta-analysis of asthma inhaler outcomes", 2020, 7, "first", "SR/MA", "Allergy/Respiratory"),
    rec(15, "Systematic review of diabetes interventions", 2020, 5, "first", "SR/MA", "Metabolic"),
    rec(16, "A practical guide to conducting a systematic review and meta-analysis", 2021, 3, "first", "Other", "Other"),
    rec(17, "Cohort study of hypertension", 2021, 8, "middle", "Other", "Cardiovascular"),
    rec(18, "Cross-sectional survey of obesity", 2022, 9, "middle", "Other", "Metabolic"),
]
r = C.score_archetypes(a4, rub)["archetypes"]["A4"]
assert r["surfaced"] and "srma_fraction" in r["fired_signals"], r
assert any(s["signal_id"] == "srma_fraction" for s in r["evidence_summary"]), "A4 needs corpus-level evidence_summary"
assert r["denominator"] == 1.0, r["denominator"]
# Drop the 'topic' column -> srma_topic_breadth becomes non-computable -> excluded from denominator.
a4_no_topic = [{k: v for k, v in row.items() if k != "topic"} for row in a4]
r2 = C.score_archetypes(a4_no_topic, rub)["archetypes"]["A4"]
assert r2["denominator"] == 0.75, ("denominator should drop to 0.75 when topic absent", r2["denominator"])

# --- A5 large-consortium participation: flag + confidence cap (8) ---
a5 = [rec(20+i, f"A consortium genome-wide study {i}", 2016+i, 250 if i < 3 else 6, "middle", "Other") for i in range(8)]
r = C.score_archetypes(a5, rub)["archetypes"]["A5"]
assert r["surfaced"] and r["confidence"] == "med", r          # capped at max_confidence_mvp=med
assert "flag" in r and "membership" in r["flag"].lower(), "A5 must carry the participation flag"

# --- A3 negative suppression: a pure-AI corpus rules A3 OUT (8) ---
ai_only = [rec(30+i, f"Deep learning model {i} for detection", 2015+i, 5, "first", "AI/ML") for i in range(8)]
r = C.score_archetypes(ai_only, rub)["archetypes"]["A3"]
assert (not r["surfaced"]) and "pure_ai_no_clinical_floor" in r["negatives_fired"], r
assert r["insufficient_evidence"], r

# --- A3 hybrid surfaces on a mixed corpus (9) ---
a3 = [
    rec(40, "MRI of the brain in stroke", 2010, 4, "first", "Other", "Neurological"),
    rec(41, "CT angiography technique in carotid disease", 2011, 5, "first", "Other", "Cardiovascular"),
    rec(42, "Ultrasound of the liver", 2012, 3, "middle", "Other", "GI/Hepatology"),
    rec(43, "Clinical imaging of intracranial vessels", 2013, 4, "last", "Other", "Radiology/Imaging"),
    rec(44, "Deep learning for lesion detection", 2020, 6, "last", "AI/ML", "Radiology/Imaging"),
    rec(45, "A convolutional model for segmentation", 2021, 5, "last", "AI/ML", "Radiology/Imaging"),
    rec(46, "Multimodal deep learning for triage", 2022, 7, "last", "AI/ML", "Radiology/Imaging"),
    rec(47, "External validation and reproducibility of a deep learning model", 2022, 6, "last", "AI/ML", "Radiology/Imaging"),
    rec(48, "Imaging follow-up of aneurysm", 2014, 4, "middle", "Other", "Neurological"),
]
r = C.score_archetypes(a3, rub)["archetypes"]["A3"]
assert r["surfaced"], r
assert r["evidence_pmids"] and r["evidence_summary"], "A3 carries both per-paper and corpus-level evidence"

# --- Composite AX: A3 + A6 + senior-on-AI (10; AI fraction exactly 0.1) ---
comp = [
    rec(50, "Flow diverter stent technique for aneurysm", 2014, 4, "last", "Other", "Neurological"),
    rec(51, "Coil embolization procedural outcomes", 2015, 5, "last", "Other", "Neurological"),
    rec(52, "Catheter angioplasty hemodynamics", 2016, 4, "first", "Other", "Cardiovascular"),
    rec(53, "Stent device for carotid disease", 2017, 6, "last", "Other", "Cardiovascular"),
    rec(54, "Endovascular technique outcomes", 2017, 5, "first", "Other", "Neurological"),
    rec(55, "Clinical outcomes of aneurysm repair", 2018, 4, "middle", "Other", "Neurological"),
    rec(56, "Imaging of intracranial vessels", 2018, 3, "middle", "Other", "Radiology/Imaging"),
    rec(57, "Natural history of unruptured aneurysm", 2019, 5, "middle", "Other", "Neurological"),
    rec(58, "Management of vasospasm", 2019, 4, "middle", "Other", "Neurological"),
    rec(59, "Deep learning for aneurysm detection", 2021, 7, "last", "AI/ML", "Neurological"),
]
res = C.score_archetypes(comp, rub)
assert res["archetypes"]["A3"]["surfaced"], res["archetypes"]["A3"]
assert res["archetypes"]["A6"]["surfaced"], res["archetypes"]["A6"]
assert res["composites"]["AX"]["surfaced"], res["composites"]["AX"]
# Composite is computed, not independent: requires its base archetypes.
assert res["composites"]["AX"]["requires_all"] == ["A3", "A6"]

# --- insufficient evidence: below min_sample ---
small = a1[:3]
r = C.score_archetypes(small, rub)["archetypes"]["A1"]
assert r["insufficient_evidence"] and "min_sample" in (r["reason"] or ""), r

# --- max_confidence cap unit behaviour ---
assert C._cap_confidence("high", "med") == "med"
assert C._cap_confidence("low", "med") == "low"

# --- disclaimer present at top level ---
assert "heuristic" in C.score_archetypes(a1, rub)["disclaimer"].lower()
print("part-A-ok")
PY
check_rc "A: pure-function scoring (labels, formula, negatives, evidence, composite, A5 flag)" "$?"

# ---------------------------------------------------------------------------
# Part B — CLI + manifest gate
# ---------------------------------------------------------------------------
python3 <<'PY'
import hashlib, json, os, shutil, subprocess, sys, tempfile, csv
from pathlib import Path
skill = Path(os.environ["SKILL_DIR"]); rubric = os.environ["RUBRIC"]
src = Path(os.environ["FIXTURES"]) / "sample_corpus.csv"
tmp = Path(tempfile.mkdtemp())
csv_path = tmp / "publications.csv"; shutil.copy(src, csv_path)
rows = list(csv.DictReader(open(csv_path, newline="", encoding="utf-8")))
pmids = sorted({r["pmid"] for r in rows})
csv_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
pmid_hash = hashlib.sha256("\n".join(pmids).encode()).hexdigest()

def write_manifest(name, **over):
    m = {"schema": "author-strategy/corpus_manifest@1", "review_status": "approved",
         "record_count": len(rows), "csv_sha256": csv_sha, "pmid_set_hash": pmid_hash,
         "disambiguators": {"initials": "AB"}}
    m.update(over)
    p = tmp / name; p.write_text(json.dumps(m)); return p

def run(manifest):
    return subprocess.run(
        [sys.executable, str(skill / "classify_archetypes.py"), str(csv_path),
         "--manifest", str(manifest), "--rubric", rubric, "-o", str(tmp / "report")],
        capture_output=True, text=True)

# approved + bound -> exit 0 and A1 surfaces
r = run(write_manifest("approved.json"))
assert r.returncode == 0, r.stderr
res = json.loads((tmp / "report" / "archetype_results.json").read_text())
assert res["archetypes"]["A1"]["surfaced"], "A1 should surface on the sample corpus"
assert res["rubric_version"], "results must record rubric_version"

# pending -> hard fail
assert run(write_manifest("pending.json", review_status="pending")).returncode != 0, "pending manifest must fail"
# tampered csv_sha256 -> hard fail
assert run(write_manifest("tampered.json", csv_sha256="0"*64)).returncode != 0, "csv hash mismatch must fail"
# tampered pmid set -> hard fail
assert run(write_manifest("tampered2.json", pmid_set_hash="0"*64)).returncode != 0, "pmid hash mismatch must fail"
shutil.rmtree(tmp, ignore_errors=True)
print("part-B-ok")
PY
check_rc "B: CLI manifest gate (approved passes; pending/tampered hard-fail)" "$?"

# ---------------------------------------------------------------------------
# Part C — target-author attribution (stdlib pubmed_parse, no Biopython)
# ---------------------------------------------------------------------------
python3 <<'PY'
import os
from pathlib import Path
import pubmed_parse as P
xml = (Path(os.environ["FIXTURES"]) / "two_samesurname_authors.xml").read_text()

# Initials disambiguate to the FIRST Smith (AB), who has NO ORCID -> must not borrow CD's.
recs = P.records_from_xml(xml, "Smith", "AB")
r = recs[0]
assert r["match_basis"] == "initials", r["match_basis"]
assert r["author_position"] == "first", r["author_position"]
assert r["target_orcid"] == "", ("co-author ORCID must not be borrowed", r["target_orcid"])
assert r["target_affiliation"].startswith("Department of Example"), r["target_affiliation"]

# Surname alone, two same-surname authors -> ambiguous -> unknown, no borrowed metadata.
amb = P.records_from_xml(xml, "Smith")[0]
assert amb["match_basis"] == "ambiguous-surname", amb["match_basis"]
assert amb["author_position"] == "unknown" and amb["target_orcid"] == "", amb

# ORCID is authoritative -> resolves to the CD author (last position).
orc = P.records_from_xml(xml, "Smith", "", "0000-0002-1234-5678")[0]
assert orc["match_basis"] == "orcid" and orc["author_position"] == "last", orc
assert orc["target_initials"] == "CD", orc
print("part-C-ok")
PY
check_rc "C: target-author attribution (no borrowed ORCID; ORCID authoritative; collision->unknown)" "$?"

# ---------------------------------------------------------------------------
# Part D — rubric .md <-> .yaml sync
# ---------------------------------------------------------------------------
python3 "$SKILL_DIR/render_archetype_doc.py" --check >/dev/null 2>&1
check_rc "D: trajectory_archetypes.md in sync with the YAML rubric" "$?"

# ---------------------------------------------------------------------------
# Part E — a supplied ORCID / initials is a constraint, not a tie-breaker
# ---------------------------------------------------------------------------
python3 <<'PY'
import pubmed_parse as P

def xml(authors, journal="J Synth Imaging"):
    a = "".join(
        "<Author><LastName>%s</LastName><Initials>%s</Initials>%s"
        "<AffiliationInfo><Affiliation>%s</Affiliation></AffiliationInfo></Author>"
        % (ln, ini, ("<Identifier Source=\"ORCID\">%s</Identifier>" % orc) if orc else "", aff)
        for ln, ini, orc, aff in authors)
    return ("<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>900002</PMID><Article>"
            "<Journal><Title>%s</Title><ISOAbbreviation>%s</ISOAbbreviation>"
            "<JournalIssue><PubDate><Year>2020</Year></PubDate></JournalIssue></Journal>"
            "<ArticleTitle>Synthetic placeholder</ArticleTitle><AuthorList>%s</AuthorList>"
            "</Article></MedlineCitation></PubmedArticle></PubmedArticleSet>") % (journal, journal, a)

namesake = xml([("Kim", "AB", "", "Aff One"), ("Lee", "XY", "0000-0009-9999-9999", "Namesake Inst")])

# POSITIVE: the only same-surname author carries a DIFFERENT ORCID -> namesake, not the target.
r = P.records_from_xml(namesake, "Lee", "JK", "0000-0001-0000-0001")[0]
assert r["match_basis"] == "orcid-conflict", r["match_basis"]
assert r["author_position"] == "unknown", r
assert r["target_orcid"] == "" and r["target_affiliation"] == "" and r["target_initials"] == "", r

# POSITIVE: no ORCID supplied, initials contradict (JK vs XY) -> initials-conflict, unknown.
r = P.records_from_xml(namesake, "Lee", "JK")[0]
assert r["match_basis"] == "initials-conflict", r["match_basis"]
assert r["author_position"] == "unknown" and r["target_orcid"] == "", r

# POSITIVE: ORCID supplied and unmatched; the remaining no-ORCID candidate is chosen, the
# different-ORCID namesake is never picked even though it is listed first.
two = xml([("Lee", "JK", "0000-0009-9999-9999", "Namesake Inst"), ("Park", "MN", "", "x"),
           ("Lee", "JK", "", "Target Inst")])
r = P.records_from_xml(two, "Lee", "JK", "0000-0001-0000-0001")[0]
assert r["match_basis"] == "initials" and r["author_position"] == "last", r
assert r["target_affiliation"] == "Target Inst" and r["target_orcid"] == "", r

# NEGATIVE controls (must stay attributed exactly as before):
# compatible abbreviated initials (PubMed 'J' vs supplied 'JK') -> surname-unique.
short = xml([("Kim", "AB", "", "a"), ("Lee", "J", "", "Target Inst")])
r = P.records_from_xml(short, "Lee", "JK")[0]
assert r["match_basis"] == "surname-unique" and r["author_position"] == "last", r
# ORCID supplied, the unique same-surname author has no ORCID -> surname-unique.
noorc = xml([("Kim", "AB", "", "a"), ("Lee", "JK", "", "Target Inst")])
r = P.records_from_xml(noorc, "Lee", "", "0000-0001-0000-0001")[0]
assert r["match_basis"] == "surname-unique" and r["target_affiliation"] == "Target Inst", r
# matching ORCID still authoritative.
r = P.records_from_xml(namesake, "Lee", "JK", "https://orcid.org/0000-0009-9999-9999")[0]
assert r["match_basis"] == "orcid" and r["author_position"] == "last", r
print("part-E-ok")
PY
check_rc "E: conflicting ORCID/initials -> unknown, no namesake metadata; compatible initials still attribute" "$?"

# ---------------------------------------------------------------------------
# Part F — venue-impact tier is never inferred from a journal name
# ---------------------------------------------------------------------------
python3 <<'PY'
import os, sys, tempfile, types
from pathlib import Path
import pubmed_parse as P

# POSITIVE: names the old substring list promoted to a tier now carry the unavailable marker.
for j in ["BMJ Open", "JAMA Netw Open", "J Cell Mol Med", "Gut Liver", "Cell Rep",
          "Allergy Asthma Immunol Res", "Lancet", "N Engl J Med", "Nature", ""]:
    assert P.classify_journal_tier(j) == P.JOURNAL_TIER_UNAVAILABLE, (j, P.classify_journal_tier(j))
xml = (Path(os.environ["FIXTURES"]) / "two_samesurname_authors.xml").read_text()
assert P.records_from_xml(xml, "Smith", "AB")[0]["journal_tier"] == P.JOURNAL_TIER_UNAVAILABLE

# The report must not compute a high-tier rate, even from a legacy CSV whose journal_tier
# column still holds the old inferred labels.
try:
    import pandas as pd
except ImportError:
    sys.stderr.write("ENV-ERR: pandas missing (needed for analyze_patterns.generate_report)\n"); sys.exit(2)
import matplotlib; matplotlib.use("Agg")
try:
    import seaborn  # noqa: F401
except ImportError:
    sys.modules["seaborn"] = types.ModuleType("seaborn")  # report generation does not use it
import warnings; warnings.filterwarnings("ignore")
import analyze_patterns as A
df = pd.DataFrame({
    "pmid": ["1", "2", "3", "4"], "year": [2019, 2020, 2021, 2021],
    "journal": ["BMJ Open", "Gut Liver", "Cell Rep", "J Synth"],
    "journal_abbrev": ["BMJ Open", "Gut Liver", "Cell Rep", "J Synth"],
    "journal_tier": ["NEJM/BMJ/JAMA", "IF>=10", "IF>=10", "Other"],
    "author_position": ["first", "last", "middle", "unknown"],
    "study_type": ["Other", "Other", "SR/MA", "Other"], "topic": ["Other"] * 4,
})
out = Path(tempfile.mkdtemp())
A.generate_report(df, out, "Synthetic")
rep = (out / "analysis_report.md").read_text()
assert "High-tier" not in rep and "IF>=10" not in rep, rep
assert "Venue-impact tier | unavailable [VERIFY]" in rep, rep
# NEGATIVE control: the counts that were already right are unchanged.
assert "| Total PubMed publications | 4 |" in rep, rep
assert "| First or last author (positional heuristic) | 2 (50.0%) |" in rep, rep
assert "04_journal_heatmap.png" in rep and "journal_tier_heatmap" not in rep
print("part-F-ok")
PY
check_rc "F: journal tier unavailable (no substring tier, no high-tier rate in report)" "$?"

# ---------------------------------------------------------------------------
# Part G — A3 'AI-pivot hybrid' needs AI papers and a clinical foundation first
# ---------------------------------------------------------------------------
python3 <<'PY'
import os, pathlib
import classify_archetypes as C
rub, _ = C.load_rubric(pathlib.Path(os.environ["RUBRIC"]))

def rec(pmid, title, year, pos="first", st="Other", n=5):
    return {"pmid": str(pmid), "title": title, "abstract": "", "year": str(year),
            "n_authors": str(n), "author_position": pos, "study_type": st, "topic": "Other"}

# POSITIVE 1: no AI paper at all; 'Multimodal analgesia' and 'claims database' titles.
no_ai = [rec(100 + i, f"Cohort study of postoperative outcomes {i}", 2010 + i) for i in range(8)]
no_ai += [rec(120, "Multimodal analgesia after knee arthroplasty", 2018, "last"),
          rec(121, "Multimodal analgesia in spine surgery", 2019, "last"),
          rec(122, "Opioid prescribing in a national claims database", 2019, "first")]
r = C.score_archetypes(no_ai, rub)["archetypes"]["A3"]
assert not r["surfaced"], r
assert r["fired_signals"] == [], r

# POSITIVE 2: the only AI paper is the FIRST paper -> no clinical foundation, no pivot.
ai_first = [rec(200, "Deep learning for fracture detection", 2010, "middle", "AI/ML")]
ai_first += [rec(201 + i, f"Cohort study of fracture outcomes {i}", 2010 + i) for i in range(9)]
r = C.score_archetypes(ai_first, rub)["archetypes"]["A3"]
assert not r["surfaced"] and "no_clinical_foundation_before_ai" in r["negatives_fired"], r

# One AI-fraction statistic is ONE signal (no confidence inflation from a duplicate).
ids = [s["id"] for s in rub["archetypes"]["A3"]["signals"] if s.get("metric") == "ai_term_fraction"]
assert len(ids) == 1, ids

# NEGATIVE control: clinical foundation then AI papers still surfaces A3.
pivot = [rec(300 + i, f"Clinical imaging of carotid disease {i}", 2010 + i) for i in range(6)]
pivot += [rec(310, "Deep learning for plaque detection", 2019, "last", "AI/ML"),
          rec(311, "A convolutional model for stenosis grading", 2020, "last", "AI/ML"),
          rec(312, "External validation of a deep learning model", 2021, "last", "AI/ML")]
r = C.score_archetypes(pivot, rub)["archetypes"]["A3"]
assert r["surfaced"] and not r["negatives_fired"], r
print("part-G-ok")
PY
check_rc "G: A3 not surfaced on non-AI 'multimodal'/'claims' corpus or AI-first corpus; real pivot surfaces" "$?"

echo "fail=$fail"
[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"

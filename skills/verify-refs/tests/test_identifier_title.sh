#!/usr/bin/env bash
# Regression test: a DOI or PMID that resolves does not verify a title it does not name.
#
# A reference whose DOI (or PMID) resolved and whose authors agreed came out OK without the cited
# title ever being compared with the record the identifier resolves to, so an invented title on a
# real DOI was "verified". The resolved title(s) are now compared with the cited title, and the
# reference is a MISMATCH when fewer than half of the cited title's words are in any of them.
#
# The comparison must not cost a clean reference its OK: a subtitle CrossRef keeps in a separate
# field, a cited title that drops the record's subtitle, publisher markup (<i>) against BibTeX
# braces, British against American spelling (even in every word), a plural, a PubMed translated title cited in the
# original language, and a title in a script the tokenizer cannot read all stay OK. A plain-text
# reference line is searched for the resolved title, since its guessed title is often the author list.
# Network-free: http_fetch, http_json and urlopen (PubMed efetch) are monkeypatched.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/verify_refs.py"

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 - "$SCRIPT" <<'PY'
import importlib.util, io, json, sys, tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("vr", sys.argv[1])
vr = importlib.util.module_from_spec(spec)
sys.modules["vr"] = vr  # dataclass resolution needs the module registered (py3.14)
spec.loader.exec_module(vr)
vr.time.sleep = lambda s: None

fail = 0
def check(label, cond):
    global fail
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    fail += 0 if cond else 1

RECORD = "Synthetic cohort study of contrast reactions in outpatient computed tomography"
INVENTED = "Deep learning prediction of renal failure after cardiac surgery in elderly adults"
AUTHORS = [{"family": "Alpha", "given": "A"}, {"family": "Beta", "given": "B"}]

def crossref(title, subtitle=None, **extra):
    msg = {"title": [title], "author": AUTHORS, "issued": {"date-parts": [[2021]]}, **extra}
    if subtitle:
        msg["subtitle"] = [subtitle]
    return (200, {"status": "ok", "message": msg})

def stub(crossref_answer=None, efetch_xml=None, esummary_title=None):
    def fetch(url, timeout):
        if "api.crossref.org" in url and crossref_answer:
            return crossref_answer
        if "esummary.fcgi" in url and esummary_title is not None:
            return (200, {"result": {"90000001": {"title": esummary_title,
                                                   "authors": [{"name": "Alpha A"}, {"name": "Beta B"}]}}})
        if "api.openalex.org" in url:
            return (200, {"results": []})
        return (None, None)
    vr.http_fetch = fetch
    vr.http_json = lambda url, timeout: (lambda s, d: d if s == 200 else None)(*fetch(url, timeout))
    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    def urlopen(req, timeout=None):
        if efetch_xml is None:
            raise OSError("no network in this test")
        return Resp(efetch_xml.encode("utf-8"))
    vr.urllib.request.urlopen = urlopen

def bib(title, doi="10.0000/synthetic.0001", pmid=None):
    ident = f"  pmid = {{{pmid}}},\n" if pmid else f"  doi = {{{doi}}},\n"
    return vr.parse_bib("@article{synthetic2021,\n  author = {Alpha, A and Beta, B},\n"
                        f"  title = {{{title}}},\n{ident}  year = {{2021}}\n}}\n")[0]

def verify(rec):
    return vr.verify_record(rec, offline=False, timeout=5, use_openalex=True)

# 1. Real DOI, matching authors, invented title -> MISMATCH; the audit is not submission-safe.
stub(crossref(RECORD))
out = verify(bib(INVENTED))
check("invented title on a resolving DOI -> MISMATCH", out.status == "MISMATCH")
check("evidence names the title mismatch", "TITLE MISMATCH" in out.evidence)
check("note says the identifier resolves to a different work", "title" in out.note.lower())
with tempfile.TemporaryDirectory() as td:
    td = Path(td); src = td / "refs.bib"; src.write_text("x", encoding="utf-8")
    vr.write_outputs([out], td, src, [])
    audit = json.loads((td / "qc" / "reference_audit.json").read_text(encoding="utf-8"))
check("audit: submission_safe is false", audit["submission_safe"] is False)

# 2. Clean references keep their OK.
stub(crossref(RECORD))
check("the record's own title -> OK", verify(bib(RECORD)).status == "OK")
stub(crossref("Synthetic cohort study of contrast reactions in outpatient <i>computed tomography</i>"))
check("publisher markup vs BibTeX braces -> OK",
      verify(bib("Synthetic cohort study of contrast reactions in outpatient {Computed Tomography}")).status == "OK")
stub(crossref(RECORD, subtitle="A multicentre registry"))
check("subtitle kept in CrossRef's separate field -> OK",
      verify(bib(RECORD + ": a multicentre registry")).status == "OK")
stub(crossref(RECORD + ": a multicentre registry of adverse events and their management"))
check("cited title drops the record's long subtitle -> OK", verify(bib(RECORD)).status == "OK")
stub(crossref("Tumor segmentation in CT image series of synthetic phantoms"))
check("British spelling and a plural -> OK",
      verify(bib("Tumour segmentation on CT images series of synthetic phantom")).status == "OK")
stub(crossref("Pediatric hematology: color Doppler of randomized tumors"))
check("British spelling in nearly every word -> OK",
      verify(bib("Paediatric haematology: colour Doppler of randomised tumours")).status == "OK")
stub(crossref("Patient-centered modeling of synthetic fiber intake"))
check("-centred, -modelling, fibre -> OK",
      verify(bib("Patient-centred modelling of synthetic fibre intake")).status == "OK")
stub(crossref("ME of synthetic predictors"))
check("an acronym is not a spelling (MAE vs ME) -> MISMATCH",
      verify(bib("MAE of synthetic estimators")).status == "MISMATCH")
stub(crossref(RECORD))
check("two-word invented title on a resolving DOI -> MISMATCH",
      verify(bib("Renal failure")).status == "MISMATCH")
stub(crossref(RECORD))
check("title in a script the tokenizer cannot read -> no title verdict (OK)",
      verify(bib("合成队列研究")).status == "OK")

# 3. The PMID path: PubMed efetch and esummary titles are compared too.
EFETCH = ("<PubmedArticleSet><PubmedArticle><Article><ArticleTitle>[{t}].</ArticleTitle>"
          "<VernacularTitle>{v}</VernacularTitle><AuthorList>"
          '<Author ValidYN="Y"><LastName>Alpha</LastName><ForeName>A</ForeName></Author>'
          '<Author ValidYN="Y"><LastName>Beta</LastName><ForeName>B</ForeName></Author>'
          "</AuthorList></Article></PubmedArticle></PubmedArticleSet>")
VERNACULAR = "Synthetische Kohortenstudie zu Kontrastmittelreaktionen in der ambulanten Computertomographie"
stub(efetch_xml=EFETCH.format(t=RECORD, v=VERNACULAR), esummary_title="[" + RECORD + "].")
check("invented title on a resolving PMID -> MISMATCH",
      verify(bib(INVENTED, pmid="90000001")).status == "MISMATCH")
check("PubMed translated title cited in the original language -> OK",
      verify(bib(VERNACULAR, pmid="90000001")).status == "OK")
# A collective author only (a guideline group): efetch has no personal authors, and the
# VernacularTitle it carries is still a title of the record.
COLLECTIVE = EFETCH.split("<AuthorList>")[0].format(t=RECORD, v=VERNACULAR) + (
    "<AuthorList><Author><CollectiveName>Synthetic Working Group</CollectiveName></Author>"
    "</AuthorList></Article></PubmedArticle></PubmedArticleSet>")
stub(efetch_xml=COLLECTIVE, esummary_title="[" + RECORD + "].")
check("collective-author record cited by its original-language title -> not MISMATCH",
      verify(bib(VERNACULAR, pmid="90000001")).status != "MISMATCH")

# A right PMID beside a wrong DOI: each identifier must resolve to the cited work.
stub(crossref(INVENTED), efetch_xml=EFETCH.format(t=RECORD, v=VERNACULAR), esummary_title=RECORD)
both = vr.parse_bib("@article{synthetic2021,\n  author = {Alpha, A and Beta, B},\n"
                    f"  title = {{{RECORD}}},\n  pmid = {{90000001}},\n"
                    "  doi = {10.0000/synthetic.0001},\n  year = {2021}\n}\n")[0]
out = verify(both)
check("right PMID, DOI of another work -> MISMATCH naming the DOI",
      out.status == "MISMATCH" and "DOI" in out.note)

# A DOI of another work is not excused because its title shares words with the PMID's title.
stub(crossref("Contrast reactions in outpatient imaging"),
     efetch_xml=EFETCH.format(t=RECORD, v=VERNACULAR), esummary_title=RECORD)
check("DOI of a related but different work -> MISMATCH", verify(both).status == "MISMATCH")
# ...but a DOI whose CrossRef record holds only the original-language title is the same work.
stub(crossref(VERNACULAR), efetch_xml=EFETCH.format(t=RECORD, v=VERNACULAR), esummary_title=RECORD)
check("PMID English title, DOI original-language title -> OK", verify(both).status == "OK")

# BibTeX parsing: `booktitle` is not the title, and a quoted title as the last field is read.
stub(crossref(RECORD))
proc = vr.parse_bib("@inproceedings{p,\n  booktitle = {Proceedings of the Synthetic Conference},\n"
                    f"  author = {{Alpha, A and Beta, B}},\n  title = {{{RECORD}}},\n"
                    "  doi = {10.0000/synthetic.0001}\n}\n")[0]
check("booktitle before title: the paper title is read (OK)",
      proc.title_guess == RECORD and verify(proc).status == "OK")
quoted = vr.parse_bib("@article{q,\n  author = {Alpha, A and Beta, B},\n"
                      f'  doi = {{10.0000/synthetic.0001}},\n  title = "{INVENTED}"\n}}\n')[0]
check("quoted title as the last field is compared -> MISMATCH", verify(quoted).status == "MISMATCH")

# 4. A plain-text reference line (Markdown, DOCX): its guessed "title" is often the author list,
#    so the line itself is searched for the resolved title.
def line(title):
    return vr.parse_reference_lines(
        "References\n1. Alpha A, Beta B, Gamma C, Delta D. " + title
        + ". J Synth. 2021;1:1-2. doi:10.0000/synthetic.0001\n")[0]
stub(crossref(RECORD))
check("plain-text reference with the record's title -> OK", verify(line(RECORD)).status == "OK")
check("plain-text reference with an invented title -> MISMATCH",
      verify(line(INVENTED)).status == "MISMATCH")
# Author and journal words in the line must not stand in for the title.
stub(crossref("Cancer research priorities"))
journal_line = vr.parse_reference_lines(
    "References\n1. Alpha A, Beta B. Renal failure. Cancer Research. 2021. doi:10.0000/synthetic.0001\n")[0]
check("journal name supplies the record's title words -> MISMATCH", verify(journal_line).status == "MISMATCH")
# A line whose title is in another script is not compared (its Latin words are authors/journal).
stub(crossref(RECORD))
check("plain-text line with a non-Latin title -> not MISMATCH",
      verify(line("\u5408\u6210\u961f\u5217\u7814\u7a76")).status != "MISMATCH")
check("plain-text line with a two-character non-Latin title -> not MISMATCH",
      verify(line("\u80ba\u764c")).status != "MISMATCH")
stub(crossref("The possibilities of patient-centered medicine in synthetic practice"))
check("plain-text line spelling -centred -> OK",
      verify(line("The possibilities of patient-centred medicine in synthetic practice")).status == "OK")
check("accented Latin and Greek letters in the line are still compared (MISMATCH)",
      verify(vr.parse_reference_lines("References\n1. S\u00f8rensen A, \u00df B. " + INVENTED
             + " of \u03b2-amyloid. J Synth. 2021. doi:10.0000/synthetic.0001\n")[0]).status == "MISMATCH")
# The record's subtitle may be left out of the line.
stub(crossref(RECORD + ": a multicentre registry of adverse events"))
check("plain-text line without the record's subtitle -> OK", verify(line(RECORD)).status == "OK")

sys.exit(1 if fail else 0)
PY
rc=$?
[[ $rc -eq 0 ]] && echo "test_identifier_title: all checks passed" || echo "test_identifier_title: FAILED"
exit $rc

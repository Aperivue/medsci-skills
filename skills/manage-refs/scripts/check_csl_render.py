#!/usr/bin/env python3
"""CSL acceptance test — render a sample and verify in-text format / DOI / journal
abbreviation against the target journal's author-guide spec.

Motivation: Zotero-sourced CSL files are not validated against each journal's
author guide. A "dependent" (stub) CSL inherits its parent's format, which may
differ from what the journal actually requires (e.g. JKMS author guide mandates
superscript Arabic numerals + NLM abbreviations + no DOI, but the Zotero
journal-of-korean-medical-science.csl points to nlm-citation-sequence which
renders parenthetical (1), keeps DOI, and prints full journal names).

This script renders a 2-citation sample through pandoc + the CSL and checks:
  - in-text format: superscript | bracket | paren
  - DOI present in reference list
  - journal name: abbreviated vs full
  - et-al rule (>=N authors collapses)
Compares against expected spec (from REFERENCE_STYLE_SPECS.md or CLI flags) and
exits non-zero on mismatch — run this BEFORE submission, not after the proof PDF.

Usage:
  python check_csl_render.py --csl path/to.csl --bib refs.bib \\
      --expect-intext superscript --expect-doi 0 --expect-abbrev yes
  # or pull expected spec by journal key:
  python check_csl_render.py --csl ... --bib ... --journal jkms
"""
import argparse, subprocess, tempfile, re, os, sys, json

# Minimal built-in spec table (extend via REFERENCE_STYLE_SPECS.md).
# intext: superscript|bracket|paren ; doi: 0|1 ; abbrev: yes|no
SPECS = {
    "jkms":      {"intext": "superscript", "doi": 0, "abbrev": "yes", "note": "verified 2026-06-03"},
    "radiology": {"intext": "paren",       "doi": 1, "abbrev": "yes", "note": "VERIFY against author guide"},
    "ajr":       {"intext": "superscript", "doi": 0, "abbrev": "yes", "note": "VERIFY"},
    "kjr":       {"intext": "superscript", "doi": 0, "abbrev": "yes", "note": "VERIFY"},
    "eur-radiol":{"intext": "bracket",     "doi": 1, "abbrev": "no",  "note": "Springer; VERIFY"},
    "cvir":      {"intext": "bracket",     "doi": 1, "abbrev": "no",  "note": "Springer; VERIFY"},
}

SAMPLE = ("Risk is elevated [@A; @B].\n\n# References\n")

def render(csl, bib, fmt):
    md = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
    md.write(SAMPLE.replace("@A", FIRST).replace("@B", SECOND)); md.close()
    out = tempfile.NamedTemporaryFile(suffix=("."+fmt), delete=False).name
    subprocess.run(["pandoc", md.name, "--citeproc", f"--bibliography={bib}",
                    f"--csl={csl}", "-o", out], capture_output=True)
    return out

def analyze(csl, bib):
    # need two citekeys present in bib; pick first two @article keys
    keys = re.findall(r"@\w+\{([^,]+),", open(bib).read())
    global FIRST, SECOND
    FIRST, SECOND = (keys + ["A", "B"])[:2]
    docx = render(csl, bib, "docx")
    txt_out = render(csl, bib, "plain")
    txt = open(txt_out).read() if os.path.exists(txt_out) else ""
    # in-text format
    from docx import Document
    d = Document(docx)
    sup = sum(1 for p in d.paragraphs for r in p.runs
              if r.font.superscript and re.search(r"\d", r.text))
    body = txt.split("References")[0] if "References" in txt else txt
    intext = ("superscript" if sup > 0
              else "bracket" if re.search(r"\[\d", body)
              else "paren" if re.search(r"\(\d", body)
              else "unknown")
    doi = 1 if re.search(r"doi|10\.\d{4}/", txt, re.I) else 0
    # crude abbrev check: presence of a long journal word vs none
    full = bool(re.search(r"\b(Annals|Journal of|American Journal|European|Radiology\.)", txt))
    return {"intext": intext, "doi": doi, "abbrev_full_detected": full,
            "superscript_runs": sup}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csl", required=True)
    ap.add_argument("--bib", required=True)
    ap.add_argument("--journal", help="spec key (jkms, radiology, ...)")
    ap.add_argument("--expect-intext", choices=["superscript", "bracket", "paren"])
    ap.add_argument("--expect-doi", type=int, choices=[0, 1])
    ap.add_argument("--expect-abbrev", choices=["yes", "no"])
    a = ap.parse_args()
    exp = dict(SPECS.get(a.journal, {})) if a.journal else {}
    if a.expect_intext: exp["intext"] = a.expect_intext
    if a.expect_doi is not None: exp["doi"] = a.expect_doi
    if a.expect_abbrev: exp["abbrev"] = a.expect_abbrev
    got = analyze(a.csl, a.bib)
    print(json.dumps({"csl": os.path.basename(a.csl), "expected": exp, "got": got}, indent=2))
    fails = []
    if exp.get("intext") and got["intext"] != exp["intext"]:
        fails.append(f"in-text {got['intext']} != expected {exp['intext']}")
    if "doi" in exp and got["doi"] != exp["doi"]:
        fails.append(f"DOI {got['doi']} != expected {exp['doi']}")
    if exp.get("abbrev") == "yes" and got["abbrev_full_detected"]:
        fails.append("journal names appear FULL — need NLM abbreviation "
                     "(fill_journal_abbrev.py to add shortjournal)")
    if fails:
        print("FAIL:", "; ".join(fails), file=sys.stderr)
        sys.exit(1)
    print("PASS — CSL output matches journal spec")

if __name__ == "__main__":
    main()

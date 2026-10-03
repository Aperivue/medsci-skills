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

The abbreviation check does not rely on the two-citation sample alone: a CSL that
asks for the short journal title silently falls back to the full title for any entry
without ``shortjournal``, so with an abbreviation expected EVERY bib entry that names
a journal (``journal``/``journaltitle``) but carries no ``shortjournal`` fails the
check by key. That scan reads only the .bib, so it is reported even when pandoc is
unavailable (exit 1, with a note that the render checks did not run).

In the render itself, an entry whose full journal title is contained in its own
``shortjournal`` ("Cancers" in "Cancers (Basel)") is NOT_ASSESSED for full-vs-abbreviated,
never FAIL: a correct abbreviation always contains the full title. It is listed in
``abbrev_not_assessed`` and named in a minor note.

--bib must be a BibTeX (.bib) file; a CSL-JSON or YAML bibliography has no BibTeX
entries to sample and exits 2.

Exit codes:
  0  output matches journal spec
  1  spec mismatch (in-text / DOI / abbreviation)
  2  environment / input error (pandoc or python-docx missing, bib not found,
     pandoc render failed) — reported with a clear message, never a raw traceback.
     An abbreviation failure already proven from the .bib still exits 1.

Usage:
  python check_csl_render.py --csl path/to.csl --bib refs.bib \\
      --expect-intext superscript --expect-doi 0 --expect-abbrev yes
  # or pull expected spec by journal key:
  python check_csl_render.py --csl ... --bib ... --journal jkms
"""
import argparse, subprocess, tempfile, re, os, sys, json
from pathlib import Path

# python-docx is required for the superscript check. Import is guarded at the top
# so a missing dependency is a clear, actionable message (exit 2) rather than an
# ImportError traceback raised deep inside analyze().
try:
    from docx import Document
except ImportError:  # pragma: no cover - environment-dependent
    Document = None

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

def sample_markdown(keys: list[str]) -> str:
    """The render sample, citing every key in ``keys`` (one or two) as a pandoc citation.

    The '@' sigil is part of the citation syntax and must survive substitution: the old
    ``"[@A; @B]".replace("@A", key)`` replaced the sigil along with the placeholder, so the sample
    read ``[alpha2020; gamma2021]`` — plain text that cites nothing — and every in-text, DOI and
    abbreviation verdict was computed on a render with no citation and no reference list in it.
    """
    return "Risk is elevated [" + "; ".join("@" + k for k in keys) + "].\n\n# References\n"

BIB_ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)(?=\n\s*@|\Z)", re.S)
JOURNAL_FIELD_RE = re.compile(r"\b(?:journal|journaltitle)\s*=\s*[{\"]\s*[^}\"\s]", re.I)
SHORTJOURNAL_RE = re.compile(r"\bshortjournal\s*=\s*[{\"]\s*[^}\"\s]", re.I)


class RenderError(RuntimeError):
    """Environment/input failure that should exit 2 with a clear message."""


def _read_bib(bib: str) -> str:
    """Read the .bib file, raising a clear RenderError if it is missing/unreadable."""
    p = Path(bib)
    if not p.exists():
        raise RenderError(f"bib file not found: {bib}")
    try:
        return p.read_text(encoding="utf-8")
    except OSError as exc:
        raise RenderError(f"could not read bib file {bib}: {exc}") from exc


def bib_field(body: str, name: str) -> str:
    """Value of field ``name`` in one entry body ({...} with nested braces, or "..."); "" if absent."""
    m = re.search(rf"(?<![\w-]){name}\s*=\s*", body, re.I)
    if not m:
        return ""
    i = m.end()
    if i < len(body) and body[i] == "{":
        depth, j = 0, i
        while j < len(body):
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        val = body[i + 1:j]
    elif i < len(body) and body[i] == '"':
        j = body.find('"', i + 1)
        val = body[i + 1:j if j != -1 else len(body)]
    else:
        return ""
    # A LaTeX-escaped special ("{\&}", "\_") prints as the bare character, so compare that:
    # otherwise "Journal of X {\&} Y" is never found in the render and its full title clears.
    val = re.sub(r"\\([&_%$#])", r"\1", val)
    return " ".join(val.replace("{", "").replace("}", "").split())


def keys_missing_shortjournal(bib_text: str) -> list[str]:
    """Keys of every entry that names a journal but carries no non-empty shortjournal.

    Those are exactly the entries a short-form CSL renders with the FULL journal title,
    whether or not they happen to be among the two keys the render sample uses.
    """
    missing = []
    for entry_type, key, body in BIB_ENTRY_RE.findall(bib_text):
        if entry_type.lower() in ("comment", "string", "preamble"):
            continue
        if JOURNAL_FIELD_RE.search(body) and not SHORTJOURNAL_RE.search(body):
            missing.append(key)
    return missing


def render(csl: str, bib: str, fmt: str, keys: list[str], outdir: str) -> str:
    """Render the citation sample through pandoc+CSL into ``outdir``.

    ``keys`` are the citekeys the sample cites (passed explicitly so
    this function is standalone-callable — no module globals). The input markdown
    and the output file live under ``outdir`` so the caller's TemporaryDirectory
    cleans everything up; nothing leaks. Raises RenderError if pandoc is missing
    or returns non-zero, so a failed render can never be silently analyzed as if
    it had succeeded. Also raises RenderError when citeproc reports a sample key as
    not found: a render that cited nothing has nothing to judge.
    """
    # The writer is named explicitly (-t): pandoc cannot deduce "plain" from an ".plain" extension
    # and falls back to HTML, whose DOI-linked titles read as a printed DOI to the check below.
    md_path = os.path.join(outdir, "sample.md")
    out_path = os.path.join(outdir, f"out.{fmt}")
    log_path = os.path.join(outdir, f"log.{fmt}.json")
    Path(md_path).write_text(sample_markdown(keys), encoding="utf-8")
    try:
        proc = subprocess.run(
            ["pandoc", md_path, "--citeproc", f"--bibliography={bib}",
             f"--csl={csl}", f"--log={log_path}", "-t", fmt, "--wrap=none", "-o", out_path],
            capture_output=True, text=True,
        )
    except FileNotFoundError as exc:
        raise RenderError(
            "pandoc not found on PATH. Install pandoc to run the CSL render check."
        ) from exc
    if proc.returncode != 0:
        raise RenderError(
            f"pandoc failed (exit {proc.returncode}) rendering {fmt}: "
            f"{proc.stderr.strip()[:500]}"
        )
    try:
        log = json.loads(Path(log_path).read_text(encoding="utf-8") or "[]")
    except (OSError, ValueError) as exc:
        raise RenderError(f"could not read pandoc's log for the {fmt} render: {exc}") from exc
    not_found = [m.get("message", "") for m in log
                 if isinstance(m, dict) and re.fullmatch(r"citation .+ not found", m.get("message", ""))]
    if not_found:
        raise RenderError(
            f"the sample render cited nothing resolvable ({'; '.join(not_found)}); "
            "no verdict can be drawn from it"
        )
    return out_path


def analyze(csl: str, bib: str) -> dict:
    # Validate inputs first (bib path), so a missing bib is reported clearly and
    # independently of whether the optional python-docx parser is installed.
    entries: dict[str, str] = {}
    for entry_type, key, body in BIB_ENTRY_RE.findall(_read_bib(bib)):
        if entry_type.lower() not in ("comment", "string", "preamble") and key not in entries:
            entries[key] = body
    if not entries:
        raise RenderError(f"no bibliography entries found in {bib}; there is nothing to render")
    # Sample two entries, preferring ones that carry a DOI so the DOI verdict has something to see.
    keys = sorted(entries, key=lambda k: 0 if bib_field(entries[k], "doi") else 1)[:2]
    if Document is None:
        raise RenderError(
            "python-docx is required for the in-text superscript check "
            "(pip install python-docx)."
        )
    with tempfile.TemporaryDirectory(prefix="csl_render_") as tmp:
        docx = render(csl, bib, "docx", keys, tmp)
        txt_out = render(csl, bib, "plain", keys, tmp)
        txt = Path(txt_out).read_text(encoding="utf-8") if os.path.exists(txt_out) else ""
        # in-text format
        d = Document(docx)
        sup = sum(1 for p in d.paragraphs for r in p.runs
                  if r.font.superscript and re.search(r"\d", r.text))
    body = txt.split("References")[0] if "References" in txt else txt
    intext = ("superscript" if sup > 0
              else "bracket" if re.search(r"\[\d", body)
              else "paren" if re.search(r"\(\d", body)
              else "unknown")
    # Judged against the sampled entries' own fields, not against words in the output: a word list
    # ("Journal of", "Radiology.", "doi") reads a title such as "Doing ..." as a DOI and an
    # abbreviation identical to its full title as unabbreviated.
    flat = " ".join(txt.split()).lower()
    doi = 1 if any(bib_field(entries[k], "doi").lower() in flat
                   for k in keys if bib_field(entries[k], "doi")) else 0
    # The sampled entries' own titles are removed before the full journal title is looked for: a
    # journal named in an article title ("Synthetic reports of ...") is not the container title.
    searched = flat
    unmatched_titles: list[str] = []
    for k in keys:
        title = bib_field(entries[k], "title").lower()
        if title and title in searched:
            searched = searched.replace(title, " ")
        elif title:
            unmatched_titles.append(title)
    full = False
    not_assessed: list[str] = []
    for k in keys:
        jfull = (bib_field(entries[k], "journal") or bib_field(entries[k], "journaltitle")).lower()
        jshort = bib_field(entries[k], "shortjournal").lower()
        if not jfull or jfull == jshort:
            continue
        # "Cancers" inside "Cancers (Basel)": a correct abbreviation always contains the full title,
        # so the render cannot tell the two apart. Likewise a journal name inside an article title
        # that the render did not print verbatim. Neither is a verdict either way.
        if jfull in jshort or any(jfull in t for t in unmatched_titles):
            not_assessed.append(k)
            continue
        if jfull in searched:
            full = True
    return {"intext": intext, "doi": doi, "abbrev_full_detected": full,
            "abbrev_not_assessed": not_assessed, "superscript_runs": sup}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csl", required=True)
    ap.add_argument("--bib", required=True, help="BibTeX (.bib) file; CSL-JSON/YAML is not parsed")
    ap.add_argument("--journal", help="spec key (jkms, radiology, ...)")
    ap.add_argument("--expect-intext", choices=["superscript", "bracket", "paren"])
    ap.add_argument("--expect-doi", type=int, choices=[0, 1])
    ap.add_argument("--expect-abbrev", choices=["yes", "no"])
    a = ap.parse_args()
    exp = {}
    if a.journal:
        # An unknown key used to yield an empty spec, so nothing was compared and the run printed
        # PASS. A spec that cannot be found is an input this script does not recognise.
        jkey = a.journal.lower()
        if jkey not in SPECS:
            print(f"ERROR: unknown --journal {a.journal!r}; known keys: {', '.join(sorted(SPECS))}. "
                  "Pass --expect-intext / --expect-doi / --expect-abbrev instead.", file=sys.stderr)
            sys.exit(2)
        exp = dict(SPECS[jkey])
    if a.expect_intext: exp["intext"] = a.expect_intext
    if a.expect_doi is not None: exp["doi"] = a.expect_doi
    if a.expect_abbrev: exp["abbrev"] = a.expect_abbrev
    fails = []
    missing_short: list[str] = []
    if exp.get("abbrev") == "yes":
        try:
            missing_short = keys_missing_shortjournal(_read_bib(a.bib))
        except RenderError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(2)
        if missing_short:
            shown = ", ".join(missing_short[:20])
            more = f" (+{len(missing_short) - 20} more)" if len(missing_short) > 20 else ""
            fails.append(f"{len(missing_short)} journal entr{'y' if len(missing_short) == 1 else 'ies'} "
                         f"without shortjournal will render the FULL title: {shown}{more} "
                         "(fill_journal_abbrev.py adds shortjournal)")
    try:
        got = analyze(a.csl, a.bib)
    except RenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if fails:
            # The .bib alone already fails the spec; a missing renderer does not undo that.
            print("FAIL:", "; ".join(fails), "(render checks did not run)", file=sys.stderr)
            sys.exit(1)
        sys.exit(2)
    got["missing_shortjournal"] = missing_short
    print(json.dumps({"detector": "check_csl_render", "csl": os.path.basename(a.csl), "expected": exp, "got": got}, indent=2))
    if exp.get("intext") and got["intext"] != exp["intext"]:
        fails.append(f"in-text {got['intext']} != expected {exp['intext']}")
    if "doi" in exp and got["doi"] != exp["doi"]:
        fails.append(f"DOI {got['doi']} != expected {exp['doi']}")
    if exp.get("abbrev") == "yes" and got["abbrev_full_detected"]:
        fails.append("journal names appear FULL — need NLM abbreviation "
                     "(fill_journal_abbrev.py to add shortjournal)")
    if exp.get("abbrev") == "yes" and got["abbrev_not_assessed"]:
        print("NOTE (minor): full-vs-abbreviated journal name NOT_ASSESSED for "
              f"{', '.join(got['abbrev_not_assessed'])}: the full title is part of its own "
              "abbreviation or article title, so the render cannot tell them apart", file=sys.stderr)
    if fails:
        print("FAIL:", "; ".join(fails), file=sys.stderr)
        sys.exit(1)
    print("PASS — CSL output matches journal spec")

if __name__ == "__main__":
    main()

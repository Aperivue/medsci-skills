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

A preprint server named as the journal (``journal = {arXiv}``, bioRxiv, medRxiv, SSRN, Research
Square, ...) has no journal abbreviation, so it is never counted as a missing ``shortjournal`` and
never read as a full title in the render; such entries are listed in ``abbrev_preprint``.

``--md manuscript.md`` limits every check to the keys the manuscript cites, as pandoc reads them
(so it needs pandoc): a real .bib usually holds entries the manuscript no longer cites, and those
never print. ``nocite: '@*'`` lists every entry, so the whole .bib is judged; so it is without
``--md``.

``--abbrev-warning --md manuscript.md`` is the light mode ``render_pandoc.sh`` runs after every
render: no sample render and no verdict, only the cited journal entries this style will print with
the full title (it reads the style, or its parent for a dependent style, for a short journal title).

With nothing to compare (no ``--journal``, no ``--expect-*``, or only ``--expect-abbrev no``,
which asks for no check) the render is still printed as JSON, but the run ends NOT_ASSESSED with
exit 2, never PASS.

--bib must be a BibTeX (.bib) file; a CSL-JSON or YAML bibliography has no BibTeX
entries to sample and exits 2.

Exit codes:
  0  output matches journal spec
  1  spec mismatch (in-text / DOI / abbreviation)
  2  environment / input error (pandoc or python-docx missing, bib not found,
     pandoc render failed), or no expectation to compare against — reported with a
     clear message, never a raw traceback.
     An abbreviation failure already proven from the .bib still exits 1.

Usage:
  python check_csl_render.py --csl path/to.csl --bib refs.bib \\
      --expect-intext superscript --expect-doi 0 --expect-abbrev yes
  # or pull expected spec by journal key, judging only what the manuscript cites:
  python check_csl_render.py --csl ... --bib ... --journal jkms --md manuscript.md
"""
import argparse, subprocess, tempfile, re, os, sys, json
import xml.etree.ElementTree as ET
from pathlib import Path

# One BibTeX reader for the skill: the brace-aware parser in fill_journal_abbrev.py. A regex that
# ended an entry at the next line starting with '@' merged two entries written on one line, so a
# cited book took on an uncited article's journal field.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fill_journal_abbrev import parse_bib, _value  # noqa: E402

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
    # JMIR asks for a PMID *or* a DOI after each journal reference, so DOI presence is not asserted.
    "jmir":      {"intext": "bracket",                "abbrev": "yes",
                  "note": "verified 2026-10-25 against the JMIR reference guide (support article 115001333067)"},
}

def sample_markdown(keys: list[str]) -> str:
    """The render sample, citing every key in ``keys`` (one or two) as a pandoc citation.

    The '@' sigil is part of the citation syntax and must survive substitution: the old
    ``"[@A; @B]".replace("@A", key)`` replaced the sigil along with the placeholder, so the sample
    read ``[alpha2020; gamma2021]`` — plain text that cites nothing — and every in-text, DOI and
    abbreviation verdict was computed on a render with no citation and no reference list in it.
    """
    return "Risk is elevated [" + "; ".join("@" + k for k in keys) + "].\n\n# References\n"

# A preprint server given as the journal has no abbreviation to print.
PREPRINT_RE = re.compile(
    r"^(?:arxiv|biorxiv|medrxiv|chemrxiv|psyarxiv|socarxiv|techrxiv|ssrn|research square"
    r"|preprints(?:\.org)?|osf preprints)\b", re.I)


class RenderError(RuntimeError):
    """Environment/input failure that should exit 2 with a clear message."""


def bib_entries(bib_text: str):
    """(entry_type, key, body) for each entry, @comment/@string/@preamble excluded.

    An entry whose braces do not balance swallows everything after it, so that is an input error
    (exit 2) rather than a shorter list.
    """
    out = []
    for e in parse_bib(bib_text):
        if e["unsupported"] == "unbalanced braces":
            raise RenderError(f"entry {e['key'] or '(no key)'} at line {e['line']} has unbalanced braces; "
                              "nothing after it can be read")
        if e["key"]:
            out.append((e["type"], e["key"], bib_text[e["body_start"]:e["body_end"]]))
    return out


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


def journal_of(body: str) -> str:
    # journaltitle first: given both, pandoc prints journaltitle, so that is the one to judge.
    return bib_field(body, "journaltitle") or bib_field(body, "journal")


def is_preprint(body: str) -> bool:
    return bool(PREPRINT_RE.match(journal_of(body)))


def cited_keys(md: str, pandoc_args=()):
    """Citation keys a markdown manuscript cites, as pandoc reads them, or None for "every entry".

    pandoc's own parse is the only authority used: a key inside an HTML comment or any kind of code
    is not a citation, a key such as `smith?2020` or `@{a.b}` is one, and `nocite: '@*'` puts every
    entry of the bibliography into the reference list (returned as None). No regex stands in when
    pandoc is missing: a guessed scope is worse than none, so that is a RenderError (exit 2).
    """
    if not Path(md).is_file():
        raise RenderError(f"manuscript not found: {md}")
    try:
        # The render's own options come last, so a reader option there (`--from=markdown-citations`)
        # decides what is cited here exactly as it did in the render.
        proc = subprocess.run(["pandoc", "-f", "markdown", *pandoc_args, "-t", "json", md],
                              capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RenderError("--md needs pandoc to read the manuscript's citations; pandoc not found on PATH") from exc
    if proc.returncode != 0:
        raise RenderError(f"pandoc could not read manuscript {md}: {proc.stderr.strip()[:300]}")
    keys: set[str] = set()
    stack = [json.loads(proc.stdout)]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if node.get("t") == "Cite":
                keys.update(c["citationId"] for c in node["c"][0])
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None if "*" in keys else keys


def _journal_entries(bib_text: str, only=None):
    """(key, has_shortjournal) for each entry in scope that names a journal, preprint servers excluded.

    Read from the parsed fields, so a journal given as a @string macro (`journal = jname`) counts:
    pandoc expands it and prints the full name. A macro shortjournal counts as present.
    """
    bib_entries(bib_text)  # raises RenderError on unbalanced braces
    out = []
    for e in parse_bib(bib_text):
        if not e["key"] or (only is not None and e["key"] not in only):
            continue
        jf = e["fields"].get("journaltitle") or e["fields"].get("journal")
        if not jf:
            continue
        literal = _value(e, "journaltitle" if "journaltitle" in e["fields"] else "journal")
        if jf[3] in ("braced", "quoted") and (not literal or PREPRINT_RE.match(literal)):
            continue
        sj = e["fields"].get("shortjournal")
        out.append((e["key"], bool(sj and (sj[3] not in ("braced", "quoted") or _value(e, "shortjournal")))))
    return out


def journal_keys(bib_text: str, only=None) -> list[str]:
    """Keys of the entries in scope whose journal field names a journal (not a preprint server)."""
    return [key for key, _has_short in _journal_entries(bib_text, only)]


def keys_missing_shortjournal(bib_text: str, only=None) -> list[str]:
    """Keys of every entry that names a journal but carries no non-empty shortjournal.

    Those are exactly the entries a short-form CSL renders with the FULL journal title,
    whether or not they happen to be among the two keys the render sample uses. A preprint
    server named as the journal is not one of them, and with ``only`` given, an entry the
    manuscript does not cite never prints at all.
    """
    return [key for key, has_short in _journal_entries(bib_text, only) if not has_short]


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


def analyze(csl: str, bib: str, only=None) -> dict:
    # Validate inputs first (bib path), so a missing bib is reported clearly and
    # independently of whether the optional python-docx parser is installed.
    entries: dict[str, str] = {}
    for _entry_type, key, body in bib_entries(_read_bib(bib)):
        if key not in entries:
            entries[key] = body
    if not entries:
        raise RenderError(f"no bibliography entries found in {bib}; there is nothing to render")
    if only is not None:
        # Only cited entries are sampled: an uncited one never prints, so its verdict is noise.
        entries = {k: v for k, v in entries.items() if k in only}
        if not entries:
            raise RenderError(f"the manuscript cites none of the entries in {bib}; there is nothing to render")
    # Sample two entries, preferring ones that carry a DOI so the DOI verdict has something to see,
    # then ones that name a real journal so the abbreviation verdict does.
    keys = sorted(entries, key=lambda k: (0 if bib_field(entries[k], "doi") else 1,
                                          0 if journal_of(entries[k]) and not is_preprint(entries[k]) else 1))[:2]
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
    preprint: list[str] = []
    for k in keys:
        jfull = journal_of(entries[k]).lower()
        jshort = bib_field(entries[k], "shortjournal").lower()
        if not jfull or jfull == jshort:
            continue
        if is_preprint(entries[k]):  # "arXiv" printed in full is correct: there is no abbreviation
            preprint.append(k)
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
            "abbrev_not_assessed": not_assessed, "abbrev_preprint": preprint,
            "sampled": keys, "superscript_runs": sup}

def prints_short_titles(csl: str):
    """True if the style prints the short journal title, False if not, None if it cannot be told.

    Read with an XML parser (attribute quoting and spacing vary between valid styles). A dependent
    style takes its layout from its parent, which is read from the same folder.
    """
    try:
        root = ET.parse(csl).getroot()
    except (OSError, ET.ParseError):
        return None
    local = lambda el: el.tag.rsplit("}", 1)[-1]
    for el in root.iter():
        if local(el) == "link" and el.get("rel") == "independent-parent":
            parent_csl = Path(csl).with_name(el.get("href", "").rstrip("/").rsplit("/", 1)[-1] + ".csl")
            return prints_short_titles(str(parent_csl)) if parent_csl.is_file() else None
    return any(local(el) == "text" and el.get("variable") == "container-title" and el.get("form") == "short"
               for el in root.iter())


def abbrev_warning(csl: str, bib: str, md: str, pandoc_args=()) -> list[str]:
    """Warning lines for the cited journal entries this style will print with the FULL title.

    Empty when there are none, or when the style prints full titles anyway (nothing to abbreviate).
    Raises RenderError when the check cannot be made (unreadable bib, pandoc missing, ...).
    """
    short = prints_short_titles(csl)
    name = os.path.basename(csl)
    if short is None:
        raise RenderError(f"cannot tell whether {name} prints abbreviated journal titles")
    if not short:
        return []
    missing = keys_missing_shortjournal(_read_bib(bib), cited_keys(md, pandoc_args))
    if not missing:
        return []
    shown = ", ".join(missing[:20]) + (f" (+{len(missing) - 20} more)" if len(missing) > 20 else "")
    return [f"journal abbreviations: {len(missing)} cited journal entr{'y has' if len(missing) == 1 else 'ies have'} "
            f"no shortjournal, so {name} prints the FULL journal name: {shown}",
            "  fill_journal_abbrev.py adds them (check any value it marks as CrossRef)"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csl", required=True)
    ap.add_argument("--bib", required=True, help="BibTeX (.bib) file; CSL-JSON/YAML is not parsed")
    ap.add_argument("--journal", help="spec key (jkms, jmir, radiology, ...)")
    ap.add_argument("--expect-intext", choices=["superscript", "bracket", "paren"])
    ap.add_argument("--expect-doi", type=int, choices=[0, 1])
    ap.add_argument("--expect-abbrev", choices=["yes", "no"])
    ap.add_argument("--md", help="manuscript (.md); judge only the keys it cites")
    ap.add_argument("pandoc_args", nargs="*", metavar="-- PANDOC_ARGS",
                    help="with --abbrev-warning: the render's extra pandoc options, after --")
    ap.add_argument("--abbrev-warning", action="store_true",
                    help="with --md: only list cited journal entries the style prints in full (no render, "
                         "no verdict); exit 0, or 2 if the check could not run")
    a = ap.parse_args()
    if a.abbrev_warning:
        if not a.md:
            print("ERROR: --abbrev-warning needs --md", file=sys.stderr)
            sys.exit(2)
        try:
            lines = abbrev_warning(a.csl, a.bib, a.md, a.pandoc_args)
        except RenderError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(2)
        if lines:
            print("\n".join(lines))
        sys.exit(0)
    only = None
    if a.md:
        try:
            only = cited_keys(a.md)
        except RenderError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(2)
        if only is None:
            print("NOTE: the manuscript has nocite '@*', which lists every entry: judging the whole bib",
                  file=sys.stderr)
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
    judged = 0
    if exp.get("abbrev") == "yes":
        try:
            bib_text = _read_bib(a.bib)
            missing_short = keys_missing_shortjournal(bib_text, only)
            judged = len(journal_keys(bib_text, only))
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
        got = analyze(a.csl, a.bib, only)
    except RenderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if fails:
            # The .bib alone already fails the spec; a missing renderer does not undo that.
            print("FAIL:", "; ".join(fails), "(render checks did not run)", file=sys.stderr)
            sys.exit(1)
        sys.exit(2)
    got["missing_shortjournal"] = missing_short
    got["scope"] = "cited keys" if only is not None else "whole bib"
    got["abbrev_judged"] = judged
    print(json.dumps({"detector": "check_csl_render", "csl": os.path.basename(a.csl), "expected": exp, "got": got}, indent=2))
    # Counted by the comparisons actually made below: `abbrev: no` ("full names acceptable") asks for
    # no check, and `abbrev: yes` over a bib with no journal entry in scope has nothing to judge, so
    # either alone compared nothing and printed PASS, as did no expectation at all.
    abbrev_compared = exp.get("abbrev") == "yes" and judged > 0
    if exp.get("abbrev") == "yes" and not judged:
        print("NOTE: no journal entry in scope, so journal abbreviation was NOT_ASSESSED", file=sys.stderr)
    compared = bool(exp.get("intext")) + ("doi" in exp) + abbrev_compared
    if not compared:
        print("NOT_ASSESSED — no expectation to compare (pass --journal, --expect-intext, --expect-doi or "
              "--expect-abbrev yes); the render above was not compared with anything", file=sys.stderr)
        sys.exit(2)
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

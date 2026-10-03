#!/usr/bin/env python3
"""Response-letter claim <-> revised-manuscript verification (rule-backed gate).

A response-to-reviewers letter asserts concrete edits: "we added the sentence
'...'", "we now cite Tariq et al. [15]". The single-source-of-truth is the
*revised manuscript*, not the response prose — yet a claimed edit can be absent
from the body (a real incident: an added Discussion citation was described in the
response but never inserted, and both a reviewer round and the authors missed it
until a body grep). This gate makes that class deterministic for both sides:
`/revise` (author, before sending) and `/peer-review` (reviewer, verifying the
author's claims against the revised manuscript).

It is deliberately conservative — it verifies only claims carrying a strong,
checkable anchor, so paraphrase and honest rewording do not false-positive:

  * RESPONSE_QUOTE_UNVERIFIED (major) — the letter says specific text was
    added / inserted / "now reads" (or labels it "Changes to text:") and quotes it
    verbatim, but that quoted text is absent from the revised manuscript body. Each
    quotation is read to its closing mark, so a long quote is checked whole.
  * RESPONSE_QUOTE_UNRESOLVED (minor) — the quoted text IS there in order, but
    only once foreign tokens are allowed between its words, or a word or two is
    missing. That is the signature of a dirty extraction (a bled reference
    column, PDF line numbers, a footnote marker, a hyphen split across a line),
    not of an edit that was never made. Reported so a human looks; never counted
    as drift. A contiguous substring test cannot tell these apart and calls a
    correct quote absent — the failure that once came one step from having two
    accurate verbatim quotes deleted. Matching lives in _quote_match.py.
  * RESPONSE_CITATION_UNVERIFIED (major) — the letter says a citation was added
    / "now cite(d)", but none of the cited tokens ([N] / [@key] / Author et al.)
    appear in the revised manuscript body.

With --values revision_values.json (the revision-time numerical audit table, declared), each
entry's anchor sentence is located in the body and its declared values are checked there:

  * RESPONSE_VALUE_MISMATCH (major) — the anchor is in the body, but a declared value is
    not among the numbers of the paragraph(s) that hold it (after folding mid-dot decimals,
    thin-space and comma thousands, decimal commas, Unicode minus and leading-dot P values).
  * RESPONSE_VALUE_NOT_ASSESSED (minor) — the anchor is not found, or the value is missing
    from a paragraph whose numbers cannot all be read (superscripts, x10^n notation).

Vague claims with no quote and no citation ("we clarified the Methods") are not
verifiable and are intentionally NOT flagged. Reviewer-comment blockquotes
(lines beginning with '>') are excluded so the reviewer's own quoted text is
never mistaken for an author addition.

Usage:
    check_response_claims.py --response response.md --manuscript revised.md [--strict]
    check_response_claims.py --response r.md --manuscript revised.md --values revision_values.json
    check_response_claims.py --response r.md --manuscript revised.docx --out qc/response_claims.json

Exit 0 when every anchored claim is verified (or none exist). With --strict,
exit 1 if any major verdict fires. Exit 2 on a missing file or an unreadable or malformed
--values file (the message names the field). Stdlib only; .docx read via python-docx when
available.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _quote_match import match_quality  # noqa: E402  (same-dir helper)
from decimal import Decimal, InvalidOperation  # noqa: E402

# A claim that asserts an addition/edit to the manuscript.
CLAIM_VERB = re.compile(
    r"\b("
    r"added the (?:sentence|statement|clause|text|following|phrase)|"
    r"added a (?:sentence|statement|clause|citation|reference|paragraph)|"
    r"we (?:have )?added|have added|now added|"
    r"inserted|included the (?:sentence|statement|text|citation|reference)|"
    r"now (?:reads|read|states|state)|"
    r"(?:revised|changed|reworded|rephrased|amended) [^.\n]{0,60}? to (?:read|state)|"
    r"now cites?|now cited|we (?:now )?cite|added (?:the )?(?:citation|reference)s?"
    r")\b"
    # The labelled form many letters use instead of a verb: 'Changes to text: "..."' or
    # 'Changes to Text (page 5, lines 3-4): "..."'. Its quote is the claimed new text.
    r"|\bchanges?\s+to\s+(?:the\s+)?text\b(?:\s*\([^)\n]{0,80}\))?\s*:",
    re.IGNORECASE,
)

# A quotation opens at one of these marks and closes at a matching one. Single marks are
# also apostrophes, so a single-quoted quotation closes only at a mark that is not followed
# by a letter or digit ("the model's output" does not end the quotation).
QUOTE_CLOSERS = {'"': '"”', "“": "”\"", "‘": "’'", "'": "'’"}
MIN_QUOTE_CHARS = 12  # a sentence-like assertion, not a single quoted term
PARA_BREAK = re.compile(r"\n[ \t]*\n")

# Citation tokens claimed as added.
CIT_NUMERIC = re.compile(r"\[(\d{1,3}(?:\s*[,–-]\s*\d{1,3})*)\]")
CIT_BIBKEY = re.compile(r"\[@([A-Za-z0-9_:.\-]+)\]")
CIT_AUTHOR = re.compile(r"\b([A-Z][A-Za-zÀ-ſ'-]{2,})\s+et\s+al\.?")
# Brackets in the BODY, pandoc's escaped '\[5\]' included. A bracket whose content parses as
# a pure numeric list ('[3; 5, 8-10]', '[5--7]', '[ 5 ]') is checked by whole element, so [15]
# does not cite 5. Any other bracket ('[5, see also 8]', '[5, p. 12]') keeps the lenient
# prefix match below, so nothing the lenient match cleared is newly flagged.
BODY_BRACKET = re.compile(r"\\?\[([^\[\]\n]{0,80}?)\\?\]")
RANGE_DASH = re.compile(r"-{2,3}|[\u2010-\u2015\u2212\uff0d~\u301c]")
NUMERIC_LIST = re.compile(r"\s*\d{1,4}(?:\s*[,;-]\s*\d{1,4})*\s*")

# Chars after a claim verb in which its object must START. A quotation that opens inside
# the window is read to its own closing mark however long it runs: truncating it at the
# window edge used to lose its closing mark, and the quote silently went unchecked.
WINDOW = 320


def _closing_mark(prose: str, i: int) -> int | None:
    """Index of the mark that closes the quotation opened at prose[i], within its paragraph."""
    closers = QUOTE_CLOSERS[prose[i]]
    single = prose[i] in "‘'"
    brk = PARA_BREAK.search(prose, i)
    limit = brk.start() if brk else len(prose)
    for j in range(i + 1, limit):
        if prose[j] in closers:
            if single and j + 1 < len(prose) and prose[j + 1].isalnum():
                continue  # an apostrophe inside the quotation, not its end
            return j
    return None


def quotes_opening_near(prose: str, start: int, window: int = WINDOW):
    """Yield (open_index, text) for each quotation that opens within `window` of `start`."""
    i, end = start, min(len(prose), start + window)
    while i < end:
        if prose[i] in QUOTE_CLOSERS and (i == 0 or not prose[i - 1].isalnum()):
            j = _closing_mark(prose, i)
            if j is not None:
                yield i, prose[i + 1 : j]
                i = j + 1
                continue
        i += 1


def read_text(path: Path) -> str:
    """Return plain text from .md/.txt or .docx (recursive paragraphs + tables)."""
    if path.suffix.lower() == ".docx":
        try:
            from docx import Document  # type: ignore
            from docx.document import Document as _Doc  # noqa: F401
        except Exception as exc:  # pragma: no cover
            raise SystemExit(f"python-docx required to read {path}: {exc}")
        doc = Document(str(path))
        parts: list[str] = []

        def walk_table(tbl):
            for row in tbl.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        parts.append(p.text)
                    for t in cell.tables:
                        walk_table(t)

        for p in doc.paragraphs:
            parts.append(p.text)
        for t in doc.tables:
            walk_table(t)
        return "\n".join(parts)
    return path.read_text(encoding="utf-8", errors="replace")


def normalize(s: str) -> str:
    """Casefold + collapse whitespace + strip markdown emphasis for substring match."""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"[*_`]", "", s)  # markdown emphasis / code ticks
    s = re.sub(r"\s+", " ", s)
    return s.casefold().strip()


def strip_response_blockquotes(text: str) -> str:
    """Drop reviewer-comment blockquote lines (>) so their quotes aren't scanned."""
    keep = [ln for ln in text.splitlines() if not ln.lstrip().startswith(">")]
    return "\n".join(keep)


def extract_claims(response: str):
    """Yield (kind, anchor, context) for anchored addition claims in Response prose."""
    prose = strip_response_blockquotes(response)
    claims = []
    seen_quotes: set[int] = set()
    for m in CLAIM_VERB.finditer(prose):
        start = m.start()
        window = prose[start : start + WINDOW]
        ctx = re.sub(r"\s+", " ", prose[max(0, start - 20) : start + 120]).strip()
        # quoted additions, each read to its own closing mark
        for at, raw in quotes_opening_near(prose, start):
            text = raw.strip()
            if at in seen_quotes or len(text) < MIN_QUOTE_CHARS or len(text.split()) < 4:
                continue
            seen_quotes.add(at)
            claims.append(("quote", text, ctx))
        # citation additions
        cits = []
        for cm in CIT_NUMERIC.finditer(window):
            for n in re.split(r"[,–-]", cm.group(1)):
                if n.strip():
                    cits.append(("num", n.strip()))
        for cm in CIT_BIBKEY.finditer(window):
            cits.append(("key", cm.group(1)))
        for cm in CIT_AUTHOR.finditer(window):
            cits.append(("author", cm.group(1)))
        # only treat a verb as a citation claim if the verb itself is citation-ish
        if cits and re.search(r"cit|reference", m.group(0), re.IGNORECASE):
            claims.append(("citation", cits, ctx))
    return claims


def grade_quote(body: str, quote: str) -> dict:
    """Grade the quote's presence in the body via the extraction-tolerant matcher.

    A contiguous search alone is not safe here: the manuscript may arrive as a .docx whose
    extraction wedges a footnote marker, a line number, or a bled column of reference text
    into the middle of the very sentence being checked. Those quotes are present and correct,
    and a substring test calls them absent — the failure that once nearly had two accurate
    verbatim quotes deleted. See _quote_match.py."""
    return match_quality(quote, body)


def body_has_citation(body: str, norm_body: str, cits) -> bool:
    """True if ANY cited token appears in the body (conservative: any-match passes)."""
    nums = rest = None
    for kind, tok in cits:
        if kind == "num":
            if nums is None:
                nums, rest = body_numeric_citations(body)
            if int(tok) in nums:
                return True
            if re.search(r"\[\s*\d*[,\s–-]*" + re.escape(tok) + r"\b", rest):
                return True
            if ("[" + tok + "]") in rest:
                return True
        if kind == "key" and ("@" + tok) in body:
            return True
        if kind == "author" and normalize(tok) in norm_body:
            return True
    return False


def body_numeric_citations(body: str):
    """(numbers cited in pure numeric bracket lists, ranges expanded; body with those removed).

    Whole elements only: [15] does not cite 5, and [14-17] cites 16."""
    out: set = set()

    def take(m):
        content = RANGE_DASH.sub("-", m.group(1))
        if not NUMERIC_LIST.fullmatch(content):
            return m.group(0)
        for part in re.split(r"[,;]", content):
            ends = [int(x) for x in part.split("-") if x.strip()]
            if len(ends) == 2 and ends[0] <= ends[1]:
                out.update(range(ends[0], ends[1] + 1))
            else:
                out.update(ends)
        return " "

    rest = BODY_BRACKET.sub(take, body)
    return out, rest


# --------------------------------------------------------------------------- declared values
# revision_values.json: {"entries": [{"id", "anchor", "values": [...], "location"?}], "notes"?}
# A declared value is a JSON number, or a string: a number, an inequality ("<0.001", "≤ .05"),
# a range ("0.88-0.95", "0.88 to 0.95") or a percentage ("12.5%"). Anything else exits 2.
VALUE_TOP_KEYS = {"entries", "notes"}
VALUE_ENTRY_KEYS = {"id", "anchor", "values", "location"}
_NUM = r"-?(?:\d+(?:\.\d+)?|\.\d+)"
_CMP = {"<": "<", ">": ">", "≤": "<=", "≥": ">=", "<=": "<=", ">=": ">=", "=<": "<=", "=>": ">="}
DECL_SINGLE = re.compile(rf"^\s*(<=|>=|=<|=>|<|>|≤|≥)?\s*({_NUM})\s*%?\s*$")
DECL_RANGE = re.compile(rf"^\s*({_NUM})\s*(?:-|–|—|to)\s*({_NUM})\s*%?\s*$")
# Body constructs whose digits cannot be read reliably: superscript digits and x10^n notation.
UNREADABLE = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]|[×x]\s*10\s*[\^⁻⁰-⁹]|\d[eE][-+]?\d")


class ValuesError(ValueError):
    pass


def _reject_constant(name: str):
    raise ValuesError(f"{name} is not a valid JSON number")


def _dec(text: str) -> Decimal:
    t = text.strip()
    neg = t.startswith("-")
    t = t.lstrip("-")
    if t.startswith("."):
        t = "0" + t
    try:
        d = Decimal(t)
    except InvalidOperation:
        raise ValuesError(f"not a number: {text!r}")
    return -d if neg else d


def _declared(value, where: str) -> list:
    """[("eq"|"<"|"<="|">"|">=", Decimal), ...] that the body must contain."""
    if isinstance(value, bool):
        raise ValuesError(f"{where}: expected a number or a value string, got {value!r}")
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValuesError(f"{where}: not a finite number")
        return [("eq", _dec(repr(value) if isinstance(value, float) else str(value)))]
    if not isinstance(value, str) or not value.strip():
        raise ValuesError(f"{where}: expected a number or a value string, got {value!r}")
    m = DECL_RANGE.match(value)
    if m:
        return [("eq", _dec(m.group(1))), ("eq", _dec(m.group(2)))]
    m = DECL_SINGLE.match(value.replace("−", "-"))
    if m:
        op = _CMP[m.group(1)] if m.group(1) else "eq"
        return [(op, _dec(m.group(2)))]
    raise ValuesError(f"{where}: {value!r} is not a number, an inequality (\"<0.001\"), a range "
                      "(\"0.88-0.95\") or a percentage (\"12.5%\"); write thousands without separators")


def load_values(path: Path) -> list:
    try:
        m = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, ValueError, RecursionError) as e:   # ValueError covers JSONDecodeError
        raise ValuesError(f"cannot read values file: {e}")
    if not isinstance(m, dict):
        raise ValuesError("values file must be a JSON object with an \"entries\" list")
    extra = set(m) - VALUE_TOP_KEYS
    if extra:
        raise ValuesError(f"unknown top-level key(s) {sorted(extra)}; allowed {sorted(VALUE_TOP_KEYS)}")
    entries = m.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValuesError("entries: expected a non-empty list")
    out = []
    for i, e in enumerate(entries):
        w = f"entries[{i}]"
        if not isinstance(e, dict):
            raise ValuesError(f"{w}: expected an object")
        extra = set(e) - VALUE_ENTRY_KEYS
        if extra:
            raise ValuesError(f"{w}: unknown key(s) {sorted(extra)}; allowed {sorted(VALUE_ENTRY_KEYS)}")
        eid = e.get("id")
        if not isinstance(eid, str) or not eid.strip():
            raise ValuesError(f"{w}.id: expected a non-empty string")
        anchor = e.get("anchor")
        if not isinstance(anchor, str) or len(anchor.split()) < 4:
            raise ValuesError(f"{w}.anchor: expected the body sentence (at least 4 words) that holds the values")
        loc = e.get("location")
        if loc is not None and not isinstance(loc, str):
            raise ValuesError(f"{w}.location: expected a string")
        vals = e.get("values")
        if not isinstance(vals, list) or not vals:
            raise ValuesError(f"{w}.values: expected a non-empty list")
        parsed = [(v, _declared(v, f"{w}.values[{j}]")) for j, v in enumerate(vals)]
        out.append({"id": eid.strip(), "anchor": anchor, "values": parsed, "location": loc})
    return out


def _fold_numbers(text: str, thousands: bool, spaces: bool) -> str:
    """Rewrite the body's number formats into plain '1234.56' tokens. Several foldings are
    read and a value counts as present under any of them, because a separator is ambiguous
    ("1,234" is a thousand or a decimal comma; "2019 100" is two numbers)."""
    t = text
    if spaces:   # thousands grouped by a space of any width: 12 345 / 12 345
        t = re.sub(r"(?<=\d)[\u00a0\u2009\u202f\u2007 ](?=\d{3}(?!\d))", "", t)
    else:        # only the typographic thin spaces, never a plain space
        t = re.sub(r"(?<=\d)[\u00a0\u2009\u202f\u2007](?=\d{3}(?!\d))", "", t)
    t = re.sub(r"(?<=\d)·(?=\d)", ".", t)                                 # 0·92
    if thousands:
        t = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", t)                    # 1,234
    t = re.sub(r"(?<=\d),(?=\d)", ".", t)                                 # 0,92 / 1,5
    t = re.sub(r"(?<![\d.])\.(?=\d)", "0.", t)                           # P=.03
    t = t.replace("≤", "<=").replace("≥", ">=").replace("&lt;", "<").replace("&gt;", ">")
    return t


_BODY_NUM = re.compile(r"(<=|>=|<|>|=)?\s*(\d+(?:\.\d+)?)")
_MINUS_BEFORE = re.compile(r"(?:^|[\s(=:;,\[])$")


def _paragraph_values(para: str) -> list:
    """(comparator, value) pairs. A sign is taken only from a true minus (U+2212) or a hyphen
    that opens a number, so the dash of a range ("0.88-0.95") never makes 0.95 negative."""
    out = []
    for th, sp in ((False, False), (True, False), (True, True)):
        t = _fold_numbers(para, th, sp)
        for m in _BODY_NUM.finditer(t):
            try:
                v = Decimal(m.group(2))
            except InvalidOperation:
                continue
            k = m.start(2)
            if k and t[k - 1] in "\u2212-" and _MINUS_BEFORE.search(t[:k - 1]) and not m.group(1):
                v = -v
            out.append((m.group(1) or "", v))
    return out


def _value_present(need: tuple, found: list) -> bool:
    op, val = need
    for fop, fval in found:
        if fval != val:
            continue
        if op == "eq" or fop == op:
            return True
    return False


def check_values(body: str, entries: list) -> list:
    paras = [p for p in re.split(r"\n\s*\n|\n", body) if p.strip()]
    findings = []
    for e in entries:
        hits = [p for p in paras if match_quality(e["anchor"], p)["grade"] != "ABSENT"]
        if not hits:
            findings.append({
                "verdict": "RESPONSE_VALUE_NOT_ASSESSED", "severity": "minor", "id": e["id"],
                "claimed_text": e["anchor"], "context": e["location"] or "",
                "message": "The declared anchor sentence is not in the revised manuscript, so its "
                           "values were not checked; fix the anchor or confirm the edit by eye.",
            })
            continue
        found = [v for p in hits for v in _paragraph_values(p)]
        unreadable = any(UNREADABLE.search(p) for p in hits)
        for raw, needs in e["values"]:
            if all(_value_present(n, found) for n in needs):
                continue
            if unreadable:
                findings.append({
                    "verdict": "RESPONSE_VALUE_NOT_ASSESSED", "severity": "minor", "id": e["id"],
                    "claimed_text": e["anchor"], "declared_value": raw, "context": e["location"] or "",
                    "message": f"Declared value {raw!r} was not found, but the paragraph has numbers "
                               "this gate cannot read (superscripts or x10^n); confirm by eye.",
                })
            else:
                shown = sorted({(op + str(v)) for op, v in found})[:12]
                findings.append({
                    "verdict": "RESPONSE_VALUE_MISMATCH", "severity": "major", "id": e["id"],
                    "claimed_text": e["anchor"], "declared_value": raw, "context": e["location"] or "",
                    "body_values": shown,
                    "message": f"Declared value {raw!r} is not in the revised manuscript paragraph "
                               f"that holds the anchor (numbers there: {', '.join(shown) or 'none'}).",
                })
    return findings


def build_report(response_path: Path, manuscript_path: Path, values: list | None = None) -> dict:
    response = read_text(response_path)
    body = read_text(manuscript_path)
    norm_body = normalize(body)
    findings = []
    for kind, anchor, ctx in extract_claims(response):
        if kind == "quote":
            g = grade_quote(body, anchor)
            if g["grade"] == "INTERLEAVED":
                findings.append(
                    {
                        "verdict": "RESPONSE_QUOTE_UNRESOLVED",
                        "severity": "minor",
                        "claimed_text": anchor,
                        "context": ctx,
                        "match": g,
                        "message": (
                            f"Every word of the quoted text appears in order, but with {g['inserted']} "
                            "foreign token(s) wedged in — consistent with a dirty extraction (a bled "
                            "reference column, line numbers, a footnote marker), not a missing edit. "
                            "Confirm by eye; do not treat as absent."
                        ),
                    }
                )
            elif g["grade"] == "PARTIAL":
                findings.append(
                    {
                        "verdict": "RESPONSE_QUOTE_UNRESOLVED",
                        "severity": "minor",
                        "claimed_text": anchor,
                        "context": ctx,
                        "match": g,
                        "message": (
                            f"{g['matched']} of {g['total']} words of the quoted text appear in order "
                            "— enough to be the same sentence damaged in extraction (a hyphen split "
                            "across a line, a dropped glyph) rather than an edit that was never made. "
                            "Confirm by eye."
                        ),
                    }
                )
            elif g["grade"] == "ABSENT":
                findings.append(
                    {
                        "verdict": "RESPONSE_QUOTE_UNVERIFIED",
                        "severity": "major",
                        "claimed_text": anchor,
                        "context": ctx,
                        "match": g,
                        "message": "Response quotes added text that is absent from the revised manuscript body.",
                    }
                )
        elif kind == "citation":
            if not body_has_citation(body, norm_body, anchor):
                findings.append(
                    {
                        "verdict": "RESPONSE_CITATION_UNVERIFIED",
                        "severity": "major",
                        "claimed_citation": [t for _, t in anchor],
                        "context": ctx,
                        "message": "Response claims a citation was added but none of the cited tokens appear in the revised manuscript body.",
                    }
                )
    if values:
        findings.extend(check_values(body, values))
    n_major = sum(1 for f in findings if f["severity"] == "major")
    return {
        "response": str(response_path),
        "manuscript": str(manuscript_path),
        "findings": findings,
        "summary": {"major": n_major, "unresolved": len(findings) - n_major},
        # An UNRESOLVED quote is a "look at this", not a defect: the words are demonstrably
        # there and only the extraction is suspect. Safety therefore turns on MAJOR findings,
        # which is what --strict has always documented.
        "submission_safe": n_major == 0,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--response", required=True, type=Path, help="response-to-reviewers letter (.md/.txt/.docx)")
    ap.add_argument("--manuscript", required=True, type=Path, help="revised manuscript (.md/.txt/.docx)")
    ap.add_argument("--values", type=Path,
                    help="revision_values.json: declared values to check in the body (see references)")
    ap.add_argument("--out", type=Path, help="write JSON report here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any major verdict fires")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    for p in (args.response, args.manuscript):
        if not p.is_file():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2

    values = None
    if args.values is not None:
        if not args.values.is_file():
            print(f"error: file not found: {args.values}", file=sys.stderr)
            return 2
        try:
            values = load_values(args.values)
        except (ValuesError, ValueError, OverflowError, RecursionError) as e:
            print(f"error: {args.values}: {e}", file=sys.stderr)
            return 2
    report = build_report(args.response, args.manuscript, values)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"detector": "check_response_claims", **report}, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        s = report["summary"]
        if not report["findings"]:
            print("OK: every anchored response claim is verified against the revised manuscript.")
        else:
            print(f"RESPONSE_CLAIM findings — {s['major']} major, {s['unresolved']} unresolved:")
            for f in report["findings"]:
                anchor = f.get("claimed_text") or ", ".join(f.get("claimed_citation", []))
                print(f"  [{f['verdict']}] ({f['severity']}) {anchor!r}")
                if "declared_value" in f:
                    print(f"      {f['message']}")
                print(f"      near: {f['context']}")
                if f["severity"] == "minor":
                    print(f"      {f['message']}")
            if s["major"] == 0:
                print("\nNo major drift: the unresolved item(s) are extraction-quality doubts, "
                      "not claims of an edit that was never made.")

    if args.strict and not report["submission_safe"]:
        print("\nRESPONSE_CLAIM_UNVERIFIED: a response-letter claim is not reflected in the revised manuscript.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

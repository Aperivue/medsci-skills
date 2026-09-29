#!/usr/bin/env python3
"""Bound how much of a text a humanize rewrite is allowed to touch (humanize Phase 3).

De-AI editing is subtractive: strip the tells, keep the author's sentences. A model asked to
"make this sound human" will also rewrite paragraphs that had nothing wrong with them, and the
result reads fluently enough that the loss is invisible on review — the author's voice is gone
and nobody can point to the sentence where it went. Pattern-by-pattern fixes touch a small
fraction of the words; a wholesale rewrite touches most of them. That difference is measurable,
so this gate measures it instead of trusting the rewrite to have been restrained.

It also enforces the two invariants the humanize skill declares but never checked: every number
and every citation present before the rewrite must still be present after it.

Verdicts:
  NUMBER_DRIFT (Major)         a numeric token's count changed across the rewrite — including a
                               dropped leading minus ("-2.4" -> "2.4") and a flipped comparison
                               ("24% lower" -> "24% above"). Each changed token is reported with
                               a short before/after context snippet.
  CITATION_DROP (Major)        a citation present before is absent after.
  EDIT_FOOTPRINT_HIGH (Minor)  more than --warn-pct of the words changed — re-read the diff.

Why the footprint is advisory and the invariants are not: the two invariants are the skill's
own declared contract ("every number, statistic, p-value, confidence interval and clinical fact
must remain identical"; "do not remove or relocate citations"), so a violation is unambiguous.
The footprint percentage has no such backing. Measured on this skill's own fixtures, a *correct*
de-AI pass over an AI-inflated Discussion changed 61% of word tokens — because Patterns 6 and 18
require replacing formulaic limitation and conclusion paragraphs with specific content, which
rewrites whole paragraphs by design. A hard threshold would therefore fail exactly the edits the
skill asks for. The percentage is reported so a human can notice an implausible one; it is not
evidence of over-editing on its own, and the default is deliberately loose.

Exit codes: 0 clean or Minor-only, 1 with --strict when any Major fires, 2 usage error.

Scoped to keep false positives low:
  * Comparison is on WORD tokens, not characters, so punctuation-only fixes (Pattern 13
    em-dash -> parenthesis, Pattern 15 curly -> straight quotes) barely move the number.
  * Citation markers are stripped before numeric extraction, so a reference number is
    checked once as a citation and never again as a number.
  * Fenced code blocks are excluded from both sides.

Stdlib-only.

Usage:
    python3 check_rewrite_fidelity.py --before original.md --after humanized.md \
        [--out qc/rewrite_fidelity.json] [--warn-pct 70] [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

DETECTOR_ID = "check_rewrite_fidelity"

FENCE_RE = re.compile(r"```.*?```", re.S)
# Pandoc citation keys and bare numeric markers, e.g. [@smith2020], [12], [3-5], [3–5].
CITEKEY_RE = re.compile(r"\[@[^\]\s]+\]")
NUMMARK_RE = re.compile(r"\[\d+(?:\s*[-–,]\s*\d+)*\]")
WORD_RE = re.compile(r"[A-Za-z0-9''-]+")
# A numeric token: integer, decimal, or percentage. Thousands separators are dropped so that
# "1,200" and "1200" compare equal. A LEADING minus (U+2212 or "-") is kept, because a rewrite
# that drops it reverses the value: "-2.4" and "2.4" must not compare equal. A hyphen that joins
# two tokens ("0.91-0.97", "COVID-19", "0.91 - 0.97") is a range or compound, not a sign.
NUMBER_RE = re.compile(
    r"(?P<sign>[−-])?"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?!\d)(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?P<pct>\s?%|\s+percent\b)?", re.IGNORECASE)
# A relative change carries its direction in the word next to it: "24% lower" and "24% above"
# share every digit and say opposite things. A percentage bound to such a word becomes
# "24% (down)" / "24% (up)", so flipping the direction changes the token and fires
# NUMBER_DRIFT. Synonyms share a polarity, so "12% lower" -> "lower by 12%" or "a 12%
# reduction" does not fire. Absolute levels ("decreased to 3.2%", "more than 5%") are not bound.
_UP = (r"higher|greater|larger|more|above|increase[sd]?|increasing|rise[sn]?|rose"
       r"|gain(?:ed|s)?")
_DOWN = (r"lower|less|fewer|smaller|below|decrease[sd]?|decreasing|reduction|reduced|reduces?"
         r"|decline[sd]?|drop(?:ped|s)?|fell|falls?")
_UP_RE = re.compile(rf"^(?:{_UP})$", re.IGNORECASE)
# Word right after the percentage: "24% lower", "a 12% increase", "5 percent fewer".
_AFTER_RE = re.compile(rf"\s*(?P<w>{_UP}|{_DOWN})\b", re.IGNORECASE)
# Word right before it: a change verb/noun ("increased by 12%", "a reduction of 12%",
# "rose 12%") or a comparative with "by" ("lower by 12%").
_CHANGE = (r"increase[sd]?|increasing|rise[sn]?|rose|gain(?:ed|s)?|decrease[sd]?|decreasing"
           r"|reduction|reduced|reduces?|decline[sd]?|drop(?:ped|s)?|fell|falls?")
_BEFORE_RE = re.compile(
    rf"\b(?:(?P<w>{_CHANGE})\s+(?:by\s+|of\s+)?"
    r"|(?P<c>higher|greater|larger|more|lower|less|fewer|smaller)\s+by\s+)$", re.IGNORECASE)
_CONTEXT = 45  # characters of context either side of a changed token in the report


def _strip_fences(text: str) -> str:
    return FENCE_RE.sub(" ", text)


def _citations(text: str) -> Counter:
    keys = CITEKEY_RE.findall(text)
    marks = NUMMARK_RE.findall(text)
    return Counter(k.strip() for k in keys + marks)


def _is_minus(text: str, i: int) -> bool:
    """Is the sign character at ``text[i]`` a leading minus (not a range/compound hyphen)?"""
    if i == 0:
        return True
    prev = text[i - 1]
    if prev.isalnum() or prev in ".%)]":
        return False  # joined: "0.91-0.97", "COVID-19"
    if prev.isspace():
        j = i - 1
        while j >= 0 and text[j].isspace():
            j -= 1
        return j < 0 or not (text[j].isdigit() or text[j] in "%)")  # "0.91 - 0.97" is a range
    return True  # "(-0.3", "=-0.3", ":-0.3"


def _number_tokens(text: str) -> list[tuple[str, int, int]]:
    """(token, start, end) for every numeric token. Citation markers are blanked first (with
    equal-length spaces, so offsets still index ``text``) so a reference number is not
    double-counted as a statistic."""
    blank = lambda m: " " * len(m.group(0))  # noqa: E731
    masked = NUMMARK_RE.sub(blank, CITEKEY_RE.sub(blank, text))
    out: list[tuple[str, int, int]] = []
    for m in NUMBER_RE.finditer(masked):
        sign = m.group("sign")
        minus = bool(sign) and _is_minus(masked, m.start("sign"))
        token = ("-" if minus else "") + m.group("num").replace(",", "")
        if m.group("pct"):
            a = _AFTER_RE.match(masked, m.end())
            b = _BEFORE_RE.search(masked[max(0, m.start() - 40):m.start()])
            word = a.group("w") if a else (b.group("w") or b.group("c")) if b else None
            if word:
                token += "% (up)" if _UP_RE.match(word) else "% (down)"
        start = m.start("num") if not minus else m.start("sign")
        out.append((token, start, m.end()))
    return out


def _snippet(text: str, start: int, end: int) -> str:
    a, b = max(0, start - _CONTEXT), min(len(text), end + _CONTEXT)
    body = re.sub(r"\s+", " ", text[a:b]).strip()
    return ("…" if a > 0 else "") + body + ("…" if b < len(text) else "")


def _context(token: str, toks: list[tuple[str, int, int]], text: str, other: str) -> str | None:
    """One short snippet showing where ``token`` sits in ``text``: preferably an occurrence
    whose surroundings the other side does not share (the edited one). If the token is absent
    here but the same number appears with a different direction, show that occurrence — a
    flipped "24% (down)" then lands next to its "24% (up)"."""
    hits = [(s, e) for t, s, e in toks if t == token]
    if not hits:
        base = token.split("%")[0].lstrip("-")
        hits = [(s, e) for t, s, e in toks if t.split("%")[0].lstrip("-") == base]
    if not hits:
        return None
    flat_other = re.sub(r"\s+", " ", other)
    for s, e in hits:
        snip = _snippet(text, s, e)
        if snip.strip("…") not in flat_other:
            return snip
    return _snippet(text, *hits[0])


def _words(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def _changed_fraction(before: list[str], after: list[str]) -> float:
    """Fraction of word tokens that differ, measured against the longer side so that a
    rewrite cannot lower the score by deleting text."""
    if not before and not after:
        return 0.0
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    denom = max(len(before), len(after))
    return 1.0 - (matched / denom) if denom else 0.0


def _diff_counter(before: Counter, after: Counter) -> list[dict]:
    out = []
    for token in sorted(set(before) | set(after)):
        b, a = before.get(token, 0), after.get(token, 0)
        if b != a:
            out.append({"token": token, "before": b, "after": a})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--before", required=True, type=Path, help="text as it was before the rewrite")
    ap.add_argument("--after", required=True, type=Path, help="text after the humanize rewrite")
    ap.add_argument("--out", type=Path, help="write the JSON envelope here")
    ap.add_argument("--warn-pct", type=float, default=70.0,
                    help="Minor above this %% of words changed (default 70; advisory, see module docstring)")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any Major fires")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    for path in (args.before, args.after):
        if not path.is_file():
            print(f"usage error: no such file: {path}", file=sys.stderr)
            return 2

    before_raw = _strip_fences(args.before.read_text(encoding="utf-8"))
    after_raw = _strip_fences(args.after.read_text(encoding="utf-8"))

    changed = _changed_fraction(_words(before_raw), _words(after_raw))
    changed_pct = round(changed * 100, 1)
    before_toks, after_toks = _number_tokens(before_raw), _number_tokens(after_raw)
    num_delta = _diff_counter(Counter(t for t, _, _ in before_toks),
                              Counter(t for t, _, _ in after_toks))
    # A bare token list sends the reader back to search both files; carry one short snippet
    # from each side so a renumbered slide and a changed statistic can be told apart at once.
    for d in num_delta[:40]:
        d["before_context"] = _context(d["token"], before_toks, before_raw, after_raw)
        d["after_context"] = _context(d["token"], after_toks, after_raw, before_raw)
    cite_delta = _diff_counter(_citations(before_raw), _citations(after_raw))

    claims: list[dict] = []
    if changed_pct > args.warn_pct:
        claims.append({
            "verdict": "EDIT_FOOTPRINT_HIGH",
            "severity": "Minor",
            "changed_pct": changed_pct,
            "threshold_pct": args.warn_pct,
            "message": (
                f"{changed_pct}% of word tokens changed (advisory threshold {args.warn_pct}%). "
                "A thorough de-AI pass can legitimately reach this level when Patterns 6 and 18 "
                "replace whole paragraphs; re-read the diff and confirm the author's argument, "
                "not just their phrasing, survived."
            ),
        })
    if num_delta:
        claims.append({
            "verdict": "NUMBER_DRIFT",
            "severity": "Major",
            "tokens": num_delta[:40],
            "message": (
                f"{len(num_delta)} numeric token(s) changed count across the rewrite. "
                "Humanize must never alter a number."
            ),
        })
    if cite_delta:
        claims.append({
            "verdict": "CITATION_DROP",
            "severity": "Major",
            "tokens": cite_delta[:40],
            "message": (
                f"{len(cite_delta)} citation(s) changed count across the rewrite. "
                "Humanize must never remove or relocate a citation."
            ),
        })

    envelope = {
        "detector": "check_rewrite_fidelity",
        "before": str(args.before),
        "after": str(args.after),
        "changed_pct": changed_pct,
        "words_before": len(_words(before_raw)),
        "words_after": len(_words(after_raw)),
        "claims": claims,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print(f"{DETECTOR_ID}: {changed_pct}% of words changed "
              f"({len(_words(before_raw))} -> {len(_words(after_raw))})")
        for claim in claims:
            print(f"  [{claim['severity']}] {claim['verdict']}: {claim['message']}")
            if claim["verdict"] == "NUMBER_DRIFT":
                for d in claim["tokens"]:
                    print(f"      {d['token']}: {d['before']} -> {d['after']}")
                    print(f"        before: {d.get('before_context') or '(absent)'}")
                    print(f"        after:  {d.get('after_context') or '(absent)'}")
        if not claims:
            print("  clean: footprint within bounds, numbers and citations preserved")

    if args.strict and any(c["severity"] == "Major" for c in claims):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

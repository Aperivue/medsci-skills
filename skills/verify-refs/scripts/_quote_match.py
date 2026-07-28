"""Quote matching that survives an extraction layer — the substrate under quote gates.

WHY THIS EXISTS (the failure it removes)

Verifying "the manuscript contains this quoted sentence" by searching a CONTIGUOUS string
is wrong whenever the haystack came out of an extractor, because extractors interleave
tokens the source never had. In one submission-day session that single assumption produced
thirteen false positives, all the same shape:

  * a two-column PDF bled reference-list text into the middle of a sentence
    ("learners form independent" | "civile." | "assessments before seeing AI output");
  * a line-numbered supplement PDF put the line number inside the sentence
    ("were" | "86" | "performed");
  * superscript markers and footnote references landed mid-clause;
  * hyphenation across a line break split one word into two ("assess-" + "ments").

Every one of those quotes was CORRECT and present. The contiguous check called them absent.
It came within one step of instructing an author to delete two accurate verbatim quotes.

THE RULE THIS ENCODES

A quote that cannot be matched contiguously is not thereby "not in the source". It is
UNRESOLVED until something stronger says otherwise. So this module grades a match instead
of answering yes/no:

  EXACT        the normalized quote is a contiguous substring — verified, no doubt.
  INTERLEAVED  every quote token appears IN ORDER, with only a bounded number of foreign
               tokens wedged between them — the text is there and the extraction is dirty.
  PARTIAL      most quote tokens appear in order but some are missing — consistent with
               extraction damage (hyphen splits, dropped glyphs); too weak to call absent.
  ABSENT       not even a partial ordered run — the text really is not there.

Only ABSENT justifies a "you claimed an edit you did not make" verdict. INTERLEAVED and
PARTIAL are reported as unresolved so a human looks, rather than as a defect.

WHY THE GAPS ARE BOUNDED (the precision that makes this safe)

An unbounded subsequence match is worthless: the tokens of almost any short sentence appear
"in order" somewhere in a long document if you allow arbitrary distance. The bound that works
is not a token budget but an INTERRUPTION COUNT, because the two cases differ in shape:

    a real extraction artifact interrupts a sentence once or twice, and each interruption can
    be long (a bled reference line is a dozen tokens);

    a spurious "match" interrupts at nearly every token, each time by a little.

So the limits are: at most MAX_GAP foreign tokens at any single join, at most
MAX_INTERRUPTIONS joins that are interrupted at all, and a total-insertion sanity cap. A
quote whose words are scattered one-by-one across a Discussion section needs an interruption
at every join and fails, while a quote split once by a column bleed passes.

Not a detector: a helper imported by the gates that need it (leading underscore keeps it out
of the detector catalog glob). Stdlib only.
"""

from __future__ import annotations

import re
import unicodedata

# At most this many foreign tokens may sit at ONE join. A bled reference line ("civile. Rev
# Med Suisse 2019;15:1122.") is around a dozen tokens; a running header a handful.
MAX_GAP = 25
# At most this many joins may be interrupted AT ALL. This is the limit that separates a dirty
# extraction (one or two interruptions) from a spurious scatter (an interruption per token).
MAX_INTERRUPTIONS = 4
# Sanity cap on total foreign tokens, so a short quote cannot absorb an entire paragraph.
MAX_TOTAL_INSERT_FRAC = 5.0
MIN_TOTAL_INSERT = 20
# A PARTIAL match must still account for this share of the quote's tokens; below it, ABSENT.
PARTIAL_COVERAGE = 0.80

_TOKEN_RE = re.compile(r"[0-9a-z]+(?:'[a-z]+)?", re.IGNORECASE)


def normalize(s: str) -> str:
    """Casefold, unify quotes/dashes, drop markdown emphasis, repair line-break hyphenation,
    and collapse whitespace. Hyphenation repair matters: an extractor that wraps "assess-
    ments" across a line otherwise destroys the token the quote is looking for."""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    # join a word split by a hyphen at a line break: "assess-\n  ments" -> "assessments"
    s = re.sub(r"(\w)[-‐‑]\s*\n\s*(\w)", r"\1\2", s)
    s = re.sub(r"[*_`]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.casefold().strip()


def tokens(s: str) -> list[str]:
    """Normalized word/number tokens. Punctuation is dropped, so an injected '.' or a stray
    bracket never breaks a match on its own."""
    return _TOKEN_RE.findall(normalize(s))


def _ordered_run(needle: list[str], hay: list[str], allow_missing: bool):
    """Best ordered match of `needle` inside `hay`.

    Walks every candidate start and consumes needle tokens in order, skipping at most
    MAX_GAP foreign tokens per join, at most MAX_INTERRUPTIONS interrupted joins, and a
    total-insertion sanity cap. With allow_missing, a needle token that cannot be found
    within the gap window is skipped (counted as missing) instead of failing the run.

    Returns (matched_count, inserted_count) for the best run, or (0, 0)."""
    if not needle or not hay:
        return (0, 0)
    budget = max(MIN_TOTAL_INSERT, int(len(needle) * MAX_TOTAL_INSERT_FRAC))
    max_missing = len(needle) - int(len(needle) * PARTIAL_COVERAGE)
    best = (0, 0)
    first = needle[0]
    starts = [i for i, t in enumerate(hay) if t == first]
    if allow_missing and not starts:
        # the opening token itself may be the damaged one — try any token of the quote
        wanted = set(needle)
        starts = [i for i, t in enumerate(hay) if t in wanted]
    for start in starts:
        hi = start
        matched = inserted = missing = interruptions = 0
        for tok in needle:
            found = -1
            for j in range(hi, min(hi + MAX_GAP + 1, len(hay))):
                if hay[j] == tok:
                    found = j
                    break
            if found < 0:
                if not allow_missing:
                    break
                missing += 1
                if missing > max_missing:
                    break
                continue
            gap = found - hi
            if gap:
                interruptions += 1
                if interruptions > MAX_INTERRUPTIONS:
                    break
            inserted += gap
            if inserted > budget:
                break
            matched += 1
            hi = found + 1
        if matched > best[0]:
            best = (matched, inserted)
        if matched == len(needle):
            break
    return best


def match_quality(quote: str, haystack: str) -> dict:
    """Grade how well `quote` is present in `haystack`.

    Returns {"grade": EXACT|INTERLEAVED|PARTIAL|ABSENT, "matched", "total", "inserted",
             "coverage"}. Only ABSENT means "this text is not in the document"."""
    nq, nh = normalize(quote), normalize(haystack)
    q_tok = tokens(quote)
    total = len(q_tok)
    if total == 0:
        return {"grade": "ABSENT", "matched": 0, "total": 0, "inserted": 0, "coverage": 0.0}
    if nq and nq in nh:
        return {"grade": "EXACT", "matched": total, "total": total, "inserted": 0, "coverage": 1.0}

    h_tok = tokens(haystack)
    matched, inserted = _ordered_run(q_tok, h_tok, allow_missing=False)
    if matched == total:
        return {"grade": "INTERLEAVED", "matched": matched, "total": total,
                "inserted": inserted, "coverage": 1.0}

    matched, inserted = _ordered_run(q_tok, h_tok, allow_missing=True)
    coverage = matched / total
    grade = "PARTIAL" if coverage >= PARTIAL_COVERAGE else "ABSENT"
    return {"grade": grade, "matched": matched, "total": total,
            "inserted": inserted, "coverage": round(coverage, 3)}

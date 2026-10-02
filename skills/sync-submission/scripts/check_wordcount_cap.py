#!/usr/bin/env python3
"""Body-word-count vs journal cap gate (the revision-inflation trap).

A revise loop monotonically *adds* words — resolving reviewer majors appends
sentences, sensitivity analyses, and caveats — and silently pushes the body over
the target journal's word limit. It is caught, if at all, only by a manual
measurement late in the cycle. This gate makes the measurement deterministic and
cheap enough to re-run after every `/revise` pass.

It counts the manuscript **body** (Introduction → Discussion), excluding YAML
front matter, the abstract, references, tables/figures, supplementary, and the
declaration sections (the same skip set as the cover-letter drift check, vendored
here so this script is self-contained), and compares it to a word cap. The body's
own subheadings ("Study population", "Statistical analysis") are counted, because
the rendered DOCX carries each one as a line of text and Word counts it.

THE BINDING NUMBER IS THE RENDERED WORD COUNT. pandoc citeproc expands each
`[@key]` to "(Author Year)", so the rendered DOCX counts higher than the markdown.
This gate approximates the rendered count as `body_words + n_inline_citations *
--citation-expansion` (default 1.6), where body_words includes subheading words.
When you have the authoritative rendered count (e.g. Word's count on the built
DOCX), pass it with `--rendered-words N` and that is used verbatim.

CAP SOURCE
  --limit N                 the body word cap (deterministic; preferred).
  --journal-profile P       a journal profile .md; the cap is read from a STRUCTURED
    [--article-type T]      field only (default match: "Original"):
                              * a markdown table whose header has one non-abstract
                                word-limit column ("Body Word Limit", "Word Limit"),
                                in the row whose first cell starts with T; or
                              * failing a table, a list item that STARTS with T, e.g.
                                "- Original Article (4,000 words, abstract <250)",
                                taking its first "N words".
                            Prose that merely mentions T ("a structured abstract
                            of 250 words required for Original Articles") is never
                            read. If no single integer results, the script exits 2
                            and asks for --limit (no fuzzy guessing).

OUTPUT
  stdout summary and, with --out, a JSON artifact:
    {manuscript, body_words, heading_words, n_inline_citations, rendered_words_est,
     limit, near_threshold, ratio, verdict}
  WORDCOUNT_OVER_CAP (Major) when the effective count exceeds the cap;
  WORDCOUNT_NEAR_CAP (Minor) when it exceeds near_threshold * cap (default 0.95).
  Exit 1 (with --strict) when WORDCOUNT_OVER_CAP fires.

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean / near (or
report-only), 1 over cap (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _yaml_frontmatter import split_yaml_front_matter

# --- measurement (shares the skip set + YAML splitter with cover_letter_drift_check.py) -----

SKIP_SECTION_RE = re.compile(
    r"^#{1,6}\s+\*{0,2}\s*("
    r"Abstract|References?|Table\s+Captions?|Table\s+Legends?|Figure\s+Legends?|"
    r"Tables?|Figures?|Supplementary\s+(Materials?|Tables?|Figures?|Appendix)|"
    r"Acknowled[gd]e?ments?|Funding|Conflicts?\s+of\s+Interest|COI|"
    r"Author\s+Contributions?|Data\s+Availability|Code\s+Availability|"
    r"AI\s+Disclosure|Artificial\s+Intelligence\s+Disclosure"
    r")\s*\*{0,2}\s*:?\s*$",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'./%\-]*")
# pandoc inline citations: [@key], [@k1; @k2], [-@k]. Count each @key.
CITE_RE = re.compile(r"@[A-Za-z0-9_][A-Za-z0-9_:.\-]*")
# Markdown has two heading syntaxes and pandoc accepts both. This recognised only ATX, and only to
# depth 3 — so under setext ("References" on one line, "==========" under it) the heading was never
# seen, `in_skip` never turned on, and the ENTIRE References section was counted as body prose.
# Byte-identical prose measured 480 words as ATX and 1,002 as setext, and this gate blocks a
# submission on a journal's word cap.
HEADER_RE = re.compile(r"^#{1,6}\s")
# A setext underline: at least two `=` or `-` alone on the line. Two, not one, so a stray "-" is not
# a heading; and the caller additionally requires the line ABOVE to be non-blank body text, which is
# what separates a setext heading from a horizontal rule.
SETEXT_UNDERLINE_RE = re.compile(r"^\s{0,3}(={2,}|-{2,})\s*$")
# The same section names as SKIP_SECTION_RE, with no leading hashes, for the setext form.
SETEXT_SKIP_RE = re.compile(
    SKIP_SECTION_RE.pattern.replace(r"^#{1,6}\s+", "^", 1), re.IGNORECASE)


def _heading_words(text: str) -> int:
    """Words in a body subheading's own text (markup stripped)."""
    return len(WORD_RE.findall(re.sub(r"^#{1,6}\s+|[*_`]", " ", text)))


def measure_body(manuscript_path: Path) -> tuple[int, int, int]:
    """Return (body_words, n_inline_citations, heading_words) over the non-skipped body.

    ``body_words`` INCLUDES the words of every body subheading ("Study population",
    "Statistical analysis"); ``heading_words`` reports that share separately. A rendered
    DOCX — the binding number — puts each heading on its own line and Word counts it, so
    an estimate that dropped them read a real overage as NEAR_CAP (fifteen four-word
    subheadings are 60 words). Headings of skipped sections (Abstract, References, ...)
    are not counted, like the sections themselves.
    """
    words = 0
    cites = 0
    heading_words = 0
    for kind, stripped in iter_body(manuscript_path):
        if kind == "heading":
            heading_words += _heading_words(stripped)
            continue
        cites += len(CITE_RE.findall(stripped))
        # Don't count the citation tokens themselves as prose words.
        prose = CITE_RE.sub(" ", stripped)
        words += len(WORD_RE.findall(prose))
    return words + heading_words, cites, heading_words


def iter_body(manuscript_path: Path):
    """Yield ("heading", line) / ("prose", line) for the body that counts toward a word cap.

    The ONE section walker shared by this gate and cover_letter_drift_check.py, so both
    agree on where the body ends: ATX headings of any depth and setext headings both open
    and close skipped sections (Abstract, References, ...). YAML front matter, code fences,
    table rows and HTML comments are never yielded.
    """
    lines = manuscript_path.read_text(encoding="utf-8").splitlines()
    _, body_lines = split_yaml_front_matter(lines)
    in_skip = False
    in_code_fence = False
    for idx, line in enumerate(body_lines):
        stripped = line.rstrip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        # A setext underline belonging to the line above: consume it, never count it as prose.
        if SETEXT_UNDERLINE_RE.match(stripped) and idx and body_lines[idx - 1].strip():
            continue
        # Setext heading: this line is titled by the underline beneath it.
        nxt = body_lines[idx + 1].rstrip() if idx + 1 < len(body_lines) else ""
        if stripped.strip() and SETEXT_UNDERLINE_RE.match(nxt):
            in_skip = bool(SETEXT_SKIP_RE.match(stripped.strip()))
            if not in_skip:
                yield "heading", stripped
            continue
        if HEADER_RE.match(stripped):
            in_skip = bool(SKIP_SECTION_RE.match(stripped))
            if not in_skip:
                yield "heading", stripped
            continue
        if in_skip:
            continue
        if stripped.startswith("|") or stripped.startswith("<!--"):
            continue
        yield "prose", stripped


# --- cap from a journal profile --------------------------------------------

# "Original Article (4,000 words ...)" / "Original Research Article (≤ 5,000 words ...)"
PROFILE_LIMIT_RE = re.compile(r"(?:≤|<=|<|up to|max(?:imum)?)?\s*([0-9][0-9,]{2,})\s*[- ]?words?",
                              re.IGNORECASE)
# A bare integer of three or more digits (table cells carry the number without "words").
CELL_INT_RE = re.compile(r"(?<![0-9.,])([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{3,})(?![0-9.,]*[0-9])")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _label(cell: str) -> str:
    return re.sub(r"[*_`]", "", cell).strip().lower()


def _table_caps(lines: list[str], want: str) -> list[tuple[int, str]]:
    """(line_no, cell) for each table row of type `want` under a body-word-limit column."""
    out: list[tuple[int, str]] = []
    i = 0
    while i + 1 < len(lines):
        if "|" in lines[i] and TABLE_SEP_RE.match(lines[i + 1]):
            header = [_label(c) for c in _cells(lines[i])]
            # The body-limit column: one header naming "body" (e.g. "Body", "Body (max)",
            # "Body Word Limit"); failing that, one non-abstract "word" header.
            body_cols = [k for k, h in enumerate(header) if "body" in h and "abstract" not in h]
            word_cols = [k for k, h in enumerate(header) if "word" in h and "abstract" not in h]
            col = body_cols or word_cols
            j = i + 2
            while j < len(lines) and "|" in lines[j]:
                row = _cells(lines[j])
                if row and _label(row[0]).startswith(want):
                    if len(col) != 1 or col[0] >= len(row):
                        out.append((j + 1, ""))  # ambiguous/absent column -> refuse
                    else:
                        out.append((j + 1, row[col[0]]))
                j += 1
            i = j
            continue
        i += 1
    return out


def parse_cap_from_profile(profile: Path, article_type: str) -> int:
    if not profile.is_file():
        sys.stderr.write(f"ERROR: journal profile not found: {profile}\n")
        sys.exit(2)
    want = article_type.lower().strip()
    lines = profile.read_text(encoding="utf-8").splitlines()
    candidates: list[int] = []
    unreadable: list[int] = []
    # 1) a table row of this article type, under the body word-limit column.
    for lineno, cell in _table_caps(lines, want):
        nums = {int(m.group(1).replace(",", "")) for m in CELL_INT_RE.finditer(cell)}
        if len(nums) == 1:
            candidates.append(nums.pop())
        else:
            unreadable.append(lineno)
    # 2) only when no table carries the type: a LIST ITEM that starts with the label.
    lead = re.compile(r"^\s*(?:[-*+]|[0-9]+[.)])\s+[*_`]*" + re.escape(want), re.IGNORECASE)
    for line in ([] if (candidates or unreadable) else lines):
        if "|" in line or not lead.match(line):
            continue
        nums = [int(m.group(1).replace(",", "")) for m in PROFILE_LIMIT_RE.finditer(line)]
        if nums:
            candidates.append(nums[0])
    uniq = sorted(set(candidates))
    if len(uniq) != 1 or unreadable:
        why = (f"found {uniq or 'none'}"
               + (f"; ambiguous table row(s) at line {', '.join(map(str, unreadable))}"
                  if unreadable else ""))
        sys.stderr.write(
            f"ERROR: could not read a single body word cap for article type "
            f"'{article_type}' from a structured field of {profile.name} ({why}). "
            f"Pass --limit N explicitly.\n")
        sys.exit(2)
    return uniq[0]


# --- core ------------------------------------------------------------------

def analyze(manuscript: Path, limit: int, citation_expansion: float,
            near_threshold: float, rendered_words: int | None) -> dict:
    if not manuscript.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    body_words, n_cites, heading_words = measure_body(manuscript)
    if rendered_words is not None:
        effective = rendered_words
        basis = "rendered_words (authoritative)"
    else:
        effective = body_words + round(n_cites * citation_expansion)
        basis = f"body_words + {n_cites} citations x {citation_expansion}"
    ratio = effective / limit if limit else 0.0
    if effective > limit:
        verdict, severity = "WORDCOUNT_OVER_CAP", "Major"
    elif effective > near_threshold * limit:
        verdict, severity = "WORDCOUNT_NEAR_CAP", "Minor"
    else:
        verdict, severity = "OK", None
    return {
        "manuscript": str(manuscript),
        "body_words": body_words,
        "heading_words": heading_words,
        "n_inline_citations": n_cites,
        "rendered_words_est": effective,
        "rendered_basis": basis,
        "limit": limit,
        "near_threshold": near_threshold,
        "ratio": round(ratio, 4),
        "verdict": verdict,
        "severity": severity,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Body word count vs journal cap gate.")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown")
    ap.add_argument("--limit", type=int, help="body word cap (preferred; deterministic)")
    ap.add_argument("--journal-profile", help="find-journal profile .md to parse the cap from")
    ap.add_argument("--article-type", default="Original",
                    help="article-type label to match in the profile (default: 'Original')")
    ap.add_argument("--rendered-words", type=int,
                    help="authoritative rendered (DOCX) body word count; overrides the estimate")
    ap.add_argument("--citation-expansion", type=float, default=1.6,
                    help="rendered words added per inline citation (citeproc expansion; default 1.6)")
    ap.add_argument("--near-threshold", type=float, default=0.95,
                    help="fraction of the cap that triggers WORDCOUNT_NEAR_CAP (default 0.95)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if over cap")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout summary")
    args = ap.parse_args()

    if args.limit is None and not args.journal_profile:
        sys.stderr.write("ERROR: pass --limit N or --journal-profile <path>\n")
        return 2
    limit = args.limit
    if limit is None:
        limit = parse_cap_from_profile(Path(args.journal_profile), args.article_type)

    result = analyze(Path(args.manuscript), limit, args.citation_expansion,
                     args.near_threshold, args.rendered_words)

    if not args.quiet:
        print("=" * 41)
        print(" Word-Count vs Journal Cap")
        print("=" * 41)
        print(f"body words (md)      : {result['body_words']:,}")
        print(f"  of which subheadings: {result['heading_words']:,}")
        print(f"inline citations     : {result['n_inline_citations']:,}")
        print(f"rendered est         : {result['rendered_words_est']:,}  [{result['rendered_basis']}]")
        print(f"journal cap          : {result['limit']:,}  (ratio {result['ratio']:.2f})")
        if result["verdict"] == "WORDCOUNT_OVER_CAP":
            print(f"\nMAJOR: body exceeds the cap by {result['rendered_words_est'] - result['limit']:,} "
                  f"words. Relocate methods/sensitivity detail to the Supplement; the binding "
                  f"number is the rendered DOCX count.")
        elif result["verdict"] == "WORDCOUNT_NEAR_CAP":
            print(f"\nMINOR: body is within {round((1 - result['ratio']) * 100)}% of the cap — a "
                  f"further revise pass will likely breach it.")
        else:
            print("\nOK: body is within the journal cap.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_wordcount_cap", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["verdict"] == "WORDCOUNT_OVER_CAP") else 0


if __name__ == "__main__":
    sys.exit(main())

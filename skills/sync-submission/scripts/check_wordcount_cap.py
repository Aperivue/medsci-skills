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
here so this script is self-contained), and compares it to a word cap.

THE BINDING NUMBER IS THE RENDERED WORD COUNT. pandoc citeproc expands each
`[@key]` to "(Author Year)", so the rendered DOCX counts higher than the markdown.
This gate approximates the rendered count as `body_words + n_inline_citations *
--citation-expansion` (default 1.6). When you have the authoritative rendered
count (e.g. Word's count on the built DOCX), pass it with `--rendered-words N` and
that is used verbatim.

CAP SOURCE
  --limit N                 the body word cap (deterministic; preferred).
  --journal-profile P       a find-journal profile .md; the cap is parsed from the
    [--article-type T]      article-type line (default match: "Original"). If the
                            cap cannot be parsed to a single integer, the script
                            errors and asks for --limit (no fuzzy guessing).

OUTPUT
  stdout summary and, with --out, a JSON artifact:
    {manuscript, body_words, n_inline_citations, rendered_words_est, limit,
     near_threshold, ratio, verdict}
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

# --- measurement (vendored from cover_letter_drift_check.py; keep in sync) -----

SKIP_SECTION_RE = re.compile(
    r"^#{1,3}\s+\*{0,2}\s*("
    r"Abstract|References?|Table\s+Captions?|Table\s+Legends?|Figure\s+Legends?|"
    r"Tables?|Figures?|Supplementary\s+(Materials?|Tables?|Figures?|Appendix)|"
    r"Acknowled[gd]e?ments?|Funding|Conflicts?\s+of\s+Interest|COI|"
    r"Author\s+Contributions?|Data\s+Availability|Code\s+Availability|"
    r"AI\s+Disclosure|Artificial\s+Intelligence\s+Disclosure"
    r")\s*\*{0,2}\s*:?\s*$",
    re.IGNORECASE,
)
YAML_FENCE_RE = re.compile(r"^---\s*$")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'./%\-]*")
# pandoc inline citations: [@key], [@k1; @k2], [-@k]. Count each @key.
CITE_RE = re.compile(r"@[A-Za-z0-9_][A-Za-z0-9_:.\-]*")
HEADER_RE = re.compile(r"^#{1,3}\s")


def _strip_yaml_front_matter(lines: list[str]) -> list[str]:
    if not lines or not YAML_FENCE_RE.match(lines[0].rstrip()):
        return lines
    for i, line in enumerate(lines[1:], start=1):
        if YAML_FENCE_RE.match(line.rstrip()):
            return lines[i + 1:]
    return lines


def measure_body(manuscript_path: Path) -> tuple[int, int]:
    """Return (body_words, n_inline_citations) over the non-skipped body."""
    lines = manuscript_path.read_text(encoding="utf-8").splitlines()
    body_lines = _strip_yaml_front_matter(lines)
    in_skip = False
    in_code_fence = False
    words = 0
    cites = 0
    for line in body_lines:
        stripped = line.rstrip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        if HEADER_RE.match(stripped):
            in_skip = bool(SKIP_SECTION_RE.match(stripped))
            continue
        if in_skip:
            continue
        if stripped.startswith("|") or stripped.startswith("<!--"):
            continue
        cites += len(CITE_RE.findall(stripped))
        # Don't count the citation tokens themselves as prose words.
        prose = CITE_RE.sub(" ", stripped)
        words += len(WORD_RE.findall(prose))
    return words, cites


# --- cap from a journal profile --------------------------------------------

# "Original Article (4,000 words ...)" / "Original Research Article (≤ 5,000 words ...)"
PROFILE_LIMIT_RE = re.compile(r"(?:≤|<=|<|up to|max(?:imum)?)?\s*([0-9][0-9,]{2,})\s*[- ]?words?",
                              re.IGNORECASE)


def parse_cap_from_profile(profile: Path, article_type: str) -> int:
    if not profile.is_file():
        sys.stderr.write(f"ERROR: journal profile not found: {profile}\n")
        sys.exit(2)
    want = article_type.lower()
    candidates: list[int] = []
    for line in profile.read_text(encoding="utf-8").splitlines():
        if want in line.lower():
            nums = [int(m.group(1).replace(",", "")) for m in PROFILE_LIMIT_RE.finditer(line)]
            # the first "N words" on the article-type line is the body cap
            if nums:
                candidates.append(nums[0])
    uniq = sorted(set(candidates))
    if len(uniq) != 1:
        sys.stderr.write(
            f"ERROR: could not parse a single body word cap for article type "
            f"'{article_type}' from {profile.name} (found {uniq or 'none'}). "
            f"Pass --limit N explicitly.\n")
        sys.exit(2)
    return uniq[0]


# --- core ------------------------------------------------------------------

def analyze(manuscript: Path, limit: int, citation_expansion: float,
            near_threshold: float, rendered_words: int | None) -> dict:
    if not manuscript.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    body_words, n_cites = measure_body(manuscript)
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
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["verdict"] == "WORDCOUNT_OVER_CAP") else 0


if __name__ == "__main__":
    sys.exit(main())

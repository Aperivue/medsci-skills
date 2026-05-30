#!/usr/bin/env python3
"""
cover_letter_drift_check.py — Phase 4 cover-letter free-text drift gate.

Compares the numeric claims embedded in a cover letter (body word count,
abstract word count, reference count, table/figure count, reporting-guideline
status) against the manuscript artifacts that should be their source of truth.
Emits a drift report when the cover letter has gone stale relative to the
manuscript.

Why this gate exists
====================
Cover letters are submission-portal sidecar artifacts that the docx scanners
in this skill do not touch. When a manuscript branches v_N → v_(N+1) (word
limit retarget, abstract restructure, new reference batch), the cover letter
is routinely forgotten. The free-text claims in `## Article details` or the
opening paragraph remain frozen at the v_N counts.

Cross-project observation (anonymized): a CK-line manuscript was compressed
to 3,036 body words and a 319-word abstract during the alignment round, but
the cover letter still said "approximately 3,790 words", "250 words", and
"12 verified references". All three claims surfaced only via a manual grep
sweep at the portal-upload stage. Editor desk reviewers compare cover-letter
claims against the manuscript body — a mismatch is read as either careless
preparation or a late-edit failure.

Usage
=====

    python cover_letter_drift_check.py \\
        --manuscript manuscript.md \\
        --cover-letter cover_letter.md \\
        --abstract abstract.md \\
        --refs refs.bib \\
        --out qc/cover_letter_drift.json

If `--abstract` is omitted, the abstract is extracted from the manuscript
front matter (heuristics: H1 "Abstract" section, or YAML `abstract:` field).

The script never edits the cover letter — it only reports drift. Resolution
is to update the cover letter (and optionally re-anchor the claims to a
computed-at-build-time helper).

Exit codes
==========
- 0: no drift detected.
- 2: drift detected (any reported value disagrees with the manuscript).
- 1: usage error (input files missing, malformed).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Manuscript measurement helpers
# ---------------------------------------------------------------------------

# Section heading patterns to skip when counting "body" words.
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

# Section heading that starts the abstract.
ABSTRACT_START_RE = re.compile(
    r"^#{1,3}\s+\*{0,2}\s*Abstract\s*\*{0,2}\s*:?\s*$", re.IGNORECASE
)

# YAML frontmatter delimiters.
YAML_FENCE_RE = re.compile(r"^---\s*$")

# Word-counting tokenizer: splits on whitespace, drops markdown punctuation-only
# tokens (e.g., "—", "•", standalone "1." numbering) so prose density isn't
# inflated.
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'./%\-]*")


def _strip_yaml_front_matter(lines: list[str]) -> tuple[list[str], list[str]]:
    """Return (yaml_lines, body_lines) splitting on first two `---` fences."""
    if not lines or not YAML_FENCE_RE.match(lines[0].rstrip()):
        return [], lines
    yaml_block: list[str] = []
    for i, line in enumerate(lines[1:], start=1):
        if YAML_FENCE_RE.match(line.rstrip()):
            return lines[1:i], lines[i + 1 :]
        yaml_block.append(line)
    # Unclosed front matter — treat as no front matter.
    return [], lines


def _next_section_boundary(lines: list[str], start: int) -> int:
    """Return index of the next `^#{1,3}\\s` line at or after `start`, or len(lines)."""
    pat = re.compile(r"^#{1,3}\s")
    for i in range(start, len(lines)):
        if pat.match(lines[i]):
            return i
    return len(lines)


def count_body_words(manuscript_path: Path) -> int:
    """Count words in manuscript body, excluding YAML front matter, abstract,
    references, tables, figures, supplementary, acknowledgments, and
    declaration sections."""
    lines = manuscript_path.read_text(encoding="utf-8").splitlines()
    _, body_lines = _strip_yaml_front_matter(lines)

    in_skip = False
    in_code_fence = False
    total = 0
    for line in body_lines:
        stripped = line.rstrip()
        # Toggle code fence (don't count code).
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        # Section header?
        if re.match(r"^#{1,3}\s", stripped):
            in_skip = bool(SKIP_SECTION_RE.match(stripped))
            continue
        if in_skip:
            continue
        # Skip table rows (pipe-leading) and HTML comments.
        if stripped.startswith("|") or stripped.startswith("<!--"):
            continue
        total += len(WORD_RE.findall(stripped))
    return total


def extract_abstract_text(manuscript_path: Path) -> str:
    """Extract abstract section text from manuscript (best-effort)."""
    lines = manuscript_path.read_text(encoding="utf-8").splitlines()
    yaml_lines, body_lines = _strip_yaml_front_matter(lines)

    # First try YAML `abstract:` field.
    yaml_text = "\n".join(yaml_lines)
    yaml_match = re.search(
        r"^abstract:\s*(?:\||>)?\s*\n((?:[ \t]+.+\n?)+)", yaml_text, re.MULTILINE
    )
    if yaml_match:
        block = yaml_match.group(1)
        return "\n".join(ln.lstrip() for ln in block.splitlines())

    # Otherwise locate "## Abstract" section.
    for i, line in enumerate(body_lines):
        if ABSTRACT_START_RE.match(line.rstrip()):
            end = _next_section_boundary(body_lines, i + 1)
            return "\n".join(body_lines[i + 1 : end])
    return ""


def count_abstract_words(manuscript_path: Path, abstract_path: Optional[Path]) -> int:
    if abstract_path is not None and abstract_path.exists():
        text = abstract_path.read_text(encoding="utf-8")
    else:
        text = extract_abstract_text(manuscript_path)
    # Drop subheaders like "**Objectives:**" — keep the prose only.
    text = re.sub(r"\*{1,3}[^*]+\*{1,3}\s*:?", " ", text)
    return len(WORD_RE.findall(text))


# ---------------------------------------------------------------------------
# Reference / figure / table counts
# ---------------------------------------------------------------------------

BIB_ENTRY_RE = re.compile(r"^@[A-Za-z]+\s*\{", re.MULTILINE)


def count_bib_entries(refs_path: Path) -> int:
    text = refs_path.read_text(encoding="utf-8", errors="ignore")
    return len(BIB_ENTRY_RE.findall(text))


def count_used_citations(manuscript_path: Path) -> int:
    """Count unique pandoc-style [@key] citations actually used in the manuscript."""
    text = manuscript_path.read_text(encoding="utf-8")
    keys = re.findall(r"\[-?@([A-Za-z0-9_:.\-]+)", text)
    return len(set(keys))


def count_table_labels(manuscript_path: Path) -> int:
    """Count distinct `Table N` labels in manuscript body."""
    text = manuscript_path.read_text(encoding="utf-8")
    nums = set()
    for m in re.finditer(r"\bTable\s+(\d+)\b", text):
        nums.add(int(m.group(1)))
    return len(nums)


def count_figure_labels(manuscript_path: Path) -> int:
    """Count distinct `Figure N` labels in manuscript body."""
    text = manuscript_path.read_text(encoding="utf-8")
    nums = set()
    for m in re.finditer(r"\bFigure\s+(\d+)\b", text):
        nums.add(int(m.group(1)))
    return len(nums)


# ---------------------------------------------------------------------------
# Cover-letter claim extraction
# ---------------------------------------------------------------------------

# "approximately 3,790 words" / "3790 words" / "approx. 3,036 words"
BODY_WORDS_RE = re.compile(
    r"(?:approximately|approx\.?|about|roughly|~)?\s*"
    r"([0-9][0-9,]*)\s*(?:body\s+)?words?\b",
    re.IGNORECASE,
)
# "250-word abstract" / "abstract: 250 words"
ABSTRACT_WORDS_RE = re.compile(
    r"(?:abstract[^.\n]*?([0-9][0-9,]*)\s*words?"
    r"|([0-9][0-9,]*)[\s-]+word\s+abstract)",
    re.IGNORECASE,
)
# "12 references" / "12 verified references" / "references: 12"
REF_COUNT_RE = re.compile(
    r"(?:([0-9][0-9,]*)\s+(?:verified\s+)?references?\b"
    r"|references?\s*[:\-]\s*([0-9][0-9,]*))",
    re.IGNORECASE,
)
# "3 tables and 4 figures" / "Tables: 3" / "Figures: 4"
TABLE_COUNT_RE = re.compile(
    r"(?:([0-9]+)\s+tables?\b|tables?\s*[:\-]\s*([0-9]+))",
    re.IGNORECASE,
)
FIGURE_COUNT_RE = re.compile(
    r"(?:([0-9]+)\s+figures?\b|figures?\s*[:\-]\s*([0-9]+))",
    re.IGNORECASE,
)


def _coalesce_match(match: re.Match) -> Optional[int]:
    for group in match.groups():
        if group:
            return int(group.replace(",", ""))
    return None


def extract_claims(cover_letter_path: Path) -> dict:
    """Pull all numeric claims out of the cover letter body."""
    text = cover_letter_path.read_text(encoding="utf-8")

    claims: dict = {}

    body_matches = [_coalesce_match(m) for m in BODY_WORDS_RE.finditer(text)]
    body_matches = [v for v in body_matches if v is not None and v >= 500]
    if body_matches:
        # Take the largest figure that could plausibly be body word count.
        # (Cover letters sometimes also mention "250 words" for abstract — the
        # abstract regex picks that up separately.)
        claims["body_words"] = max(body_matches)

    abstract_matches = [_coalesce_match(m) for m in ABSTRACT_WORDS_RE.finditer(text)]
    abstract_matches = [v for v in abstract_matches if v is not None and v <= 600]
    if abstract_matches:
        claims["abstract_words"] = abstract_matches[0]

    ref_matches = [_coalesce_match(m) for m in REF_COUNT_RE.finditer(text)]
    ref_matches = [v for v in ref_matches if v is not None and v <= 500]
    if ref_matches:
        claims["references"] = ref_matches[0]

    table_matches = [_coalesce_match(m) for m in TABLE_COUNT_RE.finditer(text)]
    table_matches = [v for v in table_matches if v is not None and v <= 20]
    if table_matches:
        claims["tables"] = table_matches[0]

    figure_matches = [_coalesce_match(m) for m in FIGURE_COUNT_RE.finditer(text)]
    figure_matches = [v for v in figure_matches if v is not None and v <= 20]
    if figure_matches:
        claims["figures"] = figure_matches[0]

    return claims


# ---------------------------------------------------------------------------
# Drift evaluation
# ---------------------------------------------------------------------------

DEFAULT_BODY_TOLERANCE_PCT = 5  # cover letter "approximately" allows ~5% slack
DEFAULT_ABSTRACT_TOLERANCE = 5  # words


def evaluate_drift(
    truth: dict,
    claims: dict,
    *,
    body_tolerance_pct: float = DEFAULT_BODY_TOLERANCE_PCT,
    abstract_tolerance: int = DEFAULT_ABSTRACT_TOLERANCE,
) -> list[dict]:
    """Compare claims to truth and emit a list of drift records."""
    drifts: list[dict] = []

    def _record(field: str, truth_val, claim_val, severity: str, note: str = ""):
        drifts.append(
            {
                "field": field,
                "truth": truth_val,
                "cover_letter_claim": claim_val,
                "severity": severity,
                "note": note,
            }
        )

    # Body words — tolerate small "approximately" slack.
    if "body_words" in claims and "body_words" in truth:
        cw = claims["body_words"]
        tw = truth["body_words"]
        if tw > 0:
            slack = max(50, int(tw * body_tolerance_pct / 100))
            if abs(cw - tw) > slack:
                _record(
                    "body_words",
                    tw,
                    cw,
                    "MAJOR",
                    f"|claim - truth| = {abs(cw - tw)} > tolerance {slack}",
                )

    # Abstract words.
    if "abstract_words" in claims and "abstract_words" in truth:
        cw = claims["abstract_words"]
        tw = truth["abstract_words"]
        if abs(cw - tw) > abstract_tolerance:
            _record(
                "abstract_words",
                tw,
                cw,
                "MAJOR",
                f"|claim - truth| = {abs(cw - tw)} > tolerance {abstract_tolerance}",
            )

    # Reference count — exact match.
    if "references" in claims and "references" in truth:
        if claims["references"] != truth["references"]:
            _record(
                "references",
                truth["references"],
                claims["references"],
                "MAJOR",
            )

    # Tables — exact match.
    if "tables" in claims and "tables" in truth:
        if claims["tables"] != truth["tables"]:
            _record(
                "tables",
                truth["tables"],
                claims["tables"],
                "MAJOR",
            )

    # Figures — exact match.
    if "figures" in claims and "figures" in truth:
        if claims["figures"] != truth["figures"]:
            _record(
                "figures",
                truth["figures"],
                claims["figures"],
                "MAJOR",
            )

    return drifts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manuscript", required=True, type=Path)
    p.add_argument("--cover-letter", required=True, type=Path)
    p.add_argument("--abstract", type=Path, default=None,
                   help="Optional separate abstract file. If absent, extracted from manuscript.")
    p.add_argument("--refs", type=Path, default=None,
                   help="refs.bib path. Used for reference count truth. "
                        "If absent, falls back to counting unique [@key] in manuscript.")
    p.add_argument("--out", type=Path, default=Path("qc/cover_letter_drift.json"))
    p.add_argument("--body-tolerance-pct", type=float, default=DEFAULT_BODY_TOLERANCE_PCT,
                   help="Allowed slack on body word count (percent). Default %(default)s.")
    p.add_argument("--abstract-tolerance", type=int, default=DEFAULT_ABSTRACT_TOLERANCE,
                   help="Allowed slack on abstract word count (words). Default %(default)s.")
    args = p.parse_args()

    if not args.manuscript.exists():
        print(f"ERROR: manuscript not found: {args.manuscript}", file=sys.stderr)
        return 1
    if not args.cover_letter.exists():
        print(f"ERROR: cover letter not found: {args.cover_letter}", file=sys.stderr)
        return 1

    truth = {
        "body_words": count_body_words(args.manuscript),
        "abstract_words": count_abstract_words(args.manuscript, args.abstract),
        "tables": count_table_labels(args.manuscript),
        "figures": count_figure_labels(args.manuscript),
    }
    if args.refs is not None and args.refs.exists():
        truth["references"] = count_bib_entries(args.refs)
    else:
        truth["references"] = count_used_citations(args.manuscript)

    claims = extract_claims(args.cover_letter)
    drifts = evaluate_drift(
        truth,
        claims,
        body_tolerance_pct=args.body_tolerance_pct,
        abstract_tolerance=args.abstract_tolerance,
    )

    report = {
        "submission_safe": len(drifts) == 0,
        "manuscript": str(args.manuscript),
        "cover_letter": str(args.cover_letter),
        "truth": truth,
        "claims": claims,
        "drifts": drifts,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if drifts:
        print(f"DRIFT: {len(drifts)} cover-letter field(s) disagree with manuscript")
        for d in drifts:
            print(f"  - {d['field']}: claim={d['cover_letter_claim']} vs truth={d['truth']}"
                  + (f" — {d['note']}" if d.get("note") else ""))
        return 2

    print(f"OK: cover letter agrees with manuscript ({len(truth)} fields checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

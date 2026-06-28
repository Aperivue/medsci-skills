#!/usr/bin/env python3
"""Model Card / Datasheet completeness gate (model-card).

A documentation-completeness linter for an AI model's Model Card (Mitchell et al.,
ACM FAccT 2019) and, optionally, its dataset Datasheet (Gebru et al., Commun. ACM
2021). It verifies that every required section is **present** and **non-empty** — i.e.
not missing and not left as an unfilled `[NEEDS INPUT]` / TODO placeholder. It is a
presence check (the documentation analogue of check_disclosure_availability /
check_summary_box); it does NOT judge whether a stated fact is true (that is
/model-validation and the human).

CHECKS (verdicts):
  1. MISSING_SECTION        (Major)  a required section heading is absent.
  2. EMPTY_REQUIRED_SECTION (Major)  a required section is present but has no real
                                     content — empty, or every content line is an
                                     unfilled placeholder ([NEEDS INPUT] / TODO /
                                     [VERIFY] / XXXX / <...>).

Required Model Card sections: Model Details, Intended Use, Out-of-Scope Use,
Training Data, Evaluation Data, Metrics, Quantitative Analyses, Ethical
Considerations, Caveats and Recommendations.
Required Datasheet sections (with --datasheet): Motivation, Composition, Collection
Process, Preprocessing / Cleaning / Labeling, Uses, Distribution, Maintenance.

INPUTS
  --card       MODEL_CARD.md (required).
  --datasheet  DATASHEET.md (optional; if given, its sections are checked too).

OUTPUT
  A table (stdout) and, with --out, a JSON artifact:
    {card, datasheet, claims[{verdict, severity, detail, where}], summary}
  Both verdicts are Major.

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A full unfilled-placeholder SPAN: the entire `[NEEDS INPUT ...]` / `[VERIFY ...]` bracket
# (so the descriptive hint inside it is removed too), plus standalone TODO / TBD / <...> / XXXX.
PLACEHOLDER_SPAN = re.compile(
    r"\[(?:NEEDS INPUT|VERIFY)[^\]]*\]|<[^>]*>|\bTODO\b|\bTBD\b|X{4,}", re.IGNORECASE)

# canonical key -> (display label, [alias regexes on the normalized heading])
MODEL_CARD_REQUIRED = [
    ("model_details", "Model Details", [r"model details"]),
    ("intended_use", "Intended Use", [r"intended use"]),
    ("out_of_scope", "Out-of-Scope Use", [r"out of scope"]),
    ("training_data", "Training Data", [r"training data"]),
    ("evaluation_data", "Evaluation Data", [r"evaluation data", r"eval data", r"test data"]),
    ("metrics", "Metrics", [r"^metrics$", r"^metrics "]),
    ("quant", "Quantitative Analyses", [r"quantitative analys[ie]s"]),
    ("ethics", "Ethical Considerations", [r"ethical considerations", r"^ethics"]),
    ("caveats", "Caveats and Recommendations", [r"caveats"]),
]
DATASHEET_REQUIRED = [
    ("motivation", "Motivation", [r"^motivation"]),
    ("composition", "Composition", [r"^composition"]),
    ("collection", "Collection Process", [r"collection"]),
    ("preprocessing", "Preprocessing / Cleaning / Labeling",
     [r"preprocessing", r"cleaning", r"labeling", r"labelling"]),
    ("uses", "Uses", [r"^uses$", r"^uses "]),
    ("distribution", "Distribution", [r"^distribution"]),
    ("maintenance", "Maintenance", [r"^maintenance"]),
]


def _norm_heading(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[*_`#]", "", t)
    t = re.sub(r"[^a-z0-9 /]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_sections(text: str) -> list[tuple[str, str]]:
    """Return [(normalized_heading, body_text)] for each ATX heading in order."""
    lines = text.splitlines()
    sections = []
    cur_h, cur_body = None, []
    for ln in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            if cur_h is not None:
                sections.append((cur_h, "\n".join(cur_body)))
            cur_h = _norm_heading(m.group(2))
            cur_body = []
        elif cur_h is not None:
            cur_body.append(ln)
    if cur_h is not None:
        sections.append((cur_h, "\n".join(cur_body)))
    return sections


def _has_real_content(body: str) -> bool:
    """True if the section carries a filled value — not empty and not only unfilled
    placeholders / field labels. The body is flattened (so a placeholder wrapped across
    lines is still removed as one span), HTML comments are dropped, then unfilled-placeholder
    spans and bold field-labels ('**Source**:') are removed; what remains is the real value."""
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.DOTALL)         # drop HTML comments
    text = " ".join(body.split())                                    # flatten line wraps
    if not text:
        return False
    text = PLACEHOLDER_SPAN.sub(" ", text)                           # remove [NEEDS INPUT ...] etc.
    text = re.sub(r"\*\*[^*]+\*\*:?", " ", text)                     # remove bold field labels
    text = re.sub(r"[*_`>#]+", " ", text)                            # strip residual markdown
    low = text.lower()
    if re.search(r"\b(n/?a|none|not applicable|not collected|nil|waived)\b", low):
        return True                                                 # an explicit "empty" answer is filled
    core = re.sub(r"[^a-z0-9]+", "", low)
    return len(core) >= 3                                            # a real value remains


def _check_doc(path: Path, required, label: str) -> list[dict]:
    claims = []
    sections = parse_sections(path.read_text(encoding="utf-8"))
    for key, disp, aliases in required:
        match = None
        for norm_h, body in sections:
            if any(re.search(a, norm_h) for a in aliases):
                match = (norm_h, body)
                break
        if match is None:
            claims.append({
                "verdict": "MISSING_SECTION", "severity": "Major",
                "detail": f"{label}: required section '{disp}' is absent",
                "where": path.name,
            })
        elif not _has_real_content(match[1]):
            claims.append({
                "verdict": "EMPTY_REQUIRED_SECTION", "severity": "Major",
                "detail": f"{label}: section '{disp}' is present but empty / only an unfilled "
                          f"placeholder ([NEEDS INPUT] etc.)",
                "where": path.name,
            })
    return claims


def analyze(card: str, datasheet: str | None) -> dict:
    claims = _check_doc(Path(card), MODEL_CARD_REQUIRED, "Model Card")
    if datasheet:
        claims += _check_doc(Path(datasheet), DATASHEET_REQUIRED, "Datasheet")
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "card": card, "datasheet": datasheet, "claims": claims,
        "summary": {"n_claims": len(claims), "n_major": n_major,
                    "verdict": "MAJOR_CANDIDATE" if n_major else "OK"},
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | all required sections present and filled |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Model Card / Datasheet completeness gate.")
    ap.add_argument("--card", required=True, help="MODEL_CARD.md")
    ap.add_argument("--datasheet", help="DATASHEET.md (optional)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    for label, p in (("--card", args.card), ("--datasheet", args.datasheet)):
        if p and not Path(p).is_file():
            sys.stderr.write(f"ERROR: {label} not found: {p}\n")
            return 2

    result = analyze(args.card, args.datasheet)

    if not args.quiet:
        print("=" * 41)
        print(" Model Card / Datasheet Completeness")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        print(f"MAJOR candidate: {s['n_major']} incomplete-documentation issue(s)." if s["n_major"]
              else "OK: all required Model Card / Datasheet sections present and filled.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

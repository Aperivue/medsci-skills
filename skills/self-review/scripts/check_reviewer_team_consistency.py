#!/usr/bin/env python3
"""
check_reviewer_team_consistency.py — fabrication-grade self-review check.

Detects manuscripts that simultaneously claim dual independent reviewers
(in Methods + PROSPERO) and confess to single-reviewer execution (in
Discussion §Limitations). Either claim alone is fine; the conjunction is
a fabrication-grade red flag.

Why this check exists
=====================
Cross-project precedent (anonymized): a reporting-quality SR-of-AI-tools
manuscript had:
- Methods: "Two reviewers independently screened titles and abstracts ..."
- PROSPERO record: "Two independent reviewers will perform full-text
  screening and data extraction."
- Discussion §Limitations: "Single primary reviewer; a 20% sample by an
  additional reviewer is deferred to before submission."

The conjunction admits in Limitations what Methods denies in narrative
form. Reviewers and editors who notice this read it as fabrication-grade
(the manuscript misrepresents what was actually done) and reject.

Detection strategy
==================
Section-aware grep for two regex families:
- DUAL claim: "(independently|dual|two reviewers|both reviewers|two
  independent)" within Methods OR a PROSPERO record file.
- SINGLE confession: "(single primary reviewer|one additional reviewer|
  20% sample|sample of records|deferred to before submission|due to
  resource constraints|by the first reviewer alone)" within Limitations
  OR Discussion.

Both present → MAJOR self-review red flag.

Two further fabrication-grade axes (the prose↔JSON↔confession 3-way):
- LLM-AS-REVIEWER (fatal): a per-study extraction JSON whose reviewer /
  screener / extractor / rater field is an LLM ("Claude", "GPT-4", "LLM",
  "Gemini"). An LLM is a tool, not an independent reviewer; listing it as
  one misrepresents the screening team regardless of the prose. Pass the
  extraction JSON (file or directory) via --extraction-json.
- DEFERRED-MITIGATION (MAJOR): a future-tense mitigation promise — "a 20%
  sample will be completed before submission" — that is unmet at the time
  the manuscript circulates. The promise is evidence the work is not done.

Usage
=====

    python check_reviewer_team_consistency.py \\
        --manuscript manuscript.md \\
        --prospero prospero/record.md \\
        --out _audit_self/reviewer_team_consistency.md

Output
======
Markdown report at `--out` summarizing matches. Also a JSON sidecar at
`--out` + ".json".

Exit codes
==========
  0  no conflict
  1  MAJOR red flag detected (both DUAL and SINGLE patterns present)
  2  invocation error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


DUAL_PATTERNS = [
    (
        re.compile(r"\btwo\s+(?:independent\s+)?reviewers?\b", re.IGNORECASE),
        "two reviewers",
    ),
    (re.compile(r"\bdual\s+(?:independent\s+)?(?:reviewers?|extractors?)\b", re.IGNORECASE),
     "dual reviewers"),
    (re.compile(r"\bindependent(?:ly)?\s+screened\b", re.IGNORECASE), "independently screened"),
    (
        re.compile(r"\bboth\s+reviewers?\s+(?:independently|extracted|screened)\b", re.IGNORECASE),
        "both reviewers",
    ),
    (
        re.compile(r"\bindependent(?:ly)?\s+(?:extracted|coded|assessed)\b", re.IGNORECASE),
        "independent extraction",
    ),
    (
        re.compile(r"\bindependent\s+reviewers?\b", re.IGNORECASE),
        "independent reviewers",
    ),
]

SINGLE_PATTERNS = [
    (re.compile(r"\bsingle\s+primary\s+reviewer\b", re.IGNORECASE), "single primary reviewer"),
    (
        re.compile(r"\bone\s+additional\s+reviewer\b", re.IGNORECASE),
        "one additional reviewer",
    ),
    (
        re.compile(r"\b20\s*%?\s+sample\b", re.IGNORECASE),
        "20% sample",
    ),
    (
        re.compile(r"\bsample\s+of\s+records\b", re.IGNORECASE),
        "sample of records",
    ),
    (
        re.compile(r"\bdeferred\s+to\s+before\s+submission\b", re.IGNORECASE),
        "deferred to before submission",
    ),
    (
        re.compile(r"\bdue\s+to\s+resource\s+constraints\b", re.IGNORECASE),
        "due to resource constraints",
    ),
    (
        re.compile(r"\b(?:by|with)\s+(?:the\s+)?first\s+reviewer\s+(?:alone|only)\b", re.IGNORECASE),
        "first reviewer alone",
    ),
]


# An LLM named where an independent reviewer should be (fatal). Bare "ai" is too
# broad (matches names), so it is excluded; explicit model families + "LLM" only.
LLM_NAME_RE = re.compile(
    r"\b(?:claude|chatgpt|gpt-?\d|gpt|llm|large language model|gemini|copilot|bard|"
    r"ai model|an ai\b)\b", re.IGNORECASE)
REVIEWER_KEY_RE = re.compile(
    r"reviewer|screener|extractor|rater|annotator|adjudicator|coder", re.IGNORECASE)

# A future-tense mitigation promised but not yet executed at circulation.
DEFERRED_MITIGATION_RE = re.compile(
    r"(?:will be|to be|is to be|are to be)\s+"
    r"(?:completed|performed|conducted|done|undertaken|carried out|finalized|finalised)\b"
    r"[^.]{0,80}?(?:before|prior to|ahead of)\s+(?:final\s+)?submission",
    re.IGNORECASE)


SECTION_HEADERS = {
    "Methods": re.compile(
        r"^#{1,3}\s*\*{0,2}(?:METHODS?|Method[s]?|Materials and Methods)\*{0,2}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Discussion": re.compile(
        r"^#{1,3}\s*\*{0,2}(?:DISCUSSION|Discussion)\*{0,2}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Limitations": re.compile(
        r"^#{1,3}\s*\*{0,2}(?:LIMITATIONS?|Limitations?|Study Limitations)\*{0,2}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
}


@dataclass
class Hit:
    pattern_label: str
    line: int
    context: str


@dataclass
class Report:
    submission_safe: bool
    dual_hits: list[dict] = field(default_factory=list)
    single_hits: list[dict] = field(default_factory=list)
    llm_reviewer_hits: list[dict] = field(default_factory=list)
    deferred_mitigation_hits: list[dict] = field(default_factory=list)


def split_sections(text: str) -> dict[str, str]:
    out: dict[str, str] = {name: "" for name in SECTION_HEADERS}
    headers: list[tuple[str, int, int]] = []
    for name, pat in SECTION_HEADERS.items():
        for m in pat.finditer(text):
            headers.append((name, m.start(), m.end()))
    headers.sort(key=lambda t: t[1])
    for i, (name, _, hdr_end) in enumerate(headers):
        end = headers[i + 1][1] if i + 1 < len(headers) else len(text)
        out[name] = (out[name] + "\n" + text[hdr_end:end]).strip()
    return out


def scan_text(text: str, patterns: list[tuple[re.Pattern[str], str]]) -> list[Hit]:
    hits: list[Hit] = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        for pat, label in patterns:
            if pat.search(line):
                ctx = line.strip()
                if len(ctx) > 200:
                    ctx = ctx[:200] + "..."
                hits.append(Hit(pattern_label=label, line=lineno, context=ctx))
    return hits


def hit_to_dict(h: Hit, source: str) -> dict:
    return {
        "source": source,
        "pattern": h.pattern_label,
        "line": h.line,
        "context": h.context,
    }


def _iter_extraction_files(path: Path):
    if path.is_dir():
        yield from sorted(path.rglob("*.json"))
    elif path.is_file():
        yield path


def _walk_reviewer_fields(obj, source: str, hits: list[dict], keypath: str = "") -> None:
    """Recursively find reviewer-role fields whose value names an LLM."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            kp = f"{keypath}.{k}" if keypath else str(k)
            if isinstance(v, str) and REVIEWER_KEY_RE.search(str(k)) and LLM_NAME_RE.search(v):
                hits.append({"source": source, "field": kp, "value": v[:120]})
            _walk_reviewer_fields(v, source, hits, kp)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk_reviewer_fields(v, source, hits, f"{keypath}[{i}]")


def scan_llm_reviewers(extraction: Path | None) -> list[dict]:
    hits: list[dict] = []
    if extraction is None:
        return hits
    for f in _iter_extraction_files(extraction):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        _walk_reviewer_fields(data, f.name, hits)
    return hits


def scan_deferred_mitigation(manuscript: str) -> list[dict]:
    hits: list[dict] = []
    for lineno, line in enumerate(manuscript.splitlines(), start=1):
        m = DEFERRED_MITIGATION_RE.search(line)
        if m:
            hits.append({"source": "manuscript", "line": lineno, "context": m.group(0).strip()[:160]})
    return hits


def build_report(manuscript: str, prospero: str | None,
                 extraction: Path | None = None) -> Report:
    sections = split_sections(manuscript)

    dual_hits: list[dict] = []
    single_hits: list[dict] = []

    # Methods → DUAL evidence.
    for h in scan_text(sections.get("Methods", ""), DUAL_PATTERNS):
        dual_hits.append(hit_to_dict(h, "manuscript:Methods"))

    # PROSPERO → DUAL evidence.
    if prospero is not None:
        for h in scan_text(prospero, DUAL_PATTERNS):
            dual_hits.append(hit_to_dict(h, "prospero"))

    # Discussion & Limitations → SINGLE evidence.
    for region in ("Limitations", "Discussion"):
        for h in scan_text(sections.get(region, ""), SINGLE_PATTERNS):
            single_hits.append(hit_to_dict(h, f"manuscript:{region}"))

    llm_reviewer_hits = scan_llm_reviewers(extraction)
    deferred_hits = scan_deferred_mitigation(manuscript)

    submission_safe = not (
        (dual_hits and single_hits) or llm_reviewer_hits or deferred_hits
    )
    return Report(
        submission_safe=submission_safe,
        dual_hits=dual_hits,
        single_hits=single_hits,
        llm_reviewer_hits=llm_reviewer_hits,
        deferred_mitigation_hits=deferred_hits,
    )


def _render_extra(lines: list[str], report: Report) -> None:
    if report.llm_reviewer_hits:
        lines.append("")
        lines.append("## LLM-AS-REVIEWER (fatal)")
        lines.append("An LLM is named where an independent reviewer is required:")
        for h in report.llm_reviewer_hits:
            lines.append(f"- `{h['source']}` field `{h['field']}` = {h['value']}")
        lines.append("Fix: list a human reviewer; an LLM is a tool, not a member of the review team.")
    if report.deferred_mitigation_hits:
        lines.append("")
        lines.append("## DEFERRED-MITIGATION (MAJOR)")
        lines.append("A mitigation is promised in the future tense but not yet executed:")
        for h in report.deferred_mitigation_hits:
            lines.append(f"- line {h['line']}: {h['context']}")
        lines.append("Fix: execute and report the mitigation before circulation, or remove the claim.")


def render_markdown(report: Report) -> str:
    lines = ["# Reviewer-team consistency audit", ""]
    if report.submission_safe:
        lines.append(
            "Status: **PASS** — no conjunction of DUAL claim + SINGLE confession."
        )
        lines.append("")
        if report.dual_hits:
            lines.append(f"DUAL claims found ({len(report.dual_hits)}, OK alone):")
            for h in report.dual_hits:
                lines.append(f"- `{h['source']}` line {h['line']}: `{h['pattern']}` — {h['context']}")
        if report.single_hits:
            lines.append("")
            lines.append(f"SINGLE confessions found ({len(report.single_hits)}, OK alone):")
            for h in report.single_hits:
                lines.append(f"- `{h['source']}` line {h['line']}: `{h['pattern']}` — {h['context']}")
    else:
        triggers = []
        if report.dual_hits and report.single_hits:
            triggers.append("DUAL claim + SINGLE confession")
        if report.llm_reviewer_hits:
            triggers.append("LLM-as-reviewer")
        if report.deferred_mitigation_hits:
            triggers.append("deferred mitigation")
        lines.append(f"Status: **MAJOR red flag** — {', '.join(triggers)}.")
        lines.append("")
        lines.append("Reviewers will read this as fabrication-grade.")
        if report.dual_hits and report.single_hits:
            lines.append("")
            lines.append("## DUAL claims (Methods / PROSPERO)")
            for h in report.dual_hits:
                lines.append(f"- `{h['source']}` line {h['line']}: `{h['pattern']}`")
                lines.append(f"  > {h['context']}")
            lines.append("")
            lines.append("## SINGLE confessions (Discussion / Limitations)")
            for h in report.single_hits:
                lines.append(f"- `{h['source']}` line {h['line']}: `{h['pattern']}`")
                lines.append(f"  > {h['context']}")
        _render_extra(lines, report)
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reviewer-team consistency check (fabrication-grade self-review)."
    )
    parser.add_argument("--manuscript", type=Path, required=True)
    parser.add_argument("--prospero", type=Path, default=None)
    parser.add_argument(
        "--extraction-json", type=Path, default=None,
        help="per-study extraction JSON file or directory (reviewer-field LLM scan)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("_audit_self/reviewer_team_consistency.md"),
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    if not args.manuscript.is_file():
        print(f"ERROR: manuscript not found: {args.manuscript}", file=sys.stderr)
        return 2
    prospero_text: str | None = None
    if args.prospero is not None:
        if not args.prospero.is_file():
            print(f"ERROR: prospero not found: {args.prospero}", file=sys.stderr)
            return 2
        prospero_text = args.prospero.read_text(encoding="utf-8")
    if args.extraction_json is not None and not args.extraction_json.exists():
        print(f"ERROR: extraction-json not found: {args.extraction_json}", file=sys.stderr)
        return 2

    text = args.manuscript.read_text(encoding="utf-8")
    report = build_report(text, prospero_text, args.extraction_json)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(report), encoding="utf-8")
    json_out = args.out.with_suffix(args.out.suffix + ".json")
    json_out.write_text(
        json.dumps({"detector": "check_reviewer_team_consistency", "submission_safe": report.submission_safe,
                "dual_hits": report.dual_hits,
                "single_hits": report.single_hits,
                "llm_reviewer_hits": report.llm_reviewer_hits,
                "deferred_mitigation_hits": report.deferred_mitigation_hits,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if not args.quiet:
        counts = (f"DUAL={len(report.dual_hits)} SINGLE={len(report.single_hits)} "
                  f"LLM={len(report.llm_reviewer_hits)} "
                  f"DEFERRED={len(report.deferred_mitigation_hits)}")
        if report.submission_safe:
            print(f"PASS: no fabrication-grade conflict. {counts}")
        else:
            print(f"FAIL: MAJOR red flag. {counts}")
            print(f"See {args.out}")

    return 0 if report.submission_safe else 1


if __name__ == "__main__":
    sys.exit(main())

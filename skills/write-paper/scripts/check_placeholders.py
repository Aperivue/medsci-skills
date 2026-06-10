#!/usr/bin/env python3
"""Flag unresolved authoring markers left in a manuscript before submission.

Drafting leaves behind placeholder/marker debris that must never reach a frozen
submission package. Until now these were caught only by grep instructions in
SKILL.md prose (write-paper Phase 0/7, self-review Phase 2.5c); this promotes the
grep to a deterministic gate so a single pre-flight run can halt on them.

Detected finding types:
  new_marker                (blocker) an unresolved [@NEW:topic] citation
                            placeholder — never legitimate in a final manuscript.
  ai_disclosure_placeholder (blocker) a literal [version]/[date]/[tool]/[model]/
                            [channel] token in an AI-use disclosure (the FLAIR/
                            TRIPOD+AI tokens were never filled in).
  generic_todo              (blocker) a TODO / FIXME / TBD / XXX authoring marker
                            outside a fenced code block.
  template_url              (blocker) a template/unfilled URL — example.com,
                            doi.org/XXXX, an empty markdown link ]( ), or a
                            literal [URL]/[link] placeholder.
  bare_numeric_cite         (warn) a bare [N] or [N-N] citation marker. WARN, not
                            blocker, because Vancouver in-text citations are
                            legitimately [N]; in a pandoc [@key] draft it is an
                            unresolved placeholder, so write-paper Phase 0 /
                            self-review escalate it with --strict.

Guards against false positives: fenced code blocks (``` or ~~~) are skipped
entirely, and a References/Bibliography section is skipped for bare_numeric_cite
(numbered reference lists legitimately read "[1] Smith J ...").

INPUTS
  --manuscript   manuscript markdown/text (required).
  --strict       also exit 1 on warn-severity findings (bare_numeric_cite).

OUTPUT
  A findings table (stdout) and, with --out, a JSON artifact:
    {schema_version, source, summary:{blocker,warn}, findings[...], submission_safe}
  submission_safe is true iff there are no blocker-severity findings.

Stdlib-only (json / re / argparse / pathlib). Exit codes: 0 clean (no blocker, and
no warn under --strict), 1 blocker found (or warn under --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- finding patterns --------------------------------------------------------
# Blocker patterns: each match is an unambiguous unresolved authoring marker.
NEW_MARKER = re.compile(r"\[@NEW:[^\]]*\]", re.IGNORECASE)
AI_DISCLOSURE_PLACEHOLDER = re.compile(r"\[(?:version|date|tool|model|channel)\]", re.IGNORECASE)
# TODO/FIXME/TBD and XXX (3+ uppercase X) — case-sensitive so "tbd"/"fix me" inside
# ordinary words or Roman numerals (XXXI) do not trip it.
GENERIC_TODO = re.compile(r"\b(?:TODO|FIXME|TBD|X{3,})\b")
TEMPLATE_URL = re.compile(
    r"https?://(?:www\.)?example\.(?:com|org|net)\S*"
    r"|(?:https?://)?(?:dx\.)?doi\.org/(?:10\.)?X{3,}\S*"
    r"|\]\(\s*\)"
    r"|\[(?:URL|link)\]",
    re.IGNORECASE,
)
# Warn pattern: bare [N] or [N-N]/[N–N] not followed by '(' (so markdown links
# [1](url) are excluded) and not a footnote [^1].
BARE_NUMERIC_CITE = re.compile(r"(?<!\w)\[\d{1,3}(?:\s*[–-]\s*\d{1,3})?\](?!\()")

BLOCKER_PATTERNS = [
    ("new_marker", NEW_MARKER),
    ("ai_disclosure_placeholder", AI_DISCLOSURE_PLACEHOLDER),
    ("generic_todo", GENERIC_TODO),
    ("template_url", TEMPLATE_URL),
]

HEADING_RE = re.compile(r"^#{1,6}\s+(.*\S)\s*$")
REFERENCES_TITLE_RE = re.compile(r"references|bibliography|works cited|reference list", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")


def scan(text: str) -> list[dict]:
    """Line-by-line scan honoring code-fence and references-section guards."""
    findings: list[dict] = []
    in_fence = False
    in_references = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        h = HEADING_RE.match(line.strip())
        if h:
            # entering / leaving a References-style section
            in_references = bool(REFERENCES_TITLE_RE.search(h.group(1).lower()))
        for type_name, pat in BLOCKER_PATTERNS:
            for m in pat.finditer(line):
                findings.append({
                    "type": type_name,
                    "line": lineno,
                    "text": m.group(0).strip()[:120],
                    "severity": "blocker",
                })
        if not in_references:
            for m in BARE_NUMERIC_CITE.finditer(line):
                findings.append({
                    "type": "bare_numeric_cite",
                    "line": lineno,
                    "text": m.group(0).strip()[:120],
                    "severity": "warn",
                })
    return findings


def analyze(manuscript: str) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    findings = scan(p.read_text(encoding="utf-8"))
    n_blocker = sum(1 for f in findings if f["severity"] == "blocker")
    n_warn = len(findings) - n_blocker
    return {
        "schema_version": 1,
        "source": str(p),
        "summary": {"blocker": n_blocker, "warn": n_warn},
        "findings": findings,
        "submission_safe": n_blocker == 0,
    }


def render(result: dict) -> str:
    lines = ["| Line | Type | Severity | Match |", "|---|---|---|---|"]
    for f in result["findings"]:
        lines.append(f"| {f['line']} | {f['type']} | {f['severity']} | `{f['text']}` |")
    if len(lines) == 2:
        lines.append("| — | (none) | — | no unresolved markers |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Flag unresolved authoring markers (placeholders) before submission.")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on warn-severity findings too (bare [N] citations)")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript)
    s = result["summary"]

    if not args.quiet:
        print("=" * 41)
        print(" Placeholder / Marker Gate")
        print("=" * 41)
        print(render(result))
        print()
        if s["blocker"]:
            print(f"BLOCKER: {s['blocker']} unresolved marker(s) must be removed before submission.")
        elif s["warn"]:
            print(f"WARN: {s['warn']} bare [N] citation(s) — confirm Vancouver style or resolve "
                  f"(escalates to blocker under --strict).")
        else:
            print("OK: no unresolved authoring markers.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    if s["blocker"]:
        return 1
    if args.strict and s["warn"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

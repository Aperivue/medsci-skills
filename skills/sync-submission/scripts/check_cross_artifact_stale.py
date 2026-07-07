#!/usr/bin/env python3
"""
check_cross_artifact_stale.py — submission-stage cross-artifact staleness gate.

Body-text QC is mature; peripheral artifacts lag. A late correction fixed in the
manuscript body can persist — sometimes *reversed* — in a supplement footnote,
and a reporting checklist is often generated against an older manuscript version
(stale section/line references and a stale version label). Both reach reviewers.

Two deterministic checks:

  1. **labeled-value drift** — for a small set of reconciliation-prone labels
     (missingness, complete-case, kappa/κ, agreement, prevalence, incidence,
     response rate, follow-up, pack-years, mortality), collect every numeric
     value the *body* attaches to each label, and every value an *auxiliary*
     file (supplement, e-table, caption, checklist) attaches to the same label.
     An auxiliary value for a label the body also reports, but which the body
     never states, is a `labeled_value_drift` (the supplement disagrees with the
     corrected body).

  2. **checklist version staleness** — a reporting checklist (file name contains
     `checklist`/`strobe`/`prisma`/`consort`/`stard`/`tripod`/`claim`) that
     embeds a manuscript-version marker (`manuscript_v6`, `v6 (2026-04-20)`,
     `Target manuscript: ... v6`) which differs from the current version
     (`--manuscript-version`, or a `vN` in the manuscript filename) is flagged
     `checklist_version_stale` — its line/section refs no longer match.

  3. **retired-term / old-value survivors** (opt-in, `--retired-term` /
     `--old-value`) — after a revision *reframes* a claim class or *changes* a
     headline number, stale copies survive in un-touched body paragraphs, figure
     / table legends, the supplement, and the response letter. Given the retired
     framing vocabulary or the superseded value(s) from the reframe diff, this
     scans the **body AND every aux file** and flags each survivor
     (`retired_framing_survivor` / `stale_old_value`). This automates the
     claim-site grep of `manuscript-versioning.md` §6.1: a reframe the body
     claims to have made "throughout" is verified across all artifacts, not a
     sample.

Exit: 0 = clean, 1 = findings, 2 = usage/error. Stdlib-only.

Usage:
    python3 check_cross_artifact_stale.py --manuscript manuscript.md \
        --aux supplement/ --aux qc/ [--manuscript-version v8] \
        [--retired-term "location-stratified benchmark"] [--old-value 1.72] \
        [--out qc/cross_artifact.json] [--strict] [--quiet]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Reconciliation-prone labels → a regex fragment matching the label.
LABELS: dict[str, str] = {
    "missingness": r"missing(?:ness)?",
    "complete_case": r"complete[-\s]?case",
    "kappa": r"κ|kappa",
    "agreement": r"agreement",
    "prevalence": r"prevalence",
    "incidence": r"incidence",
    "response_rate": r"response\s+rate",
    "follow_up": r"follow[-\s]?up",
    "pack_years": r"pack[-\s]?years?",
    "mortality": r"mortality",
}

# A number near a label: label … (within 40 chars) … value, optional %.
VALUE_RE = r"[^\n.]{0,40}?(\d+(?:\.\d+)?)\s*(%?)"

CHECKLIST_NAME_RE = re.compile(
    r"(checklist|strobe|prisma|consort|stard|tripod|claim|squire|arrive|care)",
    re.IGNORECASE,
)
# Manuscript-version markers a checklist might embed.
VERSION_MARKER_RE = re.compile(
    r"(?:manuscript[_\s]*|target\s+manuscript[^\n]*?\bv|version[^\n]*?\bv|\bv)"
    r"(\d{1,3})\b",
    re.IGNORECASE,
)
FILENAME_VERSION_RE = re.compile(r"[_\-.]v(\d{1,3})\b", re.IGNORECASE)


@dataclass
class Finding:
    type: str
    severity: str  # "stale" | "version_stale"
    path: str
    detail: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    scanned: dict[str, int] = field(default_factory=dict)

    @property
    def submission_safe(self) -> bool:
        return not self.findings

    def as_dict(self) -> dict:
        return {
            "submission_safe": self.submission_safe,
            "scanned": self.scanned,
            "summary": {
                "stale": sum(1 for f in self.findings if f.severity == "stale"),
                "version_stale": sum(1 for f in self.findings if f.severity == "version_stale"),
                "survivor": sum(1 for f in self.findings if f.severity == "survivor"),
            },
            "findings": [asdict(f) for f in self.findings],
        }


def _survivor_pattern(needle: str, numeric: bool) -> re.Pattern:
    """Case-insensitive term match, or a digit-bounded numeric match."""
    if numeric:
        return re.compile(r"(?<![\d.])" + re.escape(needle) + r"(?!\d)")
    return re.compile(re.escape(needle), re.IGNORECASE)


def scan_survivors(text: str, path: str, retired_terms: list[str],
                   old_values: list[str]) -> list["Finding"]:
    """Flag any retired framing term / superseded value that survives in text."""
    out: list[Finding] = []
    for term in retired_terms:
        m = _survivor_pattern(term, numeric=False).search(text)
        if m:
            snippet = re.sub(r"\s+", " ", text[max(0, m.start() - 30): m.start() + len(term) + 30]).strip()
            out.append(Finding(
                "retired_framing_survivor", "survivor", path,
                f"retired term {term!r} still present (…{snippet}…) — reframe not applied here"))
    for val in old_values:
        m = _survivor_pattern(val, numeric=bool(re.fullmatch(r"\d+(?:\.\d+)?", val))).search(text)
        if m:
            snippet = re.sub(r"\s+", " ", text[max(0, m.start() - 30): m.start() + len(val) + 30]).strip()
            out.append(Finding(
                "stale_old_value", "survivor", path,
                f"superseded value {val!r} still present (…{snippet}…) — headline change not propagated here"))
    return out


def label_values(text: str) -> dict[str, set[str]]:
    """Map each known label to the set of numeric values stated near it."""
    out: dict[str, set[str]] = {}
    for key, frag in LABELS.items():
        vals: set[str] = set()
        for m in re.finditer(frag + VALUE_RE, text, re.IGNORECASE):
            num, pct = m.group(1), m.group(2)
            vals.add(num + ("%" if pct else ""))
        if vals:
            out[key] = vals
    return out


def _iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files += [q for q in sorted(p.rglob("*"))
                      if q.is_file() and q.suffix.lower() in (".md", ".txt", ".csv", ".tsv", ".yaml", ".yml")]
        elif p.is_file():
            files.append(p)
    return files


def _manuscript_version(manuscript: Path, explicit: str | None) -> int | None:
    if explicit:
        m = re.search(r"\d+", explicit)
        if m:
            return int(m.group(0))
    m = FILENAME_VERSION_RE.search(manuscript.name)
    return int(m.group(1)) if m else None


def build_report(manuscript: Path, aux_paths: list[Path], version: int | None,
                 retired_terms: list[str] | None = None,
                 old_values: list[str] | None = None) -> Report:
    rep = Report()
    retired_terms = retired_terms or []
    old_values = old_values or []
    body = manuscript.read_text(encoding="utf-8", errors="replace")
    body_labels = label_values(body)

    # 3. retired-term / old-value survivors in the BODY itself (un-touched paragraphs)
    if retired_terms or old_values:
        rep.findings += scan_survivors(body, str(manuscript), retired_terms, old_values)

    aux_files = [f for f in _iter_files(aux_paths) if f.resolve() != manuscript.resolve()]
    for f in aux_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        rel = str(f)

        # 3. retired-term / old-value survivors in this aux artifact
        if retired_terms or old_values:
            rep.findings += scan_survivors(text, rel, retired_terms, old_values)

        # 1. labeled-value drift vs the body
        for key, vals in label_values(text).items():
            if key not in body_labels:
                continue  # body does not report this label — not a reconciliation target
            drift = vals - body_labels[key]
            for v in sorted(drift):
                rep.findings.append(Finding(
                    "labeled_value_drift", "stale", rel,
                    f"'{key}' = {v} here, but the body reports "
                    f"{sorted(body_labels[key])} — possible stale value"))

        # 2. checklist version staleness
        if version is not None and CHECKLIST_NAME_RE.search(f.name):
            embedded = {int(m.group(1)) for m in VERSION_MARKER_RE.finditer(text)}
            older = sorted(v for v in embedded if v < version)
            if older:
                rep.findings.append(Finding(
                    "checklist_version_stale", "version_stale", rel,
                    f"references manuscript version(s) v{older} but current is v{version}"))

    rep.scanned = {"aux_files": len(aux_files), "body_labels": len(body_labels)}
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Cross-artifact staleness gate (labeled-value drift + checklist version).")
    ap.add_argument("--manuscript", type=Path, required=True, help="Body manuscript markdown.")
    ap.add_argument("--aux", type=Path, action="append", default=[],
                    help="Auxiliary file or directory (supplement/checklist/captions). Repeatable.")
    ap.add_argument("--manuscript-version", default=None,
                    help="Current manuscript version, e.g. v8 (else inferred from filename).")
    ap.add_argument("--retired-term", action="append", default=[], metavar="TERM",
                    help="A framing term the revision retired; flag any survivor in body/aux. Repeatable.")
    ap.add_argument("--old-value", action="append", default=[], metavar="VALUE",
                    help="A superseded headline value; flag any survivor in body/aux. Repeatable.")
    ap.add_argument("--out", type=Path, default=None, help="Write JSON report here.")
    ap.add_argument("--strict", action="store_true",
                    help="(Reserved) all findings already fail; flag kept for interface parity.")
    ap.add_argument("--quiet", action="store_true", help="Suppress stdout summary.")
    args = ap.parse_args(argv)

    if not args.manuscript.is_file():
        print(f"ERROR: --manuscript not a file: {args.manuscript}", file=sys.stderr)
        return 2
    if not args.aux and not args.retired_term and not args.old_value:
        print("ERROR: pass at least one of --aux, --retired-term, --old-value", file=sys.stderr)
        return 2

    version = _manuscript_version(args.manuscript, args.manuscript_version)
    rep = build_report(args.manuscript, args.aux, version,
                       retired_terms=args.retired_term, old_values=args.old_value)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rep.as_dict(), indent=2), encoding="utf-8")

    if not args.quiet:
        if rep.submission_safe:
            print(f"PASS: no cross-artifact staleness ({rep.scanned}).")
        else:
            print(f"FAIL: cross-artifact staleness — {rep.as_dict()['summary']}")
            for f in rep.findings:
                print(f"  - [{f.severity}] {f.type} {f.path}: {f.detail}")

    return 0 if rep.submission_safe else 1


if __name__ == "__main__":
    sys.exit(main())

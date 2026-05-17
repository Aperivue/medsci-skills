#!/usr/bin/env python3
"""Blind sweep — redact author identifiers across submission artifacts for double-blind review.

Usage:
  python blind_sweep.py --registry path/to/author_registry.yaml \
                        --files file1.md file2.md ... \
                        [--inplace | --out-dir staging/blinded]

Reads an author registry (YAML) describing identifiers and their role-label
replacements, then performs phased substitution (specific patterns first,
then bare forms, then regex word-boundary forms). Reports residual identifier
counts for each file after blinding.

Registry schema (YAML):
  reviewers:
    - role: "Reviewer 1"
      full_names: ["Given Surname"]      # roman script
      native_names: ["성명"]              # native script (e.g., hangul)
      initials_with_period: ["G.S."]
      initials_no_period: ["GS"]
      email: "user@example.com"
      orcid: "0000-0000-0000-0000"
    - role: "Reviewer 2"
      ...
  institutions:
    - replace: "Institution A / University B"
      with: "the review team's affiliated institutions"
  references:
    - replace: "Given Surname, Other Author. Title"
      with: "[Authors]. Title"

Order of substitution (per file):
  1. Institution and reference patterns (longest specific strings first).
  2. Role-combination patterns (e.g., "Given Surname (GS, 1st reviewer)").
  3. Bare full names and native names.
  4. Regex word-boundary patterns for initials (period and no-period forms),
     emails, ORCIDs, and combined initial patterns.

The script does NOT hard-code any author identifiers — all PII is sourced
from the registry the caller provides. This keeps the tool PII-free for OSS
distribution.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import sys
from dataclasses import dataclass, field
from typing import Iterable

try:
    import yaml  # type: ignore
except ImportError:
    print("blind_sweep requires PyYAML. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


@dataclass
class Reviewer:
    role: str
    full_names: list[str] = field(default_factory=list)
    native_names: list[str] = field(default_factory=list)
    initials_with_period: list[str] = field(default_factory=list)
    initials_no_period: list[str] = field(default_factory=list)
    email: str | None = None
    orcid: str | None = None


def load_registry(path: pathlib.Path) -> tuple[list[Reviewer], list[tuple[str, str]], list[tuple[str, str]]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    reviewers = [Reviewer(**r) for r in data.get("reviewers", [])]
    institutions = [(i["replace"], i["with"]) for i in data.get("institutions", [])]
    references = [(r["replace"], r["with"]) for r in data.get("references", [])]
    return reviewers, institutions, references


def build_substitutions(reviewers: list[Reviewer]) -> tuple[list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (phase2_combined, phase3_bare, phase4_regex)."""
    phase2_combined: list[tuple[str, str]] = []
    phase3_bare: list[tuple[str, str]] = []
    phase4_regex: list[tuple[str, str]] = []

    for r in reviewers:
        for name in r.full_names:
            for init in r.initials_no_period + r.initials_with_period:
                for label in (
                    f"{name} ({init}, 1st reviewer)", f"{name} ({init}, 2nd reviewer)",
                    f"{name} ({init}, 1st)", f"{name} ({init}, 2nd)",
                    f"{name} ({init})",
                ):
                    phase2_combined.append((label, r.role))
            phase3_bare.append((name, r.role))
        for name in r.native_names:
            phase3_bare.append((name, r.role))
        for init in r.initials_with_period:
            esc = re.escape(init)
            phase4_regex.append((rf"\b{esc}", r.role))
        for init in r.initials_no_period:
            phase4_regex.append((rf"\b{re.escape(init)}\b", r.role))
        if r.email:
            phase4_regex.append((re.escape(r.email), "[redacted email]"))
        if r.orcid:
            phase4_regex.append((re.escape(r.orcid), "[redacted ORCID]"))

    # Sort phase2/phase3 by length desc so longer-specific patterns win
    phase2_combined.sort(key=lambda kv: -len(kv[0]))
    phase3_bare.sort(key=lambda kv: -len(kv[0]))
    return phase2_combined, phase3_bare, phase4_regex


def blind_text(text: str, phase1: Iterable[tuple[str, str]],
               phase2: Iterable[tuple[str, str]], phase3: Iterable[tuple[str, str]],
               phase4_regex: Iterable[tuple[str, str]]) -> tuple[str, int]:
    changes = 0
    for old, new in list(phase1) + list(phase2) + list(phase3):
        if old in text:
            count = text.count(old)
            text = text.replace(old, new)
            changes += count
    for pat, repl in phase4_regex:
        matches = re.findall(pat, text)
        if matches:
            text = re.sub(pat, repl, text)
            changes += len(matches)
    return text, changes


def residual_scan(text: str, reviewers: list[Reviewer]) -> list[str]:
    residual: list[str] = []
    for r in reviewers:
        for name in r.full_names + r.native_names:
            c = text.count(name)
            if c > 0:
                residual.append(f"{name}={c}")
        for init in r.initials_with_period:
            c = len(re.findall(rf"\b{re.escape(init)}", text))
            if c > 0:
                residual.append(f"{init}={c}")
        for init in r.initials_no_period:
            c = len(re.findall(rf"\b{re.escape(init)}\b", text))
            if c > 0:
                residual.append(f"{init}={c}")
        if r.email:
            c = text.count(r.email)
            if c > 0:
                residual.append(f"{r.email}={c}")
        if r.orcid:
            c = text.count(r.orcid)
            if c > 0:
                residual.append(f"{r.orcid}={c}")
    return residual


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry", required=True, type=pathlib.Path, help="Author registry YAML")
    ap.add_argument("--files", nargs="+", required=True, type=pathlib.Path, help="Files to blind")
    ap.add_argument("--inplace", action="store_true", help="Overwrite in place (default)")
    ap.add_argument("--out-dir", type=pathlib.Path, help="Write blinded copies under this directory")
    ap.add_argument("--backup-dir", type=pathlib.Path, help="Copy originals here before in-place edit")
    args = ap.parse_args()

    if not args.inplace and not args.out_dir:
        args.inplace = True

    reviewers, institutions, references = load_registry(args.registry)
    phase1 = institutions + references
    phase2, phase3, phase4_regex = build_substitutions(reviewers)

    if args.backup_dir:
        args.backup_dir.mkdir(parents=True, exist_ok=True)
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'FILE':<55} {'CHANGES':<8} RESIDUAL")
    overall_residual = False
    for src in args.files:
        if not src.exists():
            print(f"{src.name:<55} {'-':<8} MISSING")
            continue
        text = src.read_text(encoding="utf-8")
        if args.backup_dir:
            shutil.copy(src, args.backup_dir / src.name)
        new_text, changes = blind_text(text, phase1, phase2, phase3, phase4_regex)
        residual = residual_scan(new_text, reviewers)

        if args.out_dir:
            (args.out_dir / src.name).write_text(new_text, encoding="utf-8")
        else:
            src.write_text(new_text, encoding="utf-8")

        flag = "clean" if not residual else " ".join(residual) + "  WARN"
        if residual:
            overall_residual = True
        print(f"{src.name:<55} {changes:<8} {flag}")

    return 1 if overall_residual else 0


if __name__ == "__main__":
    sys.exit(main())

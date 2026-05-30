#!/usr/bin/env python3
"""
batch_metadata_audit.py — Audit multiple medical-AI repos and Hugging Face cards
for AIO compliance.

Per repository:
- README.md present, with DOI link / badge and a How-to-cite or Citation section
- CITATION.cff present at root with title/authors/version + at least one ORCID
- LICENSE present

Per Hugging Face card (model or dataset):
- YAML front matter present with license / library_name / tags
- Required prose sections: intended use, training data, evaluation, limitations,
  ethical considerations
- No PHI patterns matched

Usage:
    python batch_metadata_audit.py /path/to/repo1 /path/to/repo2 \\
        --hf-card model_card.md --output qc/aio_batch.json
    python batch_metadata_audit.py --hf-card dataset_card.md --fail-on-issue
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PHI_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                 # US SSN
    re.compile(r"\b\d{6}-\d{7}\b"),                       # KR resident registration number
    re.compile(r"MRN[:\s]*\d+", re.I),                    # medical record number
    re.compile(r"\bpatient[\s_]?id[:\s]*\d+", re.I),      # patient id
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b.*\bDOB\b", re.I),  # DOB pattern
]

CITATION_CFF_REQUIRED = ("title", "authors", "version")
HF_CARD_REQUIRED_YAML = ("license", "library_name", "tags")
HF_CARD_REQUIRED_SECTIONS = (
    "intended use",
    "training data",
    "evaluation",
    "limitations",
    "ethical considerations",
)


def _phi_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pat in PHI_PATTERNS:
        m = pat.search(text)
        if m:
            hits.append(f"Possible PHI pattern matched: {m.group(0)[:30]!r}")
    return hits


def check_readme(path: Path) -> dict:
    if not path.exists():
        return {"present": False, "issues": ["README.md missing"]}
    text = path.read_text()
    issues: list[str] = []
    if "DOI" not in text and "doi.org" not in text.lower():
        issues.append("No DOI badge or link in README")
    if "## How to cite" not in text and "## Citation" not in text:
        issues.append('No "How to cite" / "Citation" section')
    if not any(s in text.lower() for s in ("quickstart", "getting started", "installation")):
        issues.append("No quickstart / installation section")
    return {"present": True, "issues": issues}


def check_citation_cff(path: Path) -> dict:
    if not path.exists():
        return {"present": False, "issues": ["CITATION.cff missing at repo root"]}
    text = path.read_text()
    issues: list[str] = []
    for key in CITATION_CFF_REQUIRED:
        if f"{key}:" not in text:
            issues.append(f"CITATION.cff missing key: {key}")
    if "orcid" not in text.lower():
        issues.append("CITATION.cff has no ORCID identifier(s)")
    return {"present": True, "issues": issues}


def check_license(path: Path) -> dict:
    return {
        "present": path.exists(),
        "issues": [] if path.exists() else ["LICENSE missing"],
    }


def check_hf_card(path: Path) -> dict:
    if not path.exists():
        return {"present": False, "issues": ["HF card missing"]}
    text = path.read_text()
    issues: list[str] = []
    if not text.startswith("---"):
        issues.append("HF card missing YAML front matter")
    else:
        front_parts = text.split("---", 2)
        front = front_parts[1] if len(front_parts) >= 3 else ""
        for key in HF_CARD_REQUIRED_YAML:
            if f"{key}:" not in front:
                issues.append(f"HF card YAML missing key: {key}")
    body_lower = text.lower()
    for section in HF_CARD_REQUIRED_SECTIONS:
        if section not in body_lower:
            issues.append(f"HF card missing section: {section}")
    issues.extend(_phi_hits(text))
    return {"present": True, "issues": issues}


def audit_repo(repo: Path) -> dict:
    return {
        "repo": str(repo),
        "readme": check_readme(repo / "README.md"),
        "citation_cff": check_citation_cff(repo / "CITATION.cff"),
        "license": check_license(repo / "LICENSE"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit multiple repos and HF cards for AIO compliance."
    )
    parser.add_argument("paths", nargs="*", type=Path,
                        help="Repository directories to audit.")
    parser.add_argument("--hf-card", action="append", type=Path, default=[],
                        help="Path to a Hugging Face model/dataset card markdown file.")
    parser.add_argument("--output", type=Path, default=None,
                        help="Write JSON report to this path (default: stdout).")
    parser.add_argument("--fail-on-issue", action="store_true",
                        help="Exit 1 if any issues are detected.")
    args = parser.parse_args(argv)

    if not args.paths and not args.hf_card:
        parser.error("Provide at least one repo path or --hf-card.")

    report: dict = {"repos": [], "hf_cards": []}
    for path in args.paths:
        if path.is_dir():
            report["repos"].append(audit_repo(path))
        else:
            report["repos"].append({"repo": str(path),
                                    "issues": ["Not a directory"]})
    for card in args.hf_card:
        report["hf_cards"].append({"path": str(card), **check_hf_card(card)})

    out = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out)
    else:
        print(out)

    has_issues = any(
        (r.get("readme", {}).get("issues") or
         r.get("citation_cff", {}).get("issues") or
         r.get("license", {}).get("issues") or
         r.get("issues"))
        for r in report["repos"]
    ) or any(c.get("issues") for c in report["hf_cards"])

    return 1 if (args.fail_on_issue and has_issues) else 0


if __name__ == "__main__":
    sys.exit(main())

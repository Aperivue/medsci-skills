#!/usr/bin/env python3
"""Structured-summary-box conformance detector (academic-aio).

High-impact medical-AI journals require a structured summary box whose *format*
is journal-specific, and a production/technical check rejects the wrong one:

  - Radiology / Radiology:AI (RSNA): "Key Points" — exactly 3 bullets, one claim each.
  - Lancet family: "Research in context" — three labelled sub-blocks
    (Evidence before this study / Added value of this study / Implications of all
    the available evidence).
  - npj Digital Medicine: "Plain-language summary" — ~150-200 words.

academic-aio already *generates* these boxes; this detector makes the spec
deterministic so a wrong-bullet-count, missing-sub-block, or over/under-length
box is caught before submission instead of at the technical check. The spec is
read from references/summary_box_specs.json (public facts, journal-keyed).

INPUTS
  --manuscript   markdown file containing the summary box (required).
  --journal      journal stem to pick the format (e.g. radiology, lancet-digital-health,
                 npj-digital-medicine). Optional if --format is given.
  --format       force a format: key_points | research_in_context | plain_language_summary.
  --specs        path to summary_box_specs.json (default: alongside this script's skill).
  --out          write a JSON report here (default: qc/summary_box_report.json).
  --strict       exit 1 if the box is non-conformant.

VERDICT
  CONFORMANT          the box matches its format's spec.
  NONCONFORMANT       a hard rule failed (wrong bullet count, missing sub-block,
                      word count outside the band, box absent).
  ADVISORY            only soft rules fired (e.g. a bullet carries >1 claim).
  Exit: 0 conformant/advisory or report-only; 1 NONCONFORMANT under --strict;
        2 input/usage error.

Stdlib-only (csv-free: json / argparse / re / pathlib).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _default_specs() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "summary_box_specs.json"


def _err(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 2


def load_specs(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["formats"]


def pick_format(formats: dict, journal: str | None, fmt: str | None) -> str | None:
    if fmt:
        return fmt if fmt in formats else None
    if journal:
        j = journal.strip().lower()
        for key, spec in formats.items():
            if j in [x.lower() for x in spec.get("journals", [])]:
                return key
    return None


def extract_block(text: str, label: str) -> str | None:
    """Return the lines under a heading/bold label matching `label`, up to the
    next markdown heading or a blank-line-separated next bold label section."""
    lines = text.splitlines()
    label_re = re.compile(
        r"^\s*(?:#{1,6}\s*|\*\*\s*|\*\s*)?" + re.escape(label) + r"\b", re.IGNORECASE
    )
    start = None
    for i, ln in enumerate(lines):
        if label_re.search(ln):
            start = i
            break
    if start is None:
        return None
    out: list[str] = []
    for ln in lines[start + 1:]:
        if re.match(r"^\s*#{1,6}\s+\S", ln):  # next heading ends the block
            break
        out.append(ln)
    return "\n".join(out).strip()


def count_bullets(block: str) -> list[str]:
    bullets: list[str] = []
    for ln in block.splitlines():
        m = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)", ln)
        if m:
            bullets.append(m.group(1).strip())
    return bullets


def multi_claim(bullet: str) -> bool:
    """Heuristic: a one-claim bullet should not pack two independent assertions.
    Flags a sentence-final period followed by a capitalized new sentence, or a
    semicolon joining two clauses."""
    if ";" in bullet:
        return True
    return bool(re.search(r"[.!?]\s+[A-Z0-9]", bullet.rstrip(".")))


def word_count(block: str) -> int:
    # strip the label line if it leaked in; count remaining words.
    return len(re.findall(r"\b[\w'-]+\b", block))


def check(text: str, fmt: str, spec: dict) -> dict:
    label = spec["label"]
    block = extract_block(text, label)
    findings: list[dict] = []
    if block is None:
        return {
            "format": fmt, "label": label, "verdict": "NONCONFORMANT",
            "findings": [{"rule": "box_present", "severity": "hard",
                          "detail": f"no '{label}' box found in the manuscript"}],
        }

    if fmt == "key_points":
        bullets = count_bullets(block)
        want = spec["bullets"]
        if len(bullets) != want:
            findings.append({"rule": "bullet_count", "severity": "hard",
                             "detail": f"found {len(bullets)} bullets, expected {want}"})
        if spec.get("one_claim_per_bullet"):
            for b in bullets:
                if multi_claim(b):
                    findings.append({"rule": "one_claim_per_bullet", "severity": "soft",
                                     "detail": f"bullet packs >1 claim: {b[:80]}"})
    elif fmt == "research_in_context":
        low = block.lower()
        for sub in spec["subblocks"]:
            if sub.lower() not in low:
                findings.append({"rule": "subblock_present", "severity": "hard",
                                 "detail": f"missing sub-block: '{sub}'"})
    elif fmt == "plain_language_summary":
        wc = word_count(block)
        lo, hi = spec["word_min"], spec["word_max"]
        if wc < lo or wc > hi:
            findings.append({"rule": "word_band", "severity": "hard",
                             "detail": f"{wc} words, expected {lo}-{hi}"})
    else:
        return {"format": fmt, "label": label, "verdict": "NONCONFORMANT",
                "findings": [{"rule": "unknown_format", "severity": "hard",
                              "detail": f"unknown format '{fmt}'"}]}

    hard = any(f["severity"] == "hard" for f in findings)
    verdict = "NONCONFORMANT" if hard else ("ADVISORY" if findings else "CONFORMANT")
    return {"format": fmt, "label": label, "verdict": verdict, "findings": findings}


def main() -> int:
    ap = argparse.ArgumentParser(description="Check a structured summary box against its journal format spec.")
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--journal")
    ap.add_argument("--format")
    ap.add_argument("--specs")
    ap.add_argument("--out")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    man = Path(args.manuscript)
    if not man.is_file():
        return _err(f"manuscript not found: {man}")
    specs_path = Path(args.specs) if args.specs else _default_specs()
    if not specs_path.is_file():
        return _err(f"specs not found: {specs_path}")

    formats = load_specs(specs_path)
    fmt = pick_format(formats, args.journal, args.format)
    if fmt is None:
        return _err("could not select a format — pass --format or a --journal listed in the specs")

    text = man.read_text(encoding="utf-8")
    report = check(text, fmt, formats[fmt])

    out_path = Path(args.out) if args.out else Path("qc") / "summary_box_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"detector": "check_summary_box", **report}, indent=2) + "\n", encoding="utf-8")

    print("=" * 41)
    print(" Summary-Box Conformance")
    print("=" * 41)
    print(f"format: {fmt}  ({report['label']})")
    print(f"verdict: {report['verdict']}")
    for f in report["findings"]:
        print(f"  [{f['severity']}] {f['rule']}: {f['detail']}")
    print(f"report: {out_path}")

    if report["verdict"] == "NONCONFORMANT" and args.strict:
        print("\nSUMMARY_BOX_NONCONFORMANT", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

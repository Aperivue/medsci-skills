#!/usr/bin/env python3
"""Structured-summary-box conformance detector (academic-aio).

High-impact medical-AI journals require a structured summary box whose *format*
is journal-specific, and a production/technical check rejects the wrong one:

  - Radiology / Radiology:AI (RSNA): exactly 3 bullets, one claim each. The box
    label is read from the spec: "Key Points" by default; for journal stems listed
    under `labels_by_journal` (Radiology, labelled "Key Results" in
    references/journal_summarybox_templates.yaml) each listed label is accepted.
  - Lancet family: "Research in context" — three labelled sub-blocks
    (Evidence before this study / Added value of this study / Implications of all
    the available evidence).
  - A plain-language summary (150-200 words) for journals that require one; pass
    --format plain_language_summary (no journal in the spec table maps to it).

academic-aio already *generates* these boxes; this detector makes the spec
deterministic so a wrong-bullet-count, missing-sub-block, or over/under-length
box is caught before submission instead of at the technical check. The spec is
read from references/summary_box_specs.json (public facts, journal-keyed).

INPUTS
  --manuscript   markdown file containing the summary box (required).
  --journal      journal stem to pick the format (e.g. radiology, lancet-digital-health,
                 lancet-digital-health). Optional if --format is given.
  --format       force a format: key_points | research_in_context | plain_language_summary.
  --specs        path to summary_box_specs.json (default: alongside this script's skill).
  --out          write a JSON report here (default: qc/summary_box_report.json).
  --strict       exit 1 if the box is non-conformant.

VERDICT
  CONFORMANT          the box matches its format's spec.
  NONCONFORMANT       a hard rule failed (wrong top-level bullet count, missing or
                      empty sub-block, word count outside the band, box absent).
  The box starts at a heading, bold label or bare label line naming it (not at a
  body sentence that begins with the same words) and ends at the next heading or
  the next bold-only label line. In a Research-in-context box the sub-block labels
  never end it, and another bold-only line ends it only after the last sub-block.
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


_MARK = r"(?:\*\*|__|\*|_)"


def _label_line_re(label: str) -> "re.Pattern[str]":
    """A line that *is* the box label: a markdown heading starting with the label,
    a bold/italic span starting with the label, or the label alone on its line
    (optional trailing colon). A body sentence that merely begins with the label
    words ("Key points of prior work are ...") is not a label line."""
    lab = re.escape(label)
    return re.compile(
        r"^\s*(?:"
        r"#{1,6}\s*" + lab + r"\b.*"                                   # heading
        r"|" + _MARK + r"\s*" + lab + r"\b[^*_]*?" + _MARK + r".*"         # bold/italic span
        r"|" + lab + r"\s*:?\s*"                                       # bare label line
        r")$",
        re.IGNORECASE,
    )


# A line consisting only of a bold label ("**Abbreviations**", "__Funding:__") —
# the start of the next labelled section.
_BOLD_ONLY_RE = re.compile(r"^\s*(\*\*|__)\s*([^*_]+?)\s*:?\s*\1\s*:?\s*$")


def _subblock_re(sub: str) -> "re.Pattern[str]":
    """A line that opens with a sub-block label (optionally bulleted, headed,
    bold/italic, followed by ':' or '.'); group 1 is the rest of the line."""
    return re.compile(
        r"^\s*(?:[-*+]\s+)?(?:#{1,6}\s*)?" + _MARK + r"?\s*" + re.escape(sub)
        + r"\s*[.:]?\s*" + _MARK + r"?\s*[.:]?\s*(.*)$",
        re.IGNORECASE,
    )


def extract_block(text: str, label: str, keep_labels: list[str] | None = None) -> str | None:
    """Return the lines under a heading/bold label matching `label`, up to the
    next markdown heading or the next bold-only label line.

    With `keep_labels` (the format's ordered sub-block labels), a line opening
    with one of them never ends the block, and any other bold-only line ends it
    only once the last sub-block label has been seen — a bold line inside a
    sub-block ("**Search strategy**") stays in the box."""
    lines = text.splitlines()
    label_re = _label_line_re(label)
    keep_res = [_subblock_re(k) for k in (keep_labels or [])]
    start = None
    for i, ln in enumerate(lines):
        if label_re.match(ln):
            start = i
            break
    if start is None:
        return None
    out = []
    seen_last = not keep_res
    for ln in lines[start + 1:]:
        if re.match(r"^\s*#{1,6}\s+\S", ln):  # next heading ends the block
            break
        hit = [k for k, r in enumerate(keep_res) if r.match(ln)]
        if hit:
            if hit[0] == len(keep_res) - 1:
                seen_last = True
            out.append(ln)
            continue
        if seen_last and _BOLD_ONLY_RE.match(ln):
            break  # next bold-labelled section ends the block
        out.append(ln)
    return "\n".join(out).strip()


_BULLET_RE = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*\S)")


def count_bullets(block: str) -> list[str]:
    """Top-level bullets only: a bullet indented two or more columns deeper than
    the shallowest bullet in the block is a sub-bullet and is not counted."""
    found: list[tuple[int, str]] = []
    for ln in block.splitlines():
        m = _BULLET_RE.match(ln.expandtabs(4))
        if m:
            found.append((len(m.group(1)), m.group(2).strip()))
    if not found:
        return []
    top = min(ind for ind, _ in found)
    return [b for ind, b in found if ind < top + 2]


def subblock_contents(block: str, subblocks: list[str]) -> dict[str, str | None]:
    """Map each sub-block label to its content, or None when the label does not
    open a line of the block. Content is the text after the label on its line
    plus the following lines up to the next sub-block label."""
    lines = block.splitlines()
    pats = {sub: _subblock_re(sub) for sub in subblocks}
    starts: list[tuple[int, str, str]] = []
    for i, ln in enumerate(lines):
        for sub, pat in pats.items():
            m = pat.match(ln)
            if m:
                starts.append((i, sub, m.group(1)))
                break
    result: dict[str, str | None] = {sub: None for sub in subblocks}
    for k, (i, sub, rest) in enumerate(starts):
        if result[sub] is not None:
            continue
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        result[sub] = "\n".join([rest] + lines[i + 1:end]).strip()
    return result


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


def accepted_labels(spec: dict, journal: str | None) -> list[str]:
    """The box labels accepted for this journal: a per-journal list from
    `labels_by_journal` when the spec has one for the journal, else `label`."""
    by_j = spec.get("labels_by_journal") or {}
    if journal:
        j = journal.strip().lower()
        for key, labels in by_j.items():
            if key.lower() == j and labels:
                return list(labels)
    return [spec["label"]]


def check(text: str, fmt: str, spec: dict, journal: str | None = None) -> dict:
    labels = accepted_labels(spec, journal)
    keep = spec.get("subblocks") if fmt == "research_in_context" else None
    label = labels[0]
    block = None
    for cand in labels:
        block = extract_block(text, cand, keep)
        if block is not None:
            label = cand
            break
    findings: list[dict] = []
    if block is None:
        names = " / ".join(f"'{x}'" for x in labels)
        return {
            "format": fmt, "label": label, "verdict": "NONCONFORMANT",
            "findings": [{"rule": "box_present", "severity": "hard",
                          "detail": f"no {names} box found in the manuscript"}],
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
        contents = subblock_contents(block, spec["subblocks"])
        for sub in spec["subblocks"]:
            body = contents[sub]
            if body is None:
                findings.append({"rule": "subblock_present", "severity": "hard",
                                 "detail": f"missing sub-block: '{sub}' (no line opens with this label)"})
            elif not re.search(r"\w", body):
                findings.append({"rule": "subblock_content", "severity": "hard",
                                 "detail": f"empty sub-block: '{sub}' has a label but no text"})
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
    report = check(text, fmt, formats[fmt], args.journal)

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

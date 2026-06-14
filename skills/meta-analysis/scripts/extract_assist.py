#!/usr/bin/env python3
"""
AI-assisted extraction *suggestions* for SR/MA data extraction (Phase 4).

Scans a full-text paper (Markdown, e.g. produced by /fulltext-retrieval's
PDF->MD step) for schema-defined fields and emits SUGGESTED candidate values,
each carrying a page reference and a verbatim source quote. This is the
extraction-stage analog of the screening-stage `ai_pre_screening_template.py`:
it produces *suggestions, never decisions*.

CRITICAL — suggestions, not decisions
-------------------------------------
Every emitted row is labeled `extraction_consensus_status = AI_SUGGESTED` and
`needs_review = true`. A human extractor MUST confirm or overturn each value
against the source PDF before it enters the confirmed extraction table. Only
the human-confirmed DTA CSV is fed to `dta_extraction_qc.py` — this tool's
output is NOT a QC-acceptable table. Per the Phase 4.0 gate, treat every
candidate N / denominator / 2x2 cell / effect estimate as hallucination-suspect
until reconciled against the source.

The script never invents values: every `value` and `verbatim_quote` is copied
literally from the Markdown, and `source_page_ref` comes from a literal page
marker in the text. If a field is not found, it emits a `not_found` row so the
gap is explicit rather than silently dropped.

Usage
-----
    python3 extract_assist.py --md paper.md --schema schema.yaml --out suggestions.tsv
    python3 extract_assist.py --md paper.md --schema schema.json --study-id StudyA_2021

Schema (YAML or JSON)
---------------------
    study_id: StudyA_2021          # optional; --study-id overrides
    fields:
      - {name: study_design, type: study_design}
      - {name: sample_n,     type: sample_n}
      - {name: source_sens,  type: sensitivity}
      - {name: source_spec,  type: specificity}
      - {name: extracted_tp, type: tp}
      - {name: country, type: regex, pattern: "conducted in ([A-Z][A-Za-z]+)"}

Built-in field types: sensitivity, specificity, sample_n, study_design, year,
tp, fp, fn, tn, regex (requires `pattern` with one capture group).

Page markers recognized: `<!-- page: N -->`, `<!-- page N -->`, `[page N]`,
`## Page N`, `===PAGE N===` (case-insensitive).
"""

import argparse
import json
import re
import sys
from pathlib import Path

OUT_COLUMNS = [
    "study_id", "field", "value", "source_page_ref",
    "verbatim_quote", "confidence", "needs_review", "extraction_consensus_status",
]

PAGE_RE = re.compile(
    r"(?:<!--\s*page:?\s*(\d+)\s*-->|\[page\s+(\d+)\]|^#{1,3}\s*page\s+(\d+)\b|===\s*page\s+(\d+)\s*===)",
    re.I,
)

# Built-in extractors: type -> compiled regex with one numeric/text capture group.
BUILTIN = {
    "sensitivity": re.compile(r"sensitivit(?:y|ies)\s*(?:was|were|of|=|:|,)?\s*(\d{1,3}(?:\.\d+)?\s*%|0?\.\d+|\d{1,3}(?:\.\d+)?)", re.I),
    "specificity": re.compile(r"specificit(?:y|ies)\s*(?:was|were|of|=|:|,)?\s*(\d{1,3}(?:\.\d+)?\s*%|0?\.\d+|\d{1,3}(?:\.\d+)?)", re.I),
    "sample_n": re.compile(r"(?:\bn\s*=\s*(\d+)|\b(\d+)\s+(?:patients|participants|subjects|cases|nodules|lesions|images|scans|examinations))", re.I),
    "study_design": re.compile(r"\b(retrospective|prospective|cross-sectional|case-control|cohort)\b", re.I),
    "year": re.compile(r"\b(19\d{2}|20\d{2})\b"),
    "tp": re.compile(r"(?:true[\s-]?positives?|TP)\s*(?:=|:|of|was|were)?\s*(\d+)", re.I),
    "fp": re.compile(r"(?:false[\s-]?positives?|FP)\s*(?:=|:|of|was|were)?\s*(\d+)", re.I),
    "fn": re.compile(r"(?:false[\s-]?negatives?|FN)\s*(?:=|:|of|was|were)?\s*(\d+)", re.I),
    "tn": re.compile(r"(?:true[\s-]?negatives?|TN)\s*(?:=|:|of|was|were)?\s*(\d+)", re.I),
}


def load_schema(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    try:
        import yaml  # PyYAML; used across medsci-skills scripts
    except ImportError:  # pragma: no cover
        sys.exit("ERROR: PyYAML required for .yaml schemas (or use a .json schema).")
    return yaml.safe_load(text)


def page_for_line(line_pages: list[int], idx: int) -> str:
    """Page number in effect at 0-based line index idx ('?' before first marker)."""
    return str(line_pages[idx]) if line_pages[idx] is not None else "?"


def first_group(m: re.Match) -> str:
    for g in m.groups():
        if g is not None:
            return g.strip()
    return m.group(0).strip()


def find_field(field: dict, lines: list[str], line_pages: list[int]) -> list[dict]:
    """Return candidate rows (dicts) for one schema field, in document order."""
    name = field["name"]
    ftype = field.get("type", "regex")
    if ftype == "regex":
        pat = field.get("pattern")
        if not pat:
            sys.exit(f"ERROR: field '{name}' type=regex requires a 'pattern'.")
        rx = re.compile(pat)
    else:
        rx = BUILTIN.get(ftype)
        if rx is None:
            sys.exit(f"ERROR: unknown field type '{ftype}' for '{name}'.")

    hits = []
    for i, line in enumerate(lines):
        for m in rx.finditer(line):
            val = first_group(m) if m.groups() else m.group(0).strip()
            hits.append({
                "field": name,
                "value": re.sub(r"\s+", "", val) if ftype in {"sensitivity", "specificity"} else val,
                "source_page_ref": page_for_line(line_pages, i),
                "verbatim_quote": line.strip(),
            })
    n = len(hits)
    if n == 0:
        return [{
            "field": name, "value": "", "source_page_ref": "?",
            "verbatim_quote": "", "confidence": "not_found",
        }]
    for k, h in enumerate(hits, 1):
        h["confidence"] = "single" if n == 1 else f"candidate_{k}_of_{n}"
    return hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AI-assisted extraction suggestions (Phase 4).")
    ap.add_argument("--md", required=True, help="full-text paper in Markdown")
    ap.add_argument("--schema", required=True, help="extraction schema (.yaml or .json)")
    ap.add_argument("--study-id", default=None, help="overrides schema study_id")
    ap.add_argument("--out", default=None, help="output TSV (default: stdout)")
    args = ap.parse_args(argv)

    schema = load_schema(Path(args.schema))
    study_id = args.study_id or schema.get("study_id", "UNKNOWN")
    fields = schema.get("fields", [])
    if not fields:
        sys.exit("ERROR: schema has no 'fields'.")

    raw = Path(args.md).read_text(encoding="utf-8")
    lines = raw.splitlines()

    # Build per-line current-page map from literal page markers.
    line_pages: list[int] = []
    current = None
    for line in lines:
        m = PAGE_RE.search(line)
        if m:
            current = int(next(g for g in m.groups() if g is not None))
        line_pages.append(current)

    rows = []
    for field in fields:
        for cand in find_field(field, lines, line_pages):
            cand["study_id"] = study_id
            cand["needs_review"] = "true"
            cand["extraction_consensus_status"] = "AI_SUGGESTED"
            rows.append(cand)

    out_lines = ["\t".join(OUT_COLUMNS)]
    for r in rows:
        out_lines.append("\t".join(str(r.get(c, "")) for c in OUT_COLUMNS))
    blob = "\n".join(out_lines) + "\n"

    if args.out:
        Path(args.out).write_text(blob, encoding="utf-8")
    else:
        sys.stdout.write(blob)

    n_found = sum(1 for r in rows if r.get("confidence") != "not_found")
    n_missing = sum(1 for r in rows if r.get("confidence") == "not_found")
    sys.stderr.write(
        f"[extract_assist] study={study_id}: {n_found} suggestion(s), "
        f"{n_missing} field(s) not found. ALL rows are AI_SUGGESTED / needs_review=true — "
        f"a human must confirm against the source PDF before building the DTA CSV for "
        f"dta_extraction_qc.py.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

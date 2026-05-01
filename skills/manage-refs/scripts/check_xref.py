#!/usr/bin/env python3
"""check_xref.py — Manuscript ↔ rendered DOCX cross-reference QC.

Catches the failure mode where in-text references to Tables / Figures /
Supplementary Tables / Supplementary Figures point to labels that either
(a) do not exist in the rendered DOCX, (b) have no caption definition in
the manuscript body, or (c) carry a caption text in the rendered DOCX
that disagrees with the body's caption definition.

Precedent: CK-1 CAC Warranty v6.2 (2026-04-28) — body cited
"Supp Table S4 (CAC>10 sensitivity)" but the rendered DOCX S4 was
"VIF Diagnostics"; S1, S6, S7 mismatched; S8, S9 cited but absent
from DOCX. Internal consistency checks did not catch this because the
build script carried its own legacy SSOT.

Inputs
------
  --md PATH         manuscript markdown (the in-text citation source)
  --docx PATH       rendered DOCX (optional but recommended)
  --out PATH        JSON audit (default: qc/xref_audit.json)
  --strict          exit 1 on any non-OK finding (submission gate)
  --quiet           suppress stdout summary table

Output
------
  qc/xref_audit.json with submission_safe boolean and per-label rows.
  Stdout: human-readable 3-way matrix.

Exit codes
----------
  0  all OK (or non-strict and only warnings)
  1  --strict and at least one non-OK finding
  2  argument / IO error

Dependencies
------------
  python-docx (only if --docx is passed). Falls back to body-only audit
  with a warning if python-docx is unavailable.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Regex
# ---------------------------------------------------------------------------

# In-text citation token. Captures:
#   group 1: "Supplementary " | "Supp " | "" (supplementary marker)
#   group 2: Table | Figure
#   group 3: number, possibly S-prefixed, with optional letter suffix (e.g. S4, 2A)
CITE_RE = re.compile(
    r"(?<![A-Za-z])(Supplementary\s+|Supp\s+|Supp\.\s+|S\.\s*)?"
    r"(Table|Figure|Fig\.|Fig)\s+"
    r"(S?\d+[A-Za-z]?)",
    re.IGNORECASE,
)

# Caption definition (start of line, optional bold markdown). Matches:
#   Table 1. Caption text...
#   **Table 1.** Caption...
#   Supplementary Table S4. Caption...
CAPTION_RE = re.compile(
    r"^\s*(?:\*\*)?\s*"
    r"(Supplementary\s+|Supp\s+|Supp\.\s+)?"
    r"(Table|Figure|Fig\.|Fig)\s+"
    r"(S?\d+[A-Za-z]?)"
    r"\s*[.:]\s*(?:\*\*)?\s*"
    r"(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Section header patterns for the manuscript body's caption sections
CAPTION_SECTION_RE = re.compile(
    r"^#{1,3}\s+(Tables|Figures|Figure\s+Legends|Supplementary\s+Tables|"
    r"Supplementary\s+Figures|Supplementary\s+Materials?)\b",
    re.IGNORECASE | re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Label:
    """Canonical (kind, supplementary, number) tuple for a Table/Figure."""
    kind: str           # "Table" | "Figure"
    supplementary: bool
    number: str         # "1", "S4", "2A"

    @property
    def key(self) -> str:
        prefix = "S-" if self.supplementary else ""
        return f"{self.kind}:{prefix}{self.number}"

    @property
    def display(self) -> str:
        supp = "Supplementary " if self.supplementary else ""
        return f"{supp}{self.kind} {self.number}"


@dataclass
class Caption:
    label: Label
    text: str
    source: str  # "body" | "docx"


@dataclass
class Finding:
    label: str
    status: str          # OK | MISSING_DOCX | MISSING_BODY | MISMATCH | UNCITED | NOT_CITED_NO_BODY
    cited: bool
    in_body: bool
    in_docx: Optional[bool]   # None if --docx not provided
    body_caption: Optional[str]
    docx_caption: Optional[str]
    note: str = ""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _normalize(kind_raw: str, supp_raw: Optional[str], number: str) -> Label:
    kind = "Figure" if kind_raw.lower().startswith("fig") else "Table"
    supplementary = bool(supp_raw) or number.upper().startswith("S")
    # Normalize number capitalization (S4a -> S4A, lowercase letter suffix uppercase)
    if len(number) > 1 and number[-1].isalpha():
        number = number[:-1].upper() + number[-1].upper()
    else:
        number = number.upper() if number.upper().startswith("S") else number
    return Label(kind=kind, supplementary=supplementary, number=number)


def extract_citations(md_text: str, body_caption_offsets: list[tuple[int, int]]) -> list[Label]:
    """Extract in-text citations excluding ranges that are caption sections."""
    # Mask caption sections so caption first lines don't double as citations
    masked = list(md_text)
    for start, end in body_caption_offsets:
        for i in range(start, min(end, len(masked))):
            masked[i] = " "
    text = "".join(masked)

    # Strip fenced code
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]+`", "", text)

    labels: list[Label] = []
    for m in CITE_RE.finditer(text):
        labels.append(_normalize(m.group(2), m.group(1), m.group(3)))
    return labels


def find_caption_section_ranges(md_text: str) -> list[tuple[int, int]]:
    """Return (start, end) byte offsets for body caption sections."""
    headers = list(CAPTION_SECTION_RE.finditer(md_text))
    ranges: list[tuple[int, int]] = []
    for i, h in enumerate(headers):
        start = h.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(md_text)
        # If next non-caption section header appears (## something else), cut there
        # Find next ^#{1,3}\s heading after start that is NOT a caption section
        next_section = re.search(r"\n#{1,3}\s+\S", md_text[h.end():end])
        if next_section:
            tentative_end = h.end() + next_section.start()
            # Only cut if the next heading is not itself a caption section
            after = md_text[h.end() + next_section.start():end]
            if not CAPTION_SECTION_RE.match(after):
                end = tentative_end
        ranges.append((start, end))
    return ranges


def extract_body_captions(md_text: str) -> dict[str, Caption]:
    """Extract caption definitions from the manuscript body's caption sections."""
    ranges = find_caption_section_ranges(md_text)
    captions: dict[str, Caption] = {}
    for start, end in ranges:
        chunk = md_text[start:end]
        for m in CAPTION_RE.finditer(chunk):
            label = _normalize(m.group(2), m.group(1), m.group(3))
            text = m.group(4).strip().rstrip("*").strip()
            # Keep first definition per label (later ones likely continuation lines)
            if label.key not in captions:
                captions[label.key] = Caption(label=label, text=text, source="body")
    return captions


def extract_docx_captions(docx_path: Path) -> dict[str, Caption]:
    """Extract caption paragraphs from a rendered DOCX using python-docx."""
    try:
        from docx import Document  # type: ignore
    except ImportError:
        print(
            "[check_xref] WARNING: python-docx not installed; "
            "skipping rendered-DOCX audit. Install with: pip install python-docx",
            file=sys.stderr,
        )
        return {}

    doc = Document(str(docx_path))
    captions: dict[str, Caption] = {}
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        m = CAPTION_RE.match(text)
        if not m:
            continue
        label = _normalize(m.group(2), m.group(1), m.group(3))
        caption_text = m.group(4).strip()
        if label.key not in captions:
            captions[label.key] = Caption(label=label, text=caption_text, source="docx")

    # Also scan tables (Word can put captions in adjacent paragraphs that are inside cells
    # or before the table). The paragraph scan above is usually sufficient.
    return captions


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z][A-Za-z0-9]+", text.lower()))


def caption_agreement(a: str, b: str, threshold: float = 0.4) -> tuple[bool, float]:
    """Heuristic agreement: Jaccard token overlap >= threshold = agree."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False, 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    j = inter / union if union else 0.0
    return j >= threshold, j


def reconcile(
    citations: list[Label],
    body: dict[str, Caption],
    docx: Optional[dict[str, Caption]],
) -> list[Finding]:
    cited_keys = {lbl.key for lbl in citations}
    body_keys = set(body.keys())
    docx_keys = set(docx.keys()) if docx is not None else set()
    all_keys = cited_keys | body_keys | docx_keys

    findings: list[Finding] = []
    for key in sorted(all_keys, key=_sort_key):
        is_cited = key in cited_keys
        in_body = key in body_keys
        in_docx = (key in docx_keys) if docx is not None else None

        body_text = body[key].text if in_body else None
        docx_text = docx[key].text if (docx is not None and key in docx_keys) else None

        # Panel-letter fallback: "Figure 2A" cite resolves to "Figure 2" caption.
        panel_note = ""
        if is_cited and not in_body:
            base = _strip_panel(key)
            if base and base in body_keys:
                in_body = True
                body_text = body[base].text
                panel_note = f"panel reference; resolved to {base.replace(':', ' ')}"
        if is_cited and in_docx is False:
            base = _strip_panel(key)
            if base and base in docx_keys:
                in_docx = True
                docx_text = docx[base].text  # type: ignore[index]
                panel_note = (panel_note + "; " if panel_note else "") + \
                    f"panel reference resolved to {base.replace(':', ' ')} in DOCX"

        status, note = _classify(is_cited, in_body, in_docx, body_text, docx_text)
        if panel_note and status == "OK":
            note = panel_note

        findings.append(Finding(
            label=key,
            status=status,
            cited=is_cited,
            in_body=in_body,
            in_docx=in_docx,
            body_caption=body_text,
            docx_caption=docx_text,
            note=note,
        ))
    return findings


def _strip_panel(key: str) -> Optional[str]:
    """Map 'Figure:2A' -> 'Figure:2' (panel letter strip). Returns None if no change."""
    kind, num = key.split(":", 1)
    m = re.match(r"^(S?)(\d+)([A-Z])$", num)
    if m and m.group(3):
        return f"{kind}:{m.group(1)}{m.group(2)}"
    return None


def _classify(
    cited: bool,
    in_body: bool,
    in_docx: Optional[bool],
    body_text: Optional[str],
    docx_text: Optional[str],
) -> tuple[str, str]:
    if not cited:
        if in_body or in_docx:
            return "UNCITED", "defined or rendered but never cited in main text"
        return "NOT_CITED_NO_BODY", ""

    # Cited
    if in_docx is False:
        return "MISSING_DOCX", "cited but absent from rendered DOCX"
    if not in_body and in_docx is None:
        return "MISSING_BODY", "cited but no caption definition in markdown body sections"
    if not in_body and in_docx:
        return "MISSING_BODY", "cited and rendered, but no body caption definition (build SSOT drift risk)"

    # Both body and docx (or body only when in_docx is None)
    if body_text and docx_text:
        agree, j = caption_agreement(body_text, docx_text)
        if not agree:
            return "MISMATCH", f"caption text disagrees (Jaccard={j:.2f})"
    return "OK", ""


def _sort_key(key: str) -> tuple:
    # "Table:S4" -> ("Table", 1, 4) ; "Figure:2A" -> ("Figure", 0, 2, "A")
    kind, num = key.split(":", 1)
    is_supp = 1 if num.startswith("S") else 0
    digits = num.lstrip("S")
    m = re.match(r"^(\d+)([A-Z]?)$", digits)
    if m:
        return (kind, is_supp, int(m.group(1)), m.group(2))
    return (kind, is_supp, 999, digits)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render_summary(findings: list[Finding], cited_count: int) -> str:
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.status] = counts.get(f.status, 0) + 1

    lines = []
    lines.append(f"\n[check_xref] in-text citations: {cited_count}, unique labels: {len(findings)}")
    lines.append("Status summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    lines.append("")
    lines.append(f"  {'LABEL':<14} {'STATUS':<18} {'CITED':<6} {'BODY':<5} {'DOCX':<5} NOTE")
    for f in findings:
        docx_mark = "—" if f.in_docx is None else ("✓" if f.in_docx else "✗")
        lines.append(
            f"  {f.label:<14} {f.status:<18} "
            f"{'✓' if f.cited else '✗':<6} "
            f"{'✓' if f.in_body else '✗':<5} "
            f"{docx_mark:<5} {f.note}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--md", required=True, type=Path, help="manuscript.md path")
    parser.add_argument("--docx", type=Path, default=None, help="rendered DOCX path (optional)")
    parser.add_argument("--out", type=Path, default=Path("qc/xref_audit.json"))
    parser.add_argument("--strict", action="store_true", help="exit 1 on any non-OK finding")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if not args.md.exists():
        print(f"ERROR: markdown not found: {args.md}", file=sys.stderr)
        return 2

    md_text = args.md.read_text(encoding="utf-8")
    section_ranges = find_caption_section_ranges(md_text)
    citations = extract_citations(md_text, section_ranges)
    body_captions = extract_body_captions(md_text)

    docx_captions: Optional[dict[str, Caption]] = None
    if args.docx is not None:
        if not args.docx.exists():
            print(f"ERROR: docx not found: {args.docx}", file=sys.stderr)
            return 2
        docx_captions = extract_docx_captions(args.docx)

    findings = reconcile(citations, body_captions, docx_captions)

    # Submission safety: any cited label whose status is not OK or UNCITED is a blocker.
    blocking_statuses = {"MISSING_DOCX", "MISSING_BODY", "MISMATCH"}
    blockers = [f for f in findings if f.status in blocking_statuses]
    submission_safe = len(blockers) == 0

    payload = {
        "version": "1.0",
        "manuscript": str(args.md),
        "docx": str(args.docx) if args.docx else None,
        "summary": {
            "total_in_text_citations": len(citations),
            "unique_labels": len(findings),
            "ok": sum(1 for f in findings if f.status == "OK"),
            "missing_docx": sum(1 for f in findings if f.status == "MISSING_DOCX"),
            "missing_body": sum(1 for f in findings if f.status == "MISSING_BODY"),
            "mismatch": sum(1 for f in findings if f.status == "MISMATCH"),
            "uncited": sum(1 for f in findings if f.status == "UNCITED"),
        },
        "submission_safe": submission_safe,
        "findings": [asdict(f) for f in findings],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print(render_summary(findings, len(citations)))
        print(f"\n[check_xref] wrote {args.out}")
        if not submission_safe:
            print(f"[check_xref] SUBMISSION BLOCKED: {len(blockers)} cross-reference defect(s).")

    if args.strict and not submission_safe:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

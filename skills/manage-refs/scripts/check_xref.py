#!/usr/bin/env python3
"""check_xref.py — Manuscript ↔ rendered DOCX cross-reference QC.

Catches the failure mode where in-text references to Tables / Figures /
Supplementary Tables / Supplementary Figures point to labels that either
(a) do not exist in the rendered DOCX, (b) have no caption definition in
the manuscript body, or (c) carry a caption text in the rendered DOCX
that disagrees with the body's caption definition.

Precedent: an STROBE cohort manuscript revision — body cited
"Supp Table S4 (a sensitivity-analysis)" but the rendered DOCX S4 was
a diagnostics table; S1, S6, S7 mismatched; S8, S9 cited but absent
from DOCX. Internal consistency checks did not catch this because the
build script carried its own legacy SSOT.

Inputs
------
  --md PATH         manuscript markdown (the in-text citation source)
  --docx PATH       rendered DOCX (optional but recommended)
  --out PATH        JSON audit (default: qc/xref_audit.json)
  --strict          exit 1 on any non-OK finding (submission gate)
  --quiet           suppress stdout summary table
  --vN-docx-md5 PATH
                    v_N (previous version) docx path. When supplied:
                    (a) asserts the new --docx MD5 differs from this docx
                        (identity = unmodified seed copy);
                    (b) when --vN-md is also supplied, computes the
                        markdown-only diff and verifies each diff line
                        appears verbatim in the new docx body XML.
  --vN-md PATH      v_N markdown path (used by --vN-docx-md5 diff check).

v_(N+1) docx regeneration check
-------------------------------
Defense-in-depth at build time (complements verify_package_integrity.py
--assert-vN-docx-changed which runs at submission time). If a markdown
body change exists between v_N and v_(N+1) but the v_(N+1) docx is a
byte-identical copy of v_N, the change will silently revert at peer
review. The check fails fast at the QC stage.

Output
------
  qc/xref_audit.json with submission_safe boolean and per-label rows.
  When --vN-docx-md5 is used, the JSON also carries a `vN_docx_check`
  block with `identical_bytes` and `diff_line_misses` fields.

Exit codes
----------
  0  all OK (or non-strict and only warnings)
  1  --strict and at least one non-OK finding
     OR v_N docx identity / diff-miss assertion failure
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

# The same mention written the way people actually write it: a PLURAL kind word carrying a list of
# numbers — "Figures 1 and 2", "Tables 1-3", "Figures 2, 4 and 5". CITE_RE cannot see any of these
# (the plural "s" breaks its `\s+`), and the consequence was not a missed note but a DISABLED GATE:
# a float cited only this way scored UNCITED rather than MISSING_DOCX, and UNCITED is not in
# `blocking_statuses`. Two manuscripts identical in meaning got opposite verdicts —
#   "Figures 1 and 2"       -> exit 0, submission_safe
#   "Figure 1 and Figure 2" -> exit 1, SUBMISSION BLOCKED
# — so writing ordinary English turned the blocker off, while the repetitive form this tool's own
# examples happen to use kept it on.
CITE_LIST_RE = re.compile(
    r"(?<![A-Za-z])(Supplementary\s+|Supp\s+|Supp\.\s+|S\.\s*)?"
    r"(Tables|Figures|Figs\.|Figs)\s+"
    r"(S?\d+[A-Za-z]?(?:\s*(?:,|&|–|—|-|and|to|through)\s*S?\d+[A-Za-z]?)*)",
    re.IGNORECASE,
)

# One token inside a numlist, with an optional "A-B" range tail. A range must be EXPANDED: reading
# "Figures 1-3" as {1, 3} silently drops Figure 2 — the same missing-blocker outcome, one number in.
# The separators must match what CITE_LIST_RE accepts as a JOIN, or a form it lets through gets read
# as two endpoints and the interior is dropped: "Figures 3 to 5" scoring {3, 5} loses Figure 4 exactly
# as an unexpanded "3-5" would.
CITE_TOKEN_RE = re.compile(
    r"(S?)(\d+)([A-Za-z]?)(?:\s*(?:[–—-]|to|through)\s*(S?)(\d+)([A-Za-z]?))?", re.IGNORECASE)

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

# Section header patterns for the manuscript body's caption sections.
# Longer alternatives MUST come first so that "FIGURE LEGENDS" is not
# truncated to "FIGURE" by an earlier short match.
# Markdown bold wrappers (``## **FIGURE LEGENDS**``) are tolerated.
CAPTION_SECTION_RE = re.compile(
    r"^#{1,3}\s+\*{0,2}"
    r"(Supplementary\s+Tables?|Supplementary\s+Figures?|Supplementary\s+Materials?|"
    r"Figure\s+Legends?|Table\s+(?:Captions?|Legends?)|"
    r"Tables?|Figures?)"
    r"\*{0,2}",
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
    # Plural mentions carrying a numlist. Singular "Figure" is a prefix of plural "Figures", so the
    # two patterns cannot both match the same span and no citation is double-counted.
    for m in CITE_LIST_RE.finditer(text):
        supp, kind, numlist = m.group(1), m.group(2), m.group(3)
        # Normalise the plural kind word to the singular the label vocabulary uses.
        singular = "Table" if kind.lower().startswith("table") else "Figure"
        for supp_a, num_a, suf_a, supp_b, num_b, suf_b in CITE_TOKEN_RE.findall(numlist):
            if num_b and not suf_a and not suf_b and int(num_b) >= int(num_a):
                # A true range: expand it. A lettered endpoint ("2A-2C") is a panel range, not a
                # float range, so it is left to its endpoints rather than invented over.
                for n in range(int(num_a), int(num_b) + 1):
                    labels.append(_normalize(singular, supp, f"{supp_a}{n}"))
            else:
                labels.append(_normalize(singular, supp, f"{supp_a}{num_a}{suf_a}"))
                if num_b:
                    labels.append(_normalize(singular, supp, f"{supp_b}{num_b}{suf_b}"))
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


def _md5_of(path: Path) -> str:
    import hashlib
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _docx_body_text(docx_path: Path) -> str:
    """Concatenate all w:t text content from a docx for substring search."""
    import zipfile
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError, OSError):
        return ""
    # Strip XML tags — we only need text content for verbatim grep.
    return re.sub(r"<[^>]+>", " ", xml)


def _markdown_diff_lines(vN_md: Path, new_md: Path) -> list[str]:
    """Lines present in new_md but not in vN_md (added/changed lines).

    Trimmed to non-trivial substrings (≥40 chars after stripping markdown
    metacharacters) so that the verbatim grep is meaningful.
    """
    old_lines = set(vN_md.read_text(encoding="utf-8").splitlines())
    out: list[str] = []
    for ln in new_md.read_text(encoding="utf-8").splitlines():
        if ln in old_lines:
            continue
        # Strip leading markdown noise (headers, list markers) and YAML.
        clean = re.sub(r"^[\s#>*\-_+~`|]+", "", ln).strip()
        if len(clean) >= 40:
            out.append(clean)
    return out


def run_vN_docx_check(
    new_docx: Path,
    vN_docx: Path,
    new_md: Path | None,
    vN_md: Path | None,
) -> dict:
    """Returns {identical_bytes, diff_line_misses, error?}.

    identical_bytes is True if v_N and new docx have the same MD5.
    diff_line_misses lists v_N→v_(N+1) markdown additions that do NOT
    appear in the new docx body XML.
    """
    out: dict = {
        "vN_docx": str(vN_docx),
        "new_docx": str(new_docx),
        "identical_bytes": False,
        "diff_line_misses": [],
    }
    if not vN_docx.is_file():
        out["error"] = f"v_N docx not found: {vN_docx}"
        return out
    if not new_docx.is_file():
        out["error"] = f"new docx not found: {new_docx}"
        return out
    if _md5_of(vN_docx) == _md5_of(new_docx):
        out["identical_bytes"] = True
        return out  # Identity already disqualifies — no point checking diff.

    if new_md is not None and vN_md is not None:
        if not new_md.is_file() or not vN_md.is_file():
            out["error"] = "v_N md or new md not found"
            return out
        diff_lines = _markdown_diff_lines(vN_md, new_md)
        body_text = _docx_body_text(new_docx)
        # Light normalization: collapse runs of whitespace.
        body_norm = re.sub(r"\s+", " ", body_text).lower()
        misses: list[str] = []
        for diff in diff_lines:
            needle = re.sub(r"\s+", " ", diff).lower()
            if needle not in body_norm:
                misses.append(diff[:120])
        out["diff_line_misses"] = misses
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--md", required=True, type=Path, help="manuscript.md path")
    parser.add_argument("--docx", type=Path, default=None, help="rendered DOCX path (optional)")
    parser.add_argument("--out", type=Path, default=Path("qc/xref_audit.json"))
    parser.add_argument("--strict", action="store_true", help="exit 1 on any non-OK finding")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--allow-separate-attachments", action="store_true",
        help="Declare that some figures/tables are submitted as separate attachment "
             "files rather than inline (the norm in radiology and most medical "
             "journals). Downgrades two things from FAIL to WARN: MISSING_DOCX, where "
             "a supplied --docx proved the float is not in the rendered main document; "
             "and MISSING_BODY where NO --docx was supplied, so nothing was checked and "
             "the float is excused on your word. Those two are reported separately "
             "because only the first has evidence behind it. Still FAIL regardless: "
             "MISMATCH, and MISSING_BODY where the float IS in the rendered DOCX but "
             "nothing in the markdown defines its caption — that is SSOT drift, which "
             "no attachment policy makes acceptable. Run with --docx before submitting.",
    )
    parser.add_argument(
        "--vN-docx-md5",
        dest="vN_docx_md5",
        type=Path,
        default=None,
        help=(
            "v_N docx path. Asserts the new --docx MD5 != this docx. "
            "Identity = unmodified seed copy = FAIL."
        ),
    )
    parser.add_argument(
        "--vN-md",
        dest="vN_md",
        type=Path,
        default=None,
        help=(
            "v_N manuscript markdown path (companion to --vN-docx-md5). "
            "When supplied, every line added in v_(N+1) markdown must "
            "appear verbatim in the new docx body XML; missing diff "
            "lines fail."
        ),
    )
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
    #
    # --allow-separate-attachments is a declaration by the operator: "some of this
    # manuscript's floats are submitted as separate attachment files, not inline."
    # That is the normal packaging for radiology and most medical journals. Under it,
    # two situations are downgraded to warnings — and they are NOT equally well
    # evidenced, so they are reported apart:
    #
    #   MISSING_DOCX                    a DOCX was supplied and PROVED the float is not
    #                                   in the rendered main document. Evidence exists.
    #   MISSING_BODY with in_docx None  no DOCX was supplied, so nothing was checked.
    #                                   The float may equally be a caption someone
    #                                   forgot to write. Excused on the operator's word.
    #
    # MISSING_BODY with in_docx True stays a blocker under every policy: the float IS
    # rendered and nothing in the markdown defines its caption, so the build pipeline
    # is the only place that knows the text. That is SSOT drift, and no attachment
    # policy makes it acceptable. MISMATCH likewise.
    if args.allow_separate_attachments:
        blockers = [
            f for f in findings
            if f.status == "MISMATCH"
            or (f.status == "MISSING_BODY" and f.in_docx is True)
        ]
        proven_absent = [f for f in findings if f.status == "MISSING_DOCX"]
        unchecked = [
            f for f in findings
            if f.status == "MISSING_BODY" and f.in_docx is None
        ]
        warnings = proven_absent + unchecked
    else:
        blocking_statuses = {"MISSING_DOCX", "MISSING_BODY", "MISMATCH"}
        blockers = [f for f in findings if f.status in blocking_statuses]
        proven_absent = []
        unchecked = []
        warnings = []
    submission_safe = len(blockers) == 0

    vN_check: dict | None = None
    vN_check_failed = False
    if args.vN_docx_md5 is not None:
        if args.docx is None:
            print(
                "ERROR: --vN-docx-md5 requires --docx (the new manuscript docx).",
                file=sys.stderr,
            )
            return 2
        vN_check = run_vN_docx_check(
            new_docx=args.docx,
            vN_docx=args.vN_docx_md5,
            new_md=args.md,
            vN_md=args.vN_md,
        )
        if vN_check.get("error"):
            print(f"ERROR: vN docx check: {vN_check['error']}", file=sys.stderr)
            return 2
        if vN_check["identical_bytes"]:
            vN_check_failed = True
        if vN_check["diff_line_misses"]:
            vN_check_failed = True

    payload = {
        "version": "1.2",
        "manuscript": str(args.md),
        "docx": str(args.docx) if args.docx else None,
        "policy": {
            "allow_separate_attachments": bool(args.allow_separate_attachments),
        },
        "summary": {
            "total_in_text_citations": len(citations),
            "unique_labels": len(findings),
            "ok": sum(1 for f in findings if f.status == "OK"),
            "missing_docx": sum(1 for f in findings if f.status == "MISSING_DOCX"),
            "missing_body": sum(1 for f in findings if f.status == "MISSING_BODY"),
            "mismatch": sum(1 for f in findings if f.status == "MISMATCH"),
            "uncited": sum(1 for f in findings if f.status == "UNCITED"),
            "blockers": len(blockers),
            "warnings": len(warnings),
            # The two downgrades kept apart, because a consumer that treats them alike
            # cannot tell a float the DOCX proved absent from one nothing ever checked.
            "downgraded_proven_absent": len(proven_absent),
            "downgraded_unchecked": len(unchecked),
        },
        "downgraded_unchecked_labels": [f.label for f in unchecked],
        "submission_safe": submission_safe and not vN_check_failed,
        "findings": [asdict(f) for f in findings],
        "vN_docx_check": vN_check,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"detector": "check_xref", **payload}, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print(render_summary(findings, len(citations)))
        print(f"\n[check_xref] wrote {args.out}")
        # The two downgrades are printed apart because their evidence differs, and the
        # weaker one has to stay visible. Merging them into one count is how an excused
        # row starts reading like a checked one.
        if proven_absent:
            print(
                f"[check_xref] WARN: {len(proven_absent)} MISSING_DOCX row(s) downgraded under "
                f"--allow-separate-attachments: " + ", ".join(f.label for f in proven_absent) + "\n"
                f"           The DOCX was read and does not contain them, which is what a "
                f"separate attachment looks like."
            )
        if unchecked:
            print(
                f"[check_xref] WARN: {len(unchecked)} MISSING_BODY row(s) EXCUSED WITHOUT "
                f"EVIDENCE under --allow-separate-attachments:\n"
                f"           " + ", ".join(f.label for f in unchecked) + "\n"
                f"           No --docx was supplied, so nothing here was actually checked. Each "
                f"of these is either a float in a\n"
                f"           separate supplement file — which is what you declared — or a caption "
                f"nobody wrote. This run cannot\n"
                f"           tell them apart, and passed them on your word.\n"
                f"           Run again with --docx <rendered.docx> before submitting: a float "
                f"genuinely absent from the rendered\n"
                f"           output becomes MISSING_DOCX (still downgraded, but now proven), and "
                f"a caption you forgot becomes visible."
            )
        if not submission_safe:
            print(f"[check_xref] SUBMISSION BLOCKED: {len(blockers)} cross-reference defect(s).")
            drift = [f for f in blockers
                     if f.status == "MISSING_BODY" and f.in_docx is True]
            if drift and args.allow_separate_attachments:
                print(
                    f"[check_xref] NOTE: {len(drift)} of those are MISSING_BODY that "
                    f"--allow-separate-attachments does NOT excuse "
                    f"({', '.join(f.label for f in drift)}).\n"
                    f"           These floats ARE in the rendered DOCX while nothing in the "
                    f"markdown defines their caption, so the\n"
                    f"           build pipeline is the only place that knows the text. That is "
                    f"SSOT drift, not attachment style."
                )
        if vN_check is not None:
            if vN_check["identical_bytes"]:
                print(
                    "[check_xref] FAIL: v_(N+1) docx is byte-identical to "
                    "v_N docx — unmodified seed copy, regenerate via "
                    "pandoc / Zotero CWYW."
                )
            elif vN_check["diff_line_misses"]:
                print(
                    f"[check_xref] FAIL: {len(vN_check['diff_line_misses'])} "
                    "markdown diff line(s) absent from new docx body. "
                    "v_(N+1) docx body did not pick up the markdown edits."
                )
                for miss in vN_check["diff_line_misses"][:5]:
                    print(f"    - {miss}")

    block_exit = args.strict and not submission_safe
    if block_exit or vN_check_failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

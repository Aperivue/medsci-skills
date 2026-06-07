"""Claim extraction + deterministic provenance pre-fill for E5.

Extracts candidate claims from a demo manuscript, classifies them, and for
numerical claims attempts to trace the value to an analysis table cell, the
dataset manifest, and a QC/analysis-output artifact. Only exact-cell matches
earn an auto "complete" score; looser matches are downgraded to "partial" with a
match_confidence flag so a human can audit them. Provenance completeness is
scored, never claim correctness or quality.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# anchored numeric values: a metric keyword near a number, a CI range, an N, or a %
_METRIC = (r"AUC|AUROC|OR|aOR|HR|RR|sHR|sensitivity|specificity|PPV|NPV|accuracy|"
           r"Brier|I2|I²|kappa|κ|prevalence|RR|risk ratio|odds ratio")
NUM_ANCHORED = re.compile(
    rf"(?:\b(?:{_METRIC})\b)[^\n.]{{0,25}}?(\d+\.\d+|\d+%)", re.IGNORECASE)
CI_RANGE = re.compile(r"(\d+\.\d+)\s*[–\-]\s*(\d+\.\d+)")
N_COUNT = re.compile(r"\bN\s*=\s*([\d,]{2,})|\b([\d,]{4,})\s+(?:participants|adults|patients|trials|studies|nodules|samples)", re.IGNORECASE)
PERCENT = re.compile(r"(\d+\.\d+)%")

CITE = re.compile(r"\[@[\w:-]+\]|\[\d+\]")
GUIDELINE = re.compile(r"\b(STARD|PRISMA|STROBE|TRIPOD|CONSORT|QUADAS|PROBAST)\b")
FIG_TAB = re.compile(r"\b(Table|Figure)\s+(\d+)", re.IGNORECASE)
METHOD = re.compile(
    r"logistic regression|random[-\s]?effects|fixed[-\s]?effects|DeLong|REML|"
    r"survey[-\s]?weighted|random forest|support vector|Wilson (?:score )?(?:interval|CI)|"
    r"Clopper[-\s]?Pearson|inverse[-\s]?variance|Mantel[-\s]?Haenszel|bivariate|HSROC",
    re.IGNORECASE)


@dataclass
class Claim:
    claim_id: str
    claim_type: str
    claim_text: str
    value: str = ""
    loc_line: int = 0


def _line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def _excerpt(text: str, start: int, end: int, pad: int = 40) -> str:
    s = text[max(0, start - pad):end + pad]
    return re.sub(r"\s+", " ", s).strip()[:160]


def extract(manuscript: str) -> list[Claim]:
    text = Path(manuscript).read_text(encoding="utf-8")
    claims: list[Claim] = []
    seen_vals: set = set()
    i = 0

    def add(ctype, m, value=""):
        nonlocal i
        i += 1
        claims.append(Claim(
            claim_id=f"C{i:03d}", claim_type=ctype,
            claim_text=_excerpt(text, m.start(), m.end()),
            value=value, loc_line=_line_of(text, m.start()),
        ))

    CI_LEVELS = {"90", "95", "99"}  # CI-level percentages are not data claims
    for m in NUM_ANCHORED.finditer(text):
        v = m.group(1)
        if v.endswith("%") and v.rstrip("%") in CI_LEVELS:
            continue
        key = ("num", v, m.start() // 200)
        if key in seen_vals:
            continue
        seen_vals.add(key)
        add("numerical", m, v)
    for m in CI_RANGE.finditer(text):
        # emit one claim per bound (each can match its own table cell)
        for v in (m.group(1), m.group(2)):
            key = ("num", v, m.start() // 200)
            if key in seen_vals:
                continue
            seen_vals.add(key)
            add("numerical", m, v)
    for m in N_COUNT.finditer(text):
        v = (m.group(1) or m.group(2) or "").replace(",", "")
        add("numerical", m, v)
    for m in PERCENT.finditer(text):
        add("numerical", m, m.group(1))
    for m in CITE.finditer(text):
        add("citation", m)
    for m in GUIDELINE.finditer(text):
        add("reporting", m, m.group(1))
    for m in FIG_TAB.finditer(text):
        add("figure_table", m, f"{m.group(1)} {m.group(2)}")
    for m in METHOD.finditer(text):
        add("analysis_method", m, m.group(0))
    return claims


# --- provenance sources ----------------------------------------------------

@dataclass
class Provenance:
    cell_values: set = field(default_factory=set)   # exact CSV cell strings
    csv_blob: str = ""                                # all CSV text (loose match)
    manifest_files: set = field(default_factory=set)
    outputs_md: str = ""
    qc_blob: str = ""
    script_blob: str = ""


def load_provenance(demo_root: Path) -> Provenance:
    p = Provenance()
    manifest = demo_root / "manifest.lock.json"
    if manifest.is_file():
        d = json.loads(manifest.read_text(encoding="utf-8"))
        p.manifest_files = set(d.get("files", {}).keys())
    tables = sorted((demo_root / "analysis" / "tables").glob("*.csv")) if (demo_root / "analysis" / "tables").is_dir() else []
    blobs = []
    for t in tables:
        txt = t.read_text(encoding="utf-8", errors="ignore")
        blobs.append(txt)
        for row in csv.reader(txt.splitlines()):
            for cell in row:
                p.cell_values.add(cell.strip())
    p.csv_blob = "\n".join(blobs)
    om = demo_root / "analysis" / "_analysis_outputs.md"
    if om.is_file():
        p.outputs_md = om.read_text(encoding="utf-8", errors="ignore")
    qcs = []
    if (demo_root / "qc").is_dir():
        for q in sorted((demo_root / "qc").glob("*")):
            if q.is_file():
                qcs.append(q.read_text(encoding="utf-8", errors="ignore"))
    p.qc_blob = "\n".join(qcs)
    scripts = []
    if (demo_root / "analysis").is_dir():
        for s in sorted((demo_root / "analysis").rglob("*")):
            if s.is_file() and s.suffix.lower() in (".py", ".r"):
                scripts.append(s.read_text(encoding="utf-8", errors="ignore"))
    p.script_blob = "\n".join(scripts)
    return p


def _num_in_cells(value: str, prov: Provenance) -> str:
    """Return 'exact' if value matches a full CSV cell (allowing rounded forms),
    'loose' if it appears as a substring of the CSV text or outputs md, else ''.
    """
    if not value:
        return ""
    base = value.rstrip("%")
    if base in prov.cell_values:
        return "exact"
    # rounded match: a cell that starts with the manuscript value (0.998 vs 0.9979)
    for cell in prov.cell_values:
        c = cell.strip()
        if c and (c.startswith(base) or base.startswith(c)) and len(base) >= 3:
            try:
                if abs(float(c) - float(base)) <= 0.005:
                    return "exact"
            except ValueError:
                pass
    if base and (base in prov.csv_blob or base in prov.outputs_md):
        return "loose"
    return ""


def score_claim(c: Claim, prov: Provenance) -> dict:
    qc = analysis_table = manifest = vcite = ""
    score = "missing"
    conf = ""
    auto = "auto"

    if c.claim_type == "numerical":
        conf = _num_in_cells(c.value, prov)
        if conf:
            analysis_table = "yes"
            # which file(s) in manifest carry tables
            has_table_in_manifest = any("analysis/tables/" in f for f in prov.manifest_files)
            manifest = "yes" if has_table_in_manifest else "no"
        base = c.value.rstrip("%")
        if base and base in prov.qc_blob:
            qc = "yes"
        if base and base in prov.outputs_md:
            qc = qc or "outputs_md"
        if conf == "exact" and manifest == "yes":
            score = "complete"
        elif conf in ("exact", "loose"):
            score = "partial"
        else:
            score = "missing"
    elif c.claim_type == "reporting":
        # trace to a vendored/produced reporting checklist artifact
        if "reporting_checklist" in prov.qc_blob or c.value.upper() in prov.qc_blob.upper():
            qc = "yes"
            score = "complete"
        else:
            score = "partial"
    elif c.claim_type == "analysis_method":
        if c.value and c.value.lower() in prov.script_blob.lower():
            analysis_table = "script"
            manifest = "yes" if prov.manifest_files else "no"
            score = "complete" if manifest == "yes" else "partial"
        else:
            score = "manual-only"
            auto = "manual"
    elif c.claim_type == "figure_table":
        score = "manual-only"
        auto = "manual"
    elif c.claim_type == "citation":
        # demos use [UNVERIFIED] placeholder references by design
        vcite = "placeholder"
        score = "manual-only"
        auto = "manual"

    return {
        "qc_artifact": qc, "analysis_table": analysis_table,
        "source_data_manifest": manifest, "verified_citation": vcite,
        "provenance_score": score, "match_confidence": conf, "auto_or_manual": auto,
    }

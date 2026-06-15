#!/usr/bin/env python3
"""Generate metadata/detectors_catalog.json — the MedSci-Audit detector registry.

Why: the repo ships 24 deterministic analysis-integrity detectors, but until now
they were only *counted* (`metadata/catalog_counts.json: integrity_detectors`),
never *enumerated* in a machine-readable single source of truth. This catalog
names and groups them so MEDSCI_AUDIT.md (and any external surface) can reference
one authoritative list instead of hand-maintaining a parallel copy. It is the
detector analogue of metadata/skills_catalog.json.

Discovery uses the EXACT same glob as scripts/validate_catalog_consistency.py:
`check_*.py`/`detect_*.py`/`derive_*.py`/`verify_refs.py` under `skills/*/scripts/`
ONLY — top-level `scripts/` validators (validate_*, repo-CI/host gates) are NOT
manuscript-integrity detectors and are excluded. So `detector_count` here equals
`catalog_counts.json::integrity_detectors` (24); the self-test asserts it.

Family: detectors have no in-file category, so each detector id is mapped to one
of a small set of audit families via the explicit table below (the v4.0.0
CHANGELOG groupings). An unmapped detector aborts generation (fail loud) so a new
detector must be deliberately categorized — exactly like gen_skills_catalog_json.py
fails on an unmapped owner_domain.

Stdlib-only, deterministic (sorted, no timestamps) so `--check` is meaningful.

Usage:
  python3 scripts/gen_detectors_catalog_json.py          # write metadata/detectors_catalog.json
  python3 scripts/gen_detectors_catalog_json.py --check   # verify in sync; exit 1 on drift (CI gate)
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
OUT = ROOT / "metadata" / "detectors_catalog.json"

# Same glob as validate_catalog_consistency.py (skills/*/scripts only).
DETECTOR_GLOBS = ("check_*.py", "detect_*.py", "derive_*.py", "verify_refs.py")

# detector id (filename stem) -> audit family key. Every detector found by the
# glob must appear here; an unmapped id fails generation (see build()).
FAMILY_BY_ID: dict[str, str] = {
    # Numerical, cohort & pool arithmetic
    "check_cohort_arithmetic": "numerical_cohort",
    "check_artifact_coverage": "numerical_cohort",
    "check_pool_consistency": "numerical_cohort",
    "detect_copy_divergence": "numerical_cohort",
    "derive_figure_legend_counts": "numerical_cohort",
    # Citation & reference integrity
    "verify_refs": "citation_reference",
    "check_citation_keys": "citation_reference",
    "check_xref": "citation_reference",
    "check_csl_render": "citation_reference",
    "check_reference_adequacy": "citation_reference",
    "check_placeholders": "citation_reference",
    # Style & review-process integrity
    "check_classical_style": "style_review",
    "check_generated_code": "style_review",
    "check_panel_diversity": "style_review",
    "check_reviewer_team_consistency": "style_review",
    "check_paren_spans": "style_review",
    # Confounding, scope & estimand contracts
    "check_scope_coherence": "confounding_scope_estimand",
    "check_confounding_completeness": "confounding_scope_estimand",
    "check_claim_artifact": "confounding_scope_estimand",
    # Reporting compliance
    "check_framework_naming": "reporting_compliance",
    "check_checklist_exists": "reporting_compliance",
    "check_checklist_version": "reporting_compliance",
    "check_prisma_figure": "reporting_compliance",
    "check_wordcount_cap": "reporting_compliance",
    # Data preparation & validation
    "check_structural_zero": "data_preparation",
    "check_asset_anonymization": "data_preparation",
    "check_cross_artifact_stale": "data_preparation",
}

# Stable display order + human labels for the families array.
FAMILY_ORDER = [
    "numerical_cohort",
    "citation_reference",
    "style_review",
    "confounding_scope_estimand",
    "reporting_compliance",
    "data_preparation",
]
FAMILY_LABELS = {
    "numerical_cohort": "Numerical, cohort & pool arithmetic",
    "citation_reference": "Citation & reference integrity",
    "style_review": "Style & review-process integrity",
    "confounding_scope_estimand": "Confounding, scope & estimand contracts",
    "reporting_compliance": "Reporting compliance",
    "data_preparation": "Data preparation & validation",
}


class DetectorError(Exception):
    """Raised when a detector cannot be parsed into a valid catalog entry."""


def _doc_summary(path: Path, cap: int = 200) -> str:
    """First sentence of the module docstring's opening paragraph, with a leading
    `<filename>.py —/:/- ` self-reference stripped. Mirrors gen_skills_catalog_json's
    short_desc (first sentence, capped) but collapses a wrapped opening paragraph
    first so a sentence that spans lines is not truncated. Empty string if none."""
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    except (SyntaxError, ValueError):
        return ""
    if not doc:
        return ""
    # Opening paragraph: lines up to the first blank line, whitespace-collapsed.
    para_lines: list[str] = []
    for line in doc.strip().splitlines():
        if line.strip() == "":
            break
        para_lines.append(line.strip())
    para = re.sub(r"^[\w.]+\.py\s*[—:\-]\s*", "", " ".join(para_lines)).strip()
    if not para:
        return ""
    # First sentence (ends at ". "), capped — same rule as the skills catalog.
    end = len(para)
    p = para.find(". ")
    if p != -1:
        end = p + 1
    end = min(end, cap)
    s = para[:end].rstrip()
    if end < len(para) and not s.endswith("."):
        s += "…"
    return s


def build(skills_dir: Path = SKILLS_DIR) -> dict:
    if not skills_dir.is_dir():
        raise DetectorError(f"{skills_dir} directory not found")
    paths = sorted(
        {p for g in DETECTOR_GLOBS for p in skills_dir.glob(f"*/scripts/{g}")},
        key=lambda p: p.stem,
    )
    if not paths:
        raise DetectorError("no detectors found under */scripts/")

    detectors: list[dict] = []
    for p in paths:
        det_id = p.stem
        # skills_dir/<skill>/scripts/<file>.py -> <skill>
        skill = p.parent.parent.name
        if det_id not in FAMILY_BY_ID:
            raise DetectorError(
                f"{det_id} ({skill}) is not mapped to a family in "
                "gen_detectors_catalog_json.py (FAMILY_BY_ID). Add it before release."
            )
        family = FAMILY_BY_ID[det_id]
        desc = _doc_summary(p)
        if not desc:
            raise DetectorError(f"{det_id}: no module docstring to derive a description from")
        detectors.append({
            "id": det_id,
            "skill": skill,
            "family": family,
            "family_label": FAMILY_LABELS[family],
            "description": desc,
        })

    by_family: dict[str, list[str]] = {k: [] for k in FAMILY_ORDER}
    for d in detectors:
        by_family[d["family"]].append(d["id"])
    families = [
        {"key": k, "label": FAMILY_LABELS[k], "ids": sorted(by_family[k])}
        for k in FAMILY_ORDER
        if by_family[k]
    ]

    return {
        "_comment": (
            "AUTO-GENERATED by scripts/gen_detectors_catalog_json.py from the "
            "analysis-integrity detectors under skills/*/scripts/ (same glob as "
            "validate_catalog_consistency.py). Machine-readable registry of the "
            "MedSci-Audit detector suite (single source of truth). Do not hand-edit; "
            "CI gate: python3 scripts/gen_detectors_catalog_json.py --check."
        ),
        "detector_count": len(detectors),
        "families": families,
        "detectors": detectors,
    }


def render(catalog: dict) -> str:
    return json.dumps(catalog, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate metadata/detectors_catalog.json.")
    ap.add_argument("--check", action="store_true",
                    help="verify the catalog is in sync; exit 1 on drift (CI gate)")
    ap.add_argument("--skills-dir", type=Path, default=SKILLS_DIR,
                    help="skills/ directory to scan (default: repo skills/; for tests)")
    ap.add_argument("--out", type=Path, default=OUT,
                    help="output JSON path (default: metadata/detectors_catalog.json)")
    args = ap.parse_args()

    try:
        content = render(build(args.skills_dir))
    except DetectorError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    out = args.out
    if args.check:
        if not out.exists():
            print(f"DETECTORS_CATALOG_DRIFT — MISSING {out}; run "
                  "`python3 scripts/gen_detectors_catalog_json.py`", file=sys.stderr)
            return 1
        if out.read_text(encoding="utf-8") != content:
            print(f"DETECTORS_CATALOG_DRIFT — {out} out of sync; run "
                  "`python3 scripts/gen_detectors_catalog_json.py`", file=sys.stderr)
            return 1
        catalog = json.loads(content)
        print(f"OK: {out} in sync ({catalog['detector_count']} detectors, "
              f"{len(catalog['families'])} families).")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    catalog = json.loads(content)
    print(f"OK: wrote {out} ({catalog['detector_count']} detectors, "
          f"{len(catalog['families'])} families).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

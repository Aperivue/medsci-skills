#!/usr/bin/env python3
"""Generate .claude-plugin/marketplace.json — the Claude Code plugin marketplace.

Why: the one-line `/plugin marketplace add Aperivue/medsci-skills` + `/plugin`
discovery flow is the highest-ROI distribution channel for this repo. Rather than
one monolithic plugin, the 8 research-lifecycle categories already defined in
`metadata/skills_catalog.json` become 8 themed `medsci-*` plugins, so a user can
browse and enable just the categories they want.

This is a PURE DOWNSTREAM TRANSFORM of metadata/skills_catalog.json (it does NOT
re-scan skills/), keeping the single-source chain intact:
  skills/<slug>/{SKILL.md,skill.yml}
    -> metadata/skills_catalog.json   (gen_skills_catalog_json.py, --check-gated)
    -> .claude-plugin/marketplace.json (this script, --check-gated)
The only non-SSOT inputs are the two hand-authored tables below (plugin short
names + public-facing descriptions), mirroring how gen_skills_catalog_json.py
hand-authors CATEGORY_BY_OWNER_DOMAIN. A catalog category with no plugin mapping
aborts generation (fail loud) so a new category is deliberately surfaced.

Version semantics: this marketplace serves from `main` HEAD (no release cut), so
NO `version` is emitted at the marketplace top level or per plugin — each commit
is a new version via its git SHA. The marketplace top-level `version` does NOT
control plugin updates (that is each plugin entry's `version`), so emitting one
would falsely imply control. Consequence: this generator has no version logic and
no CITATION.cff coupling — marketplace.json is a pure function of the catalog +
the tables below (deterministic, so `--check` is meaningful).

Stdlib-only, deterministic (sorted, no timestamps).

Usage:
  python3 scripts/gen_marketplace_json.py          # write .claude-plugin/marketplace.json
  python3 scripts/gen_marketplace_json.py --check   # verify in sync; exit 1 on drift (CI gate)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "metadata" / "skills_catalog.json"
OUT = ROOT / ".claude-plugin" / "marketplace.json"

# Editor/validation hint only; runtime ignores it. URL the current Anthropic
# official repo uses (anthropics/claude-code/.claude-plugin/marketplace.json).
SCHEMA_URL = "https://json.schemastore.org/claude-code-marketplace.json"
MARKETPLACE_NAME = "medsci-skills"  # not a reserved name
MARKETPLACE_DESCRIPTION = (
    "Physician-built Claude Code skills for clinical manuscript preparation, with "
    "deterministic integrity gates — reporting-guideline and risk-of-bias compliance, "
    "reference/citation verification, and numerical-consistency checks — plus literature "
    "search, study design, statistics, publication-ready figures, IMRAD drafting, journal "
    "selection, peer review, and revision. Submission-grade, not a generic skill catalog."
)
OWNER = {"name": "Aperivue"}  # public org; no personal email (PII-safe)

# catalog category key -> plugin name (kebab-case, no spaces). Every category in
# metadata/skills_catalog.json must appear here; an unmapped key fails generation.
PLUGIN_NAME_BY_CATEGORY: dict[str, str] = {
    "literature_references": "medsci-literature",
    "data_study_design": "medsci-data",
    "analysis_figures": "medsci-analysis",
    "writing_manuscript": "medsci-writing",
    "review_compliance": "medsci-review",
    "submission_journals": "medsci-submission",
    "project_workflow": "medsci-project",
    "presentation_tooling": "medsci-presentation",
}

# catalog category key -> one-sentence public-facing plugin description.
PLUGIN_DESC_BY_CATEGORY: dict[str, str] = {
    "literature_references": (
        "Literature search with anti-hallucination citation verification, full-text "
        "retrieval, Zotero/Obsidian sync, and reference-integrity audits."
    ),
    "data_study_design": (
        "Study design and validity review, literature-grounded variable "
        "operationalization, sample-size planning, data cleaning, de-identification, "
        "codebook generation, and dataset versioning."
    ),
    "analysis_figures": (
        "Reproducible statistical analysis, publication-ready figures, "
        "batch/cross-national/replication analysis, and meta-analysis synthesis."
    ),
    "writing_manuscript": (
        "IMRAD manuscript and IRB-protocol drafting, AI-pattern removal, "
        "AI-search optimization, and reviewer-response letters."
    ),
    "review_compliance": (
        "Pre-submission self-review, peer-review drafting, and reporting-guideline "
        "compliance audits against EQUATOR checklists."
    ),
    "submission_journals": (
        "Submission packaging, journal recommendation and profiling, institutional "
        "form filling (ICMJE COI, IRB), and grant proposals."
    ),
    "project_workflow": (
        "Research orchestration, project intake and management, research-gap and "
        "meta-analysis topic discovery, and author-strategy analysis."
    ),
    "presentation_tooling": (
        "Academic presentation and PPTX building, PDF/document rendering, "
        "environment setup, and skill publishing."
    ),
}


class MarketplaceError(Exception):
    """Raised when the catalog cannot be transformed into a valid marketplace."""


def build(catalog_path: Path = CATALOG) -> dict:
    if not catalog_path.is_file():
        raise MarketplaceError(
            f"{catalog_path} not found; run scripts/gen_skills_catalog_json.py first"
        )
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise MarketplaceError(f"{catalog_path} is not valid JSON: {e}")

    categories = catalog.get("categories")
    if not isinstance(categories, list) or not categories:
        raise MarketplaceError(f"{catalog_path} has no 'categories' array")

    plugins: list[dict] = []
    for cat in categories:
        key = cat.get("key")
        slugs = cat.get("slugs") or []
        if key not in PLUGIN_NAME_BY_CATEGORY:
            raise MarketplaceError(
                f"category '{key}' is not mapped to a plugin name in "
                "gen_marketplace_json.py (PLUGIN_NAME_BY_CATEGORY). Add it before release."
            )
        if key not in PLUGIN_DESC_BY_CATEGORY:
            raise MarketplaceError(
                f"category '{key}' is not mapped to a plugin description in "
                "gen_marketplace_json.py (PLUGIN_DESC_BY_CATEGORY). Add it before release."
            )
        if not slugs:
            raise MarketplaceError(f"category '{key}' has no skills")
        plugins.append({
            "name": PLUGIN_NAME_BY_CATEGORY[key],
            "description": PLUGIN_DESC_BY_CATEGORY[key],
            "source": "./",
            "strict": False,
            "skills": [f"./skills/{slug}" for slug in sorted(slugs)],
        })

    return {
        "$schema": SCHEMA_URL,
        "name": MARKETPLACE_NAME,
        "description": MARKETPLACE_DESCRIPTION,
        "owner": OWNER,
        "plugins": plugins,
    }


def render(marketplace: dict) -> str:
    return json.dumps(marketplace, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate .claude-plugin/marketplace.json.")
    ap.add_argument("--check", action="store_true",
                    help="verify the marketplace is in sync; exit 1 on drift (CI gate)")
    ap.add_argument("--catalog", type=Path, default=CATALOG,
                    help="skills_catalog.json to read (default: metadata/skills_catalog.json; for tests)")
    ap.add_argument("--out", type=Path, default=OUT,
                    help="output JSON path (default: .claude-plugin/marketplace.json)")
    args = ap.parse_args()

    try:
        content = render(build(args.catalog))
    except MarketplaceError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    out = args.out
    if args.check:
        if not out.exists():
            print(f"MARKETPLACE_DRIFT — MISSING {out}; run "
                  "`python3 scripts/gen_marketplace_json.py`", file=sys.stderr)
            return 1
        if out.read_text(encoding="utf-8") != content:
            print(f"MARKETPLACE_DRIFT — {out} out of sync; run "
                  "`python3 scripts/gen_marketplace_json.py`", file=sys.stderr)
            return 1
        mk = json.loads(content)
        print(f"OK: {out} in sync ({len(mk['plugins'])} plugins).")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    mk = json.loads(content)
    print(f"OK: wrote {out} ({len(mk['plugins'])} plugins).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

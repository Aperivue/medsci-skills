#!/usr/bin/env python3
"""Generate metadata/skills_catalog.json — the machine-readable skill catalog.

Why: external surfaces (notably the aperivue.com storefront) need a single,
authoritative list of *which skills exist* plus a stable category for each, so
the public site can never silently drift behind the repo (it shipped "40 skills"
while the repo had 43). This file is that source of truth. It is GENERATED from
each `skills/<slug>/SKILL.md` (name + description) and `skill.yml` (owner_domain
+ layer), never hand-maintained — a parallel copy drifts — and CI-gated with
`--check`, exactly like `gen_skill_docs.py` gates the per-skill docs and
`catalog_counts.json` gates the counts.

Category: `skill.yml` has no `category` field (only `owner_domain`, which is too
granular — ~37 distinct values for 43 skills). We map `owner_domain` to one of a
small set of research-lifecycle categories via the explicit table below. An
unmapped `owner_domain` aborts generation (fail loud) so a new skill must be
deliberately categorized rather than silently dropped from the storefront filter.

Stdlib-only, deterministic (sorted, no timestamps) so `--check` is meaningful.

Usage:
  python3 scripts/gen_skills_catalog_json.py          # write metadata/skills_catalog.json
  python3 scripts/gen_skills_catalog_json.py --check   # verify in sync; exit 1 on drift (CI gate)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
OUT = ROOT / "metadata" / "skills_catalog.json"

# owner_domain -> (category key, category label). Research-lifecycle buckets sized
# for a usable storefront filter. Every owner_domain in skills/*/skill.yml must
# appear here; an unmapped value fails generation (see build()).
CATEGORY_BY_OWNER_DOMAIN: dict[str, tuple[str, str]] = {
    # Literature & references
    "literature_discovery": ("literature_references", "Literature & References"),
    "zotero_sync": ("literature_references", "Literature & References"),
    "reference_integrity": ("literature_references", "Literature & References"),
    "manuscript_lifecycle": ("literature_references", "Literature & References"),
    # Data & study design
    "study_design": ("data_study_design", "Data & Study Design"),
    "variable_operationalization": ("data_study_design", "Data & Study Design"),
    "data_preparation": ("data_study_design", "Data & Study Design"),
    "data_documentation": ("data_study_design", "Data & Study Design"),
    "dataset_versioning": ("data_study_design", "Data & Study Design"),
    # Analysis & figures
    "statistical_analysis": ("analysis_figures", "Analysis & Figures"),
    "figure_generation": ("analysis_figures", "Analysis & Figures"),
    "batch_analysis": ("analysis_figures", "Analysis & Figures"),
    "cross_national_comparison": ("analysis_figures", "Analysis & Figures"),
    "study_replication": ("analysis_figures", "Analysis & Figures"),
    "meta_analysis_integrity": ("analysis_figures", "Analysis & Figures"),
    # Writing & manuscript
    "manuscript_drafting": ("writing_manuscript", "Writing & Manuscript"),
    "manuscript_authoring": ("writing_manuscript", "Writing & Manuscript"),
    "protocol_drafting": ("writing_manuscript", "Writing & Manuscript"),
    "manuscript_optimization": ("writing_manuscript", "Writing & Manuscript"),
    "ai_pattern_removal": ("writing_manuscript", "Writing & Manuscript"),
    "reviewer_response": ("writing_manuscript", "Writing & Manuscript"),
    # Review & compliance
    "own_manuscript_critique": ("review_compliance", "Review & Compliance"),
    "external_peer_review": ("review_compliance", "Review & Compliance"),
    "reporting_compliance": ("review_compliance", "Review & Compliance"),
    # Submission & journals
    "submission_packaging": ("submission_journals", "Submission & Journals"),
    "journal_recommendation": ("submission_journals", "Submission & Journals"),
    "journal_profile_authoring": ("submission_journals", "Submission & Journals"),
    "form_filling": ("submission_journals", "Submission & Journals"),
    "grant_proposal": ("submission_journals", "Submission & Journals"),
    # Project & workflow
    "orchestration": ("project_workflow", "Project & Workflow"),
    "project_intake": ("project_workflow", "Project & Workflow"),
    "project_management": ("project_workflow", "Project & Workflow"),
    "research_gap_analysis": ("project_workflow", "Project & Workflow"),
    "ma_topic_discovery": ("project_workflow", "Project & Workflow"),
    "author_profile_analysis": ("project_workflow", "Project & Workflow"),
    # Presentation & tooling
    "presentation": ("presentation_tooling", "Presentation & Tooling"),
    "document_layout": ("presentation_tooling", "Presentation & Tooling"),
    "environment_setup": ("presentation_tooling", "Presentation & Tooling"),
    "skill_publishing": ("presentation_tooling", "Presentation & Tooling"),
}

# Stable display order for the categories array.
CATEGORY_ORDER = [
    "literature_references",
    "data_study_design",
    "analysis_figures",
    "writing_manuscript",
    "review_compliance",
    "submission_journals",
    "project_workflow",
    "presentation_tooling",
]

# key -> label, derived once from the mapping above (each key has one stable label).
CATEGORY_LABELS = {k: label for (k, label) in CATEGORY_BY_OWNER_DOMAIN.values()}


class SkillError(Exception):
    """Raised when a skill cannot be parsed into a valid catalog entry."""


def _frontmatter_field(text: str, key: str) -> str | None:
    """Return a single-line `key: value` from the SKILL.md frontmatter block.
    Supports folded/literal block scalars (`key: >` / `key: |`). None if absent."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillError("SKILL.md must open with a '---' frontmatter line")
    body: list[str] = []
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        body.append(line)
    if not closed:
        raise SkillError("frontmatter block is not closed by a second '---'")

    n = len(body)
    for i, line in enumerate(body):
        m = re.match(rf"^{re.escape(key)}:(.*)$", line)
        if not m or line[:1].isspace():
            continue
        rest = m.group(1).strip()
        if rest in {">", "|", ">-", "|-", ">+", "|+"}:
            block: list[str] = []
            for nxt in body[i + 1:]:
                if nxt.strip() == "":
                    continue
                if not nxt[:1].isspace():
                    break
                block.append(nxt.strip())
            return " ".join(block).strip()
        return rest.strip().strip('"').strip("'")
    return None


def _yml_scalar(text: str, key: str) -> str | None:
    """Return a top-level single-line `key: value` from a skill.yml (stdlib, narrow)."""
    for line in text.splitlines():
        m = re.match(rf"^{re.escape(key)}:\s*(.*)$", line)
        if m and not line[:1].isspace():
            return m.group(1).strip().strip('"').strip("'") or None
    return None


def short_desc(desc: str, cap: int = 200) -> str:
    """First sentence (or capped prefix) of the canonical description."""
    end = len(desc)
    p = desc.find(". ")
    if p != -1:
        end = p + 1
    end = min(end, cap)
    s = desc[:end].rstrip()
    if end < len(desc) and not s.endswith("."):
        s += "…"
    return s


def build(skills_dir: Path = SKILLS_DIR) -> dict:
    if not skills_dir.is_dir():
        raise SkillError(f"{skills_dir} directory not found")
    skill_dirs = sorted(
        (p for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").exists()),
        key=lambda p: p.name,
    )
    if not skill_dirs:
        raise SkillError("no skills with a SKILL.md found")

    skills: list[dict] = []
    for sd in skill_dirs:
        slug = sd.name
        try:
            name = _frontmatter_field((sd / "SKILL.md").read_text(encoding="utf-8"), "name")
            desc = _frontmatter_field((sd / "SKILL.md").read_text(encoding="utf-8"), "description")
        except SkillError as e:
            raise SkillError(f"{slug}: {e}")
        if name != slug:
            raise SkillError(f"{slug}: SKILL.md name '{name}' != directory name")
        if not desc:
            raise SkillError(f"{slug}: SKILL.md has no 'description'")

        yml = sd / "skill.yml"
        if not yml.is_file():
            raise SkillError(f"{slug}: missing skill.yml")
        yml_text = yml.read_text(encoding="utf-8")
        owner_domain = _yml_scalar(yml_text, "owner_domain")
        layer = _yml_scalar(yml_text, "layer")
        maturity = _yml_scalar(yml_text, "maturity")
        if not owner_domain:
            raise SkillError(f"{slug}: skill.yml has no 'owner_domain'")
        if not maturity:
            raise SkillError(f"{slug}: skill.yml has no 'maturity' (official/experimental/community)")
        if owner_domain not in CATEGORY_BY_OWNER_DOMAIN:
            raise SkillError(
                f"{slug}: owner_domain '{owner_domain}' is not mapped to a category in "
                "gen_skills_catalog_json.py (CATEGORY_BY_OWNER_DOMAIN). Add it before release."
            )
        cat_key, cat_label = CATEGORY_BY_OWNER_DOMAIN[owner_domain]
        skills.append({
            "slug": slug,
            "category": cat_key,
            "category_label": cat_label,
            "layer": layer or "",
            "owner_domain": owner_domain,
            "maturity": maturity,
            "description": short_desc(desc),
        })

    by_cat: dict[str, list[str]] = {k: [] for k in CATEGORY_ORDER}
    for s in skills:
        by_cat[s["category"]].append(s["slug"])
    categories = [
        {"key": k, "label": CATEGORY_LABELS[k], "slugs": sorted(by_cat[k])}
        for k in CATEGORY_ORDER
        if by_cat[k]
    ]

    return {
        "_comment": (
            "AUTO-GENERATED by scripts/gen_skills_catalog_json.py from each "
            "skills/<slug>/SKILL.md + skill.yml. Machine-readable skill catalog (single "
            "source of truth) consumed by external surfaces such as the aperivue.com "
            "storefront to gate skill-list completeness. Do not hand-edit; CI gate: "
            "python3 scripts/gen_skills_catalog_json.py --check."
        ),
        "skill_count": len(skills),
        "categories": categories,
        "skills": skills,
    }


def render(catalog: dict) -> str:
    return json.dumps(catalog, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate metadata/skills_catalog.json.")
    ap.add_argument("--check", action="store_true",
                    help="verify the catalog is in sync; exit 1 on drift (CI gate)")
    ap.add_argument("--skills-dir", type=Path, default=SKILLS_DIR,
                    help="skills/ directory to scan (default: repo skills/; for tests)")
    ap.add_argument("--out", type=Path, default=OUT,
                    help="output JSON path (default: metadata/skills_catalog.json)")
    args = ap.parse_args()

    try:
        content = render(build(args.skills_dir))
    except SkillError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    out = args.out
    if args.check:
        if not out.exists():
            print(f"SKILLS_CATALOG_DRIFT — MISSING {out}; run "
                  "`python3 scripts/gen_skills_catalog_json.py`", file=sys.stderr)
            return 1
        if out.read_text(encoding="utf-8") != content:
            print(f"SKILLS_CATALOG_DRIFT — {out} out of sync; run "
                  "`python3 scripts/gen_skills_catalog_json.py`", file=sys.stderr)
            return 1
        catalog = json.loads(content)
        print(f"OK: {out} in sync ({catalog['skill_count']} skills, "
              f"{len(catalog['categories'])} categories).")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    catalog = json.loads(content)
    print(f"OK: wrote {out} ({catalog['skill_count']} skills, "
          f"{len(catalog['categories'])} categories).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

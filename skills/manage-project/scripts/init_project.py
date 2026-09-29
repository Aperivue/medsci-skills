#!/usr/bin/env python3
"""Initialize a medsci research project scaffold.

Usage:
    python3 scripts/init_project.py --name <id> --type <type> --journal <journal> \
        [--ssot] [--project-root <path>] [--force]

Writes either `SSOT.yaml` (schema v1, with `--ssot`) from
`skills/manage-project/templates/SSOT.yaml.template`, or legacy
`project.yaml`. Also creates the directory scaffold and stub memory files
documented in `skills/manage-project/SKILL.md`.

Exit codes: 0 success, 2 bad args, 3 output collision without --force.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_SSOT = SKILL_DIR / "templates" / "SSOT.yaml.template"

TYPE_TO_SSOT_ENUM = {
    "original": "original_research",
    "meta": "meta_analysis",
    "case": "case_report",
    "ai_validation": "ai_validation",
}

VALID_TYPES = {"original", "meta", "case", "animal", "technical", "ai_validation", "letter"}

SCAFFOLD_DIRS = [
    "paper/sections",
    "paper/figures",
    "paper/tables",
    "paper/supplementary",
    "analysis/scripts",
    "analysis/outputs",
    "references",
    "revision",
    "submission",
    "qc",
    "manuscript/_src",
    "manuscript/figures",
]

STUB_FILES: dict[str, str] = {
    "PROJECT.md": "# PROJECT\n\n- Identity:\n- Scope:\n- Primary claim:\n",
    "STATUS.md": "# STATUS\n\n- Current phase: 0_init\n- Blockers:\n- Next actions:\n",
    "CLAIMS.md": "# CLAIMS\n\n| Claim | Result ID | Location |\n|-------|-----------|----------|\n",
    "DATA_DICTIONARY.md": "# DATA DICTIONARY\n\n| Variable | Definition | Timing | Notes |\n|----------|------------|--------|------|\n",
    "ANALYSIS_PLAN.md": "# ANALYSIS PLAN\n\n- Primary endpoint:\n- Secondary endpoints:\n- Statistical methods:\n",
    "REVIEW_LOG.md": "# REVIEW LOG\n\n| Reviewer comment | Planned action | Status | Location |\n|--|--|--|--|\n",
    "README.md": "# Project\n\nScaffolded by /manage-project init.\n",
    "references/library.bib": "",
    "manuscript/_src/refs.bib": "",
    "manuscript/index.qmd": "---\ntitle: TBD\n---\n\n<!-- scaffolded by /manage-project init -->\n",
    "artifact_manifest.json": "{\n  \"artifacts\": []\n}\n",
    "qc/status.json": "{\n  \"phase\": \"0_init\"\n}\n",
}


def map_project_type_to_ssot(paper_type: str) -> str:
    return TYPE_TO_SSOT_ENUM.get(paper_type, "other")


def render_ssot(project_id: str, project_type: str) -> str:
    if not TEMPLATE_SSOT.is_file():
        sys.exit(f"ERROR: SSOT template not found: {TEMPLATE_SSOT}")
    text = TEMPLATE_SSOT.read_text(encoding="utf-8")
    return text.replace("{{PROJECT_ID}}", project_id).replace("{{PROJECT_TYPE}}", project_type)


def render_legacy_project_yaml(project_id: str, paper_type: str, journal: str, today: str) -> str:
    ssot_type = map_project_type_to_ssot(paper_type)
    return (
        f"schema_version: 1\n"
        f"project_id: {project_id}\n"
        f"project_type: {ssot_type}\n"
        f"canonical_manuscript: manuscript/index.qmd\n"
        f"references_bib: manuscript/_src/refs.bib\n"
        f"artifact_manifest: artifact_manifest.json\n"
        f"status_file: qc/status.json\n"
        f"submission_root: submission/\n"
        f"target_journal: {journal}\n"
        f"reporting_guideline: TBD\n"
        f"zotero_collection: null\n"
        f"created: {today}\n"
        f"last_reviewed: {today}\n"
    )


def render_project_state(name: str, paper_type: str, journal: str, today: str) -> str:
    state = {
        "name": name,
        "type": paper_type,
        "journal": journal,
        "created": today,
        "target_submission": None,
        "current_phase": 0,
        "phases": {
            "0_init": "complete",
            "1_outline": "pending",
            "2_tables_figures": "pending",
            "3_methods": "pending",
            "4_results": "pending",
            "5_discussion": "pending",
            "6_intro_abstract": "pending",
            "7_polish": "pending",
        },
        "word_counts": {k: 0 for k in ("abstract", "introduction", "methods", "results", "discussion", "total")},
        "checklist_status": "pending",
        "citation_status": "unverified",
        "revision_round": None,
        "memory_files": {f: True for f in (
            "PROJECT.md", "STATUS.md", "CLAIMS.md", "DATA_DICTIONARY.md", "ANALYSIS_PLAN.md", "REVIEW_LOG.md"
        )},
    }
    return json.dumps(state, indent=2) + "\n"


def create_zotero_collection(name: str) -> tuple[str | None, str | None, str | None]:
    """Create a Zotero collection via pyzotero; return (library_id, collection_key, reason).

    Reads env vars: ZOTERO_API_KEY, ZOTERO_LIBRARY_ID, ZOTERO_LIBRARY_TYPE
    (user|group, default: user). Degrades gracefully — returns (None, None, reason)
    if pyzotero is missing or credentials are absent.
    """
    api_key = os.environ.get("ZOTERO_API_KEY")
    library_id = os.environ.get("ZOTERO_LIBRARY_ID")
    library_type = os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
    if not api_key or not library_id:
        return None, None, "env ZOTERO_API_KEY / ZOTERO_LIBRARY_ID not set"
    try:
        from pyzotero import zotero  # type: ignore
    except ImportError:
        return None, None, "pyzotero not installed (pip install pyzotero)"
    try:
        zot = zotero.Zotero(library_id, library_type, api_key)
        result = zot.create_collections([{"name": name}])
        successful = result.get("successful") or result.get("success") or {}
        if not successful:
            return None, None, f"Zotero API returned no successful collection: {result}"
        first = next(iter(successful.values()))
        key = first.get("key") if isinstance(first, dict) else first
        return library_id, key, None
    except Exception as exc:
        return None, None, f"Zotero API error: {exc}"


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        sys.exit(f"ERROR: {path} already exists (use --force to overwrite). Code=3")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold a medsci research project.")
    ap.add_argument("--name", required=True, help="Project identifier (e.g. rfa-meta-analysis).")
    ap.add_argument("--type", required=True, choices=sorted(VALID_TYPES))
    ap.add_argument("--journal", required=True)
    ap.add_argument("--ssot", action="store_true", help="Emit SSOT.yaml (schema v1) instead of legacy project.yaml.")
    ap.add_argument("--project-root", default=".", help="Target directory (default: CWD).")
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--zotero-collection",
        default=None,
        metavar="NAME",
        help="Create a Zotero collection with NAME via pyzotero and populate "
             "library_id / collection_key in the contract. Requires env "
             "ZOTERO_API_KEY + ZOTERO_LIBRARY_ID (ZOTERO_LIBRARY_TYPE "
             "optional, default 'user'). Degrades with a warning if "
             "pyzotero or credentials are unavailable.",
    )
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    today = _dt.date.today().isoformat()

    # 1. Dirs
    for d in SCAFFOLD_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
        gk = root / d / ".gitkeep"
        if not gk.exists():
            gk.touch()

    # 2. Stub memory/bib files
    for rel, content in STUB_FILES.items():
        tgt = root / rel
        if tgt.exists() and not args.force:
            continue
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tgt.write_text(content, encoding="utf-8")

    # 3. Zotero collection (optional)
    zot_library_id: str | None = None
    zot_collection_key: str | None = None
    if args.zotero_collection:
        zot_library_id, zot_collection_key, zot_err = create_zotero_collection(args.zotero_collection)
        if zot_err:
            print(f"WARN: Zotero collection not created — {zot_err}. "
                  f"Contract fields will stay null.", file=sys.stderr)
        else:
            print(f"OK: Zotero collection '{args.zotero_collection}' "
                  f"(library={zot_library_id}, key={zot_collection_key})")

    # 4. Contract file (SSOT.yaml or project.yaml)
    if args.ssot:
        ssot_type = map_project_type_to_ssot(args.type)
        ssot_text = render_ssot(args.name, ssot_type)
        if zot_library_id and zot_collection_key:
            ssot_text = ssot_text.replace(
                "  library_id: null", f"  library_id: \"{zot_library_id}\""
            ).replace(
                "  collection_key: null", f"  collection_key: \"{zot_collection_key}\""
            )
        write_file(root / "SSOT.yaml", ssot_text, args.force)
        contract = "SSOT.yaml"
    else:
        legacy_text = render_legacy_project_yaml(args.name, args.type, args.journal, today)
        if zot_library_id and zot_collection_key:
            legacy_text = legacy_text.replace(
                "zotero_collection: null\n",
                f"zotero_collection:\n  library_id: \"{zot_library_id}\"\n  "
                f"collection_key: \"{zot_collection_key}\"\n",
            )
        write_file(root / "project.yaml", legacy_text, args.force)
        contract = "project.yaml"

    # 5. project_state.json
    write_file(root / "project_state.json",
               render_project_state(args.name, args.type, args.journal, today),
               args.force)

    print(f"OK: scaffolded {args.name} at {root} (contract={contract})")
    if args.ssot:
        print("NOTE: SSOT.yaml written but `qc/migration_complete` marker NOT set.")
        print("      New SSOT-native projects are enforce-ready once the pipeline")
        print("      validates the contract and touches qc/migration_complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

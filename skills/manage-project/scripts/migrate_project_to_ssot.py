#!/usr/bin/env python3
"""Migrate legacy project.yaml to SSOT.yaml (schema v1).

Usage:
    python3 scripts/migrate_project_to_ssot.py --project-root <path> [--write] [--verbose]

Default is dry-run (prints proposed SSOT.yaml to stdout). Use --write to persist
to <project-root>/SSOT.yaml. The original project.yaml is preserved as a legacy
alias for the 6-month transition window (sunset 2026-10-24).

Mapping: see docs/ssot_schema_v1.md "project.yaml -> SSOT.yaml field mapping".
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


SUNSET_DATE = "2026-10-24"

KNOWN_FIELDS = {
    "schema_version",
    "project_id",
    "project_type",
    "canonical_manuscript",
    "references_bib",
    "artifact_manifest",
    "status_file",
    "submission_root",
    "target_journal",
    "reporting_guideline",
    "zotero_collection",
    "created",
    "last_reviewed",
}


def read_simple_yaml(path: Path) -> dict[str, str]:
    """Flat key:value YAML parser (same logic as validate_project_contract.py)."""
    data: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        if raw.startswith((" ", "\t", "-")):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def build_ssot(project: dict[str, str]) -> str:
    project_id = project.get("project_id", "TODO_project_id")
    project_type = project.get("project_type", "original_research")
    manuscript = project.get("canonical_manuscript", "manuscript/index.qmd")
    refs_bib = project.get("references_bib", "manuscript/_src/refs.bib")
    artifact_manifest = project.get("artifact_manifest", "artifact_manifest.json")
    status_file = project.get("status_file", "qc/status.json")
    zotero_collection = project.get("zotero_collection") or "null"
    if zotero_collection != "null":
        zotero_collection = f'"{zotero_collection}"'

    return f"""schema_version: 1
project_id: {project_id}
project_type: {project_type}

truth:
  manuscript: {manuscript}
  refs_bib: {refs_bib}
  numbers_yaml: manuscript/_src/numbers.yaml
  tables_yaml: manuscript/_src/tables.yaml
  figures_dir: manuscript/figures/
  metadata: manuscript/_metadata.yml

reference_manager:
  type: zotero
  required_for: project_owner
  library_type: user
  library_id: null
  collection_key: {zotero_collection}
  sync_method: better_bibtex_auto_export
  fallback_for_collaborator: snapshot_only
  citekey_policy: pinned_or_stable
  refs_bib_snapshot: {refs_bib}

renders: {{}}

derived:
  artifact_manifest: {artifact_manifest}
  status_file: {status_file}

policy:
  ssot_only_editable: true
  submission_readonly: true
  back_merge_required_before: render
  manuscript_citations: citekey_only
  allow_new_reference_from_llm: false
  missing_citekey: block
  unverified_reference: block_before_submission

legacy:
  project_yaml_alias: project.yaml
  sunset_date: "{SUNSET_DATE}"
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate project.yaml to SSOT.yaml")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--write", action="store_true", help="Write SSOT.yaml (default: dry-run to stdout)")
    parser.add_argument("--verbose", action="store_true", help="Warn on dropped fields")
    parser.add_argument(
        "--mark-complete",
        action="store_true",
        help="After --write, validate via scripts/validate_project_contract.py and "
        "touch qc/migration_complete on PASS. Required to activate Phase 1C auto-enforce.",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    legacy = root / "project.yaml"
    target = root / "SSOT.yaml"

    if not legacy.exists():
        print(f"ERROR: {legacy} not found", file=sys.stderr)
        return 2

    project = read_simple_yaml(legacy)
    if not project.get("project_id"):
        print("WARN: project.yaml has no project_id; using placeholder", file=sys.stderr)

    if args.verbose:
        extra = set(project) - KNOWN_FIELDS
        for field in sorted(extra):
            print(f"WARN: dropped unknown field '{field}' (not in SSOT v1 schema)", file=sys.stderr)
        dropped = {"submission_root", "target_journal", "reporting_guideline", "created", "last_reviewed"} & set(project)
        for field in sorted(dropped):
            print(f"INFO: field '{field}' has no direct SSOT slot (see docs/ssot_schema_v1.md)", file=sys.stderr)

    output = build_ssot(project)

    if args.write:
        if target.exists():
            print(f"ERROR: {target} already exists; refusing to overwrite", file=sys.stderr)
            return 3
        target.write_text(output, encoding="utf-8")
        print(f"Wrote {target}")
        print(f"Legacy project.yaml preserved (sunset {SUNSET_DATE}). Remove after migration verified.")
        if args.mark_complete:
            rc = _validate_and_mark(root)
            return rc
    else:
        print(output)

    return 0


def _validate_and_mark(root: Path) -> int:
    """Run validator against the freshly-written SSOT.yaml. On PASS, touch
    qc/migration_complete so the Phase 1C hook switches from warn to enforce.

    Returns the process exit code (0 on success, non-zero on validator failure).
    """
    validator = Path(__file__).resolve().parent / "validate_project_contract.py"
    if not validator.exists():
        print(f"ERROR: validator not found at {validator}", file=sys.stderr)
        return 4

    proc = subprocess.run(
        [sys.executable, str(validator), "--project-root", str(root)],
        capture_output=True,
        text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)

    if proc.returncode != 0:
        print(
            "MIGRATION INCOMPLETE: validator failed — qc/migration_complete not written. "
            "Fix failures above and re-run with --mark-complete.",
            file=sys.stderr,
        )
        return proc.returncode

    try:
        payload = json.loads(proc.stdout)
        if payload.get("contract_mode") != "ssot":
            print(
                f"MIGRATION INCOMPLETE: expected contract_mode=ssot, got {payload.get('contract_mode')!r}",
                file=sys.stderr,
            )
            return 5
    except json.JSONDecodeError:
        # validator printed non-JSON; treat as PASS on rc=0 but warn.
        print("WARN: validator stdout not JSON; proceeding based on exit code.", file=sys.stderr)

    marker_dir = root / "qc"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker = marker_dir / "migration_complete"
    marker.touch()
    print(f"Wrote marker {marker} — Phase 1C auto-enforce is now active for this project.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

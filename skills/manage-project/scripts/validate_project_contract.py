#!/usr/bin/env python3
"""Validate a project-level artifact contract (dual-path v1.1.1).

Two valid forms:
  - SSOT.yaml (schema v1, preferred)  -> enforced
  - project.yaml (legacy)             -> warn + sunset after 2026-10-24
  - Both present                      -> SSOT.yaml wins, project.yaml warns
  - Neither                           -> fail
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path


SUNSET_DATE = "2026-10-24"

REQUIRED_LEGACY_KEYS = {
    "schema_version",
    "project_id",
    "project_type",
    "canonical_manuscript",
    "artifact_manifest",
    "status_file",
    "submission_root",
}

REQUIRED_SSOT_TOP_LEVEL = {
    "schema_version",
    "project_id",
    "project_type",
    "truth",
    "reference_manager",
    "derived",
    "policy",
}

REQUIRED_SSOT_TRUTH = {"manuscript", "refs_bib", "figures_dir", "metadata"}
REQUIRED_SSOT_POLICY = {
    "ssot_only_editable",
    "submission_readonly",
    "back_merge_required_before",
    "manuscript_citations",
    "allow_new_reference_from_llm",
    "missing_citekey",
    "unverified_reference",
}
REQUIRED_SSOT_DERIVED = {"artifact_manifest", "status_file"}
REQUIRED_SSOT_REFMGR = {"type", "required_for", "refs_bib_snapshot"}


def read_flat_yaml(path: Path) -> dict[str, str]:
    """Flat top-level key:value (legacy project.yaml format)."""
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


def read_nested_yaml(path: Path) -> dict:
    """Minimal nested YAML parser: 2-space indent, key:value pairs, no lists-of-maps.

    Supports SSOT.yaml structure: top-level keys + one level of nesting.
    """
    root: dict = {}
    current: dict = root
    stack: list[tuple[int, dict]] = [(-1, root)]

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        # Pop stack to parent level
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else root
        line = raw.strip()
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value == "" or value == "{}":
            new_map: dict = {}
            parent[key] = new_map
            stack.append((indent, new_map))
        else:
            parent[key] = value
    return root


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rel_exists(root: Path, rel: str | None) -> bool:
    return bool(rel) and (root / rel).exists()


def past_sunset() -> bool:
    today = _dt.date.today().isoformat()
    return today >= SUNSET_DATE


def validate_ssot(root: Path, data: dict, strict: bool) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    missing_top = REQUIRED_SSOT_TOP_LEVEL - set(data)
    if missing_top:
        failures.append(f"SSOT.yaml missing top-level keys: {', '.join(sorted(missing_top))}")

    if str(data.get("schema_version", "")) != "1":
        failures.append(f"SSOT.yaml schema_version must be 1 (got {data.get('schema_version')!r})")

    truth = data.get("truth") or {}
    if isinstance(truth, dict):
        missing = REQUIRED_SSOT_TRUTH - set(truth)
        if missing:
            failures.append(f"SSOT.yaml truth.* missing: {', '.join(sorted(missing))}")
        manuscript = truth.get("manuscript") if isinstance(truth, dict) else None
        if manuscript and not rel_exists(root, manuscript):
            failures.append(f"truth.manuscript missing on disk: {manuscript}")
    else:
        failures.append("SSOT.yaml truth block is not a mapping")

    policy = data.get("policy") or {}
    if isinstance(policy, dict):
        missing = REQUIRED_SSOT_POLICY - set(policy)
        if missing:
            failures.append(f"SSOT.yaml policy.* missing: {', '.join(sorted(missing))}")
    else:
        failures.append("SSOT.yaml policy block is not a mapping")

    derived = data.get("derived") or {}
    if isinstance(derived, dict):
        missing = REQUIRED_SSOT_DERIVED - set(derived)
        if missing:
            failures.append(f"SSOT.yaml derived.* missing: {', '.join(sorted(missing))}")
    else:
        failures.append("SSOT.yaml derived block is not a mapping")

    refmgr = data.get("reference_manager") or {}
    if isinstance(refmgr, dict):
        missing = REQUIRED_SSOT_REFMGR - set(refmgr)
        if missing:
            failures.append(f"SSOT.yaml reference_manager.* missing: {', '.join(sorted(missing))}")
        required_for = refmgr.get("required_for")
        if required_for and required_for not in {"project_owner", "all_contributors", "none"}:
            failures.append(
                f"reference_manager.required_for invalid: {required_for!r} "
                "(must be project_owner | all_contributors | none)"
            )
        snapshot = refmgr.get("refs_bib_snapshot")
        truth_refs = truth.get("refs_bib") if isinstance(truth, dict) else None
        if snapshot and truth_refs and snapshot != truth_refs:
            failures.append(
                f"reference_manager.refs_bib_snapshot ({snapshot}) must equal truth.refs_bib ({truth_refs})"
            )
    else:
        failures.append("SSOT.yaml reference_manager block is not a mapping")

    # derived artifacts on disk (warn unless strict)
    if isinstance(derived, dict):
        for label in ("artifact_manifest", "status_file"):
            rel = derived.get(label)
            if rel and not rel_exists(root, rel):
                msg = f"derived.{label} missing on disk: {rel}"
                (failures if strict else warnings).append(msg)

    return failures, warnings


def validate_legacy(root: Path, project: dict, strict: bool) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    missing = REQUIRED_LEGACY_KEYS - set(project)
    if missing:
        failures.append("project.yaml missing keys: " + ", ".join(sorted(missing)))

    canonical = project.get("canonical_manuscript")
    if canonical and not rel_exists(root, canonical):
        failures.append(f"canonical_manuscript missing: {canonical}")

    manifest_rel = project.get("artifact_manifest", "artifact_manifest.json")
    if not rel_exists(root, manifest_rel):
        failures.append(f"artifact manifest missing: {manifest_rel}")
    else:
        try:
            load_json(root / manifest_rel)
        except Exception as exc:
            failures.append(f"artifact manifest invalid JSON: {exc}")

    status_rel = project.get("status_file", "qc/status.json")
    if not rel_exists(root, status_rel):
        warnings.append(f"status file missing: {status_rel}")
    else:
        try:
            load_json(root / status_rel)
        except Exception as exc:
            failures.append(f"status file invalid JSON: {exc}")

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate medsci project artifact contract (dual-path).")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    ssot_path = root / "SSOT.yaml"
    legacy_path = root / "project.yaml"

    mode: str
    failures: list[str] = []
    warnings: list[str] = []

    if ssot_path.exists():
        mode = "ssot"
        ssot_data = read_nested_yaml(ssot_path)
        f, w = validate_ssot(root, ssot_data, args.strict)
        failures.extend(f)
        warnings.extend(w)
        if legacy_path.exists():
            warnings.append(
                f"legacy project.yaml present alongside SSOT.yaml — remove by {SUNSET_DATE}"
            )
    elif legacy_path.exists():
        mode = "legacy"
        project = read_flat_yaml(legacy_path)
        f, w = validate_legacy(root, project, args.strict)
        if past_sunset():
            # After sunset, legacy path escalates to failure
            failures.append(
                f"project.yaml only (no SSOT.yaml) — past sunset {SUNSET_DATE}; "
                "run scripts/migrate_project_to_ssot.py"
            )
            failures.extend(f)
        else:
            warnings.append(
                f"project.yaml detected (no SSOT.yaml) — migrate with scripts/migrate_project_to_ssot.py "
                f"before sunset {SUNSET_DATE}"
            )
            failures.extend(f)
        warnings.extend(w)
    else:
        mode = "none"
        failures.append("neither SSOT.yaml nor project.yaml found at project root")

    payload = {
        "schema_version": 1,
        "project_root": str(root),
        "contract_mode": mode,
        "sunset_date": SUNSET_DATE,
        "failures": failures,
        "warnings": warnings,
        "valid": not failures,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Audit and build submission packages from canonical manuscript sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def read_project_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def resolve_canonical(project_root: Path, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        return path if path.is_absolute() else project_root / path
    project = read_project_yaml(project_root / "project.yaml")
    rel = project.get("canonical_manuscript", "manuscript/manuscript.md")
    return project_root / rel


def submission_md_path(project_root: Path, journal: str) -> Path:
    return project_root / "submission" / journal / "manuscript" / "manuscript.md"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def update_manifest(project_root: Path, journal: str, meta_rel: str, status: str, source_hash: str) -> None:
    manifest_path = project_root / "artifact_manifest.json"
    manifest = load_json(manifest_path) or {"schema_version": 1, "submissions": {}}
    manifest.setdefault("schema_version", 1)
    manifest.setdefault("submissions", {})
    manifest["submissions"][journal] = {
        "path": f"submission/{journal}",
        "metadata": meta_rel,
        "status": status,
        "source_hash": source_hash,
    }
    write_json(manifest_path, manifest)


def audit(project_root: Path, journal: str, canonical: Path) -> int:
    qc_path = project_root / "qc" / f"submission_sync_{journal}.json"
    sub_path = submission_md_path(project_root, journal)
    if not canonical.exists():
        write_json(qc_path, {"schema_version": 1, "journal": journal, "status": "ERROR", "message": "canonical manuscript missing"})
        return 2
    source_hash = sha256_file(canonical)
    meta_path = project_root / "submission" / journal / ".journal_meta.json"
    meta = load_json(meta_path)
    current_hash = sha256_file(sub_path) if sub_path.exists() else None
    recorded_hash = meta.get("source_hash")
    drift = bool(sub_path.exists() and current_hash != source_hash)
    status = "DRIFT" if drift else "CURRENT" if sub_path.exists() else "MISSING_SUBMISSION"
    payload = {
        "schema_version": 1,
        "journal": journal,
        "status": status,
        "canonical": str(canonical.relative_to(project_root)),
        "submission_manuscript": str(sub_path.relative_to(project_root)),
        "source_hash": source_hash,
        "submission_hash": current_hash,
        "recorded_source_hash": recorded_hash,
        "message": "Submission differs from canonical manuscript" if drift else "",
    }
    write_json(qc_path, payload)
    print(json.dumps(payload, indent=2))
    return 1 if drift else 0


def build(project_root: Path, journal: str, canonical: Path) -> int:
    if not canonical.exists():
        print(f"Canonical manuscript missing: {canonical}", file=sys.stderr)
        return 2
    sub_path = submission_md_path(project_root, journal)
    sub_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(canonical, sub_path)
    source_hash = sha256_file(canonical)
    meta_path = project_root / "submission" / journal / ".journal_meta.json"
    meta = {
        "schema_version": 1,
        "journal": journal,
        "status": "built",
        "canonical": str(canonical.relative_to(project_root)),
        "submission_manuscript": str(sub_path.relative_to(project_root)),
        "source_hash": source_hash,
        "built_date": date.today().isoformat(),
        "frozen": False,
    }
    write_json(meta_path, meta)
    update_manifest(project_root, journal, str(meta_path.relative_to(project_root)), "built", source_hash)
    return audit(project_root, journal, canonical)


def freeze(project_root: Path, journal: str, canonical: Path, status: str) -> int:
    audit_code = audit(project_root, journal, canonical)
    if audit_code != 0:
        print("Cannot freeze a drifted or invalid submission package.", file=sys.stderr)
        return audit_code
    meta_path = project_root / "submission" / journal / ".journal_meta.json"
    meta = load_json(meta_path)
    meta.update({"status": status, "frozen": True, "frozen_date": date.today().isoformat()})
    write_json(meta_path, meta)
    update_manifest(project_root, journal, str(meta_path.relative_to(project_root)), status, meta.get("source_hash", ""))
    print(json.dumps(meta, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit or build journal submission package.")
    parser.add_argument("mode", choices=["audit", "build", "freeze"])
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--journal", required=True)
    parser.add_argument("--canonical")
    parser.add_argument("--status", default="submitted")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    canonical = resolve_canonical(project_root, args.canonical).resolve()
    try:
        canonical.relative_to(project_root)
    except ValueError:
        print("Canonical manuscript must be inside project root.", file=sys.stderr)
        return 2

    if args.mode == "audit":
        return audit(project_root, args.journal, canonical)
    if args.mode == "build":
        return build(project_root, args.journal, canonical)
    return freeze(project_root, args.journal, canonical, args.status)


if __name__ == "__main__":
    sys.exit(main())

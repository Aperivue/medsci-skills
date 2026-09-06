#!/usr/bin/env python3
"""Copy and audit declared submission artifacts without rewriting source files.

Usage: sync_submission.py build --project-root . --journal example
       sync_submission.py build --project-root . --journal example --bundle-spec bundle.json
       sync_submission.py audit --project-root . --journal example

Rendering stays with the existing renderers. A bundle spec records the input
hashes observed for that render; build never refreshes those hashes for you.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def digest(payload) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()).hexdigest()


def read_project_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    # Use the repository's declared YAML dependency, not indentation-blind parsing.
    import yaml
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError("project.yaml is invalid YAML") from exc
    if not isinstance(value, dict):
        raise ValueError("project.yaml must be a mapping")
    return value


def resolve_canonical(project_root: Path, explicit: str | None) -> Path:
    rel = explicit or read_project_yaml(project_root / "project.yaml").get(
        "canonical_manuscript", "manuscript/manuscript.md")
    path = Path(rel)
    return path if path.is_absolute() else project_root / path


def safe_path(root: Path, relative: str) -> Path:
    """Confine named files and reject symlinks, hidden components and traversal."""
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("Expected a relative POSIX path")
    parts = PurePosixPath(relative).parts
    if relative.startswith("/") or any(p.startswith(".") for p in parts):
        raise ValueError("Hidden, absolute or traversing paths are not supported")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlink paths are not supported")
    path.resolve().relative_to(root.resolve())
    return path


def journal_root(root: Path, journal: str) -> Path:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", journal):
        raise ValueError("Journal must be a single letter/digit/underscore/hyphen slug")
    return safe_path(root, f"submission/{journal}")


def submission_md_path(project_root: Path, journal: str) -> Path:
    return journal_root(project_root, journal) / "manuscript/manuscript.md"


def load_json(path: Path) -> dict:
    if path.is_symlink():
        raise ValueError("JSON metadata must not be a symlink")
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON metadata must be an object")
    return payload


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("Refusing to overwrite a symlink")
    fd, temp = tempfile.mkstemp(prefix=".sync-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


@contextmanager
def mutation_lock(root: Path):
    """Serialize cooperating builds/freezes, including the shared manifest update."""
    lock = root / ".submission-sync.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError("Another sync mutation is active; inspect .submission-sync.lock") from None
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()


def manifest_payload(root: Path, journal: str, meta: dict) -> dict:
    manifest = load_json(safe_path(root, "artifact_manifest.json")) or {"schema_version": 1}
    submissions = manifest.setdefault("submissions", {})
    if not isinstance(submissions, dict) or not isinstance(submissions.get(journal, {}), dict):
        raise ValueError("Manifest submissions must contain objects")
    entry = submissions.setdefault(journal, {})
    entry.update({
        "path": f"submission/{journal}",
        "metadata": f"submission/{journal}/.journal_meta.json",
        "status": meta["status"], "source_hash": meta["source_hash"],
        "artifacts": meta.get("artifacts", []),
        "readiness": "not_assessed",  # Neither copying nor freezing is a submission approval.
    })
    return manifest


def inventory(directory: Path) -> list[str]:
    """Only the selected submission directory; never discover project-wide inputs."""
    if not directory.exists():
        return []
    result = []
    for base, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs + files:
            if (Path(base) / name).is_symlink():
                raise ValueError("Submission package contains a symlink")
        result.extend((Path(base) / name).relative_to(directory).as_posix() for name in files)
    return sorted(result)


def bundle_binding(root: Path, journal: str | None) -> dict | None:
    """Byte snapshot, not a statement that every file was inspected by every check."""
    if not journal:
        return None
    directory = journal_root(root, journal)
    meta = load_json(directory / ".journal_meta.json")
    if not meta.get("artifacts"):
        return None
    package_paths = {f"submission/{journal}/{name}" for name in inventory(directory)
             if name != ".journal_meta.json"}
    paths = set(package_paths)
    for row in meta["artifacts"]:
        paths.add(row["source"])
        paths.update(d["path"] for d in row.get("derived_from", []))
    files = {}
    for relative in sorted(paths):
        path = root / relative if relative in package_paths else safe_path(root, relative)
        files[relative] = sha256_file(path) if path.is_file() else None
    # Exclude status/freeze dates so freezing doesn't invalidate its own evidence.
    data = {"files": files, "declaration_hash": digest(meta["artifacts"])}
    return {**data, "sha256": digest(data)}


def verification_context(root: Path, journal: str) -> dict:
    report_path = safe_path(root, "qc/preflight_gate_report.json")
    report = load_json(report_path)
    if not report or report.get("journal") != journal:
        return {"status": "not_run", "checks": [], "readiness": "not_assessed"}
    now = bundle_binding(root, journal)
    recorded = report.get("bundle_binding")
    state = "unbound" if not now or not recorded else (
        "package_bytes_current" if recorded == now and report.get("bundle_unchanged_during_checks") is True else "stale")
    return {"status": state, "report": "qc/preflight_gate_report.json",
            "report_hash": sha256_file(report_path), "checks": report.get("checks", []),
            "coverage": report.get("coverage", {}), "readiness": "not_assessed",
            "scope": "Bundle byte binding only; other check inputs are not bound. No visual, semantic or rights approval."}


def prepare_artifacts(root: Path, journal: str, canonical: Path, spec: dict) -> list[dict]:
    if spec and spec.get("schema_version") != 1:
        raise ValueError("Bundle spec schema_version must be 1")
    extra = spec.get("artifacts", [])
    if not isinstance(extra, list):
        raise ValueError("Bundle artifacts must be a list")
    rows = [{"id": "canonical", "role": "manuscript_source",
             "source": canonical.relative_to(root).as_posix(),
             "target": "manuscript/manuscript.md"}] + extra
    directory = journal_root(root, journal)
    prepared, ids, targets, inputs = [], set(), [], set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
            raise ValueError("Each artifact requires an id")
        if row["id"] in ids:
            raise ValueError("Duplicate artifact id")
        ids.add(row["id"])
        source = safe_path(root, row["source"])
        target = safe_path(directory, row["target"])
        if not source.is_file() or source.is_relative_to(directory):
            raise ValueError("Artifact source must exist outside the destination package")
        key = target.relative_to(directory).as_posix().casefold()
        if any(key == old or key.startswith(old + "/") or old.startswith(key + "/") for old in targets):
            raise ValueError("Overlapping or case-colliding artifact targets")
        targets.append(key)
        deps = row.get("derived_from", [])
        if not isinstance(deps, list):
            raise ValueError("derived_from must be a list")
        for dep in deps:
            path = safe_path(root, dep["path"])
            if path.is_relative_to(directory) or not path.is_file() or sha256_file(path) != dep["sha256"]:
                raise ValueError("Render dependency missing or changed; rebuild with the existing renderer")
            inputs.add(path)
        transformation = row.get("transformation", {"kind": "not_recorded"})
        if not isinstance(transformation, dict):
            raise ValueError("transformation must be an object")
        if transformation.get("kind") == "rendered" and not deps:
            raise ValueError("Rendered artifacts require pinned derived_from inputs")
        rights = row.get("rights", {"status": "unknown"})
        if not isinstance(rights, dict) or rights.get("status") not in {"unknown", "original", "documented"}:
            raise ValueError("rights.status must be unknown, original or documented")
        if rights["status"] == "documented" and not all(rights.get(k) for k in (
                "source", "license_or_permission", "attribution", "changes")):
            raise ValueError("Documented rights require source, license_or_permission, attribution and changes")
        inputs.add(source)
        prepared.append({"id": row["id"], "role": row.get("role", "unspecified"),
                         "source": row["source"], "target": row["target"],
                         "source_hash": sha256_file(source), "derived_from": deps,
                         "transformation": transformation, "rights": rights,
                         "copy_fidelity": "byte_identical",
                         "content_fidelity": "not_assessed", "visual_review": "not_assessed"})
    controls = [root / "artifact_manifest.json", root / "project.yaml"]
    for source in inputs:
        if source in controls or source.is_relative_to(root / "qc"):
            raise ValueError("Source aliases a mutable control/report path")
        for row in prepared:
            target = directory / row["target"]
            if target.exists() and source.samefile(target):
                raise ValueError("Source and output alias the same file")
    return prepared


def audit(project_root: Path, journal: str, canonical: Path) -> int:
    directory = journal_root(project_root, journal)
    qc_path = safe_path(project_root, f"qc/submission_sync_{journal}.json")
    sub_path = submission_md_path(project_root, journal)
    meta = load_json(directory / ".journal_meta.json")
    if not canonical.is_file():
        write_json(qc_path, {"schema_version": 2, "journal": journal, "status": "ERROR",
                             "message": "canonical manuscript missing"})
        return 2
    source_hash = sha256_file(canonical)
    current_hash = sha256_file(sub_path) if sub_path.is_file() else None
    problems, artifacts = [], []
    if current_hash is not None and current_hash != source_hash:
        problems.append("canonical_copy_differs")
    if meta.get("canonical") and meta["canonical"] != canonical.relative_to(project_root).as_posix():
        problems.append("canonical_source_changed")
    if meta.get("source_hash") and meta["source_hash"] != source_hash:
        problems.append("recorded_canonical_changed")
    for row in meta.get("artifacts", []):
        source = safe_path(project_root, row["source"])
        output = safe_path(directory, row["target"])
        actual_source = sha256_file(source) if source.is_file() else None
        actual_output = sha256_file(output) if output.is_file() else None
        state = []
        if actual_source != row["source_hash"]:
            state.append("source_changed_or_missing")
        if actual_output != row["output_hash"]:
            state.append("output_changed_or_missing")
        for dep in row.get("derived_from", []):
            path = safe_path(project_root, dep["path"])
            if not path.is_file() or sha256_file(path) != dep["sha256"]:
                state.append("render_input_changed_or_missing")
        if state:
            problems.append(row["id"])
        artifacts.append({**row, "current_source_hash": actual_source,
                          "current_output_hash": actual_output, "drift": state})
    expected = {r["target"] for r in meta.get("artifacts", [])} | {".journal_meta.json"}
    unregistered = sorted(set(inventory(directory)) - expected) if artifacts else []
    if unregistered:
        problems.append("unregistered_files")
    status = "MISSING_SUBMISSION" if current_hash is None else "DRIFT" if problems else "CURRENT"
    payload = {"schema_version": 2, "journal": journal, "status": status,
               "canonical": canonical.relative_to(project_root).as_posix(),
               "submission_manuscript": sub_path.relative_to(project_root).as_posix(),
               "source_hash": source_hash, "submission_hash": current_hash,
               "recorded_source_hash": meta.get("source_hash"), "artifacts": artifacts,
               "unregistered_files": unregistered, "issues": problems,
               "verification": verification_context(project_root, journal),
               "readiness": "not_assessed", "message": "; ".join(problems)}
    write_json(qc_path, payload)
    print(json.dumps(payload, indent=2))
    # Missing input is distinct from detected drift (preflight already understands exit 2).
    return 2 if current_hash is None else 1 if problems else 0


def build(project_root: Path, journal: str, canonical: Path, spec: dict | None = None) -> int:
    directory = journal_root(project_root, journal)
    old_meta = load_json(directory / ".journal_meta.json")
    # Validate a pre-existing report before modifying the package; malformed
    # evidence must not turn a completed build into a late parse failure.
    load_json(safe_path(project_root, "qc/preflight_gate_report.json"))
    if old_meta.get("frozen") or old_meta.get("status") in {"submitted", "accepted", "published"}:
        raise ValueError("Frozen/submitted package is immutable; use a new revision journal slug")
    rows = prepare_artifacts(project_root, journal, canonical, spec or {})
    old_rows = old_meta.get("artifacts", [])
    allowed = {r["target"] for r in old_rows} | {".journal_meta.json"}
    if old_meta and not old_rows:
        allowed.add("manuscript/manuscript.md")
        if submission_md_path(project_root, journal).is_file() and sha256_file(
                submission_md_path(project_root, journal)) != old_meta.get("source_hash"):
            raise ValueError("Legacy submission was edited; preserve it and reconcile before building")
    if set(inventory(directory)) - allowed:
        raise ValueError("Unregistered package files would be lost; use a new revision slug")
    if {r["target"] for r in old_rows} - {r["target"] for r in rows}:
        raise ValueError("Build would remove a registered artifact; use a new revision slug")
    for row in old_rows:
        target = safe_path(directory, row["target"])
        if target.is_file() and sha256_file(target) != row["output_hash"]:
            raise ValueError("Submission output was edited; preserve it and reconcile before building")
    meta = {**old_meta, "schema_version": 2, "journal": journal, "status": "built",
            "canonical": canonical.relative_to(project_root).as_posix(),
            "submission_manuscript": f"submission/{journal}/manuscript/manuscript.md",
            "source_hash": rows[0]["source_hash"], "built_date": date.today().isoformat(),
            "frozen": False, "artifacts": rows, "readiness": "not_assessed"}
    for row in rows:
        row["output_hash"] = row["source_hash"]
    manifest = manifest_payload(project_root, journal, meta)  # Validate before any replacement.
    safe_path(project_root, "qc/submission_sync_" + journal + ".json")
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".sync-build-", dir=directory.parent) as temp:
        stage, backup = Path(temp) / "stage", Path(temp) / "backup"
        stage.mkdir()
        for row in rows:
            output = stage / row["target"]
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(project_root / row["source"], output)
            if sha256_file(output) != row["source_hash"]:
                raise ValueError("Source changed during copy; package not replaced")
        # Recheck pinned sources, including dependencies, before installing the staged package.
        if prepare_artifacts(project_root, journal, canonical, spec or {}) != [
                {k: v for k, v in r.items() if k != "output_hash"} for r in rows]:
            raise ValueError("Source changed during build; package not replaced")
        write_json(stage / ".journal_meta.json", meta)
        existed = directory.exists()
        if existed:
            directory.rename(backup)
        try:
            stage.rename(directory)
            write_json(project_root / "artifact_manifest.json", manifest)
        except BaseException:
            if directory.exists():
                shutil.rmtree(directory)
            if existed:
                backup.rename(directory)
            raise
    return audit(project_root, journal, canonical)


def freeze(project_root: Path, journal: str, canonical: Path, status: str) -> int:
    code = audit(project_root, journal, canonical)
    if code:
        print("Cannot freeze a missing, drifted or invalid submission package.", file=sys.stderr)
        return code
    meta_path = journal_root(project_root, journal) / ".journal_meta.json"
    meta = load_json(meta_path)
    if not meta or not meta.get("source_hash"):
        raise ValueError("Build metadata is required before freeze")
    if meta.get("frozen"):
        if meta.get("status") != status:
            raise ValueError("Frozen status cannot be overwritten")
        return 0
    meta.update({"status": status, "frozen": True, "frozen_date": date.today().isoformat(),
                 "verification_at_freeze": verification_context(project_root, journal),
                 "readiness": "not_assessed"})
    manifest = manifest_payload(project_root, journal, meta)
    previous = meta_path.read_bytes()
    try:
        write_json(meta_path, meta)
        write_json(project_root / "artifact_manifest.json", manifest)
    except BaseException:
        write_json(meta_path, json.loads(previous))
        raise
    print("Frozen byte snapshot; visual, semantic, permissions and submission approval remain separate.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["audit", "build", "freeze"])
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--journal", required=True)
    parser.add_argument("--canonical")
    parser.add_argument("--bundle-spec", help="JSON declaration of additional files and pinned render inputs (build only)")
    parser.add_argument("--status", default="submitted")
    args = parser.parse_args()
    try:
        root = Path(args.project_root).resolve()
        if not root.is_dir():
            raise ValueError("Project root must exist")
        journal_root(root, args.journal)
        canonical = resolve_canonical(root, args.canonical)
        canonical = safe_path(root, canonical.relative_to(root).as_posix())
        if canonical.is_relative_to(journal_root(root, args.journal)):
            raise ValueError("Canonical manuscript must be outside its submission package")
        if canonical.is_relative_to(root / "qc") or canonical in {root / "artifact_manifest.json", root / "project.yaml"}:
            raise ValueError("Canonical manuscript aliases a mutable control/report path")
        if args.bundle_spec and args.mode != "build":
            raise ValueError("--bundle-spec is only supported by build")
        if args.mode == "audit":
            return audit(root, args.journal, canonical)
        with mutation_lock(root):
            if args.mode == "build":
                spec = load_json(safe_path(root, args.bundle_spec)) if args.bundle_spec else {}
                if args.bundle_spec and not spec:
                    raise ValueError("Bundle spec is missing or empty")
                return build(root, args.journal, canonical, spec)
            return freeze(root, args.journal, canonical, args.status)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Submission sync error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""Registry that normalises the medsci-skills deterministic detectors to one
calling convention for the evaluation harnesses.

Each detector is invoked as a subprocess with a scrubbed, deterministic
environment (LC_ALL=C, PYTHONHASHSEED=0). The non-uniform CLIs (verify_refs's
positional input + project-root output; check_citation_keys's two positionals +
stdout) are handled by per-mode builders/parsers. ``found_codes`` is the set of
machine-readable codes a detector emitted, used to decide whether a seeded
defect was caught.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .workspace import REPO_ROOT


@dataclass(frozen=True)
class DetectorInputs:
    manuscript: Optional[Path] = None
    data_csv: Optional[Path] = None
    analysis_dir: Optional[Path] = None
    analysis_files: tuple = ()
    refs_input: Optional[Path] = None      # .bib/.md for verify_refs
    md_for_keys: Optional[Path] = None     # manuscript for check_citation_keys
    bib_for_keys: Optional[Path] = None    # bib for check_citation_keys
    project_root: Optional[Path] = None    # verify_refs output root


@dataclass(frozen=True)
class DetectorResult:
    detector_id: str
    exit_code: int
    found_codes: frozenset
    json_obj: Optional[dict]
    raw_stdout: str
    raw_stderr: str
    duration_s: float


# id -> spec. script paths are relative to REPO_ROOT.
DETECTORS: dict[str, dict] = {
    "classical_style": {
        "script": "skills/self-review/scripts/check_classical_style.py",
        "mode": "manuscript",
        "family": "Style and review-process integrity",
        "network": False,
    },
    "scope_coherence": {
        "script": "skills/self-review/scripts/check_scope_coherence.py",
        "mode": "manuscript",
        "family": "Confounding, scope, and estimand contracts",
        "network": False,
    },
    "cohort_arithmetic": {
        "script": "skills/self-review/scripts/check_cohort_arithmetic.py",
        "mode": "manuscript_data",
        "family": "Numerical, cohort, and pool arithmetic",
        "network": False,
    },
    "artifact_coverage": {
        "script": "skills/self-review/scripts/check_artifact_coverage.py",
        "mode": "manuscript_analysisdir",
        "family": "Numerical, cohort, and pool arithmetic",
        "network": False,
    },
    "framework_naming": {
        "script": "skills/check-reporting/scripts/check_framework_naming.py",
        "mode": "manuscript",
        "family": "Reporting compliance",
        "network": False,
    },
    "generated_code": {
        "script": "skills/analyze-stats/scripts/check_generated_code.py",
        "mode": "code",
        "family": "Style and review-process integrity",
        "network": False,
    },
    "verify_refs": {
        "script": "skills/verify-refs/scripts/verify_refs.py",
        "mode": "verify_refs",
        "family": "Citation and reference integrity",
        "network": True,   # FABRICATED/MISMATCH need network; offline yields PAGINATION/DUPLICATE
    },
    "citation_keys": {
        "script": "skills/manage-refs/scripts/check_citation_keys.py",
        "mode": "citation_keys",
        "family": "Citation and reference integrity",
        "network": False,
    },
}


def _env() -> dict:
    e = dict(os.environ)
    e["LC_ALL"] = "C"
    e["PYTHONHASHSEED"] = "0"
    return e


def _verify_refs_codes(audit: dict) -> set:
    codes: set = set()
    for rec in audit.get("records", []):
        st = rec.get("status")
        if st:
            codes.add(st)
        note = (rec.get("note") or "").lower()
        if "pagination_placeholder" in note:
            codes.add("PAGINATION_PLACEHOLDER")
    if audit.get("duplicate_findings"):
        codes.add("DUPLICATE")
    return codes


def run_detector(
    det_id: str,
    inputs: DetectorInputs,
    out_path: Path,
    *,
    online: bool = False,
    cwd: Optional[Path] = None,
    timeout: int = 120,
) -> DetectorResult:
    spec = DETECTORS[det_id]
    script = REPO_ROOT / spec["script"]
    mode = spec["mode"]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    py = sys.executable
    if mode in ("manuscript", "manuscript_data", "manuscript_analysisdir"):
        argv = [py, str(script), "--manuscript", str(inputs.manuscript),
                "--out", str(out_path), "--quiet"]
        if mode == "manuscript_data" and inputs.data_csv:
            argv += ["--data", str(inputs.data_csv)]
        if mode == "manuscript_analysisdir" and inputs.analysis_dir:
            argv += ["--analysis-dir", str(inputs.analysis_dir)]
    elif mode == "code":
        argv = [py, str(script), *[str(f) for f in inputs.analysis_files],
                "--out", str(out_path), "--quiet"]
    elif mode == "verify_refs":
        proj = inputs.project_root or out_path.parent
        argv = [py, str(script), str(inputs.refs_input),
                "--project-root", str(proj)]
        if not online:
            argv += ["--offline"]
    elif mode == "citation_keys":
        argv = [py, str(script), str(inputs.md_for_keys), str(inputs.bib_for_keys)]
    else:
        raise ValueError(f"unknown mode: {mode}")

    if cwd is None:
        cwd = out_path.parent

    t0 = time.monotonic()
    proc = subprocess.run(
        argv, env=_env(), cwd=str(cwd),
        capture_output=True, text=True, timeout=timeout,
    )
    dt = time.monotonic() - t0

    json_obj: Optional[dict] = None
    found: set = set()

    if mode in ("manuscript", "manuscript_data", "manuscript_analysisdir", "code"):
        if out_path.is_file():
            json_obj = json.loads(out_path.read_text(encoding="utf-8"))
            found = {c.get("verdict") for c in json_obj.get("claims", []) if c.get("verdict")}
    elif mode == "verify_refs":
        proj = inputs.project_root or out_path.parent
        audit_path = Path(proj) / "qc" / "reference_audit.json"
        if audit_path.is_file():
            json_obj = json.loads(audit_path.read_text(encoding="utf-8"))
            found = _verify_refs_codes(json_obj)
    elif mode == "citation_keys":
        json_obj = {"stdout": proc.stdout}
        if "UNDEFINED (" in proc.stdout:
            # "UNDEFINED (N) — ..."; flag only when N>0
            import re
            m = re.search(r"UNDEFINED \((\d+)\)", proc.stdout)
            if m and int(m.group(1)) > 0:
                found.add("UNDEFINED")

    return DetectorResult(
        detector_id=det_id,
        exit_code=proc.returncode,
        found_codes=frozenset(found),
        json_obj=json_obj,
        raw_stdout=proc.stdout,
        raw_stderr=proc.stderr,
        duration_s=dt,
    )

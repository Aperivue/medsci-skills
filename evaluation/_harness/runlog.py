"""Run-logging helper producing the evaluation log package.

One RunLogger per harness invocation. It writes the package described in the
plan: run_manifest.json, commands.sh, environment.txt, git_commit.txt,
input_files_manifest.json, timing_cost.json, limitations.md, plus
detector_outputs/ (populated by the harness) and, for fault-injection
harnesses, injected_defects.jsonl.

Real Python: datetime.now() and subprocess (git) are used here intentionally.
The reproducibility hash deliberately covers only deterministic artifacts
(metrics.csv, detector_outputs/, injected_defects.jsonl) and excludes
environment/timing/git files, which legitimately vary.
"""

from __future__ import annotations

import json
import platform
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import hashing
from .schema import ComponentRecord, InjectionRecord
from .workspace import EVAL_ROOT, REPO_ROOT


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
    except Exception:
        return ""


class RunLogger:
    def __init__(self, experiment_id: str, run_dir: Path, git_sha: str) -> None:
        self.experiment_id = experiment_id
        self.run_dir = run_dir
        self.git_sha = git_sha
        self.components: list[dict] = []
        self.commands: list[str] = []
        self.input_paths: set[str] = set()
        self._t0 = time.monotonic()
        self._wall_start = datetime.now().isoformat(timespec="seconds")
        self._per_component_timing: list[dict] = []

    # ---- construction -------------------------------------------------
    @classmethod
    def start(cls, experiment_id: str, *, runs_root: Optional[Path] = None) -> "RunLogger":
        runs_root = runs_root or (EVAL_ROOT / "runs")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = runs_root / f"{ts}_{experiment_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "detector_outputs").mkdir(exist_ok=True)
        self = cls(experiment_id, run_dir, _git("rev-parse", "HEAD"))
        self._write_environment()
        self._write_git_commit()
        return self

    def _write_environment(self) -> None:
        lines = [
            f"python: {sys.version.splitlines()[0]}",
            f"executable: {sys.executable}",
            f"platform: {platform.platform()}",
            f"machine: {platform.machine()}",
        ]
        for mod in ("pandas", "numpy"):
            try:
                m = __import__(mod)
                lines.append(f"{mod}: {getattr(m, '__version__', '?')}")
            except Exception:
                lines.append(f"{mod}: (not installed)")
        (self.run_dir / "environment.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_git_commit(self) -> None:
        head = _git("rev-parse", "HEAD")
        desc = _git("describe", "--tags", "--always")
        porcelain = _git("status", "--porcelain")
        txt = (
            f"HEAD: {head}\n"
            f"describe: {desc}\n"
            f"dirty: {'yes' if porcelain else 'no'}\n"
            f"--- status --porcelain ---\n{porcelain}\n"
        )
        (self.run_dir / "git_commit.txt").write_text(txt, encoding="utf-8")

    # ---- logging ------------------------------------------------------
    def log_component(
        self,
        *,
        component_type: str,
        command_args: list,
        expected_reproducibility: str,
        rerun_policy: str,
        script_path: Optional[str] = None,
        model_name: Optional[str] = None,
        seed: Optional[int] = None,
        input_paths: Optional[list] = None,
        output_path: Optional[Path] = None,
        duration_s: Optional[float] = None,
    ) -> None:
        rec = ComponentRecord(
            component_type=component_type,
            git_sha=self.git_sha,
            command_args=list(command_args),
            expected_reproducibility=expected_reproducibility,
            rerun_policy=rerun_policy,
            script_path=script_path,
            model_name=model_name,
            seed=seed,
            input_hash=hashing.sha256_paths(input_paths) if input_paths else None,
            output_hash=hashing.sha256_file(output_path)
            if output_path and Path(output_path).is_file() else None,
        )
        self.components.append(rec.to_dict())
        head = script_path or model_name or "component"
        self.commands.append(" ".join(shlex.quote(str(x)) for x in [head, *command_args]))
        if input_paths:
            self.input_paths.update(str(p) for p in input_paths)
        if duration_s is not None:
            self._per_component_timing.append(
                {"component": script_path or model_name, "duration_s": round(duration_s, 4)}
            )

    def append_injected_defect(self, rec: InjectionRecord) -> None:
        with (self.run_dir / "injected_defects.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")

    def add_input(self, *paths) -> None:
        self.input_paths.update(str(p) for p in paths)

    def detector_output_path(self, *parts: str) -> Path:
        p = self.run_dir / "detector_outputs"
        for part in parts:
            p = p / part
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # ---- finalize -----------------------------------------------------
    def finalize(
        self,
        *,
        metrics_path: Optional[Path] = None,
        limitations: str = "",
        repro_hash_extra: Optional[list] = None,
        hash_detector_outputs: bool = False,
        api_cost_usd=None,
    ) -> Path:
        # input_files_manifest.json (repo-relative keys; no absolute home paths)
        def _key(pp: Path) -> str:
            try:
                return pp.resolve().relative_to(REPO_ROOT).as_posix()
            except ValueError:
                return pp.name
        manifest = {}
        for p in sorted(self.input_paths):
            pp = Path(p)
            k = _key(pp)
            if pp.is_file():
                manifest[k] = hashing.sha256_file(pp)
            elif pp.is_dir():
                manifest[k] = "dir:" + hashing.sha256_dir(pp)
            else:
                manifest[k] = "MISSING"
        (self.run_dir / "input_files_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8"
        )

        # commands.sh
        cmds = "#!/usr/bin/env bash\nset -euo pipefail\n" + "\n".join(self.commands) + "\n"
        (self.run_dir / "commands.sh").write_text(cmds, encoding="utf-8")

        # timing_cost.json
        timing = {
            "wall_start": self._wall_start,
            "wall_end": datetime.now().isoformat(timespec="seconds"),
            "wall_clock_s": round(time.monotonic() - self._t0, 3),
            "per_component": self._per_component_timing,
            "machine": platform.platform(),
            "api_cost_usd": api_cost_usd,
        }
        (self.run_dir / "timing_cost.json").write_text(
            json.dumps(timing, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # reproducibility hash: deterministic, path-free result artifacts only.
        # detector_outputs/ is preserved raw evidence that embeds per-run temp
        # paths, so it is excluded by default (opt in with hash_detector_outputs).
        repro_targets = []
        if metrics_path and Path(metrics_path).is_file():
            repro_targets.append(("metrics.csv", hashing.sha256_file(metrics_path)))
        if hash_detector_outputs:
            det_dir = self.run_dir / "detector_outputs"
            repro_targets.append(("detector_outputs/", hashing.sha256_dir(det_dir)))
        inj = self.run_dir / "injected_defects.jsonl"
        if inj.is_file():
            repro_targets.append(("injected_defects.jsonl", hashing.sha256_file(inj)))
        for extra in (repro_hash_extra or []):
            ep = Path(extra)
            if ep.is_file():
                repro_targets.append((ep.name, hashing.sha256_file(ep)))
        repro_summary = hashing.sha256_json(dict(repro_targets))

        # run_manifest.json
        run_manifest = {
            "experiment_id": self.experiment_id,
            "timestamp": self._wall_start,
            "git_sha": self.git_sha,
            "git_dirty": bool(_git("status", "--porcelain")),
            "reproducibility_hash": repro_summary,
            "reproducibility_targets": dict(repro_targets),
            "components": self.components,
        }
        (self.run_dir / "run_manifest.json").write_text(
            json.dumps(run_manifest, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8"
        )

        (self.run_dir / "limitations.md").write_text(
            limitations or "(no limitations recorded)\n", encoding="utf-8"
        )
        return self.run_dir

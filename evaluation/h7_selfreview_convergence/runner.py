"""Pluggable self-review runner for the E9 convergence harness.

The self-review loop is LLM/agent-driven (it orchestrates the deterministic
detectors but the verdict/scoring and --fix edits are model judgments), so it is
the non-deterministic boundary of E9. This module exposes a single contract that
a host can implement; the default returns None so the harness records NOT_RUN.

Contract:
    self_review_runner(manuscript_path: Path, mode: str) -> dict | None
        mode in {"single", "fix", "panel"}.
        Returns None when no runner is configured (-> NOT_RUN), else a dict:
          {
            "verdict": "PASS" | "REVISE" | "ACCEPT-WITH-NOTES",
            "overall_score": int | None,
            "findings": [ {severity, fixable_by_ai, category, suggested_fix, ...}, ... ],
            "raw_output": str,                 # full self-review text
            "fix_diff": str,                   # unified diff applied in --fix mode ("" otherwise)
            "output_manuscript": str,          # manuscript text after this round's fixes
            "model_version": str,              # tool/model id for logging
            "panel_lenses": [str, ...],        # fixed reviewer lens definitions (panel mode)
          }

To enable execution, set the environment variable MEDSCI_SELFREVIEW_RUNNER to a
"module:function" path implementing the contract, or replace get_runner() below.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Callable, Optional


def get_runner() -> Optional[Callable]:
    spec = os.environ.get("MEDSCI_SELFREVIEW_RUNNER")
    if not spec or ":" not in spec:
        return None
    mod_name, fn_name = spec.split(":", 1)
    try:
        mod = importlib.import_module(mod_name)
        return getattr(mod, fn_name)
    except Exception:
        return None


def self_review_runner(manuscript_path: Path, mode: str):
    runner = get_runner()
    if runner is None:
        return None
    return runner(manuscript_path, mode)

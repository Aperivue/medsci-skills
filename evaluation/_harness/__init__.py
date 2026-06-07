"""Shared, stdlib-only spine for the medsci-skills evaluation harness suite.

Submodules:
  hashing   - canonical SHA-256 of files / dirs / JSON
  workspace - golden-input resolution + safe temp-copy workspaces
  detectors - registry normalising the deterministic detector CLIs
  schema    - dataclasses for log-package records
  runlog    - RunLogger producing the evaluation log package
"""

from . import detectors, hashing, runlog, schema, workspace  # noqa: F401

__all__ = ["hashing", "workspace", "detectors", "schema", "runlog"]

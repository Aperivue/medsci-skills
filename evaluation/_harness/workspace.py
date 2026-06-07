"""Golden-input resolution and safe temp-copy workspaces.

Invariant: harnesses NEVER write to the real demo directories or the real
repo. Every mutation happens inside a temp copy whose path begins with the
module's temp prefix; ``safe_write`` enforces this so an injector cannot, by a
path bug, clobber the source of truth.
"""

from __future__ import annotations

import contextlib
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

# evaluation/_harness/workspace.py -> repo root is parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_ROOT = REPO_ROOT / "evaluation"
DEMO_ROOT = REPO_ROOT / "demo"

TEMP_PREFIX = "medsci-eval-"

DEMOS = ("01_wisconsin_bc", "02_metafor_bcg", "03_nhanes_obesity")


@dataclass(frozen=True)
class GoldenDemo:
    """Read-only handles into one demo directory."""

    demo_id: str
    root: Path

    @property
    def manuscript(self) -> Path:
        return self.root / "manuscript" / "manuscript.md"

    @property
    def refs_bib(self) -> Path:
        return self.root / "manuscript" / "_src" / "refs.bib"

    @property
    def analysis_dir(self) -> Path:
        return self.root / "analysis"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def qc_dir(self) -> Path:
        return self.root / "qc"

    @property
    def manifest(self) -> Path:
        return self.root / "manifest.lock.json"

    def data_csvs(self) -> list[Path]:
        if not self.data_dir.is_dir():
            return []
        return sorted(self.data_dir.glob("*.csv"))

    def has(self, attr: str) -> bool:
        p = getattr(self, attr)
        return p.exists()


def golden_inputs() -> dict[str, GoldenDemo]:
    """Resolve the three demos as read-only golden inputs."""
    out = {}
    for d in DEMOS:
        root = DEMO_ROOT / d
        if root.is_dir():
            out[d] = GoldenDemo(demo_id=d, root=root)
    return out


def _under_temp(path: Path) -> bool:
    parts = Path(path).resolve().parts
    return any(seg.startswith(TEMP_PREFIX) for seg in parts)


def safe_write(path: str | Path, text: str, *, encoding: str = "utf-8") -> None:
    """Write text only if the path lives inside a temp workspace.

    Hard guard against accidentally mutating real demos / repo files.
    """
    p = Path(path)
    if not _under_temp(p):
        raise RuntimeError(
            f"refusing to write outside a temp workspace: {p} "
            f"(paths must contain a '{TEMP_PREFIX}*' segment)"
        )
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding=encoding)


@contextlib.contextmanager
def temp_copy(src: str | Path, *, label: str = "") -> Iterator[Path]:
    """Copy ``src`` (file or dir) into a fresh temp dir and yield the copy root.

    For a directory, the whole tree is copied and the copied directory path is
    yielded. For a file, the file is copied into the temp dir and the copied
    file path is yielded. Cleaned up on exit.
    """
    src = Path(src)
    tmp = Path(tempfile.mkdtemp(prefix=f"{TEMP_PREFIX}{label + '-' if label else ''}"))
    try:
        if src.is_dir():
            dst = tmp / src.name
            shutil.copytree(src, dst)
            yield dst
        else:
            dst = tmp / src.name
            shutil.copy2(src, dst)
            yield dst
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@contextlib.contextmanager
def temp_demo(demo: GoldenDemo) -> Iterator[Path]:
    """Yield a writable temp copy of a demo's root directory."""
    with temp_copy(demo.root, label=demo.demo_id) as dst:
        yield dst


@contextlib.contextmanager
def temp_dir(label: str = "") -> Iterator[Path]:
    """A bare temp directory (for fixture-based harnesses)."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{TEMP_PREFIX}{label + '-' if label else ''}"))
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

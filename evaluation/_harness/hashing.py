"""Canonical content hashing for the evaluation suite.

Stdlib-only. All hashes are SHA-256. JSON hashing uses sorted keys + compact
separators so the same logical object always produces the same digest,
independent of insertion order or whitespace. This is the backbone of the
"same input -> same output hash" reproducibility guarantee for the
deterministic harnesses (E1, E4, E7, E8).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

_BLOCK = 64 * 1024


def sha256_file(path: str | Path) -> str:
    """SHA-256 of a file's raw bytes, streamed."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(_BLOCK), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(obj) -> str:
    """SHA-256 of a JSON-serialisable object, key-order independent."""
    payload = json.dumps(
        obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return sha256_text(payload)


def sha256_dir(root: str | Path) -> str:
    """SHA-256 over a directory tree: sorted "relpath:filehash" lines.

    Deterministic regardless of filesystem walk order. Empty / missing dir
    hashes the empty string so the value is still well-defined.
    """
    root = Path(root)
    if not root.exists():
        return sha256_text("")
    entries = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            entries.append(f"{rel}:{sha256_file(p)}")
    return sha256_text("\n".join(entries))


def sha256_paths(paths: Iterable[str | Path]) -> str:
    """Stable hash over a set of input files (sorted by posix relpath of the
    absolute path). Used to fingerprint a harness's golden inputs."""
    items = []
    for p in sorted(str(Path(x)) for x in paths):
        pp = Path(p)
        if pp.is_file():
            items.append(f"{pp.as_posix()}:{sha256_file(pp)}")
        elif pp.is_dir():
            items.append(f"{pp.as_posix()}/:{sha256_dir(pp)}")
        else:
            items.append(f"{pp.as_posix()}:MISSING")
    return sha256_text("\n".join(items))

#!/usr/bin/env python3
"""Dataset version control: content-hash manifest, drift verification, and diff.

Records a deterministic fingerprint of a dataset (or any analysis artifact) so a
later run can prove the inputs/outputs are unchanged, and so two versions can be
compared. Serves two needs:

  1. Dataset versioning for research — detect that an extract changed between
     analysis runs (schema drift, row-count change, value changes) instead of
     silently re-running on different data (data-integrity rule, seed=42).
  2. Reproducibility lock for bundled demos — hash input data + deterministic
     outputs into a manifest.lock so CI can verify a demo still reproduces.

Subcommands:
  manifest <paths...> --out FILE   build a manifest (file SHA-256 + tabular schema)
  verify   --manifest FILE [paths] recompute and compare; --strict exits non-zero on drift
  diff     --old A --new B         compare two manifests

File-level SHA-256 works with the stdlib alone. Tabular schema/column hashing
uses pandas when available; without it, files are still hashed at the byte level.
Deterministic by design: no timestamps are written unless passed via --stamp.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    import pandas as pd
    _HAVE_PANDAS = True
except ImportError:
    _HAVE_PANDAS = False

TABULAR = {".csv", ".tsv", ".parquet", ".pq", ".dta", ".sas7bdat", ".xlsx"}


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_str(path: Path):
    """Read a tabular file with every cell as its literal string.

    Hashing must depend only on the data, not on the reader's environment. Native
    dtype inference (int64 vs int32, object vs string, NaN coercion, float repr)
    varies across pandas versions and platforms, which made manifests fail to
    reproduce in CI. Reading CSV/TSV with dtype=str + keep_default_na=False
    captures the exact textual content; other formats are read then stringified.
    """
    suf = path.suffix.lower()
    if suf in (".csv", ".txt"):
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    if suf == ".tsv":
        return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    if suf in (".parquet", ".pq"):
        df = pd.read_parquet(path)
    elif suf == ".dta":
        df = pd.read_stata(path)
    elif suf == ".sas7bdat":
        df = pd.read_sas(path)
    elif suf == ".xlsx":
        df = pd.read_excel(path, dtype=str)
    else:
        return None
    return df.astype(str)


def column_hashes(path: Path, ignore_cols: set[str]) -> dict | None:
    if not _HAVE_PANDAS or path.suffix.lower() not in TABULAR:
        return None
    try:
        df = _read_str(path)
    except Exception:
        return None
    if df is None:
        return None
    cols = {}
    for c in df.columns:
        if c in ignore_cols:
            continue
        # Cells are already canonical strings (environment-independent); the
        # pandas dtype is deliberately NOT part of the digest.
        payload = ("\x1e".join(df[c].tolist())).encode("utf-8")
        cols[str(c)] = hashlib.sha256(payload).hexdigest()
    return {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "column_hashes": cols,
    }


def build_entry(path: Path, ignore_cols: set[str]) -> dict:
    entry = {"sha256": file_sha256(path), "bytes": path.stat().st_size}
    tab = column_hashes(path, ignore_cols)
    if tab is not None:
        entry["tabular"] = tab
    return entry


def cmd_manifest(args: argparse.Namespace) -> int:
    ignore = set(args.ignore_cols or [])
    files = sorted(Path(p) for p in args.paths)
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        print(f"ERROR: not found: {', '.join(missing)}", file=sys.stderr)
        return 2
    base = Path(args.base).resolve() if args.base else None
    entries = {}
    for p in files:
        key = p.resolve().relative_to(base).as_posix() if base else p.as_posix()
        entries[key] = build_entry(p, ignore)
    manifest = {
        "schema_version": 1,
        "seed": args.seed,
        "provenance": args.provenance,
        "files": entries,
    }
    if args.stamp:
        manifest["stamp"] = args.stamp
    out = Path(args.out)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"files": len(entries), "out": str(out)}, indent=2))
    return 0


def _compare(expected: dict, actual: dict) -> list[str]:
    drift: list[str] = []
    exp_files, act_files = expected.get("files", {}), actual.get("files", {})
    for name in sorted(set(exp_files) | set(act_files)):
        if name not in act_files:
            drift.append(f"MISSING file: {name}")
            continue
        if name not in exp_files:
            drift.append(f"UNEXPECTED file: {name}")
            continue
        e, a = exp_files[name], act_files[name]
        et, at = e.get("tabular"), a.get("tabular")
        if et and at:
            # Tabular: compare LOGICAL content (schema + column hashes), not raw
            # bytes. Byte hash is over-sensitive (re-save, float formatting, an
            # --ignore-cols column) and the column hashes fully characterize the
            # data; only flag a byte change for non-tabular files below.
            if et["n_rows"] != at["n_rows"]:
                drift.append(f"ROW COUNT {name}: {et['n_rows']} -> {at['n_rows']}")
            ec, ac = set(et["column_hashes"]), set(at["column_hashes"])
            for col in sorted(ec - ac):
                drift.append(f"REMOVED column {name}:{col}")
            for col in sorted(ac - ec):
                drift.append(f"ADDED column {name}:{col}")
            for col in sorted(ec & ac):
                if et["column_hashes"][col] != at["column_hashes"][col]:
                    drift.append(f"CHANGED column {name}:{col}")
        else:
            # Non-tabular (or no longer readable as tabular): byte hash is the
            # only available signal.
            if e.get("sha256") != a.get("sha256"):
                drift.append(f"CHANGED bytes: {name}")
    return drift


def cmd_verify(args: argparse.Namespace) -> int:
    expected = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    ignore = set(args.ignore_cols or [])
    base = Path(args.base).resolve() if args.base else None
    actual_files = {}
    for name in expected.get("files", {}):
        p = (base / name) if base else Path(name)
        if not p.is_file():
            actual_files[name] = {"sha256": None}
            continue
        actual_files[name] = build_entry(p, ignore)
    actual = {"files": actual_files}
    drift = _compare(expected, actual)
    print("=" * 41)
    print(" Dataset Manifest Verify")
    print("=" * 41)
    if not drift:
        print(f"OK: {len(expected.get('files', {}))} file(s) match the manifest.")
        return 0
    print(f"DRIFT ({len(drift)}):")
    for d in drift:
        print(f"  {d}")
    if args.strict:
        print("\nMANIFEST_DRIFT: dataset differs from manifest.", file=sys.stderr)
        return 1
    print("\n(non-strict: reported only; rerun with --strict to fail.)")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    old = json.loads(Path(args.old).read_text(encoding="utf-8"))
    new = json.loads(Path(args.new).read_text(encoding="utf-8"))
    drift = _compare(old, new)
    if not drift:
        print("No differences between manifests.")
        return 0
    print(f"Differences ({len(drift)}):")
    for d in drift:
        print(f"  {d}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Dataset version control: manifest / verify / diff.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("manifest", help="Build a content-hash manifest.")
    m.add_argument("paths", nargs="+", help="Data/artifact files to fingerprint.")
    m.add_argument("--out", default="manifest.json", help="Output manifest path.")
    m.add_argument("--base", help="Base dir; manifest keys are paths relative to it.")
    m.add_argument("--seed", type=int, default=None, help="Analysis seed to record (e.g. 42).")
    m.add_argument("--provenance", default=None, help="Free-text provenance note.")
    m.add_argument("--stamp", default=None, help="Optional timestamp string to record (omitted by default for determinism).")
    m.add_argument("--ignore-cols", nargs="*", help="Column names excluded from hashing.")
    m.set_defaults(func=cmd_manifest)

    v = sub.add_parser("verify", help="Recompute and compare against a manifest.")
    v.add_argument("--manifest", required=True)
    v.add_argument("--base", help="Base dir for resolving manifest file keys.")
    v.add_argument("--ignore-cols", nargs="*")
    v.add_argument("--strict", action="store_true", help="Exit non-zero on any drift.")
    v.set_defaults(func=cmd_verify)

    d = sub.add_parser("diff", help="Compare two manifests.")
    d.add_argument("--old", required=True)
    d.add_argument("--new", required=True)
    d.set_defaults(func=cmd_diff)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

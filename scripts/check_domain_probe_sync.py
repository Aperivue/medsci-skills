#!/usr/bin/env python3
"""Domain-probe vendoring drift gate.

The six domain-specific critique probe modules (sr_ma, survival_prognostic,
radiomics, narrative_review, observational_confounding, ai_overclaiming) live
canonically inside the peer-review skill and are vendored BYTE-IDENTICAL into the
self-review skill.
Skills are distributed
individually (/publish-skill), so a runtime cross-skill import is forbidden;
build-time vendoring with this drift gate is the portability-preserving pattern
(see docs/dedup_audit.md; same idea as the vendored citation writer).

This gate asserts the canonical set and the vendored set are identical:
  - same file set (no module added/removed on one side only)
  - byte-identical content (sha256 per module)

Modes:
  --strict (default behavior is report-only): exit 1 on any drift / missing /
           extra module. Wire this into CI and validate_skills.sh.
  --sync:  copy canonical -> vendored (the one-command fix after editing the
           canonical copy). Mutually exclusive with --strict.

Stdlib-only. Exit codes: 0 in sync (or after --sync), 1 drift (with --strict),
2 a canonical/vendored dir is missing.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

MODULES = (
    "sr_ma.md",
    "survival_prognostic.md",
    "radiomics.md",
    "narrative_review.md",
    "observational_confounding.md",
    "ai_overclaiming.md",
    "rct_trial.md",
)

CANONICAL_REL = "skills/peer-review/references/domain-probes"
VENDORED_REL = "skills/self-review/references/domain-probes"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def listing(d: Path) -> set[str]:
    return {p.name for p in d.glob("*.md")} if d.is_dir() else set()


def do_sync(canonical: Path, vendored: Path) -> int:
    vendored.mkdir(parents=True, exist_ok=True)
    for name in MODULES:
        src = canonical / name
        if not src.is_file():
            print(f"ERROR: canonical module missing: {src}", file=sys.stderr)
            return 2
        shutil.copyfile(src, vendored / name)
        print(f"synced  {name}")
    # Remove any stray vendored files not in the canonical set.
    for stray in sorted(listing(vendored) - set(MODULES)):
        (vendored / stray).unlink()
        print(f"removed stray vendored file  {stray}")
    print(f"OK: {len(MODULES)} module(s) vendored canonical -> self-review")
    return 0


def do_check(canonical: Path, vendored: Path, strict: bool) -> int:
    if not canonical.is_dir():
        print(f"ERROR: canonical dir missing: {canonical}", file=sys.stderr)
        return 2
    if not vendored.is_dir():
        print(f"ERROR: vendored dir missing: {vendored}", file=sys.stderr)
        return 2

    problems: list[str] = []

    # File-set equality (each side must hold exactly the expected modules).
    canon_set, vend_set = listing(canonical), listing(vendored)
    for name in MODULES:
        if name not in canon_set:
            problems.append(f"canonical missing module: {name}")
        if name not in vend_set:
            problems.append(f"vendored missing module: {name}")
    for extra in sorted(canon_set - set(MODULES)):
        problems.append(f"unexpected file in canonical dir: {extra}")
    for extra in sorted(vend_set - set(MODULES)):
        problems.append(f"unexpected file in vendored dir: {extra}")

    # Byte-identity per module.
    for name in MODULES:
        c, v = canonical / name, vendored / name
        if c.is_file() and v.is_file():
            ch, vh = sha256_file(c), sha256_file(v)
            if ch != vh:
                problems.append(
                    f"drift: {name} canonical={ch[:12]}... vendored={vh[:12]}..."
                )

    print("=" * 41)
    print(" Domain-Probe Vendoring Sync")
    print("=" * 41)
    print(f"canonical: {CANONICAL_REL}")
    print(f"vendored:  {VENDORED_REL}")
    if not problems:
        print(f"OK: {len(MODULES)} module(s) byte-identical across both skills.")
        return 0

    print(f"\nDOMAIN_PROBE_DRIFT ({len(problems)}):")
    for p in problems:
        print(f"  - {p}")
    print("\nFix: python3 scripts/check_domain_probe_sync.py --sync")
    return 1 if strict else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Domain-probe vendoring drift gate.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--strict", action="store_true",
                      help="Exit non-zero on any drift (CI gate).")
    mode.add_argument("--sync", action="store_true",
                      help="Copy canonical -> vendored (fix drift).")
    args = ap.parse_args()

    root = repo_root()
    canonical = root / CANONICAL_REL
    vendored = root / VENDORED_REL

    if args.sync:
        return do_sync(canonical, vendored)
    return do_check(canonical, vendored, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Vendoring drift gate — every vendored set, not just the one we remembered.

Skills ship standalone (`/publish-skill`), so a runtime cross-skill import is forbidden.
Build-time vendoring — keep one canonical copy, copy it byte-identical into the consuming skill —
is the portability-preserving pattern (see docs/dedup_audit.md; same idea as the vendored citation
writer). It is only safe if something asserts the copies never drift apart.

This gate used to guard exactly ONE vendored set: the domain probes. Meanwhile SIX risk-of-bias
checklists (RoB2, NOS, ROBINS_I, QUADAS2, PROBAST, PRISMA_DTA) were vendored from `/check-reporting`
into `/meta-analysis` byte-identically and gated by NOTHING. No drift had happened yet — but the
probes prove the maintainer already believes this guard is necessary, and the checklists were simply
forgotten. A guard that exists for one instance of a pattern and not for its twin is not a guard;
it is a coincidence.

So the gate is now table-driven (`VENDOR_SETS`) AND self-discovering:

  1. DECLARED SETS — for each set: same files on both sides, byte-identical (sha256).
  2. UNDECLARED VENDORING — hash every file under skills/ and flag any content that appears in
     TWO OR MORE skills without being declared above. This is the part that makes a THIRD vendored
     set impossible to forget: you do not have to remember to add it to the table, because the gate
     finds it and fails until you do.

Step 2 is why this file does not need to be renamed every time a new pair is vendored. It is the
vendoring gate, not the domain-probe gate; the filename is kept only because ~50 files (including
the header of every vendored probe) point at it by name.

Modes:
  --strict : exit 1 on any drift / missing / extra / undeclared duplicate. Wired into CI and
             validate_skills.sh.
  --sync   : copy canonical -> vendored for every declared set (the one-command fix).
  --root   : operate on an alternate tree (used by tests/test_vendoring_sync.sh).

Stdlib-only. Exit codes: 0 in sync (or after --sync), 1 drift (with --strict), 2 a dir is missing.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import shutil
import sys
from pathlib import Path
from typing import NamedTuple


class VendorSet(NamedTuple):
    """One canonical -> vendored relationship."""

    name: str
    canonical: str  # dir, relative to root
    vendored: str  # dir, relative to root
    files: tuple[str, ...]  # must exist on BOTH sides, byte-identical
    # True  -> the canonical dir may hold NOTHING but `files` (every canonical file must be
    #          vendored; adding one there without vendoring it is the drift we want to catch).
    # False -> the canonical dir is a larger library and the vendored skill takes only a subset.
    canonical_exhaustive: bool
    # Files allowed to live in the vendored dir with no canonical counterpart. Named explicitly so
    # a local-only file is a decision, not an accident.
    vendored_local: tuple[str, ...] = ()


DOMAIN_PROBES = (
    "sr_ma.md",
    "survival_prognostic.md",
    "clinical_prediction_model.md",
    "radiomics.md",
    "image_synthesis.md",
    "narrative_review.md",
    "observational_confounding.md",
    "ai_overclaiming.md",
    "rct_trial.md",
    "diagnostic_accuracy.md",
    "case_report.md",
    "equity_fairness.md",
    "mendelian_randomization.md",
    "polygenic_risk_score.md",
    "network_meta_analysis.md",
    "model_development.md",
    "mllm_evaluation.md",
    "health_economic_evaluation.md",
    "record_routinely_collected_data.md",
    "survey_research.md",
    "scoping_review.md",
    "qualitative_research.md",
    "self_improving_system.md",
)

# The risk-of-bias tools /meta-analysis actually applies during its own RoB step. /check-reporting
# is the 46-checklist library and is NOT exhaustive here: adding a 47th checklist there must not
# force it into /meta-analysis.
ROB_CHECKLISTS = (
    "RoB2.md",
    "NOS.md",
    "ROBINS_I.md",
    "QUADAS2.md",
    "PROBAST.md",
    "PRISMA_DTA.md",
)

VENDOR_SETS: tuple[VendorSet, ...] = (
    VendorSet(
        name="domain-probes",
        canonical="skills/peer-review/references/domain-probes",
        vendored="skills/self-review/references/domain-probes",
        files=DOMAIN_PROBES,
        canonical_exhaustive=True,
    ),
    VendorSet(
        name="rob-checklists",
        canonical="skills/check-reporting/references/checklists",
        vendored="skills/meta-analysis/references/checklists",
        files=ROB_CHECKLISTS,
        canonical_exhaustive=False,
        # JBI critical-appraisal for case series: used by /meta-analysis, has no /check-reporting
        # counterpart. Declared so the gate stays silent on it instead of crying wolf.
        vendored_local=("JBI_Case_Series.md",),
    ),
)

# Content that is byte-identical across skills but is NOT a vendoring relationship (a coincidental
# collision — e.g. two trivially identical stubs). Empty today. A gate with no escape hatch gets
# switched off, and takes the honest gates with it.
UNDECLARED_EXEMPT: frozenset[str] = frozenset()

# Fixtures prove a thing works; they are not shipped payload and may legitimately duplicate.
SCAN_SKIP = ("/tests/", "_challenge/", "/challenge/")


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


def do_sync(root: Path) -> int:
    total = 0
    for vs in VENDOR_SETS:
        canonical, vendored = root / vs.canonical, root / vs.vendored
        vendored.mkdir(parents=True, exist_ok=True)
        for name in vs.files:
            src = canonical / name
            if not src.is_file():
                print(f"ERROR: canonical file missing: {src}", file=sys.stderr)
                return 2
            shutil.copyfile(src, vendored / name)
            print(f"synced  [{vs.name}] {name}")
            total += 1
        allowed = set(vs.files) | set(vs.vendored_local)
        for stray in sorted(listing(vendored) - allowed):
            (vendored / stray).unlink()
            print(f"removed stray vendored file  [{vs.name}] {stray}")
    print(f"OK: {total} file(s) vendored canonical -> vendored across {len(VENDOR_SETS)} set(s)")
    return 0


def check_set(root: Path, vs: VendorSet) -> tuple[list[str], int]:
    """Returns (problems, fatal) — fatal=2 when a declared directory is absent."""
    canonical, vendored = root / vs.canonical, root / vs.vendored
    if not canonical.is_dir():
        print(f"ERROR: canonical dir missing: {canonical}", file=sys.stderr)
        return [], 2
    if not vendored.is_dir():
        print(f"ERROR: vendored dir missing: {vendored}", file=sys.stderr)
        return [], 2

    problems: list[str] = []
    canon_set, vend_set = listing(canonical), listing(vendored)

    for name in vs.files:
        if name not in canon_set:
            problems.append(f"[{vs.name}] canonical missing file: {name}")
        if name not in vend_set:
            problems.append(f"[{vs.name}] vendored missing file: {name}")

    if vs.canonical_exhaustive:
        for extra in sorted(canon_set - set(vs.files)):
            problems.append(
                f"[{vs.name}] canonical file is not vendored: {extra} "
                "(add it to this set's file list, or the consuming skill silently lacks it)"
            )
    for extra in sorted(vend_set - set(vs.files) - set(vs.vendored_local)):
        problems.append(f"[{vs.name}] unexpected file in vendored dir: {extra}")

    for name in vs.files:
        c, v = canonical / name, vendored / name
        if c.is_file() and v.is_file():
            ch, vh = sha256_file(c), sha256_file(v)
            if ch != vh:
                problems.append(
                    f"[{vs.name}] drift: {name} canonical={ch[:12]}... vendored={vh[:12]}..."
                )
    return problems, 0


def declared_paths(root: Path) -> set[Path]:
    out: set[Path] = set()
    for vs in VENDOR_SETS:
        for name in vs.files:
            out.add((root / vs.canonical / name).resolve())
            out.add((root / vs.vendored / name).resolve())
    return out


def undeclared_duplicates(root: Path) -> list[str]:
    """Byte-identical content living in 2+ skills without a declared vendoring set.

    This is the anti-forgetting mechanism: a third vendored set cannot slip in ungated, because it
    does not need to be remembered — it gets found.
    """
    skills = root / "skills"
    if not skills.is_dir():
        return []
    known = declared_paths(root)
    by_hash: dict[str, list[Path]] = collections.defaultdict(list)
    for p in skills.rglob("*"):
        if not p.is_file() or p.is_symlink():
            continue
        if any(t in "/" + str(p.relative_to(root)) for t in SCAN_SKIP):
            continue
        if p.resolve() in known or p.name in UNDECLARED_EXEMPT:
            continue
        try:
            if p.stat().st_size == 0:
                continue
            by_hash[sha256_file(p)].append(p)
        except OSError:
            continue

    problems: list[str] = []
    for _h, paths in sorted(by_hash.items(), key=lambda kv: str(kv[1][0])):
        owners = {p.relative_to(skills).parts[0] for p in paths}
        if len(owners) < 2:
            continue
        rels = ", ".join(sorted(str(p.relative_to(root)) for p in paths))
        problems.append(
            f"[undeclared] identical content vendored across {sorted(owners)} but not declared: {rels}"
        )
    return problems


def do_check(root: Path, strict: bool) -> int:
    print("=" * 41)
    print(" Vendoring Sync (canonical -> vendored)")
    print("=" * 41)

    problems: list[str] = []
    for vs in VENDOR_SETS:
        print(f"{vs.name:16s} {vs.canonical}\n{'':16s}  -> {vs.vendored}  ({len(vs.files)} file(s))")
        found, fatal = check_set(root, vs)
        if fatal:
            return fatal
        problems += found

    problems += undeclared_duplicates(root)

    if not problems:
        n = sum(len(v.files) for v in VENDOR_SETS)
        print(f"\nOK: {n} vendored file(s) byte-identical across {len(VENDOR_SETS)} declared set(s);")
        print("    no undeclared cross-skill duplicate content.")
        return 0

    print(f"\nVENDORING_DRIFT ({len(problems)}):")
    for p in problems:
        print(f"  - {p}")
    print("\nFix (declared drift): python3 scripts/check_domain_probe_sync.py --sync")
    print("Fix (undeclared):     add the pair to VENDOR_SETS in this script, or de-duplicate it.")
    return 1 if strict else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Vendoring drift gate (all vendored sets).")
    ap.add_argument("--root", default=None, help="operate on an alternate tree (tests)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--strict", action="store_true", help="Exit non-zero on any drift (CI gate).")
    mode.add_argument("--sync", action="store_true", help="Copy canonical -> vendored (fix drift).")
    args = ap.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root()

    if args.sync:
        return do_sync(root)
    return do_check(root, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())

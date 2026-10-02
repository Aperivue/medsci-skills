#!/usr/bin/env python3
"""The anchor-and-rotate sizing code in the reference note returns only possible allocations.

`references/anchor_rotate_reader_allocation.md` ships a ```python block (`plan`,
`max_pool_for_readers`) that an agent copies. This test executes that block -- the text itself,
not a re-implementation -- and checks it.

Regression (F1): the block used to return impossible values silently: more average raters per
item than there are readers (plan(30,25,20,2) -> readers 2, raters_per_unique 4.0), negative or
infinite raters (pool <= anchor), and a pool for fewer readers than raters per item
(max_pool_for_readers(30,20,2,R=1) -> 25). Those inputs must now raise or be capped.

Controls: the worked example in the note (cap 30, anchor 20, m 2, 4-8 readers -> pool 40-60) and
the large-pool use case must be unchanged.

Usage:
    test_reader_allocation.py [--md PATH]   # --md runs the checks against another copy of the note
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
NOTE = REPO / "skills/design-ai-benchmarking/references/anchor_rotate_reader_allocation.md"


def load(md: Path) -> dict:
    text = md.read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, flags=re.S)
    if len(blocks) != 1:
        print(f"ERROR: expected exactly one python block in {md}, found {len(blocks)}")
        sys.exit(2)
    ns: dict = {}
    exec(compile(blocks[0], str(md), "exec"), ns)
    for name in ("plan", "max_pool_for_readers"):
        if name not in ns:
            print(f"ERROR: {md} python block defines no `{name}`")
            sys.exit(2)
    return ns


def raises(fn, *args) -> bool:
    try:
        fn(*args)
    except ValueError:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", type=Path, default=NOTE)
    args = ap.parse_args()
    ns = load(args.md)
    plan, max_pool = ns["plan"], ns["max_pool_for_readers"]
    failures: list[str] = []

    def check(label: str, ok: bool) -> None:
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            failures.append(label)

    # --- positive cases: origin/main returned these silently --------------------------------
    for pool in (21, 22, 25):  # unique items fewer than one reader's rotating slots
        p = plan(30, pool, 20, 2)
        check(f"plan(30,{pool},20,2): raters_per_unique {p['raters_per_unique']} <= readers "
              f"{p['readers']}", p["raters_per_unique"] <= p["readers"])
        check(f"plan(30,{pool},20,2): reads_per_reader {p['reads_per_reader']} == "
              f"anchor + unique {pool}", p["reads_per_reader"] == pool)
    check("plan(30,10,20,2) (pool < anchor) raises ValueError", raises(plan, 30, 10, 20, 2))
    check("plan(30,20,20,2) (pool == anchor) raises ValueError", raises(plan, 30, 20, 20, 2))
    check("plan(30,60,20,0) (m < 1) raises ValueError", raises(plan, 30, 60, 20, 0))
    check("max_pool_for_readers(30,20,2,R=1) (R < m) raises ValueError",
          raises(max_pool, 30, 20, 2, 1))
    check("max_pool_for_readers(30,20,3,R=2) (R < m) raises ValueError",
          raises(max_pool, 30, 20, 3, 2))

    # --- negative controls: must stay exactly as before -------------------------------------
    for R, expected in zip(range(4, 9), (40, 45, 50, 55, 60)):  # the note's worked example
        got = max_pool(30, 20, 2, R)
        check(f"max_pool_for_readers(30,20,2,R={R}) == {expected} (got {got})", got == expected)
        p = plan(30, got, 20, 2)
        check(f"round trip plan(30,{got},20,2): readers {p['readers']} == {R}, "
              f"raters_per_unique {p['raters_per_unique']} == 2.0, reads {p['reads_per_reader']} "
              f"== 30", p["readers"] == R and p["raters_per_unique"] == 2.0
              and p["reads_per_reader"] == 30)
    p = plan(30, 47, 20, 2)
    check(f"plan(30,47,20,2): readers 6, reads 30 (got {p['readers']}, {p['reads_per_reader']})",
          p["readers"] == 6 and p["reads_per_reader"] == 30)
    check("plan(30,60,30,2) (anchor >= cap) still returns None", plan(30, 60, 30, 2) is None)
    check("max_pool_for_readers(30,30,2,4) (anchor >= cap) still returns None",
          max_pool(30, 30, 2, 4) is None)
    check("max_pool_for_readers(30,20,2,R=2) (R == m) still allowed: 30",
          max_pool(30, 20, 2, 2) == 30)

    if failures:
        print(f"\n{len(failures)} FAILED")
        return 1
    print("\nall reader-allocation checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

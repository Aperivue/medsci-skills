#!/usr/bin/env python3
"""STROBE participant-flow cascade closure check for a build_strobe_template.py config.

A STROBE flow diagram's exclusion cascade must balance: the count in a spine box, minus the
exclusions declared after it, must equal the count in the next spine box. A real cohort
figure once read "500 excluded -> N = 9,470" while the enrolled box said 10,000, so
10,000 - 500 = 9,500, not 9,470 — a second exclusion, present in the legend, had been
dropped from the figure. It survived a full round of peer review and was found only by
rendering the submission PDF to an image and reading it by eye, because figure-image numbers
are text-grep blind.

`check_cohort_arithmetic.py` already asserts this closure in manuscript prose, GFM tables and
committed CSVs. The number that a reviewer actually sees, though, lives as text in the flow
diagram, generated here from a structured YAML — so the diagram can drift from the prose.
This makes the figure carry its own assertion.

Low false-positive by construction: a spine link is checked ONLY when at least one exclusion
is declared after that box (the author is asserting "A minus these gives B"), and only when
every count involved is extractable. A branching Analysis leaf (two boxes sharing a parent,
no exclusion between them) is never treated as a cascade step. A box with no "n = …" count is
skipped, not guessed.

Reused by build_strobe_template.py (a loud warning during the build; fatal under
--strict-cascade) and runnable standalone (`_strobe_cascade.py --config figure1.yaml
--strict`) so the check travels without python-pptx.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# The box TOTAL is the first "n = X" / "N = X" in the box text — the parenthetical after the
# label ("Enrolled (n = 10,000)", "Excluded (n = 500):"). Sub-bullet counts come after it.
_COUNT_RE = re.compile(r"[nN]\s*=\s*([\d,]+)")


def extract_count(text: str | None) -> int | None:
    """First `n = X` in the box text as an int, or None when the box carries no count."""
    if not text:
        return None
    m = _COUNT_RE.search(str(text))
    return int(m.group(1).replace(",", "")) if m else None


def check_cascade(cfg: dict) -> list[dict]:
    """Return an imbalance finding for every declared exclusion link A -> B where
    ``A.count - sum(exclusions after A) != B.count``."""
    spine = cfg.get("spine") or []
    exclusions = cfg.get("exclusions") or []
    if len(spine) < 2:
        return []

    counts = {b.get("id"): extract_count(b.get("text")) for b in spine if isinstance(b, dict)}
    excl_after: dict[str, list[int | None]] = {}
    for e in exclusions:
        if isinstance(e, dict) and e.get("after"):
            excl_after.setdefault(e["after"], []).append(extract_count(e.get("text")))

    findings: list[dict] = []
    for i in range(len(spine) - 1):
        a, b = spine[i], spine[i + 1]
        if not (isinstance(a, dict) and isinstance(b, dict)):
            continue
        aid = a.get("id")
        excls = excl_after.get(aid)
        if not excls:                       # only a DECLARED exclusion link is a cascade step
            continue
        a_n, b_n = counts.get(aid), counts.get(b.get("id"))
        if a_n is None or b_n is None or any(x is None for x in excls):
            continue                        # never guess a missing count
        got = a_n - sum(excls)
        if got != b_n:
            findings.append({
                "after": aid,
                "next": b.get("id"),
                "detail": (f"STROBE cascade does not close after '{aid}': {a_n:,} - "
                           f"{'+'.join(f'{x:,}' for x in excls)} = {got:,}, but the next box "
                           f"'{b.get('id')}' says {b_n:,} (off by {b_n - got:+,})"),
            })
    return findings


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # noqa: PLC0415
        except ModuleNotFoundError:
            sys.exit("PyYAML not installed; install it or pass a JSON config.")
        return yaml.safe_load(text) or {}
    import json  # noqa: PLC0415
    return json.loads(text)


def main() -> int:
    ap = argparse.ArgumentParser(description="STROBE flow cascade-closure check.")
    ap.add_argument("--config", required=True, help="build_strobe_template.py YAML/JSON config")
    ap.add_argument("--strict", action="store_true", help="exit 1 if the cascade does not close")
    a = ap.parse_args()
    findings = check_cascade(_load(Path(a.config)))
    if findings:
        for f in findings:
            print(f"CASCADE_IMBALANCE: {f['detail']}")
    else:
        print("OK: STROBE exclusion cascade closes at every declared link.")
    return 1 if (findings and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())

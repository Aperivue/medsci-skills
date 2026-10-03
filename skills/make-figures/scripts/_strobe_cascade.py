#!/usr/bin/env python3
"""Participant-flow cascade closure check for a build_strobe_template.py (spine/exclusions)
config or a generate_flow_diagram.R (nodes/edges, dashed exclusion edges) config.

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
--strict`) so the check travels without python-pptx. generate_flow_diagram.R calls it before
rendering. A config in neither schema is an input error (exit 2), never a silent OK; under
--strict, a config with no evaluable exclusion link also exits 2 (the check could not run).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Spine schema: the box TOTAL is the first "n = X" / "N = X" in the box text — the parenthetical
# after the label ("Enrolled (n = 10,000)", "Excluded (n = 500):"). Sub-bullet counts come after
# it. The nodes/edges schema reads totals with box_total() instead.
_COUNT_RE = re.compile(r"[nN]\s*=\s*([\d,]+)")


def extract_count(text: str | None) -> int | None:
    """First `n = X` in the box text as an int, or None when the box carries no count."""
    if not text:
        return None
    m = _COUNT_RE.search(str(text))
    return int(m.group(1).replace(",", "")) if m else None


def box_total(text: str | None) -> int | None:
    """Total of a nodes/edges box (flow or exclusion), or None when the label states no
    unambiguous total.

    A box often lists its parts with no total of its own: an exclusion box listing reasons
    ("Excluded:\\n- Age < 18 (n = 60)\\n- Missing imaging (n = 40)"), or a PRISMA 2020
    identification box listing sources ("Records identified from:\\nDatabases (n = 1,800)
    \\nRegisters (n = 200)"). Reading the first sub-count as the total would flag a cascade that
    closes. A total is read only when the label has exactly one count, or when a count standing
    alone on the first or the last line equals the sum of every other count in the label (a stated
    total with its breakdown). Anything else is an unknown total: the link is not assessed, never
    guessed.
    """
    if not text:
        return None
    text = str(text).replace("\\n", "\n")
    counts = [int(c.replace(",", "")) for c in _COUNT_RE.findall(text)]
    if not counts:
        return None
    if len(counts) == 1:
        return counts[0]
    lines = [ln for ln in text.split("\n") if ln.strip()]
    found = set()
    for line, idx in ((lines[0], 0), (lines[-1], len(counts) - 1)):
        if len(_COUNT_RE.findall(line)) != 1:
            continue
        if counts[idx] == sum(counts) - counts[idx]:
            found.add(counts[idx])
    return found.pop() if len(found) == 1 else None


# Kept for callers of the previous name: an exclusion box follows the same total rule.
exclusion_total = box_total


def _check_spine(cfg: dict) -> tuple[list[dict], int]:
    """Spine/exclusions schema (build_strobe_template.py). Returns (findings, links checked)."""
    spine = cfg.get("spine") or []
    exclusions = cfg.get("exclusions") or []
    if len(spine) < 2:
        return [], 0

    counts = {b.get("id"): extract_count(b.get("text")) for b in spine if isinstance(b, dict)}
    excl_after: dict[str, list[int | None]] = {}
    for e in exclusions:
        if isinstance(e, dict) and e.get("after"):
            excl_after.setdefault(e["after"], []).append(extract_count(e.get("text")))

    findings: list[dict] = []
    checked = 0
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
        checked += 1
        got = a_n - sum(excls)
        if got != b_n:
            findings.append({
                "after": aid,
                "next": b.get("id"),
                "detail": (f"STROBE cascade does not close after '{aid}': {a_n:,} - "
                           f"{'+'.join(f'{x:,}' for x in excls)} = {got:,}, but the next box "
                           f"'{b.get('id')}' says {b_n:,} (off by {b_n - got:+,})"),
            })
    return findings, checked


def check_cascade(cfg: dict) -> list[dict]:
    """Return an imbalance finding for every declared exclusion link A -> B where
    ``A.count - sum(exclusions after A) != B.count`` (spine/exclusions schema)."""
    return _check_spine(cfg)[0]


def _check_graph(cfg: dict) -> tuple[list[dict], int, list[str]]:
    """nodes/edges schema (generate_flow_diagram.R). Returns (findings, links checked,
    links not assessed).

    An exclusion is a node reached from box A by a ``style: dashed`` edge. Two attachment
    conventions are in use: the exclusion sits beside the box it is subtracted FROM (A - excl =
    A's single solid child) or beside the box it produced (A's single solid parent - excl = A).
    A convention is evaluable only on a linear step (one solid child that has one solid parent,
    or one solid parent that has one solid child) with every count extractable, so a branching
    step is never read as a cascade. The link passes when any evaluable convention closes and is
    flagged only when at least one is evaluable and none closes. Every box count, on either
    side of the exclusion and in the exclusion itself, is read with ``box_total``; a link whose
    boxes have no unambiguous total (several ``n = X`` and no stated total) is NOT ASSESSED and
    reported as such, never evaluated from a sub-count.
    """
    nodes = [n for n in (cfg.get("nodes") or []) if isinstance(n, dict) and n.get("id") is not None]
    edges = [e for e in (cfg.get("edges") or []) if isinstance(e, dict)]
    counts = {n["id"]: box_total(n.get("label")) for n in nodes}
    labels = {n["id"]: n.get("label") for n in nodes}
    has_count = {k: extract_count(v) is not None for k, v in labels.items()}
    solid_children: dict = {}
    solid_parents: dict = {}
    excl_of: dict = {}
    for e in edges:
        frm, to = e.get("from"), e.get("to")
        if frm is None or to is None:
            continue
        if str(e.get("style") or "solid").lower() == "dashed":
            excl_of.setdefault(frm, []).append(to)
        else:
            solid_children.setdefault(frm, []).append(to)
            solid_parents.setdefault(to, []).append(frm)

    def ambiguous(ids: list) -> list:
        """Boxes that carry counts but no unambiguous total."""
        return [x for x in ids if counts.get(x) is None and has_count.get(x)]

    findings: list[dict] = []
    checked = 0
    not_assessed: list[str] = []
    for n in nodes:
        aid = n["id"]
        if aid not in excl_of:
            continue
        excls = [counts.get(x) for x in excl_of[aid]]
        a_n = counts.get(aid)
        kids = solid_children.get(aid, [])
        pars = solid_parents.get(aid, [])
        linear_kid = len(kids) == 1 and len(solid_parents.get(kids[0], [])) == 1
        linear_par = len(pars) == 1 and len(solid_children.get(pars[0], [])) == 1
        if a_n is None or any(x is None for x in excls):
            amb = ambiguous([aid] + list(excl_of[aid]))
            if amb and (linear_kid or linear_par):
                not_assessed.append(f"exclusion(s) {excl_of[aid]} of '{aid}': no unambiguous "
                                    f"total in {amb} (several 'n = X', no stated total)")
            continue                        # never guess a missing count
        total = sum(excls)
        tried = []                          # (description, expected, actual)
        amb = []
        if linear_kid:
            b = kids[0]
            if counts.get(b) is not None:
                tried.append((f"'{aid}' {a_n:,} - {total:,} = {a_n - total:,} but the next box "
                              f"'{b}' says {counts[b]:,}", a_n - total, counts[b]))
            else:
                amb += ambiguous([b])
        if linear_par:
            q = pars[0]
            if counts.get(q) is not None:
                tried.append((f"the previous box '{q}' {counts[q]:,} - {total:,} = "
                              f"{counts[q] - total:,} but '{aid}' says {a_n:,}",
                              counts[q] - total, a_n))
            else:
                amb += ambiguous([q])
        closes = any(exp == act for _, exp, act in tried)
        if amb and not closes:
            # One side of the step has no unambiguous total, so the convention that would have
            # used it is unknown; a non-closing reading of the other side proves nothing.
            not_assessed.append(f"exclusion(s) {excl_of[aid]} of '{aid}': no unambiguous "
                                f"total in {amb} (several 'n = X', no stated total)")
            continue
        if not tried:
            continue
        checked += 1
        if closes:
            continue
        findings.append({
            "after": aid,
            "next": None,
            "detail": (f"flow cascade does not close at the exclusion(s) {excl_of[aid]} of '{aid}': "
                       + "; ".join(d for d, _, _ in tried)),
        })
    return findings, checked, not_assessed


def check_config(cfg: object) -> tuple[str | None, list[dict], int, list[str]]:
    """Dispatch on schema: (schema name, or None when unrecognised; findings; links checked;
    links not assessed)."""
    if not isinstance(cfg, dict):
        return None, [], 0, []
    if isinstance(cfg.get("spine"), list):
        f, c = _check_spine(cfg)
        return "spine", f, c, []
    if isinstance(cfg.get("nodes"), list) and isinstance(cfg.get("edges"), list):
        return ("nodes/edges",) + _check_graph(cfg)
    return None, [], 0, []


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
    ap = argparse.ArgumentParser(description="Flow-diagram exclusion cascade-closure check.")
    ap.add_argument("--config", required=True,
                    help="build_strobe_template.py (spine/exclusions) or generate_flow_diagram.R "
                         "(nodes/edges) YAML/JSON config")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if the cascade does not close; exit 2 if no link could be checked")
    a = ap.parse_args()
    path = Path(a.config)
    if not path.is_file():
        sys.stderr.write(f"ERROR: config not found: {a.config}\n")
        return 2
    schema, findings, checked, not_assessed = check_config(_load(path))
    if schema is None:
        sys.stderr.write(f"ERROR: unrecognised config schema in {a.config}: expected a 'spine' "
                         "list (build_strobe_template.py) or 'nodes' + 'edges' lists "
                         "(generate_flow_diagram.R); nothing was checked.\n")
        return 2
    for na in not_assessed:
        print(f"NOT_ASSESSED: {na}")
    if findings:
        for f in findings:
            print(f"CASCADE_IMBALANCE: {f['detail']}")
        return 1 if a.strict else 0
    if checked == 0:
        print(f"NOT CHECKED: no evaluable exclusion link in {a.config} ({schema} schema); "
              "the cascade closure could not be verified (a link is skipped when a box has no "
              "'n = X', a box lists several 'n = X' with no stated total, or the step branches).")
        return 2 if a.strict else 0
    extra = f", {len(not_assessed)} not assessed" if not_assessed else ""
    print(f"OK: exclusion cascade closes at every evaluated link ({checked} checked{extra}, "
          f"{schema} schema).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

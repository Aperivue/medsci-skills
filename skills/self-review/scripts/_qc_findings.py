"""Shared finding-extraction across the heterogeneous detector JSON schemas.

The detectors do **not** share one output envelope. Some list their findings under
`claims`, some under `findings`; per item the verdict is `verdict` | `kind` | `type`, the
severity casing varies (`Major` vs `MAJOR`), and the location is `where` | `location` |
`line` | `table_line`. The only contract `check_detector_envelopes` enforces is the
top-level `detector` key. The refinement loop controllers (`refinement_stop`,
`refinement_regression`) aggregate every gate's `qc/*.json`, so they must read all of these
shapes — and, critically, make an *unreadable* one LOUD, not silent: a controller that
quietly skips a detector whose schema it does not recognise can report a clean STOP_ZERO_EDIT
while a `findings`-schema gate held a Major.

`parse_gate(obj)` returns None when the object is not a gate artifact (this tool's own
`{"tool": ...}` output, a ledger line), else:
    {name, kind: "ceiling"|"floor", major, minor, keys: ["verdict@where", ...], parsed: bool}
`parsed` is False for a `detector`-keyed file whose finding list is under an unknown key —
the caller surfaces it (gates_unparsed) rather than counting it as clean.

Stdlib-only. Imported by refinement_stop.py / refinement_regression.py from the same dir.
"""

from __future__ import annotations

_LIST_KEYS = ("claims", "findings")
_VERDICT_KEYS = ("verdict", "kind", "type")
_WHERE_KEYS = ("where", "location", "line", "table_line")
_MAJOR = {"MAJOR", "FATAL"}


def parse_gate(obj) -> dict | None:
    if not isinstance(obj, dict):
        return None
    summary = obj.get("summary") if isinstance(obj.get("summary"), dict) else {}
    items = None
    for k in _LIST_KEYS:
        if isinstance(obj.get(k), list):
            items = obj[k]
            break
    has_detector = "detector" in obj
    if items is None and not has_detector:
        return None  # not a gate artifact (e.g. a controller's own {"tool": ...} output)

    name = obj.get("detector") or "?"
    if items is None:
        # detector-keyed but no recognisable finding list: a novel schema. Flag it loudly.
        return {"name": name, "kind": "floor", "major": 0, "minor": 0, "keys": [], "parsed": False}

    dict_items = [it for it in items if isinstance(it, dict)]
    kind = "ceiling" if "by_action" in summary else "floor"

    # Prefer an authoritative summary.n_major (claims-schema gates); otherwise count Majors from
    # each item's severity (findings-schema gates carry no such summary).
    n_major_sum = summary.get("n_major")
    if isinstance(n_major_sum, int):
        major = n_major_sum
        minor = max(0, len(dict_items) - major)
    else:
        major = sum(1 for it in dict_items if str(it.get("severity", "")).strip().upper() in _MAJOR)
        minor = len(dict_items) - major

    keys = []
    for it in dict_items:
        verdict = next((str(it[v]) for v in _VERDICT_KEYS if it.get(v)), "?")
        where = next((str(it[w]) for w in _WHERE_KEYS if it.get(w) is not None), "?")
        keys.append(f"{verdict}@{where}")

    return {"name": name, "kind": kind, "major": major, "minor": minor, "keys": keys, "parsed": True}

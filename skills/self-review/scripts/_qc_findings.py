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
# The severity vocabulary is not one word. Detectors were written independently and each picked its
# own, and `_MAJOR` knew two of them — so a gate that says a manuscript CANNOT be submitted was
# counted as an optional Minor. `check_placeholders` marks a leftover `TODO` as `blocker` and exits 1
# on it unconditionally; the stop controller read that as "no required edits, do not loop".
#
# Membership below is derived from each detector's OWN exit contract, not from what the word sounds
# like — the word had to make its detector return 1:
#   blocker  check_placeholders            `if s["blocker"]: return 1`        (no --strict needed)
#   hard     check_disclosure_availability `verdict == "BLOCKER"  -> 1`
#            check_summary_box             `NONCONFORMANT and --strict -> 1`
#            build_title_page_affiliations `rc = 1`
#   stale    check_checklist_version       docstring: "0 = in sync, 1 = stale / unverifiable"
#   unverif. check_checklist_version       same detector, same `return 0 if safe else 1`; its own
#                                          output line reads "FAIL: checklist is stale or
#                                          unverifiable". Found by the repo-wide assertion in
#                                          test_qc_severity_vocabulary.sh, not by enumeration —
#                                          which is the point of having that assertion.
#   FAIL     validate_pptx_mac_compat      `--strict and not ok   -> 1`
#
# `Flag` is deliberately NOT here, and that is the control that shows this is a derivation rather
# than a widening: check_generated_code computes `n_flag = len(claims) - n_major` and exits only on
# `n_major`, so its own contract says Flag is advisory. `soft` and `warn` likewise.
_MAJOR = {"MAJOR", "FATAL", "BLOCKER", "HARD", "STALE", "UNVERIFIABLE", "FAIL"}

# Known-advisory. Kept explicit so that a severity belonging to NEITHER set is a novel word rather
# than an assumption — see `_classify` below.
_MINOR = {"MINOR", "FLAG", "SOFT", "WARN", "WARNING", "INFO", "NOTE", "OK", "PASS", ""}


def _classify(severity: str) -> str:
    """Return "major" | "minor" | "unknown" for a raw severity string.

    Unknown counts as MAJOR. This module's docstring already states the rule for an unrecognised
    *schema* — make it loud, never silent, because a controller that quietly skips what it cannot
    read can report a clean STOP_ZERO_EDIT over a held Major. An unrecognised *severity* is the same
    hazard one level down, and it defaulted the other way: straight into `minor`, straight into
    "nothing to do". For a stop controller, guessing "major" costs one more loop; guessing "minor"
    ends the loop over an unfixed blocker.
    """
    s = str(severity).strip().upper()
    if s in _MAJOR:
        return "major"
    if s in _MINOR:
        return "minor"
    return "unknown"


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
    unknown_severities: list[str] = []
    if isinstance(n_major_sum, int):
        major = n_major_sum
        minor = max(0, len(dict_items) - major)
    else:
        major = minor = 0
        for it in dict_items:
            verdict = _classify(it.get("severity", ""))
            if verdict == "minor":
                minor += 1
            else:
                major += 1  # "major", and "unknown" fails toward the loop continuing
                if verdict == "unknown":
                    unknown_severities.append(str(it.get("severity", "")).strip())

    keys = []
    for it in dict_items:
        verdict = next((str(it[v]) for v in _VERDICT_KEYS if it.get(v)), "?")
        where = next((str(it[w]) for w in _WHERE_KEYS if it.get(w) is not None), "?")
        keys.append(f"{verdict}@{where}")

    return {"name": name, "kind": kind, "major": major, "minor": minor, "keys": keys,
            "parsed": True, "unknown_severities": sorted(set(unknown_severities))}

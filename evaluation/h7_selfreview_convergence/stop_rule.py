"""Predefined, bounded stopping rule for the E9 self-review convergence loop.

Stop when ANY holds:
  - round_idx has reached max_rounds (default 5; the plan allows 3-5), OR
  - the internal verdict is PASS / ACCEPT-WITH-NOTES, OR
  - no actionable Major remains (no finding with severity Major AND
    fixable_by_ai true).

Never loops to success without reporting; non-convergence is a first-class,
recorded outcome. This measures internal rubric (self-review QC) convergence,
never external manuscript quality or reviewer acceptance.
"""

from __future__ import annotations

MAX_ROUNDS_DEFAULT = 5


def actionable_majors(findings: list[dict]) -> int:
    n = 0
    for f in findings:
        sev = str(f.get("severity", "")).lower()
        fixable = bool(f.get("fixable_by_ai", False))
        if ("major" in sev or "fatal" in sev) and fixable:
            n += 1
    return n


def should_stop(verdict: str, findings: list[dict], round_idx: int,
                max_rounds: int = MAX_ROUNDS_DEFAULT) -> tuple[bool, str]:
    v = (verdict or "").upper().replace(" ", "-")
    if v in ("PASS", "ACCEPT-WITH-NOTES", "ACCEPT"):
        return True, f"internal verdict {v}"
    if actionable_majors(findings) == 0:
        return True, "no actionable fixable_by_ai Major remains"
    if round_idx >= max_rounds:
        return True, f"reached max_rounds={max_rounds} (non-convergence)"
    return False, ""

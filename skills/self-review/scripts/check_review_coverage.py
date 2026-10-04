#!/usr/bin/env python3
"""Coverage-ledger gate for the self-review JSON (Phase 3c).

A self-review that returns `"verdict": "PASS"` says the manuscript is ready. That statement is only
as good as the categories the review actually worked. Before this gate, the JSON recorded what was
FOUND (issues[]) and nothing about what was LOOKED AT, so a review that never reached category C
(validation & statistics) produced the same PASS as one that worked C and found nothing: "not
checked" read as "no problem".

The Phase 3c schema therefore carries a `coverage` ledger:

    "coverage": {
      "categories": {                       # every letter A-L, no others
        "A": {"status": "assessed", "evidence": ["Methods, Study design para 1-2", "Table 1"]},
        "K": {"status": "not_applicable", "reason": "Not a systematic review"},
        "I": {"status": "not_assessed", "reason": "Acquisition protocol table not supplied"}
      },
      "probes": {                           # every domain-probe module the review loaded
        "observational_confounding": {"status": "assessed", "evidence": ["Table 1", "Methods 2.4"]}
      }
    }

`status` is one of assessed | not_applicable | not_assessed. `assessed` needs a non-empty
`evidence` list (section / line / table references); `not_applicable` needs a one-line `reason`;
`not_assessed` may carry a `reason`. Probe keys are module stems of
references/domain-probes/*.md (read from disk, so the list cannot drift).

RULE: the review cannot return PASS while any applicable entry (a category or a loaded probe module)
is not_assessed.

CLAIMS
  COVERAGE_GAP_PASS      (Major) verdict is PASS and at least one entry is not_assessed. Certain from
                         the input: the JSON states both facts itself.
  COVERAGE_GAP           (Minor) an entry is not_assessed under a REVISE verdict -- the gap does not
                         contradict the verdict, but it is reported so it is not read as clean.
  COVERAGE_NOT_RECORDED  (Minor) the JSON has no `coverage` object (written before the ledger
                         existed). Treated as legacy, not as a failure: the run still reads the
                         verdict and reports OK, so an older self_review.json keeps validating.

The ledger is the reviewer's own declaration ("basis": "declared"): this gate checks that the
declaration is complete and consistent with the verdict, not that the work behind an `assessed`
entry was done, and not whether a `not_applicable` call is right for the manuscript type.

INPUT
  --review   qc/self_review.json (the Phase 3c object; UTF-8, a BOM is accepted). NaN / Infinity,
             a missing or unknown `verdict`, or a malformed `coverage` object exits 2 and names the
             field.
  --out      optional JSON artifact path (qc/review_coverage.json).
  --strict   exit 1 when a Major claim fired.
  --quiet    suppress the stdout table.

OUTPUT
  {detector, basis, review, verdict_read, claims[{verdict, severity, detail, where}],
   summary{n_entries, n_assessed, n_not_applicable, n_not_assessed, n_major, n_minor, verdict}}

Stdlib-only. Exit codes: 0 run completed (report-only, or --strict with no Major), 1 --strict and a
Major claim, 2 input or usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DETECTOR = "check_review_coverage"
CATEGORIES = tuple("ABCDEFGHIJKL")
STATUSES = ("assessed", "not_applicable", "not_assessed")
VERDICTS = ("PASS", "REVISE")
ENTRY_KEYS = {"status", "evidence", "reason"}
COVERAGE_KEYS = {"categories", "probes"}
PROBE_DIR = Path(__file__).resolve().parent.parent / "references" / "domain-probes"


class InputError(ValueError):
    pass


def _reject_constant(name: str):
    raise InputError(f"{name} is not a valid JSON number")


def _probe_modules() -> set:
    return {p.stem for p in PROBE_DIR.glob("*.md")}


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _entry(value, where: str) -> str:
    """Validate one ledger entry and return its status."""
    if not isinstance(value, dict):
        raise InputError(f"{where}: expected an object with a 'status', got {type(value).__name__}")
    extra = set(value) - ENTRY_KEYS
    if extra:
        raise InputError(f"{where}: unknown key(s) {sorted(extra)} (allowed: {sorted(ENTRY_KEYS)})")
    status = value.get("status")
    if status not in STATUSES:
        raise InputError(f"{where}.status: {status!r} is not one of {list(STATUSES)}")
    ev = value.get("evidence")
    if ev is not None and not (isinstance(ev, list) and all(_nonempty_str(e) for e in ev)):
        raise InputError(f"{where}.evidence: expected a list of non-empty strings")
    reason = value.get("reason")
    if reason is not None and not _nonempty_str(reason):
        raise InputError(f"{where}.reason: expected a non-empty string")
    if status == "assessed" and not ev:
        raise InputError(f"{where}.evidence: required (a non-empty list of section / line / table "
                         f"references) when status is 'assessed'")
    if status == "not_applicable" and reason is None:
        raise InputError(f"{where}.reason: required (one line) when status is 'not_applicable'")
    return status


def load(path: str) -> dict:
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        raise InputError(f"cannot read {path}: {e}")
    try:
        obj = json.loads(text, parse_constant=_reject_constant)
    except InputError:
        raise
    except (ValueError, OverflowError, RecursionError) as e:
        raise InputError(f"{path}: not valid JSON ({e})")
    if not isinstance(obj, dict):
        raise InputError(f"{path}: expected a JSON object (the Phase 3c self-review block)")
    return obj


def analyze(obj: dict, review: str) -> dict:
    verdict = obj.get("verdict")
    if verdict not in VERDICTS:
        raise InputError(f"verdict: {verdict!r} is not one of {list(VERDICTS)}")

    claims = []

    def add(code, severity, detail, where):
        claims.append({"verdict": code, "severity": severity, "detail": detail, "where": where})

    counts = {s: 0 for s in STATUSES}
    gaps = []
    if "coverage" not in obj:
        add("COVERAGE_NOT_RECORDED", "Minor",
            "no `coverage` ledger in the self-review JSON (legacy format): which of categories A-L "
            "and which domain-probe modules were worked is not recorded, so the verdict cannot be "
            "checked against coverage", "coverage")
    else:
        cov = obj["coverage"]
        if not isinstance(cov, dict):
            raise InputError(f"coverage: expected an object, got {type(cov).__name__}")
        extra = set(cov) - COVERAGE_KEYS
        if extra:
            raise InputError(f"coverage: unknown key(s) {sorted(extra)} (allowed: {sorted(COVERAGE_KEYS)})")
        cats = cov.get("categories")
        if not isinstance(cats, dict):
            raise InputError("coverage.categories: required object keyed by category letter A-L")
        unknown = sorted(set(cats) - set(CATEGORIES))
        if unknown:
            raise InputError(f"coverage.categories: unknown key(s) {unknown} (letters A-L only)")
        missing = [c for c in CATEGORIES if c not in cats]
        if missing:
            raise InputError(f"coverage.categories: missing {missing}; every category A-L needs an "
                             f"entry (use not_applicable with a reason when it does not apply)")
        probes = cov.get("probes")
        if not isinstance(probes, dict):
            raise InputError("coverage.probes: required object keyed by domain-probe module "
                             "(use {} when no module was loaded)")
        known = _probe_modules()
        bad = sorted(k for k in probes if k not in known)
        if bad:
            raise InputError(f"coverage.probes: unknown module(s) {bad} (module stems of "
                             f"references/domain-probes/*.md, e.g. 'sr_ma')")
        entries = [(f"coverage.categories.{c}", cats[c]) for c in CATEGORIES]
        entries += [(f"coverage.probes.{k}", probes[k]) for k in sorted(probes)]
        for where, value in entries:
            status = _entry(value, where)
            counts[status] += 1
            if status == "not_assessed":
                gaps.append((where, value.get("reason")))

    for where, reason in gaps:
        why = f" ({reason.strip()})" if reason else ""
        if verdict == "PASS":
            add("COVERAGE_GAP_PASS", "Major",
                f"verdict is PASS but {where} is not_assessed{why}; a PASS needs every applicable "
                f"category and loaded probe module assessed -- assess it, mark it not_applicable "
                f"with a reason, or return REVISE", where)
        else:
            add("COVERAGE_GAP", "Minor",
                f"{where} is not_assessed{why}; the review did not work it, so its absence of "
                f"findings is not a clean result", where)

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    n_minor = len(claims) - n_major
    return {
        "detector": DETECTOR,
        "basis": "declared",
        "review": review,
        "verdict_read": verdict,
        "claims": claims,
        "summary": {
            "n_entries": sum(counts.values()),
            "n_assessed": counts["assessed"],
            "n_not_applicable": counts["not_applicable"],
            "n_not_assessed": counts["not_assessed"],
            "n_major": n_major,
            "n_minor": n_minor,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    s = result["summary"]
    lines = [f"Review verdict read: {result['verdict_read']}",
             f"Coverage entries: {s['n_entries']} (assessed {s['n_assessed']}, not_applicable "
             f"{s['n_not_applicable']}, not_assessed {s['n_not_assessed']})"]
    for c in result["claims"]:
        lines.append(f"  [{c['severity']}] {c['verdict']}: {c['detail']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check the self-review JSON coverage ledger against its verdict.")
    ap.add_argument("--review", required=True, help="qc/self_review.json (Phase 3c output)")
    ap.add_argument("--out", help="write the JSON artifact here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if a Major claim fired")
    ap.add_argument("--quiet", action="store_true", help="suppress the stdout table")
    args = ap.parse_args(argv)

    try:
        result = analyze(load(args.review), args.review)
    except InputError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    s = result["summary"]
    if not args.quiet:
        print(render(result))
        print()
        if s["n_major"]:
            print(f"MAJOR candidate: PASS returned with {s['n_major']} not_assessed coverage entr"
                  f"{'y' if s['n_major'] == 1 else 'ies'}.")
        elif s["n_minor"]:
            print(f"No Major issue (as declared): {s['n_minor']} Minor (see list).")
        else:
            print(f"OK (as declared): all {s['n_entries']} coverage entries are assessed or "
                  f"not_applicable with a reason.")
    if args.out:
        try:
            Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        except OSError as e:
            print(f"ERROR: cannot write {args.out}: {e}", file=sys.stderr)
            return 2
    return 1 if (args.strict and s["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

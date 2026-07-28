#!/usr/bin/env python3
"""Effect-stability gate — a wide interval is a direction, not a magnitude
(self-review Phase 2.5).

The errors here are pure arithmetic on the printed cells, and two independent
reviewers hit the same number when they occur:

  1. UNSTABLE_EFFECT_ESTIMATE  an OR / HR / RR / IRR reported in the Abstract or
                               Conclusions whose 95% CI upper/lower ratio exceeds
                               ~10 (default --ratio-threshold 10). "OR 50.9; 95%
                               CI 5.8-443.6" is a 76-fold interval: the data
                               support a direction, not the point estimate. Fires
                               only when the estimate is presented as a magnitude
                               with NO co-located caveat (exploratory /
                               hypothesis-generating / underpowered / imprecise /
                               unstable / wide CI / interpret with caution) — the
                               same suppression discipline as check_null_calibration.
  2. EPV_LOW                   events / covariates < 10 (events per variable). A
                               model estimated on too few events per covariate
                               produces exactly the unstable estimates above;
                               fires only when both an event count and a covariate
                               count are printed in proximity.

Both are computable from the manuscript's own numbers. Deterministic and
conservative: it reads only the headline regions for the ratio (so a wide CI on
a clearly-labelled exploratory subgroup deep in the Results does not fire), and
it requires the caveat to be absent from the estimate's own neighbourhood.

INPUT
  --manuscript          manuscript markdown/text (required).
  --ratio-threshold N   CI upper/lower ratio above which an estimate is unstable
                        (default 10; a 10-fold interval already spans an order of
                        magnitude).

OUTPUT  (--out path)
  {"detector": "check_effect_stability", "manuscript", "claims":
     [{verdict, severity, detail, where}], "summary": {...}}
  UNSTABLE_EFFECT_ESTIMATE and EPV_LOW are Major candidates.

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 a Major claim exists (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_RATIO_THRESHOLD = 10.0

# An effect estimate with a 95% CI: (a)OR / (a)HR / RR / IRR, point, low-high.
# Longer kinds (aOR/aHR) precede OR/HR so they match first. The gap between the
# point estimate and the CI is bounded and allowed to contain "95%" (which has
# digits), so `.` rather than `\D` is used there.
EFFECT_RE = re.compile(
    r"\b(?:adjusted\s+)?(?P<kind>aOR|aHR|OR|HR|RR|IRR)\s*[=:]?\s*"
    r"(?P<pt>[0-9]+(?:\.[0-9]+)?)"
    r".{0,22}?(?:95\s*%\s*)?(?:CI|confidence\s+interval)[^0-9]{0,5}"
    r"(?P<lo>[0-9]+(?:\.[0-9]+)?)\s*(?:[–—\-]|to)\s*(?P<hi>[0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)

# A co-located caveat that acknowledges the instability: if present, the author is
# already reporting the estimate as a direction, so the gate stays silent.
INSTABILITY_CAVEAT = re.compile(
    r"exploratory|hypothesis[-\s]?generating|underpowered|imprecise|unstable|"
    r"wide\s+(?:confidence\s+interval|CI)|(?:confidence\s+interval|CI)\s+(?:is\s+)?wide|"
    r"interpret(?:ed)?\s+with\s+caution|should\s+be\s+interpreted\s+as\s+(?:a\s+)?direction|"
    r"not\s+(?:a\s+)?precise|direction(?:al)?\s+(?:rather\s+than|not)|caution",
    re.IGNORECASE,
)

# EPV operands.
EVENTS_RE = re.compile(r"\b([0-9]+)\s+events?\b", re.IGNORECASE)
COVAR_RE = re.compile(
    r"\b([0-9]+)\s+(?:covariates?|predictors?|(?:independent\s+)?variables?|"
    r"degrees?\s+of\s+freedom|parameters?)\b",
    re.IGNORECASE,
)

REGION_HEADINGS = re.compile(
    r"^#{1,4}\s*\*{0,2}(?:ABSTRACT|Abstract|CONCLUSIONS?|Conclusions?|DISCUSSION|Discussion|"
    r"Interpretation|Clinical Implications?|Summary)\*{0,2}\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_COLOCATE_WINDOW = 160   # chars each side of an estimate searched for a caveat
_EPV_WINDOW = 130        # chars between an event count and a covariate count


def headline_region(text: str) -> str:
    """Title + Abstract + Conclusion/Discussion regions + inline 'Conclusion:'
    clauses. Fallback: whole text. (Mirrors check_null_calibration.)"""
    spans: list[str] = []
    mt = re.search(r"^#{1,6}\s+(.+)$", text, re.MULTILINE)
    if mt:
        spans.append(mt.group(1))
    else:
        for line in text.splitlines():
            if line.strip():
                spans.append(line.strip())
                break
    all_headings = [m.start() for m in re.finditer(r"^#{1,4}\s", text, re.MULTILINE)]
    for m in REGION_HEADINGS.finditer(text):
        s = m.end()
        nxt = next((h for h in all_headings if h > s), len(text))
        spans.append(text[s:nxt])
    for m in re.finditer(r"(?:^|\n)\s*\*{0,2}(?:Conclusions?|Interpretation)\*{0,2}\s*[:.]\s*(.+?)(?:\n\n|$)",
                         text, re.IGNORECASE | re.DOTALL):
        spans.append(m.group(1))
    if not spans:
        spans.append(text)
    return "\n".join(spans)


def check(text: str, ratio_threshold: float = DEFAULT_RATIO_THRESHOLD) -> list[dict]:
    claims: list[dict] = []

    # 1. UNSTABLE_EFFECT_ESTIMATE — headline regions only.
    region = headline_region(text)
    seen: set[str] = set()
    for m in EFFECT_RE.finditer(region):
        lo, hi = float(m.group("lo")), float(m.group("hi"))
        if lo <= 0 or hi <= lo:
            continue
        ratio = hi / lo
        if ratio <= ratio_threshold:
            continue
        window = region[max(0, m.start() - _COLOCATE_WINDOW):m.end() + _COLOCATE_WINDOW]
        if INSTABILITY_CAVEAT.search(window):
            continue  # the author already flags this estimate as unstable
        key = m.group(0).lower()
        if key in seen:
            continue
        seen.add(key)
        claims.append({
            "verdict": "UNSTABLE_EFFECT_ESTIMATE",
            "severity": "Major",
            "detail": (f"{m.group('kind').upper()} {m.group('pt')} has a 95% CI "
                       f"{m.group('lo')}-{m.group('hi')} spanning {ratio:.0f}-fold "
                       f"(> {ratio_threshold:g}x) in the Abstract/Conclusions with no co-located "
                       f"caveat; a {ratio:.0f}-fold interval supports a direction, not the point "
                       f"estimate — report it as such or add an imprecision/exploratory caveat"),
            "where": m.group(0).replace("\n", " ").strip()[:160],
        })

    # 2. EPV_LOW — an event count and a covariate count printed in proximity.
    for em in EVENTS_RE.finditer(text):
        events = int(em.group(1))
        win = text[em.start():em.end() + _EPV_WINDOW]
        cm = COVAR_RE.search(win)
        if not cm:
            # also look just before the event count
            win2 = text[max(0, em.start() - _EPV_WINDOW):em.start()]
            cm = COVAR_RE.search(win2)
        if not cm:
            continue
        covar = int(cm.group(1))
        if covar <= 0:
            continue
        epv = events / covar
        if epv >= 10:
            continue
        claims.append({
            "verdict": "EPV_LOW",
            "severity": "Major",
            "detail": (f"{events} events for {covar} covariates is {epv:.1f} events per variable "
                       f"(< 10); the model is underpowered for stable coefficient estimation — "
                       f"reduce covariates, use penalisation, or report the estimates as exploratory"),
            "where": text[em.start():em.start() + 120].replace("\n", " ").strip()[:160],
        })
        break  # one EPV finding is enough; the first printed pair is representative

    return claims


def analyze(manuscript: str, ratio_threshold: float = DEFAULT_RATIO_THRESHOLD) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"), ratio_threshold=ratio_threshold)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | no headline estimate has an order-of-magnitude interval |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Effect-stability gate (Phase 2.5).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--ratio-threshold", type=float, default=DEFAULT_RATIO_THRESHOLD,
                    help="CI upper/lower ratio above which an estimate is unstable (default %(default)s)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript, ratio_threshold=args.ratio_threshold)

    if not args.quiet:
        print("=" * 41)
        print(" Effect Stability (Phase 2.5)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} unstable effect estimate / low-EPV finding(s).")
        else:
            print("OK: no headline estimate spans an order of magnitude without a caveat.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_effect_stability", **result}, indent=2),
                                  encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

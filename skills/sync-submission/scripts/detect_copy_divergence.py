#!/usr/bin/env python3
"""Multi-copy manuscript divergence detector (sync-submission Phase 8).

When a project keeps several hand-maintained manuscript copies — `manuscript.md`
(the working SSOT), `manuscript_circulation.md` (co-author feedback), and
`submission/<journal>/manuscript.md` (portal) — a batch of edits applied to the
SSOT routinely lands in only some of the copies. The portal then receives a stale
copy missing a subset of the edits, and the divergence surfaces (if at all) only
when a reviewer notices an inconsistency.

This detector is directional: it treats one file as the SSOT and reports, for each
copy, the SSOT *claims* (numeric assertions and section headings) that did not
propagate into the copy. A claim present in the SSOT but absent from a copy is an
unpropagated edit; a claim present only in a copy is a copy-side divergence.

INPUTS
  --ssot   the canonical manuscript file.
  --copy   a copy to check against the SSOT (repeatable).

OUTPUT  (--out path)
  {ssot, copies: [{copy, unpropagated_to_copy, copy_only, stale_in_copy, verdict}], verdict}
  STALE_COPY is the Major finding: a copy missing SSOT claims, OR a copy carrying a
  numeric claim the SSOT does not make (`stale_in_copy` — e.g. an old `n = 118`
  left next to the propagated `n = 120`). Exit 1 (with --strict) when any copy is
  stale.

Claims are matched as normalized strings, so wording differences do not register —
only a changed/absent number or heading does. A heading present only in a copy
(e.g. a circulation cover note) is listed in `copy_only` but does not make the copy
stale; a NUMERIC claim present only in a copy does, because it is the shape a stale
number takes once the new one has been pasted beside it.

Stdlib-only (re / json / argparse). Exit codes: 0 in sync (or report-only),
1 a stale copy (with --strict), 2 input/usage error (including a --copy that does
not exist or cannot be decoded as UTF-8 — a named copy is never silently skipped).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CLAIM_PATTERNS = [
    re.compile(r"\bn\s*=\s*[0-9][0-9,]*", re.I),                       # n = 1,284
    re.compile(r"[0-9]+\.[0-9]+\s*%|\b[0-9]+\s*%"),                    # 12.5% / 30%
    re.compile(r"\bp\s*[=<>]\s*0?\.[0-9]+", re.I),                     # p = 0.034
    re.compile(r"\b(?:a?OR|a?HR|RR|sHR)\s*[=:]?\s*[0-9]+\.[0-9]+", re.I),  # OR 1.34
    re.compile(r"\b95%\s*CI[^)]*[0-9]\.[0-9]+", re.I),                 # 95% CI ... 1.02
]
HEADING_RE = re.compile(r"^#{1,4}\s+\**([^\n*]+)", re.M)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower()).replace(" ", "")


def claims(text: str) -> set[str]:
    out: set[str] = set()
    for pat in CLAIM_PATTERNS:
        out.update(_norm(m.group(0)) for m in pat.finditer(text))
    for m in HEADING_RE.finditer(text):
        out.add("h:" + _norm(m.group(1)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Multi-copy manuscript divergence detector.")
    ap.add_argument("--ssot", required=True, help="canonical manuscript file")
    ap.add_argument("--copy", action="append", default=[], help="copy to check (repeatable)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any copy is stale")
    args = ap.parse_args()

    sp = Path(args.ssot)
    if not sp.is_file():
        sys.stderr.write(f"ERROR: SSOT not found: {args.ssot}\n")
        return 2
    if not args.copy:
        sys.stderr.write("ERROR: provide at least one --copy\n")
        return 2

    missing = [c for c in args.copy if not Path(c).is_file()]
    if missing:
        sys.stderr.write(f"ERROR: copy not found: {', '.join(missing)}\n")
        return 2
    texts = {}
    for f in [args.ssot] + args.copy:
        try:
            texts[f] = Path(f).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            sys.stderr.write(f"ERROR: cannot decode as UTF-8: {f}\n")
            return 2

    ssot_claims = claims(texts[args.ssot])
    copies = []
    n_stale = 0
    for c in args.copy:
        cp = Path(c)
        cc = claims(texts[c])
        unprop = sorted(ssot_claims - cc)
        copy_only = sorted(cc - ssot_claims)
        # Numeric claims only the copy makes; headings ("h:...") stay advisory.
        stale_in_copy = [x for x in copy_only if not x.startswith("h:")]
        verdict = "STALE_COPY" if (unprop or stale_in_copy) else "OK"
        if verdict == "STALE_COPY":
            n_stale += 1
        copies.append({
            "copy": str(cp),
            "unpropagated_to_copy": unprop,
            "copy_only": copy_only,
            "stale_in_copy": stale_in_copy,
            "verdict": verdict,
        })

    result = {
        "ssot": str(sp),
        "copies": copies,
        "verdict": "DIVERGENT" if n_stale else "OK",
        "suggested_fix": (
            "Re-propagate the unpropagated SSOT claims into each stale copy and remove "
            "the numbers the SSOT no longer states (stale_in_copy), or "
            "generate the copies from the SSOT via a build step instead of hand-maintaining them."
        ) if n_stale else None,
    }

    print("=" * 41)
    print(" Multi-copy manuscript divergence (Phase 8)")
    print("=" * 41)
    print(f"SSOT: {sp}")
    for c in copies:
        mark = "✗" if c["verdict"] == "STALE_COPY" else "✓"
        print(f"{mark} {c['copy']}")
        if c["unpropagated_to_copy"]:
            print(f"    unpropagated SSOT claims ({len(c['unpropagated_to_copy'])}): "
                  f"{c['unpropagated_to_copy'][:6]}")
        if c["stale_in_copy"]:
            print(f"    numeric claims absent from the SSOT ({len(c['stale_in_copy'])}): "
                  f"{c['stale_in_copy'][:6]}")
    if n_stale:
        print(f"\nDIVERGENT: {n_stale} stale copy(ies). {result['suggested_fix']}")
    else:
        print("\nOK: every SSOT claim propagated to all copies.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "detect_copy_divergence", **result}, indent=2), encoding="utf-8")
        print(f"wrote {args.out}")

    return 1 if (args.strict and n_stale) else 0


if __name__ == "__main__":
    sys.exit(main())

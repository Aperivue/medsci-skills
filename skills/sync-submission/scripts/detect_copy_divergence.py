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
  {ssot, copies: [{copy, unpropagated_to_copy, copy_only, verdict}], verdict}
  STALE_COPY (a copy missing SSOT claims) is the Major finding. Exit 1 (with
  --strict) when any copy is stale.

Claims are matched as normalized strings, so wording differences do not register —
only a changed/absent number or heading does. Review the lists; legitimately
copy-specific sections (e.g. a circulation cover note) will show up as `copy_only`
and can be ignored.

Stdlib-only (re / json / argparse). Exit codes: 0 in sync (or report-only),
1 a stale copy (with --strict), 2 input/usage error.
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

    ssot_claims = claims(sp.read_text(encoding="utf-8"))
    copies = []
    n_stale = 0
    for c in args.copy:
        cp = Path(c)
        if not cp.is_file():
            sys.stderr.write(f"WARN: copy not found, skipping: {c}\n")
            continue
        cc = claims(cp.read_text(encoding="utf-8"))
        unprop = sorted(ssot_claims - cc)
        copy_only = sorted(cc - ssot_claims)
        verdict = "STALE_COPY" if unprop else "OK"
        if unprop:
            n_stale += 1
        copies.append({
            "copy": str(cp),
            "unpropagated_to_copy": unprop,
            "copy_only": copy_only,
            "verdict": verdict,
        })

    result = {
        "ssot": str(sp),
        "copies": copies,
        "verdict": "DIVERGENT" if n_stale else "OK",
        "suggested_fix": (
            "Re-propagate the unpropagated SSOT claims into each stale copy, or "
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

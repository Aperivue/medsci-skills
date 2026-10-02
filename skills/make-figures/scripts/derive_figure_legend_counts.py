#!/usr/bin/env python3
"""Reconcile a flow-diagram figure caption against the flow-diagram SSOT.

A recurring submission error: the Figure 1 caption states participant counts
("n = 1,284 assessed ... n = 998 in the analytic cohort") that disagree with the
boxes of the flow diagram itself. It happens because the flow-diagram config (the
SSOT, e.g. `figure1_strobe_graphviz.yaml` consumed by generate_flow_diagram.R) is
updated for a final cohort lock while the hand-written caption is not. This script
re-derives the counts from the flow config and flags any `n = N` in the caption
that the diagram does not contain.

INPUTS
  --flow-config   the flow-diagram config file (YAML / R / text) whose box labels
                  carry the counts. Parsed as raw text (regex), so no YAML
                  dependency and it works for any flow-tool config.
  --manuscript    manuscript markdown (the Figure 1 caption is located by header)
                  OR --caption to pass the caption text directly.

OUTPUT  (--out path)
  {flow_counts, caption_counts, stale_in_caption, missing_in_caption, verdict}
  `stale_in_caption` (a caption count absent from the flow SSOT) is the Major
  finding. Exit 1 (with --strict) when any stale count exists. When no caption is located or the
  caption carries no `n = N`, the verdict is NOT_CHECKED (exit 2 under --strict), never OK.

KNOWN LIMITS
  Only `n = N` notation is parsed (a bare "1,150 patients" is not read), and agreement is set
  membership: a count moved to the wrong box (excluded and analysed swapped) is not detected.

Stdlib-only (re / json / argparse). Exit codes: 0 clean (or report-only),
1 caption count not in the flow SSOT (with --strict), 2 input/usage error, a flow config with no
`n = N` count, or (with --strict) a caption that could not be checked.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# "n = 1,284", "n=998", "N = 1284" — the standard flow-box / caption notation.
N_RE = re.compile(r"\bn\s*=\s*([0-9][0-9,]*)", re.I)

CAPTION_HDR_RE = re.compile(
    r"^#{0,4}\s*\**\s*(Figure\s*1|Fig\.?\s*1|Figure\s+1\.)\b", re.I | re.M
)


def _ints(text: str) -> list[int]:
    out = []
    for m in N_RE.finditer(text):
        try:
            out.append(int(m.group(1).replace(",", "")))
        except ValueError:
            pass
    return out


def extract_caption(manuscript_text: str) -> str:
    """Return the Figure 1 caption block (header line to the next blank line / header).

    When the header line carries no caption text of its own ("## Figure 1", "**Figure 1:**"),
    the caption is the next paragraph after any blank lines.
    """
    m = CAPTION_HDR_RE.search(manuscript_text)
    if not m:
        return ""
    start = m.start()
    rest = manuscript_text[m.end():]
    head_line, _, after = rest.partition("\n")
    if not re.sub(r"[\s*_:.|\-–—]", "", head_line):
        # The header line carries no caption text ("## Figure 1", "**Figure 1:**"): the caption
        # is the next paragraph, after any blank lines — not the empty header alone.
        body = after.lstrip("\n \t\r")
        if re.match(r"#{1,4}\s|\**\s*(Figure|Fig\.?)\s*\d", body):
            return ""                       # the next block is another header / caption
        head = manuscript_text[start:m.end() + len(head_line)]
        nxt = re.search(r"\n\s*\n|^#{1,4}\s|\bFigure\s*[2-9]\b", body, re.M)
        return head + "\n" + (body[:nxt.start()] if nxt else body)
    # caption ends at the next blank line followed by a header, or a new "Figure N"
    end_rel = len(rest)
    nxt = re.search(r"\n\s*\n|^#{1,4}\s|\bFigure\s*[2-9]\b", rest, re.M)
    if nxt:
        end_rel = nxt.start()
    return manuscript_text[start:m.end() + end_rel]


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconcile Figure 1 caption counts against the flow SSOT.")
    ap.add_argument("--flow-config", required=True, help="flow-diagram config (YAML/R/text)")
    ap.add_argument("--manuscript", help="manuscript markdown (Figure 1 caption auto-located)")
    ap.add_argument("--caption", help="caption text directly (alternative to --manuscript)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if a caption count is not in the SSOT")
    args = ap.parse_args()

    fc = Path(args.flow_config)
    if not fc.is_file():
        sys.stderr.write(f"ERROR: flow config not found: {args.flow_config}\n")
        return 2
    flow_counts = sorted(set(_ints(fc.read_text(encoding="utf-8"))))
    if not flow_counts:
        sys.stderr.write(f"ERROR: no 'n = N' count found in the flow config {args.flow_config}; "
                         "nothing to reconcile against.\n")
        return 2

    if args.caption:
        caption = args.caption
    elif args.manuscript:
        mp = Path(args.manuscript)
        if not mp.is_file():
            sys.stderr.write(f"ERROR: manuscript not found: {args.manuscript}\n")
            return 2
        caption = extract_caption(mp.read_text(encoding="utf-8"))
        if not caption:
            sys.stderr.write("WARN: no 'Figure 1' caption located; pass --caption to override.\n")
    else:
        sys.stderr.write("ERROR: provide --manuscript or --caption\n")
        return 2

    caption_counts = sorted(set(_ints(caption)))
    flow_set = set(flow_counts)
    not_checked = None
    if not caption:
        not_checked = "no 'Figure 1' caption located"
    elif not caption_counts:
        not_checked = "the Figure 1 caption carries no 'n = N' count"
    stale = [n for n in caption_counts if n not in flow_set]          # caption cites a number the diagram lacks
    missing = [n for n in flow_counts if n not in set(caption_counts)]  # diagram box not mentioned in caption

    result = {
        "flow_config": str(fc),
        "flow_counts": flow_counts,
        "caption_counts": caption_counts,
        "stale_in_caption": stale,
        "missing_in_caption": missing,
        "verdict": "MISMATCH" if stale else ("NOT_CHECKED" if not_checked else "OK"),
        "not_checked_reason": not_checked,
        "suggested_fix": (
            "Re-derive the caption counts from the flow-diagram config and update the caption; "
            "the flow diagram is the single source of truth."
        ) if stale else None,
    }

    print("=" * 41)
    print(" Figure 1 caption ↔ flow SSOT reconciliation")
    print("=" * 41)
    print(f"flow counts (SSOT): {flow_counts}")
    print(f"caption counts:     {caption_counts}")
    if stale:
        print(f"\nMISMATCH: caption cites {stale} not present in the flow diagram.")
        print(result["suggested_fix"])
    elif not_checked:
        print(f"\nNOT CHECKED: {not_checked}; the caption could not be reconciled "
              "(counts written without 'n =' are not parsed).")
    else:
        print("\nOK: every caption count is present in the flow diagram.")
    if missing:
        print(f"(note: flow boxes not mentioned in the caption: {missing})")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "derive_figure_legend_counts", **result}, indent=2), encoding="utf-8")
        print(f"wrote {args.out}")

    if args.strict and stale:
        return 1
    return 2 if (args.strict and not_checked) else 0


if __name__ == "__main__":
    sys.exit(main())

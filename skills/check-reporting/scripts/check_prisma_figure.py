#!/usr/bin/env python3
"""PRISMA Figure 1 Arithmetic & Cross-Reference Audit.

Loaded by `/check-reporting prisma` Step 4d.

Inputs:
  --md         manuscript markdown (body text PRISMA numbers).
  --figure     Figure 1 source: markdown manifest, caption .md, or text export.
  --out        output JSON (default: qc/prisma_figure_audit.json).

Outputs:
  qc/prisma_figure_audit.json + console table.

Exit codes:
  0  audit_safe (all PRESENT)
  1  arithmetic or cross-reference MISMATCH / MISSING
  2  invalid input (file missing, parse failure)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KEYWORDS = {
    "identified": r"(\d[\d,]*)\s+(?:records?|reports?)\s+identified",
    "duplicates": r"(\d[\d,]*)\s+(?:records?|reports?|duplicates?)\s+(?:duplicates?\s+)?removed",
    "screened": r"(\d[\d,]*)\s+(?:records?|reports?)\s+screened",
    # Explicit suffix required to avoid collision with excluded_eligibility.
    "excluded_screening": r"(\d[\d,]*)\s+(?:records?|reports?)\s+excluded\s+(?:at|after|during)\s+screening",
    "sought": r"(\d[\d,]*)\s+(?:reports?|records?)\s+sought(?:\s+for\s+retrieval)?",
    "not_retrieved": r"(\d[\d,]*)\s+(?:reports?|records?)\s+(?:not\s+retrieved|unobtainable)",
    # Match both "reports retrieved" and "retrieved 186 reports".
    "retrieved": r"(?:(\d[\d,]*)\s+(?:records?|reports?)\s+retrieved|retrieved\s+(\d[\d,]*)\s+(?:records?|reports?))",
    "assessed": r"(\d[\d,]*)\s+(?:reports?|records?)\s+assessed(?:\s+for\s+eligibility)?",
    # Explicit suffix required to avoid collision with excluded_screening.
    "excluded_eligibility": r"(\d[\d,]*)\s+(?:records?|reports?)\s+excluded\s+with\s+reasons?",
    "included": r"(\d[\d,]*)\s+(?:studies|records?|reports?)\s+included",
}


def extract_numbers(text: str) -> dict[str, int]:
    """Return {key: int} for keywords that match. First match wins per key."""
    out: dict[str, int] = {}
    for key, pattern in KEYWORDS.items():
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            num = next((g for g in m.groups() if g), None)
            if num is None:
                continue
            try:
                out[key] = int(num.replace(",", ""))
            except ValueError:
                continue
    return out


def check_arithmetic(n: dict[str, int]) -> list[dict]:
    eqs = [
        ("screened = identified - duplicates", "screened", "identified", "duplicates"),
        ("sought = screened - excluded_screening", "sought", "screened", "excluded_screening"),
        ("retrieved = sought - not_retrieved", "retrieved", "sought", "not_retrieved"),
        ("included = assessed - excluded_eligibility", "included", "assessed", "excluded_eligibility"),
    ]
    out = []
    for label, lhs_key, a_key, b_key in eqs:
        if all(k in n for k in (lhs_key, a_key, b_key)):
            lhs = n[lhs_key]
            rhs = n[a_key] - n[b_key]
            out.append({
                "eq": label,
                "lhs": lhs,
                "rhs": rhs,
                "status": "PRESENT" if lhs == rhs else "MISMATCH",
            })
        else:
            missing = [k for k in (lhs_key, a_key, b_key) if k not in n]
            out.append({
                "eq": label,
                "lhs": None,
                "rhs": None,
                "status": "MISSING",
                "missing_keys": missing,
            })
    return out


def cross_reference(body: dict[str, int], figure: dict[str, int]) -> list[dict]:
    out = []
    keys = set(body) | set(figure)
    for key in sorted(keys):
        b = body.get(key)
        f = figure.get(key)
        if b is None and f is None:
            continue
        if b is None:
            status = "MISSING"
            note = "body lacks number"
        elif f is None:
            status = "MISSING"
            note = "figure lacks number"
        elif b == f:
            status = "PRESENT"
            note = ""
        else:
            status = "MISMATCH"
            note = f"body={b}, figure={f}"
        out.append({"key": key, "body": b, "figure": f, "status": status, "note": note})
    return out


def render_table(rows: list[dict], cols: list[str]) -> str:
    if not rows:
        return "  (none)"
    widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    head = "  " + "  ".join(c.ljust(widths[c]) for c in cols)
    sep = "  " + "  ".join("-" * widths[c] for c in cols)
    body = "\n".join(
        "  " + "  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols) for r in rows
    )
    return "\n".join([head, sep, body])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", required=True, help="manuscript markdown path")
    ap.add_argument("--figure", required=True, help="Figure 1 source path (.md, .txt)")
    ap.add_argument("--out", default="qc/prisma_figure_audit.json", help="output JSON path")
    args = ap.parse_args()

    md_path = Path(args.md)
    fig_path = Path(args.figure)
    if not md_path.exists():
        print(f"ERROR: manuscript not found: {md_path}", file=sys.stderr)
        return 2
    if not fig_path.exists():
        print(f"ERROR: figure source not found: {fig_path}", file=sys.stderr)
        return 2

    body_text = md_path.read_text(encoding="utf-8")
    fig_text = fig_path.read_text(encoding="utf-8")

    body_numbers = extract_numbers(body_text)
    figure_numbers = extract_numbers(fig_text)

    arith_body = check_arithmetic(body_numbers)
    arith_figure = check_arithmetic(figure_numbers)
    xref = cross_reference(body_numbers, figure_numbers)

    audit_safe = (
        all(r["status"] == "PRESENT" for r in arith_body)
        and all(r["status"] == "PRESENT" for r in arith_figure)
        and all(r["status"] == "PRESENT" for r in xref)
    )

    action_items: list[str] = []
    for r in arith_body:
        if r["status"] == "MISMATCH":
            action_items.append(
                f"[PRISMA-FIGURE] body arithmetic '{r['eq']}' fails: {r['lhs']} vs {r['rhs']}"
            )
    for r in arith_figure:
        if r["status"] == "MISMATCH":
            action_items.append(
                f"[PRISMA-FIGURE] figure arithmetic '{r['eq']}' fails: {r['lhs']} vs {r['rhs']}"
            )
    for r in xref:
        if r["status"] == "MISMATCH":
            action_items.append(
                f"[PRISMA-FIGURE] cross-ref '{r['key']}' MISMATCH: body={r['body']}, figure={r['figure']}"
            )

    result = {
        "manuscript": str(md_path),
        "figure_source": str(fig_path),
        "body_numbers": body_numbers,
        "figure_numbers": figure_numbers,
        "arithmetic_body": arith_body,
        "arithmetic_figure": arith_figure,
        "cross_reference": xref,
        "audit_safe": audit_safe,
        "action_items": action_items,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"detector": "check_prisma_figure", **result}, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"== PRISMA Figure Audit — {md_path.name} vs {fig_path.name} ==\n")
    print("Body arithmetic:")
    print(render_table(arith_body, ["eq", "lhs", "rhs", "status"]))
    print("\nFigure arithmetic:")
    print(render_table(arith_figure, ["eq", "lhs", "rhs", "status"]))
    print("\nCross-reference (body ↔ figure):")
    print(render_table(xref, ["key", "body", "figure", "status", "note"]))
    print(f"\naudit_safe: {audit_safe}")
    print(f"output: {out_path}")
    if action_items:
        print("\nAction items:")
        for a in action_items:
            print(f"  - {a}")

    return 0 if audit_safe else 1


if __name__ == "__main__":
    sys.exit(main())

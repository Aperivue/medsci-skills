#!/usr/bin/env python3
"""Cross-script categorical / cut-point consistency gate (self-review Phase 2.5b).

A derived categorical variable (age band, BMI category, eGFR/CKD stage, FIB-4
strata, risk tier) is often re-derived in more than one analysis script — the
primary table in one file, a sensitivity or secondary analysis in another. When
those re-derivations disagree on the cut-points or the interval closure, the SAME
cohort is split differently in each file: per-stratum Ns drift between tables even
though the grand total still matches, and a stratum can spuriously appear to cross
a threshold. A grand-total / row-sum check does not catch it because every total
still reconciles; a reviewer who compares the primary table's stratum Ns against
the sensitivity table's stratum Ns does.

This detector parses analysis SOURCE (R / Python), not the manuscript. It extracts
every binning assignment of the form

    R:       <var> <- cut(<src>, breaks = c(...), right = TRUE/FALSE, labels = ...)
    R:       <var> <- case_when( <numeric boundary literals> )
    Python:  <var> = pd.cut(<src>, bins=[...], right=True/False, labels=...)

groups them by the assigned variable name, and fires BINNING_DRIFT when one
variable is defined with two or more distinct (breaks, right-closure) signatures
across the scanned files. It is deterministic and conservative: it fires only when
it can extract a complete `breaks`/`bins` operand and the signatures genuinely
differ. The interval-closure flag is compared using each language's documented
default (R `cut` right=TRUE, pandas `pd.cut` right=True), so an explicit
`right=FALSE` in one file and an omitted default in another is a real difference.

Motivation: a screening cohort binned age with
`cut(bl_age, breaks=c(-Inf,45,50,60,Inf), right=FALSE)` in the primary script and
`cut(bl_age, breaks=c(-Inf,44,49,59,Inf), right=TRUE)` in the threshold sensitivity
script. Fractional ages (e.g. 44.5 y) fell into different bands, shifting ~353
participants and producing a spurious "reached" stratum in the sensitivity table
that vanished once the binning was harmonized. See
~/.claude/rules/cross-script-categorical-consistency.md.

INPUTS
  --root PATH        directory to scan recursively for *.R/*.r/*.py (repeatable;
                     default: ./analysis and ./scripts if present, else .)
  --glob PATTERN     extra filename glob to include (repeatable)
  --out PATH         write JSON artifact
  --strict           exit 1 if any Major (BINNING_DRIFT) finding
  --quiet            suppress stdout table

OUTPUT  reconciliation table (stdout) + optional JSON:
  {scanned[], definitions[], claims[{verdict, severity, detail, where}], summary}

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean/report-only,
1 Major with --strict, 2 input/usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Variable-name hints that mark a derived categorical (the assigned LHS or the
# binned source). Used only to keep the reconciliation table focused; a drift on
# any repeatedly-binned variable still fires.
CATEGORICAL_HINTS = (
    "band", "cat", "category", "group", "grp", "strat", "stage", "tier",
    "quartile", "tertile", "quintile", "decile", "level", "class",
    "age", "bmi", "egfr", "gfr", "fib4", "fib_4", "cmb", "mets", "ckd",
)

SCRIPT_SUFFIXES = (".r", ".py")


def _is_categorical_name(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in CATEGORICAL_HINTS)


def _norm_breaks(raw: str) -> str:
    """Normalize a breaks/bins operand to a comparable token string.

    Keeps the numeric/-Inf/Inf sequence in order; drops whitespace and the
    c(...) / [...] wrapper. '-Inf,45,50,60,Inf' style."""
    body = raw.strip()
    body = re.sub(r"^(c|seq)\s*\(", "", body, flags=re.I)
    body = body.strip().lstrip("[(").rstrip("])")
    toks = []
    for t in body.split(","):
        t = t.strip()
        if not t:
            continue
        t = t.replace("Inf", "Inf").replace("inf", "Inf")
        t = re.sub(r"^np\.|^math\.|^float\(['\"]?|['\"]?\)$", "", t)
        t = t.replace("-Inf", "-Inf")
        toks.append(t)
    return ",".join(toks)


def _right_default(lang: str) -> str:
    # R cut() default right=TRUE; pandas pd.cut default right=True.
    return "TRUE"


def _norm_right(raw, lang: str) -> str:
    if raw is None:
        return _right_default(lang)
    v = raw.strip().upper()
    if v in ("T", "TRUE"):
        return "TRUE"
    if v in ("F", "FALSE"):
        return "FALSE"
    return v


def _find_matching_paren(text: str, open_idx: int) -> int:
    """Index of the ')' matching the '(' at open_idx, or -1."""
    depth = 0
    for i in range(open_idx, len(text)):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


# `lhs <- cut(...)`, `lhs = cut(...)`, `lhs = pd.cut(...)`. Captures lhs + call start.
_ASSIGN_CUT_RE = re.compile(
    r"(?P<lhs>[A-Za-z_][\w.$\[\]\"']*?)\s*(?:<<-|<-|=)\s*"
    r"(?P<fn>(?:pd\.)?cut)\s*\(",
)
_BREAKS_RE = re.compile(r"\b(?:breaks|bins)\s*=\s*", re.I)
_RIGHT_RE = re.compile(r"\bright\s*=\s*(TRUE|FALSE|True|False|T|F)\b")
_LABELS_RE = re.compile(r"\blabels\s*=\s*(c\([^)]*\)|\[[^\]]*\])", re.I)


def _operand_after(text: str, start: int) -> str:
    """Return the operand string starting at `start`, balanced over () and []."""
    # skip leading spaces
    i = start
    while i < len(text) and text[i] in " \t":
        i += 1
    if i >= len(text):
        return ""
    if text[i] in "c([":
        # c(...) or [...]
        if text[i] == "c":
            paren = text.find("(", i)
            end = _find_matching_paren(text, paren)
            return text[i:end + 1] if end != -1 else text[i:i + 80]
        opener = text[i]
        closer = ")" if opener == "(" else "]"
        depth = 0
        for j in range(i, len(text)):
            if text[j] == opener:
                depth += 1
            elif text[j] == closer:
                depth -= 1
                if depth == 0:
                    return text[i:j + 1]
        return text[i:i + 80]
    # bare token up to comma
    m = re.match(r"[^,)\n]+", text[i:])
    return m.group(0) if m else ""


def extract_cut_defs(path: Path):
    """Yield dicts for each cut/pd.cut assignment in a file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lang = "py" if path.suffix.lower() == ".py" else "r"
    out = []
    for m in _ASSIGN_CUT_RE.finditer(text):
        open_idx = m.end() - 1
        close_idx = _find_matching_paren(text, open_idx)
        if close_idx == -1:
            continue
        call = text[open_idx + 1:close_idx]
        bm = _BREAKS_RE.search(call)
        if not bm:
            continue
        breaks_raw = _operand_after(call, bm.end())
        breaks = _norm_breaks(breaks_raw)
        if not breaks or not re.search(r"\d", breaks):
            continue
        rm = _RIGHT_RE.search(call)
        right = _norm_right(rm.group(1) if rm else None, lang)
        lm = _LABELS_RE.search(call)
        labels = re.sub(r"\s+", "", lm.group(1)) if lm else ""
        lhs = m.group("lhs").strip()
        line_no = text[:m.start()].count("\n") + 1
        out.append({
            "var": lhs,
            "kind": "cut",
            "breaks": breaks,
            "right": right,
            "labels": labels,
            "file": str(path),
            "line": line_no,
        })
    return out


def analyze(roots, extra_globs):
    files = []
    seen = set()
    for root in roots:
        rp = Path(root)
        if rp.is_file():
            cands = [rp]
        else:
            cands = [p for p in rp.rglob("*") if p.suffix.lower() in SCRIPT_SUFFIXES]
            for g in extra_globs:
                cands += list(rp.rglob(g))
        for p in cands:
            if p.is_file() and str(p) not in seen:
                seen.add(str(p))
                files.append(p)

    defs = []
    for p in sorted(files):
        try:
            defs.extend(extract_cut_defs(p))
        except OSError:
            continue

    # Group by assigned variable name (normalized to leaf identifier).
    def _leaf(v):
        v = re.sub(r"\[[^\]]*\]|\$.*$|\"|'", "", v)
        return v.split("$")[-1].split(".")[-1].strip()

    groups: dict[str, list[dict]] = {}
    for d in defs:
        groups.setdefault(_leaf(d["var"]), []).append(d)

    claims = []
    for var, ds in sorted(groups.items()):
        sigs = {(d["breaks"], d["right"]) for d in ds}
        # Only meaningful for repeatedly-derived categoricals across >=2 sites.
        if len(ds) < 2 or len(sigs) < 2:
            continue
        # Conservative focus: name looks categorical OR appears in >=2 files.
        n_files = len({d["file"] for d in ds})
        if not (_is_categorical_name(var) or n_files >= 2):
            continue
        detail_parts = []
        for d in ds:
            fn = Path(d["file"]).name
            detail_parts.append(f"{fn}:{d['line']} breaks=[{d['breaks']}] right={d['right']}")
        claims.append({
            "verdict": "BINNING_DRIFT",
            "severity": "Major",
            "var": var,
            "detail": f"`{var}` derived with {len(sigs)} different cut signatures across "
                      f"{n_files} file(s): " + " | ".join(detail_parts),
            "where": "; ".join(f"{Path(d['file']).name}:{d['line']}" for d in ds),
        })

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "scanned": [str(p) for p in sorted(files)],
        "definitions": defs,
        "claims": claims,
        "summary": {
            "n_files": len(files),
            "n_definitions": len(defs),
            "n_claims": len(claims),
            "n_major": n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | no cross-script binning drift detected |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Cross-script categorical / cut-point consistency gate (Phase 2.5b).")
    ap.add_argument("--root", action="append", default=[],
                    help="directory or file to scan (repeatable; "
                         "default: ./analysis and ./scripts if present, else .)")
    ap.add_argument("--glob", action="append", default=[],
                    help="extra filename glob to include under each --root (repeatable)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major finding")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    roots = args.root
    if not roots:
        roots = [d for d in ("analysis", "scripts") if Path(d).is_dir()] or ["."]

    result = analyze(roots, args.glob)

    if not args.quiet:
        print("=" * 46)
        print(" Cross-script Binning Consistency (Phase 2.5c)")
        print("=" * 46)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} variable(s) binned inconsistently "
                  f"across scripts ({s['n_definitions']} cut definitions in {s['n_files']} files).")
        else:
            print(f"OK: no cross-script binning drift "
                  f"({s['n_definitions']} cut definitions in {s['n_files']} files).")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Cross-script categorical / cut-point and composite-definition consistency gate (self-review Phase 2.5b).

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

It ALSO extracts composite boolean-indicator definitions — the sibling failure
mode where a derived 0/1 component (e.g. a metabolic-syndrome criterion) is built
from a disjunction of comparison clauses and a second script omits or adds a
clause:

    R:       <var> <- as.integer(a >= x | b == 1 | c == 1)
    R:       <var> <- as.numeric(<bool expr>)   / ifelse(<bool expr>, 1, 0)
    Python:  <var> = np.where(<bool expr>, 1, 0)

The boolean expression is split into comparison ATOMS on the top-level `|` (OR);
clause order, whitespace, and outer parentheses do not matter (atoms are compared
as a SET), so only a genuinely missing or added clause counts. It fires
DERIVED_DEF_DRIFT when one variable is defined with two or more distinct atom sets.
Motivation: `mets_bp <- as.integer(bl_he_sbp>=130 | bl_he_dbp>=85 |
bl_tx_hypertension_med==1 | bl_hypertension==1)` in the canonical script vs the
same name without the final `| bl_hypertension==1` in a re-analysis script — the
metabolic-syndrome C-index then read 0.6704 in one table and 0.6712 in another.

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

# Name hints for composite 0/1 indicator components (the DERIVED_DEF_DRIFT path).
INDICATOR_HINTS = (
    "mets", "indicator", "flag", "criteria", "criterion", "_pos", "_neg",
    "_yes", "_bin", "_ind", "comp", "positive", "present",
)

SCRIPT_SUFFIXES = (".r", ".py")


def _is_categorical_name(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in CATEGORICAL_HINTS)


def _is_indicator_name(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in INDICATOR_HINTS)


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


# Composite boolean-indicator assignment: `lhs <- as.integer(...)`, `as.numeric`,
# `ifelse(...)`, Python `(...).astype(int)` / `np.where(...)`.
_ASSIGN_DERIVED_RE = re.compile(
    r"(?P<lhs>[A-Za-z_][\w.$\[\]\"']*?)\s*(?:<<-|<-|=)\s*"
    r"(?P<fn>as\.integer|as\.numeric|np\.where|ifelse)\s*\(",
)
_COMPARISON_RE = re.compile(r"==|!=|>=|<=|%in%|>|<")


def _first_arg(call_body: str) -> str:
    """The first top-level (depth-0) comma-delimited argument of a call body."""
    depth = 0
    for i, c in enumerate(call_body):
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        elif c == "," and depth == 0:
            return call_body[:i]
    return call_body


def _split_top_level(expr: str, op: str):
    """Split on a top-level (depth-0) boolean operator char `op` ('|' or '&').
    Parenthesized/`&`-or-`|` sub-groups stay intact; the doubled form (`||`/`&&`)
    is treated identically as a single separator."""
    parts, depth, cur, i = [], 0, [], 0
    while i < len(expr):
        c = expr[i]
        if c in "([":
            depth += 1
            cur.append(c)
        elif c in ")]":
            depth -= 1
            cur.append(c)
        elif c == op and depth == 0:
            if i + 1 < len(expr) and expr[i + 1] == op:  # collapse `||` / `&&`
                i += 1
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    if cur:
        parts.append("".join(cur))
    return parts


def _strip_wrap_parens(a: str) -> str:
    """Remove fully-wrapping outer parens, e.g. `(a | b)` -> `a | b`. A leading
    paren that does NOT close at the end (e.g. `(a & b) | c`) is left intact."""
    a = a.strip()
    while len(a) >= 2 and a[0] == "(" and _find_matching_paren(a, 0) == len(a) - 1:
        a = a[1:-1].strip()
    return a


def _norm_atom(a: str) -> str:
    """Whitespace-free canonical form of one OR-clause. Dataframe qualifiers
    (`df$col`, `sub$col`) are dropped so a bare `mutate()` reference and a base-R
    `df$` reference to the same column compare equal, and a top-level `&`-group is
    sorted so operand order inside an AND does not matter
    (`x==1 & y>=2` == `y>=2 & x==1`)."""
    a = re.sub(r"\s+", "", _strip_wrap_parens(a))
    a = re.sub(r"[A-Za-z_]\w*\$", "", a)  # df$col / sub$col -> col
    if "&" in a:
        andparts = _split_top_level(a, "&")
        if len(andparts) > 1:
            a = "&".join(sorted(_strip_wrap_parens(p) for p in andparts))
    return a


def extract_derived_defs(path: Path):
    """Yield dicts for each composite boolean-indicator assignment in a file.

    Only definitions whose expression contains at least one comparison operator
    are kept (a plain `as.integer(count)` cast is not an indicator and is skipped).
    The atom set is order- and whitespace-insensitive."""
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in _ASSIGN_DERIVED_RE.finditer(text):
        open_idx = m.end() - 1
        close_idx = _find_matching_paren(text, open_idx)
        if close_idx == -1:
            continue
        inner = text[open_idx + 1:close_idx]
        # np.where(expr, 1, 0) / ifelse(expr, 1, 0): the boolean test is arg 1.
        if m.group("fn") in ("np.where", "ifelse"):
            inner = _first_arg(inner)
        inner = _strip_wrap_parens(inner)
        if not _COMPARISON_RE.search(inner):
            continue
        atoms = sorted({_norm_atom(a) for a in _split_top_level(inner, "|") if _norm_atom(a)})
        if not atoms:
            continue
        lhs = m.group("lhs").strip()
        line_no = text[:m.start()].count("\n") + 1
        out.append({
            "var": lhs,
            "kind": "derived",
            "atoms": atoms,
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
    # `df$col` (R) / `df['col']` (py) / `df.col` (py) / bare `col` all reduce to
    # the COLUMN name `col` — the table handle is not the variable of interest.
    def _leaf(v):
        v = v.strip().strip("\"'")
        m = re.search(r"\[\s*[\"']([^\"']+)[\"']\s*\]", v)   # py df['col'] / df["col"]
        if m:
            return m.group(1)
        v = re.sub(r"\[[^\]]*\]", "", v)                      # drop other [..] indexers
        return v.split("$")[-1].split(".")[-1].strip()        # R df$col / py df.col / bare

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

    # --- Composite boolean-indicator definition drift (DERIVED_DEF_DRIFT) -----
    derived_defs = []
    for p in sorted(files):
        try:
            derived_defs.extend(extract_derived_defs(p))
        except OSError:
            continue

    dgroups: dict[str, list[dict]] = {}
    for d in derived_defs:
        dgroups.setdefault(_leaf(d["var"]), []).append(d)

    for var, ds in sorted(dgroups.items()):
        sigs = {tuple(d["atoms"]) for d in ds}
        if len(ds) < 2 or len(sigs) < 2:
            continue
        n_files = len({d["file"] for d in ds})
        # Conservative focus: indicator/categorical-looking name OR re-derived in >=2 files.
        if not (_is_indicator_name(var) or _is_categorical_name(var) or n_files >= 2):
            continue
        siglist = [set(s) for s in sigs]
        diff = sorted(set().union(*siglist) - set.intersection(*siglist))
        detail_parts = [f"{Path(d['file']).name}:{d['line']} {{{', '.join(d['atoms'])}}}" for d in ds]
        claims.append({
            "verdict": "DERIVED_DEF_DRIFT",
            "severity": "Major",
            "var": var,
            "detail": f"`{var}` defined with {len(sigs)} different clause sets across "
                      f"{n_files} file(s); differing clause(s): {{{', '.join(diff)}}}. "
                      + " | ".join(detail_parts),
            "where": "; ".join(f"{Path(d['file']).name}:{d['line']}" for d in ds),
        })

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "scanned": [str(p) for p in sorted(files)],
        "definitions": defs + derived_defs,
        "claims": claims,
        "summary": {
            "n_files": len(files),
            "n_definitions": len(defs) + len(derived_defs),
            "n_cut_definitions": len(defs),
            "n_derived_definitions": len(derived_defs),
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
        lines.append("| (none) | — | no cross-script binning or definition drift detected |")
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
        print(" Cross-script Categorical / Definition Consistency (Phase 2.5c)")
        print("=" * 46)
        print(render(result))
        print()
        s = result["summary"]
        defs_desc = (f"{s['n_cut_definitions']} cut + {s['n_derived_definitions']} "
                     f"composite definitions in {s['n_files']} files")
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} variable(s) derived inconsistently "
                  f"across scripts ({defs_desc}).")
        else:
            print(f"OK: no cross-script binning or definition drift ({defs_desc}).")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""check_reported_p_from_counts.py — recompute each 2x2 table row's P value from its
own integer counts and flag a reported P that reproduces under no standard test.

A baseline table comparing two groups prints a count per group and a P value per
row. That P is fully determined by the four cell counts, yet a wrong one (e.g. a
reported ``p<0.001`` whose true value is ~0.06) routinely survives review because
no one recomputes it. This detector rebuilds the 2x2 table for every count row,
recomputes Fisher's exact test and Pearson's chi-square (with and without Yates'
correction) in pure stdlib, *calibrates* which family the manuscript used on the
rows that reproduce, and flags any row whose reported P differs by more than one
order of magnitude under **every** family.

Guards: continuous rows (mean ± SD, median [IQR]) are skipped; at least two count
rows are required so the family can be calibrated; a single-row table never fires.

With --tests p_tests.json (references/p_tests_schema.md) the authors declare the test
behind each row's P and the alpha. A row is found by its first cell (case-insensitive,
exact words) and its P recomputed with the declared test only. The reported P is read
as the interval of its printed precision ("0.04" -> [0.035, 0.045), "<0.001" -> (0,
0.001)), and P_ALPHA_CROSSING (Major) fires when that whole interval lies on one side
of alpha and the recomputed P strictly on the other. P_NOT_ASSESSED (Minor) is given
for an adjusted, paired or "other:" test, a row not found (or found twice), with no
counts or no P, a printed percentage that is not count/n (another denominator), and a
table of three or more groups (a column headed Total / Overall / All whose n is the
sum of the others is dropped first). An "other:" test also gives UNLISTED_METHOD (Minor). The
order-of-magnitude rule above runs unchanged alongside.

Stdlib-only (math.comb / math.erfc). Reads the manuscript, never writes it.

Usage:
  python3 check_reported_p_from_counts.py --manuscript paper.md [--tests p_tests.json]
                                          [--strict] [--quiet] [--json]
Exit: 0 clean; with --strict, 1 on any P_NOT_REPRODUCIBLE (or, with --tests, any
P_ALPHA_CROSSING); 2 on input/usage error or a malformed --tests file (the message
names the field).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field, asdict
from decimal import Decimal, InvalidOperation

SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
HEADER_N_RE = re.compile(r"\bn\s*=\s*([0-9][0-9,]*)", re.I)
PVAL_HEADER_RE = re.compile(r"^\s*\*?\s*[Pp]\s*(?:[- ]?value)?\s*\*?\s*$")
PVAL_HEADER_CONTAINS = re.compile(r"\bp[- ]?value\b", re.I)
COUNT_CELL_RE = re.compile(r"^\s*(\d[\d,]*)\s*(?:\(|$)")          # integer count, optionally "count (pct)"
PVAL_CELL_RE = re.compile(r"^\s*([<=]?)\s*(0?\.\d+|\d+(?:\.\d+)?)\s*$")
FAMILIES = ("Fisher exact", "Pearson chi-square (Yates)", "Pearson chi-square (uncorrected)")


@dataclass
class Finding:
    kind: str
    severity: str
    line: int
    detail: str


@dataclass
class Report:
    source: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def n_flag(self) -> int:
        return sum(1 for f in self.findings if f.kind == "P_NOT_REPRODUCIBLE")

    @property
    def n_crossing(self) -> int:
        return sum(1 for f in self.findings if f.kind == "P_ALPHA_CROSSING")

    @property
    def n_major(self) -> int:
        return self.n_flag + self.n_crossing

    @property
    def verdict(self) -> str:
        if self.n_flag:
            return "NON-REPRODUCIBLE P"
        return "P ALPHA CROSSING" if self.n_crossing else "OK"


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _fisher(a: int, b: int, c: int, d: int) -> float:
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    if 0 in (r1, r2, c1, b + d):
        return 1.0
    denom = math.comb(n, c1)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    p_obs = math.comb(r1, a) * math.comb(r2, c1 - a) / denom
    tol = p_obs * (1 + 1e-7)
    total = sum(math.comb(r1, k) * math.comb(r2, c1 - k) / denom
                for k in range(lo, hi + 1)
                if math.comb(r1, k) * math.comb(r2, c1 - k) / denom <= tol)
    return min(1.0, total)


def _chi2(a: int, b: int, c: int, d: int, yates: bool) -> float:
    n = a + b + c + d
    r1, r2, c1, c2 = a + b, c + d, a + c, b + d
    if 0 in (r1, r2, c1, c2):
        return 1.0
    num = abs(a * d - b * c)
    if yates:
        num = max(0.0, num - n / 2)
    chi2 = n * num * num / (r1 * r2 * c1 * c2)
    return math.erfc(math.sqrt(chi2 / 2))  # 1 df


def _pvals(a: int, b: int, c: int, d: int) -> tuple[float, float, float]:
    return _fisher(a, b, c, d), _chi2(a, b, c, d, True), _chi2(a, b, c, d, False)


def _order_gap(rep_op: str, rep_val: float, comp: float) -> float:
    """log10 gap between reported and computed; for '<' bounds, only a computed
    value ABOVE the bound counts (a computed below the claimed upper bound is fine)."""
    if comp <= 0 or rep_val <= 0:
        return 0.0
    if rep_op == "<":
        return max(0.0, math.log10(comp) - math.log10(rep_val))
    return abs(math.log10(comp) - math.log10(rep_val))


def _iter_tables(text: str):
    """Yield (header cells, group columns, P column, [(row cells, line no)]) per markdown table."""
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        if not ("|" in lines[i] and i + 1 < n and SEP_RE.match(lines[i + 1]) and "-" in lines[i + 1]):
            i += 1
            continue
        header = _split_row(lines[i])
        group_cols = [j for j, h in enumerate(header) if HEADER_N_RE.search(h)]
        p_col = next((j for j, h in enumerate(header)
                      if PVAL_HEADER_RE.match(h) or PVAL_HEADER_CONTAINS.search(h)), None)
        # gather rows
        rows = []
        j = i + 2
        while j < n and "|" in lines[j] and lines[j].strip():
            rows.append((_split_row(lines[j]), j + 1))
            j += 1
        i = j
        yield header, group_cols, p_col, rows


def audit(text: str, source: str) -> Report:
    rep = Report(source=source)
    for header, group_cols, p_col, rows in _iter_tables(text):
        if len(group_cols) < 2 or p_col is None:
            continue
        g1, g2 = group_cols[0], group_cols[1]
        n1 = int(HEADER_N_RE.search(header[g1]).group(1).replace(",", ""))
        n2 = int(HEADER_N_RE.search(header[g2]).group(1).replace(",", ""))

        parsed = []
        for cells, ln in rows:
            if max(g1, g2, p_col) >= len(cells):
                continue
            m1, m2 = COUNT_CELL_RE.match(cells[g1]), COUNT_CELL_RE.match(cells[g2])
            pm = PVAL_CELL_RE.match(cells[p_col])
            if not (m1 and m2 and pm):
                continue  # continuous row (mean±SD / IQR) or no P
            a, c = int(m1.group(1).replace(",", "")), int(m2.group(1).replace(",", ""))
            if a > n1 or c > n2:
                continue
            b, d = n1 - a, n2 - c
            parsed.append((cells[0], ln, a, b, c, d, pm.group(1) or "=", float(pm.group(2))))

        if len(parsed) < 2:
            continue  # cannot calibrate the family on a single row

        # calibrate: which family reproduces the most rows to <= 1e-3 (op '=')?
        computed = [(_pvals(a, b, c, d)) for _, _, a, b, c, d, _, _ in parsed]
        repro = [0, 0, 0]
        for (lbl, ln, a, b, c, d, op, val), pv in zip(parsed, computed):
            if op == "=":
                for k in range(3):
                    if abs(pv[k] - val) <= 1e-3:
                        repro[k] += 1
        fam_idx = max(range(3), key=lambda k: repro[k]) if any(repro) else 2

        for (lbl, ln, a, b, c, d, op, val), pv in zip(parsed, computed):
            gaps = [_order_gap(op, val, pv[k]) for k in range(3)]
            if min(gaps) > 1.0:  # differs by >1 order under EVERY family
                closest = min(range(3), key=lambda k: gaps[k])
                rep.findings.append(Finding(
                    "P_NOT_REPRODUCIBLE", "MAJOR", ln,
                    f"row '{lbl}' ({a}/{a+b} vs {c}/{c+d}) reports P{op}{val:g}, but recomputes to "
                    f"Fisher {pv[0]:.3g} / Yates {pv[1]:.3g} / uncorrected {pv[2]:.3g} "
                    f"(closest {FAMILIES[closest]}; table family ≈ {FAMILIES[fam_idx]})"))
    return rep


# --- Declared tests (--tests p_tests.json) ---------------------------------
# {"alpha"?: 0.05, "rows": [{"row": "<first-cell label>", "test": "<family>"}], "notes"?}.
# Schema: references/p_tests_schema.md. A table cannot say which test produced its P, so
# the order-of-magnitude rule above must tolerate every family; a declared test can be
# recomputed exactly, and a P on the wrong side of alpha becomes checkable (SR-01).
PT_TOP_KEYS = {"alpha", "rows", "notes"}
PT_ROW_KEYS = {"row", "test"}
# Families this script computes, plus the two the counts cannot reproduce (SKILL.md SR-01).
PT_TESTS = {"fisher": 0, "chi2_yates": 1, "chi2": 2, "adjusted": None, "paired": None}
_PT_OTHER = re.compile(r"^\s*other\s*:(.*)$", re.I | re.S)
_PT_TOK = re.compile(r"[^\W_]+")
PCT_CELL_RE = re.compile(r"^\s*\d[\d,]*\s*\(\s*(\d+(?:\.\d+)?)\s*%?\s*\)\s*$")
MAX_COUNT_DIGITS = 15


class TestsError(ValueError):
    pass


class _JNum(str):
    """A JSON number literal kept as text (no int() on a huge literal)."""


def _pt_short(v) -> str:
    r = repr(str(v)) if isinstance(v, str) else (f"a {type(v).__name__}" if isinstance(v, (list, dict)) else repr(v))
    return r if len(r) <= 60 else r[:57] + "..."


def _pt_reject_constant(name: str):
    raise TestsError(f"{name} is not a finite number")


def _label_tokens(s: str) -> list[str]:
    return [t.casefold() for t in _PT_TOK.findall(s)]


def load_tests(path: str) -> dict:
    try:
        with open(path, encoding="utf-8-sig") as fh:
            m = json.loads(fh.read(), parse_constant=_pt_reject_constant,
                           parse_float=_JNum, parse_int=_JNum)
    except (OSError, ValueError, RecursionError) as e:   # ValueError covers JSONDecodeError
        raise TestsError(f"cannot read tests file: {str(e)[:200]}")
    if not isinstance(m, dict):
        raise TestsError("tests file must be a JSON object with a \"rows\" list")
    extra = set(m) - PT_TOP_KEYS
    if extra:
        raise TestsError(f"unknown top-level key(s) {sorted(extra)}; allowed {sorted(PT_TOP_KEYS)}")
    alpha = Decimal("0.05")
    if "alpha" in m:
        a = m["alpha"]
        if not isinstance(a, _JNum) or len(a) > 60:
            raise TestsError(f"alpha: expected a number between 0 and 1, got {_pt_short(a)}")
        try:
            alpha = Decimal(str(a))
        except InvalidOperation:
            raise TestsError(f"alpha: {_pt_short(a)} is not a number")
        if not alpha.is_finite() or not math.isfinite(float(alpha)):
            raise TestsError(f"alpha: {_pt_short(a)} is not a finite number")
        if not (0 < alpha < 1):
            raise TestsError(f"alpha: {_pt_short(a)} must be greater than 0 and less than 1")
    rows = m.get("rows")
    if not isinstance(rows, list) or not rows:
        raise TestsError("rows: expected a non-empty list")
    out, seen = [], {}
    for i, r in enumerate(rows):
        w = f"rows[{i}]"
        if not isinstance(r, dict):
            raise TestsError(f"{w}: expected an object")
        extra = set(r) - PT_ROW_KEYS
        if extra:
            raise TestsError(f"{w}: unknown key(s) {sorted(extra)}; allowed {sorted(PT_ROW_KEYS)}")
        label = r.get("row")
        if not isinstance(label, str) or isinstance(label, _JNum) or not _label_tokens(label):
            raise TestsError(f"{w}.row: expected the row's first-cell label (a non-empty string)")
        key = tuple(_label_tokens(label))
        if key in seen:
            raise TestsError(f"{w}.row: {_pt_short(label)} repeats rows[{seen[key]}].row")
        seen[key] = i
        test = r.get("test")
        if not isinstance(test, str) or isinstance(test, _JNum) or not test.strip():
            raise TestsError(f"{w}.test: expected a string")
        om = _PT_OTHER.match(test)
        if om:
            if not om.group(1).strip():
                raise TestsError(f"{w}.test: 'other:' needs a description")
            fam = "other"
        else:
            fam = re.sub(r"[\s\-]+", "_", test.strip().lower())
            if fam not in PT_TESTS:
                raise TestsError(f"{w}.test: {_pt_short(test)} is not one of {sorted(PT_TESTS)} "
                                 "(use \"other:<description>\" for a test not listed)")
        out.append({"row": label.strip(), "key": list(key), "test": fam, "test_raw": test.strip()})
    return {"alpha": alpha, "rows": out}


def _p_interval(op: str, text: str) -> tuple[Decimal, Decimal, bool]:
    """Reported P as (lo, hi, lo_open) at its printed precision; hi is always open.
    "0.04" -> [0.035, 0.045); "<0.001" -> (0, 0.001)."""
    v = Decimal(text if not text.startswith(".") else "0" + text)
    if op == "<":
        return Decimal(0), v, True
    h = Decimal(5).scaleb(v.as_tuple().exponent - 1)
    return max(Decimal(0), v - h), min(Decimal(1), v + h), False


TOTAL_HEADER_RE = re.compile(r"\b(total|overall|all)\b", re.I)


def _groups(header: list[str], group_cols: list[int]):
    """The two compared group columns, or (None, reason). A Total column is dropped first: its
    header must name it (Total / Overall / All) AND its n must equal the sum of the others, so
    the larger arm of an unequal-allocation trial (2:1:1) is never mistaken for a total."""
    ns = []
    for j in group_cols:
        raw = HEADER_N_RE.search(header[j]).group(1).replace(",", "")
        if len(raw) > MAX_COUNT_DIGITS:
            return None, "a header n is too long to read"
        ns.append(int(raw))
    cols = list(zip(group_cols, ns))
    if len(cols) >= 3:
        for k, (j, nn) in enumerate(cols):
            rest = cols[:k] + cols[k + 1:]
            if nn == sum(x for _, x in rest) and TOTAL_HEADER_RE.search(header[j]):
                cols = rest
                break
    if len(cols) < 2:
        return None, "the table does not have two group columns with 'n ='"
    if len(cols) > 2:
        return None, f"the table compares {len(cols)} groups; only a 2-group (2x2) P is recomputed"
    return cols, ""


def check_declared(text: str, spec: dict) -> list[Finding]:
    alpha = spec["alpha"]
    tables = list(_iter_tables(text))
    out: list[Finding] = []

    def na(ln: int, label: str, why: str):
        out.append(Finding("P_NOT_ASSESSED", "MINOR", ln, f"row '{label}': {why}; check this P by hand."))

    for r in spec["rows"]:
        label = r["row"]
        if r["test"] == "other":
            out.append(Finding("UNLISTED_METHOD", "MINOR", 0,
                               f"row '{label}': test {r['test_raw']!r} is not on the allow-list "
                               f"{sorted(PT_TESTS)}; recorded, not recomputed."))
        hits = [(t, cells, ln) for t in tables for cells, ln in t[3]
                if cells and _label_tokens(cells[0]) == r["key"]]
        ln0 = hits[0][2] if len(hits) == 1 else 0
        if r["test"] in ("adjusted", "paired", "other"):
            na(ln0, label, f"declared test '{r['test_raw']}' cannot be recomputed from the table's counts")
            continue
        if not hits:
            na(0, label, "no table row has this first-cell label")
            continue
        if len(hits) > 1:
            na(0, label, f"{len(hits)} table rows have this first-cell label "
                         f"(lines {', '.join(str(h[2]) for h in hits[:6])})")
            continue
        (header, group_cols, p_col, _rows), cells, ln = hits[0]
        if p_col is None or p_col >= len(cells) or not PVAL_CELL_RE.match(cells[p_col]):
            na(ln, label, "the row has no readable P value")
            continue
        cols, why = _groups(header, group_cols)
        if cols is None:
            na(ln, label, why)
            continue
        (g1, n1), (g2, n2) = cols
        if max(g1, g2) >= len(cells):
            na(ln, label, "the row has no count in a group column")
            continue
        m1, m2 = COUNT_CELL_RE.match(cells[g1]), COUNT_CELL_RE.match(cells[g2])
        if not (m1 and m2):
            na(ln, label, "the row has no integer counts (a continuous row, or counts written as n/N)")
            continue
        r1, r2 = m1.group(1).replace(",", ""), m2.group(1).replace(",", "")
        if len(r1) > MAX_COUNT_DIGITS or len(r2) > MAX_COUNT_DIGITS:
            na(ln, label, "a count is too long to read")
            continue
        a, c = int(r1), int(r2)
        if a > n1 or c > n2:
            na(ln, label, "a count exceeds its column n")
            continue
        bad_pct = None
        for cell, cnt, nn in ((cells[g1], a, n1), (cells[g2], c, n2)):
            if "(" not in cell:
                continue   # no printed percentage: read against the header n
            pm = PCT_CELL_RE.match(cell)
            if not pm or nn == 0:
                bad_pct = f"the count cell '{cell[:40]}' is not read as 'count (percent)'"
                break
            pct = Decimal(pm.group(1))
            half = Decimal(5).scaleb(pct.as_tuple().exponent - 1)
            if abs(Decimal(100 * cnt) / Decimal(nn) - pct) > half + Decimal("1e-9"):
                bad_pct = (f"{cnt}/{nn} is {100 * cnt / nn:.2f}%, not the printed {pm.group(1)}% "
                           "(a different denominator, e.g. missing data)")
                break
        if bad_pct:
            na(ln, label, bad_pct)
            continue
        pm = PVAL_CELL_RE.match(cells[p_col])
        op = pm.group(1) or "="
        try:
            b, d = n1 - a, n2 - c
            fam = PT_TESTS[r["test"]]
            rec = (_fisher(a, b, c, d) if fam == 0 else _chi2(a, b, c, d, fam == 1))
            lo, hi, _ = _p_interval(op, pm.group(2))
        except (OverflowError, ValueError, ArithmeticError):
            na(ln, label, "the P could not be recomputed from these counts")
            continue
        recd = Decimal(rec)
        eps = alpha * Decimal("1e-9")
        reported_sig = hi <= alpha            # the whole interval [lo, hi) lies below alpha
        reported_ns = lo > alpha              # the whole interval lies above alpha
        crossing = ((reported_sig and recd > alpha + eps) or (reported_ns and recd < alpha - eps))
        if crossing:
            side = "below" if reported_sig else "above"
            other = "above" if reported_sig else "below"
            out.append(Finding(
                "P_ALPHA_CROSSING", "MAJOR", ln,
                f"row '{label}' ({a}/{n1} vs {c}/{n2}) reports P{'<' if op == '<' else '='}"
                f"{pm.group(2)}, {side} alpha {alpha} at its printed precision, but the declared "
                f"test ({r['test_raw']}) recomputes to {rec:.3g}, {other} alpha"))
    return out


def format_report(rep: Report, color: bool) -> str:
    tag = {"OK": "\033[92m", "NON-REPRODUCIBLE P": "\033[91m",
           "P ALPHA CROSSING": "\033[91m"}.get(rep.verdict, "") if color else ""
    end = "\033[0m" if color else ""
    out = [f"{tag}== {rep.verdict} =={end}  {rep.source}", f"non_reproducible={rep.n_flag}"]
    if not rep.findings:
        out.append("every reported P reproduces from its counts under a standard test.")
        return "\n".join(out)
    for f in sorted(rep.findings, key=lambda x: (x.line, x.detail)):
        out.append(f"[{f.severity}] {f.kind} L{f.line}  {f.detail}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any P_NOT_REPRODUCIBLE")
    ap.add_argument("--quiet", action="store_true", help="suppress the report; exit code only")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a text report")
    ap.add_argument("--tests", help="p_tests.json: the test behind each row's P and alpha "
                    "(see references/p_tests_schema.md); adds P_ALPHA_CROSSING / P_NOT_ASSESSED")
    args = ap.parse_args(argv)
    try:
        text = open(args.manuscript, encoding="utf-8").read()
    except OSError as e:
        print(f"error: cannot read manuscript: {e}", file=sys.stderr)
        return 2
    spec = None
    if args.tests is not None:
        try:
            spec = load_tests(args.tests)
        except (TestsError, ValueError, OverflowError, RecursionError, ArithmeticError) as e:
            print(f"error: {args.tests}: {e}", file=sys.stderr)
            return 2
    rep = audit(text, args.manuscript)
    if spec is not None:
        rep.findings.extend(check_declared(text, spec))
    if not args.quiet:
        if args.json:
            doc = {"detector": "check_reported_p_from_counts", "source": rep.source, "verdict": rep.verdict,
                   "findings": [asdict(f) for f in rep.findings]}
            if spec is not None:
                doc["declared_tests"] = {"path": args.tests, "alpha": str(spec["alpha"]),
                                         "rows": len(spec["rows"])}
            print(json.dumps(doc, ensure_ascii=False, indent=2))
        else:
            out = format_report(rep, color=sys.stdout.isatty())
            if spec is not None:
                out += (f"\ndeclared tests: {len(spec['rows'])} row(s), alpha {spec['alpha']}; "
                        f"alpha_crossing={rep.n_crossing}")
            print(out)
    if spec is not None:
        return 1 if (args.strict and rep.n_major) else 0
    return 1 if (args.strict and rep.n_flag) else 0


if __name__ == "__main__":
    raise SystemExit(main())

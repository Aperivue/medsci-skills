#!/usr/bin/env python3
"""check_test_statistic_p.py — recompute the P value of each reported test statistic from the
statistic and its degrees of freedom, and check declared means for GRIM consistency.

A results sentence such as ``t(48) = 2.10, P = .041`` or ``χ2(2, N = 120) = 7.4, P = .02``
carries everything needed to recompute its own P. A P that the printed statistic cannot
produce is a transcription or analysis error a reviewer can find with a calculator; one that
lands on the other side of alpha changes the conclusion.

Text mode (--manuscript). In each sentence the detector finds
  t(df) = x,  F(df1, df2) = x,  χ2 / χ² / chi2 / X2 (df) = x  (also "χ2 (df, N = n) = x"
  and "χ2 = x, df = d"),  z = x  (only when the P follows it directly, "z = 2.31, P = .021"
  or "z = 2.31 (P = .021)"); markdown emphasis on the symbol (*t*, *P*) is ignored,
and pairs each with the first P after it (``P =``, ``P <``, ``P >``, ``≤``, ``≥``; P or p;
"·" as a decimal mark; ``2.1 × 10^-5`` / ``2.1e-5``) before the next statistic in the same
sentence, never across a ")" that closes a parenthesis opened before the statistic. A
statistic written with a thousands separator, a decimal comma or an exponent ("1,024.3",
"2,10", "1e5"), a P with a decimal comma, a P labelled as from another method between the
statistic and the P (Fisher, exact, permutation, bootstrap, Monte Carlo) and a df above 10^7
are not recomputed (P_STAT_NOT_ASSESSED). The two-sided P is recomputed (t two-sided, F and χ2 upper tail, z two-sided) with
a pure-Python regularized incomplete beta / gamma function.

Rounding is honoured on both sides. A reported ``P = 0.041`` stands for [0.0405, 0.0415];
``P < 0.001`` for [0, 0.001]; ``P > 0.05`` for [0.05, 1]. A statistic printed with k
decimals stands for [x - 0.5·10^-k, x + 0.5·10^-k] (a decimal df likewise). A result is
inconsistent only when NO statistic in its interval gives a P inside the reported P's
interval.

  P_STAT_INCONSISTENT     Minor  the reported P cannot come from the printed statistic.
  P_STAT_DECISION_ERROR   Major  inconsistent AND the whole recomputed-P range and the whole
                                 reported-P range lie on opposite sides of alpha (--alpha,
                                 default 0.05). Replaces the Minor for that result.
  P_STAT_NOT_ASSESSED     Minor  a statistic without a P in its sentence, a P the functions
                                 could not recompute, or a manuscript with no statistic at all.

Sidedness. When the sentence says one-sided / one-tailed (and not two-sided), a t or z result
is compared against the one-sided P (half the two-sided P). A result that matches only the
one-sided P without saying so, a sentence that names both, a one-sided F or χ2, or any
manuscript that mentions one-sided tests elsewhere, is never Major: an inconsistency there is
the Minor. A sentence that mentions an adjusted / corrected P (Bonferroni, Holm, FDR, Tukey,
Šidák, "adjusted", "corrected") or a method whose P differs from the textbook distribution of
the printed statistic (Greenhouse-Geisser, Huynh-Feldt, ε, exact, permutation, bootstrap,
Monte Carlo, Welch, robust, sandwich, Satterthwaite, Kenward) is likewise never Major, and so
is a P separated from its statistic by a semicolon.

Declared GRIM (--grim grim.json). A list of {"label", "mean", "n", "items"?, "decimals"?}:
a mean of n responses to `items` integer-valued items (default 1), printed with `decimals`
decimals (default: the decimals written in "mean"). The mean times n·items must be reachable
by an integer sum given the rounding.
  GRIM_INCONSISTENT       Major  no integer sum gives the mean at its printed precision.
  GRIM_NOT_ASSESSED       Minor  n·items >= 10^decimals: every mean is reachable, so the
                                 test has no power for this entry.

Stdlib-only. Reads its inputs, never writes them.

Usage:
  python3 check_test_statistic_p.py [--manuscript paper.md] [--grim grim.json]
                                    [--alpha 0.05] [--strict] [--quiet] [--json]
At least one of --manuscript / --grim is required.
Exit: 0 run completed (report-only, or --strict with no Major); 1 --strict and a Major claim;
2 input or usage error (the message names the field), or --strict with verdict NOT_ASSESSED.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _frontmatter import strip_frontmatter  # noqa: E402  (same-directory helper)

DETECTOR = "check_test_statistic_p"

# --- special functions (pure Python) ----------------------------------------------------

_EPS = 1e-15
_FPMIN = 1e-300
_MAXIT = 20000


class CalcError(ArithmeticError):
    pass


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (modified Lentz)."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < _FPMIN:
        d = _FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, _MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _FPMIN:
            d = _FPMIN
        c = 1.0 + aa / c
        if abs(c) < _FPMIN:
            c = _FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _FPMIN:
            d = _FPMIN
        c = 1.0 + aa / c
        if abs(c) < _FPMIN:
            c = _FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < _EPS:
            return h
    raise CalcError("incomplete beta did not converge")


def betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if not (a > 0 and b > 0) or not (0.0 <= x <= 1.0):
        raise CalcError("incomplete beta outside its domain")
    if x == 0.0 or x == 1.0:
        return x
    lbt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
           + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * _betacf(b, a, 1.0 - x) / b


def gammaincc(a: float, x: float) -> float:
    """Regularized upper incomplete gamma Q(a, x)."""
    if not a > 0 or x < 0:
        raise CalcError("incomplete gamma outside its domain")
    if x == 0.0:
        return 1.0
    lpre = -x + a * math.log(x) - math.lgamma(a)
    if x < a + 1.0:                       # series for P(a, x)
        ap, s = a, 1.0 / a
        dl = s
        for _ in range(_MAXIT):
            ap += 1.0
            dl *= x / ap
            s += dl
            if abs(dl) < abs(s) * _EPS:
                return max(0.0, 1.0 - s * math.exp(lpre))
        raise CalcError("incomplete gamma series did not converge")
    b = x + 1.0 - a                       # continued fraction for Q(a, x)
    c, d = 1.0 / _FPMIN, 1.0 / b
    h = d
    for i in range(1, _MAXIT + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < _FPMIN:
            d = _FPMIN
        c = b + an / c
        if abs(c) < _FPMIN:
            c = _FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < _EPS:
            return math.exp(lpre) * h
    raise CalcError("incomplete gamma continued fraction did not converge")


def p_t(t: float, df: float) -> float:
    """Two-sided P for Student's t."""
    return betainc(df / 2.0, 0.5, df / (df + t * t))


def p_f(f: float, df1: float, df2: float) -> float:
    """Upper-tail P for F."""
    if f <= 0:
        return 1.0
    return betainc(df2 / 2.0, df1 / 2.0, df2 / (df2 + df1 * f))


def p_chi2(x: float, df: float) -> float:
    """Upper-tail P for chi-square."""
    if x <= 0:
        return 1.0
    return gammaincc(df / 2.0, x / 2.0)


def p_z(z: float) -> float:
    """Two-sided P for a standard normal z."""
    return math.erfc(abs(z) / math.sqrt(2.0))


# --- text parsing --------------------------------------------------------------------------

_NUM = r"[-−–]?\s?\d+(?:[.·]\d+)?"
_DF = r"\d+(?:[.·]\d+)?"
# Whatever continues a number past _NUM (a thousands separator "1,024.3", a decimal comma
# "2,10", e-notation "1e5", "1.2 × 10^5"). Captured as the last group so that the statistic is
# never read truncated; a non-empty tail sends the result to P_STAT_NOT_ASSESSED.
_TAIL = r"(?P<tail>(?:[,.·]\d|[eE]\s*[-−–+]?\d|\s*[×x*]\s*10\b(?:\s*\^?\s*[-−–+]?\d+)?)(?:[,.·]?\d)*)?"
_CHI = (r"(?:χ\s*(?:\^\s*)?(?:2|²)|(?<![A-Za-z])chi\s*(?:\^\s*)?(?:2|²)|"
        r"(?<![A-Za-z0-9_])X\s*(?:\^\s*)?(?:2|²)|χ<sup>2</sup>)")
# (kind, regex, order): `order` maps the regex groups (tail excluded) to [df..., statistic].
STAT_RES = (
    ("t", re.compile(r"(?<![A-Za-z0-9_])t\s*\(\s*(" + _DF + r")\s*\)\s*=\s*(" + _NUM + r")" + _TAIL),
     None),
    ("F", re.compile(r"(?<![A-Za-z0-9_])F\s*\(\s*(" + _DF + r")\s*,\s*(" + _DF + r")\s*\)\s*=\s*("
                     + _NUM + r")" + _TAIL), None),
    ("chi2", re.compile(_CHI + r"\s*\(\s*(" + _DF + r")\s*(?:,\s*[Nn]\s*=\s*[\d,]+\s*)?\)\s*=\s*("
                        + _NUM + r")" + _TAIL, re.I), None),
    # "χ2 = 5.2, df = 1": the df written after the statistic
    ("chi2", re.compile(_CHI + r"\s*=\s*(" + _NUM + r")" + _TAIL
                        + r"\s*[,;]\s*(?:df|d\.f\.)\s*=\s*(\d+)(?![\d]|[.,·]\d)", re.I), (1, 0)),
    ("z", re.compile(r"(?<![A-Za-z0-9_\-])[zZ]\s*=\s*(" + _NUM + r")" + _TAIL), None),
)
_MANT = r"(\d*[.·]?\d+)"
_EXP = (r"(?:\s*[×x*]\s*10\s*(?:\^|<sup>)?\s*\(?\s*([-−–]\s?\d+)\s*\)?(?:</sup>)?"
        r"|[eE]\s*([-−–+]?\d+))?")
# group 5: a decimal comma ("P < 0,001"), which would otherwise be read as P < 0
P_RE = re.compile(r"(?<![A-Za-z0-9_])[Pp](?:\s*[-‐‑]?\s*value)?\s*(<=|>=|≤|≥|=|<|>)\s*"
                  + _MANT + _EXP + r"(,\d+)?")
# Markdown emphasis around a one-letter symbol: *t*(48), _P_ = .04, **F**(2, 96)
EMPH_RE = re.compile(r"(?<![\w*])(\*{1,2}|_{1,2})([tFzZpPχX])\1(?![\w*])")
ONE_SIDED_RE = re.compile(r"\bone[\s-]*(?:sided|tailed)\b", re.I)
TWO_SIDED_RE = re.compile(r"\btwo[\s-]*(?:sided|tailed)\b", re.I)
# A P that is adjusted, corrected, or from a method whose P legitimately differs from the
# textbook distribution of the printed statistic: never Major.
ADJUSTED_RE = re.compile(r"\b(?:adjusted|corrected|bonferroni|holm|fdr|false discovery|tukey|"
                         r"[sš]id[aá]k|benjamini|greenhouse|geisser|huynh|feldt|ε|exact|"
                         r"permutation|bootstrap\w*|monte[\s-]*carlo|welch|robust|sandwich|"
                         r"satterthwaite|kenward)\b", re.I)
# A P labelled as coming from another test, between the statistic and the P
OTHER_TEST_P_RE = re.compile(r"\b(?:fisher|exact|permutation|bootstrap\w*|monte[\s-]*carlo)\b", re.I)
MAX_DF = Decimal(10) ** 7
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[(])|\n\s*\n|\n(?=\s*(?:[-*+]|\d+\.|#|\|)\s)")
MAX_GAP = 120


def _num(s: str) -> str:
    return re.sub(r"\s", "", s).replace("·", ".").replace("−", "-").replace("–", "-")


def _interval(text: str) -> tuple[Decimal, Decimal, int]:
    """A printed number as [v - h, v + h] with h half a unit in its last printed place."""
    v = Decimal(text)
    h = Decimal(5).scaleb(v.as_tuple().exponent - 1)
    return v - h, v + h, -v.as_tuple().exponent


def _p_reported(op: str, mant: str, e1: str | None, e2: str | None):
    """Reported P as (lo, hi, value-as-printed) or None when it is not a probability."""
    m = Decimal(_num(mant) if not _num(mant).startswith(".") else "0" + _num(mant))
    exp_s = e1 or e2
    scale = Decimal(1)
    if exp_s:
        ex = int(_num(exp_s).replace("+", ""))
        if abs(ex) > 400:
            return None
        scale = Decimal(10) ** ex
    v = m * scale
    if not (0 <= v <= 1):
        return None
    if op in ("<", "<=", "≤"):
        return Decimal(0), v, v
    if op in (">", ">=", "≥"):
        return v, Decimal(1), v
    h = Decimal(5).scaleb(m.as_tuple().exponent - 1) * scale
    return max(Decimal(0), v - h), min(Decimal(1), v + h), v


def _sentences(text: str):
    """Yield (start offset, sentence text)."""
    pos = 0
    for m in SENT_SPLIT_RE.finditer(text):
        yield pos, text[pos:m.start()]
        pos = m.end()
    yield pos, text[pos:]


def _p_range(kind: str, args: list[str]) -> tuple[float, float]:
    """Min and max two-sided P over the rounding intervals of the statistic and its df."""
    stat_lo, stat_hi, _ = _interval(args[-1])
    dfs = [_interval(a) if "." in a else (Decimal(a), Decimal(a), 0) for a in args[:-1]]
    for lo, _hi, _k in dfs:
        if lo <= 0:
            raise CalcError("degrees of freedom must be positive")
        if _hi > MAX_DF:
            raise CalcError("degrees of freedom above 10^7 exceed floating-point precision")
    if kind in ("t", "z"):
        if stat_lo <= 0 <= stat_hi:
            a_lo = Decimal(0)
        else:
            a_lo = min(abs(stat_lo), abs(stat_hi))
        a_hi = max(abs(stat_lo), abs(stat_hi))
        stat_pts = (float(a_lo), float(a_hi))
    else:
        stat_pts = (float(max(Decimal(0), stat_lo)), float(stat_hi))
    df_pts = [sorted({float(lo), float((lo + hi) / 2), float(hi)}) for lo, hi, _ in dfs]
    vals = []
    for s in stat_pts:
        if kind == "z":
            vals.append(p_z(s))
        elif kind == "t":
            for d in df_pts[0]:
                vals.append(p_t(s, d))
        elif kind == "chi2":
            for d in df_pts[0]:
                vals.append(p_chi2(s, d))
        else:
            for d1 in df_pts[0]:
                for d2 in df_pts[1]:
                    vals.append(p_f(s, d1, d2))
    if any(not math.isfinite(v) for v in vals):
        raise CalcError("non-finite P")
    return min(vals), max(vals)


def _closes_paren(gap: str) -> bool:
    """True when the gap closes a parenthesis opened before the statistic: the P is in
    another clause."""
    depth = 0
    for ch in gap:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return True
    return False


def _depth0(gap: str) -> str:
    """The gap with nested parenthetical text removed."""
    out, depth = [], 0
    for ch in gap:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def _fmt_stat(kind: str, args: list[str]) -> str:
    if kind == "t":
        return f"t({args[0]}) = {args[1]}"
    if kind == "F":
        return f"F({args[0]}, {args[1]}) = {args[2]}"
    if kind == "chi2":
        return f"χ2({args[0]}) = {args[1]}"
    return f"z = {args[0]}"


def _g(x: float) -> str:
    return f"{x:.3g}" if x >= 1e-3 else f"{x:.2e}"


def check_text(text: str, alpha: Decimal) -> tuple[list[dict], int, int]:
    """Return (claims, n_checked, n_found)."""
    claims: list[dict] = []
    body = strip_frontmatter(text)
    if body != text and text.endswith(body):
        # blank the YAML front matter (status:/changelog: notes are not results) and keep
        # line numbers aligned with the file
        text = "\n" * text[:len(text) - len(body)].count("\n") + body
    elif body != text:
        text = body
    # *t*(48), *P* = .04: drop the emphasis (same line, so line numbers are unchanged)
    text = EMPH_RE.sub(r"\2", text)
    doc_one_sided = bool(ONE_SIDED_RE.search(text))
    line_starts = [0] + [m.end() for m in re.finditer(r"\n", text)]

    def line_of(off: int) -> int:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= off:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    n_checked = n_found = 0
    unpaired: list[str] = []
    unparsed: list[str] = []
    for start, sent in _sentences(text):
        stats = []
        for kind, rx, order in STAT_RES:
            ti = rx.groupindex["tail"]
            for m in rx.finditer(sent):
                gs = [_num(g) for i, g in enumerate(m.groups(), 1) if i != ti]
                if order is not None:
                    gs = [gs[i] for i in order]
                stats.append((m.start(), m.end(), kind, gs, m.group("tail")))
        if not stats:
            continue
        stats.sort()
        ps = list(P_RE.finditer(sent))
        one = bool(ONE_SIDED_RE.search(sent))
        two = bool(TWO_SIDED_RE.search(sent))
        adjusted = ADJUSTED_RE.search(sent)
        for i, (s0, s1, kind, args, tail) in enumerate(stats):
            nxt = stats[i + 1][0] if i + 1 < len(stats) else len(sent)
            pm = next((p for p in ps if s1 <= p.start() < nxt), None)
            gap = ""
            if pm is not None:
                gap = sent[s1:pm.start()]
                if (len(gap) > MAX_GAP or _closes_paren(gap)
                        or (kind == "z" and not re.fullmatch(r"\s*[,;]?\s*\(?\s*", gap))):
                    pm = None
            if kind == "z" and pm is None:
                continue                  # a bare "z = 1.2" is not taken as a test statistic
            n_found += 1
            ln = line_of(start + s0)
            label = _fmt_stat(kind, args)
            if tail:
                unparsed.append(f"L{ln} {label}{tail}")
                continue
            if pm is None:
                unpaired.append(f"L{ln} {label}")
                continue
            rep = _p_reported(pm.group(1), pm.group(2), pm.group(3), pm.group(4))
            ptxt = pm.group(0).strip()
            where = f"L{ln}"
            if pm.group(5):
                claims.append(_claim("P_STAT_NOT_ASSESSED", "Minor", where,
                                     f"{label}, {ptxt}: the P is written with a decimal comma; "
                                     "check it by hand."))
                continue
            other = OTHER_TEST_P_RE.search(gap)
            if other:
                claims.append(_claim("P_STAT_NOT_ASSESSED", "Minor", where,
                                     f"{label}, {ptxt}: the P is labelled as from another method "
                                     f"('{other.group(0)}'), not from the printed statistic; "
                                     "check it by hand."))
                continue
            if rep is None:
                claims.append(_claim("P_STAT_NOT_ASSESSED", "Minor", where,
                                     f"{label}, {ptxt}: the reported P is not a probability; "
                                     "check it by hand."))
                continue
            r_lo, r_hi, _v = rep
            try:
                p_lo, p_hi = _p_range(kind, args)
            except (CalcError, ValueError, OverflowError, ArithmeticError) as e:
                claims.append(_claim("P_STAT_NOT_ASSESSED", "Minor", where,
                                     f"{label}, {ptxt}: P could not be recomputed ({e}); "
                                     "check it by hand."))
                continue
            if p_hi < 1e-290 and r_lo > 0 and r_lo < Decimal("1e-280"):
                claims.append(_claim("P_STAT_NOT_ASSESSED", "Minor", where,
                                     f"{label}, {ptxt}: P is below floating-point range; "
                                     "check it by hand."))
                continue
            one_capable = kind in ("t", "z")
            if one and not two and not one_capable:
                claims.append(_claim("P_STAT_NOT_ASSESSED", "Minor", where,
                                     f"{label}, {ptxt}: the sentence says one-sided, which has no "
                                     f"standard meaning for {'F' if kind == 'F' else 'χ2'}; check it by hand."))
                continue
            n_checked += 1
            dlo, dhi = Decimal(p_lo), Decimal(p_hi)

            def consistent(lo: Decimal, hi: Decimal) -> bool:
                return lo <= r_hi and hi >= r_lo

            sidedness = "two-sided" if one_capable else "upper-tail"
            if one and not two:
                lo_u, hi_u = dlo / 2, dhi / 2
                sidedness = "one-sided (as stated)"
            else:
                lo_u, hi_u = dlo, dhi
            if consistent(lo_u, hi_u):
                continue
            notes = []
            may_major = True
            if sidedness == "two-sided" and one_capable and consistent(dlo / 2, dhi / 2):
                if one and two:
                    continue      # sentence names both sidednesses and one of them matches
                notes.append("it matches the one-sided P; state the sidedness if the test was one-sided")
                may_major = False
            if one and two:
                notes.append("the sentence names both one- and two-sided tests")
                may_major = False
            if doc_one_sided and not one and one_capable:
                notes.append("the manuscript mentions one-sided tests elsewhere")
                may_major = False
            if adjusted:
                notes.append("the sentence mentions an adjusted, corrected or non-standard P "
                             f"('{adjusted.group(0)}'), which differs from the textbook P")
                may_major = False
            if re.search(r";", _depth0(gap)):
                notes.append("a semicolon separates the statistic from the P")
                may_major = False
            rec_sig, rec_ns = hi_u < alpha, lo_u > alpha
            rep_sig, rep_ns = r_hi <= alpha, r_lo >= alpha
            decision = may_major and ((rep_sig and rec_ns) or (rep_ns and rec_sig))
            g_lo, g_hi = _g(float(lo_u)), _g(float(hi_u))
            rng = g_lo if g_lo == g_hi else f"{g_lo}–{g_hi}"
            detail = (f"{label}, {ptxt}: the {sidedness} P recomputes to {rng} over the statistic's "
                      f"rounding interval, outside the reported P at its printed precision")
            if decision:
                detail += (f"; the reported P is {'below' if rep_sig else 'above'} alpha {alpha} and "
                           f"the recomputed P {'above' if rep_sig else 'below'} it")
            if notes:
                detail += " (" + "; ".join(notes) + ")"
            claims.append(_claim("P_STAT_DECISION_ERROR" if decision else "P_STAT_INCONSISTENT",
                                 "Major" if decision else "Minor", where, detail + "."))
    if unpaired:
        claims.append(_claim("P_STAT_NOT_ASSESSED", "Minor", "manuscript",
                             f"{len(unpaired)} test statistic(s) without a P in the same sentence "
                             f"were not checked: {', '.join(unpaired[:8])}"
                             + (", ..." if len(unpaired) > 8 else "") + "."))
    if unparsed:
        claims.append(_claim("P_STAT_NOT_ASSESSED", "Minor", "manuscript",
                             f"{len(unparsed)} test statistic(s) written with a thousands separator, "
                             f"decimal comma or exponent were not checked: {', '.join(unparsed[:8])}"
                             + (", ..." if len(unparsed) > 8 else "") + "."))
    if n_checked == 0 and not unpaired and not unparsed and not any(c["verdict"] == "P_STAT_NOT_ASSESSED" for c in claims):
        claims.append(_claim("P_STAT_NOT_ASSESSED", "Minor", "manuscript",
                             "no test statistic (t(df), F(df1, df2), χ2(df), z) with a P in the same "
                             "sentence was found; nothing was recomputed."))
    return claims, n_checked, n_found


def _claim(code: str, severity: str, where: str, detail: str) -> dict:
    return {"verdict": code, "severity": severity, "where": where, "detail": detail}


# --- declared GRIM -------------------------------------------------------------------------

GRIM_KEYS = {"label", "mean", "n", "items", "decimals"}
MAX_DIGITS = 30


class InputError(ValueError):
    pass


class _JNum(str):
    """A JSON number literal kept as text."""


def _short(v) -> str:
    r = repr(str(v)) if isinstance(v, str) else (f"a {type(v).__name__}" if isinstance(v, (list, dict)) else repr(v))
    return r if len(r) <= 60 else r[:57] + "..."


def _reject_constant(name: str):
    raise InputError(f"{name} is not a finite number")


def _pos_int(v, where: str, minimum: int) -> int:
    if not isinstance(v, _JNum) or not re.fullmatch(r"-?\d+", v) or len(v) > MAX_DIGITS:
        raise InputError(f"{where}: expected an integer >= {minimum}, got {_short(v)}")
    i = int(v)
    if i < minimum:
        raise InputError(f"{where}: expected an integer >= {minimum}, got {i}")
    return i


def load_grim(path: str) -> list[dict]:
    try:
        with open(path, encoding="utf-8-sig") as fh:
            data = json.loads(fh.read(), parse_constant=_reject_constant,
                              parse_float=_JNum, parse_int=_JNum)
    except (OSError, ValueError, RecursionError) as e:
        raise InputError(f"cannot read GRIM file: {str(e)[:200]}")
    if not isinstance(data, list) or not data:
        raise InputError("expected a non-empty JSON list of {\"label\", \"mean\", \"n\", ...} objects")
    out, seen = [], {}
    for i, e in enumerate(data):
        w = f"[{i}]"
        if not isinstance(e, dict):
            raise InputError(f"{w}: expected an object")
        extra = set(e) - GRIM_KEYS
        if extra:
            raise InputError(f"{w}: unknown key(s) {sorted(extra)}; allowed {sorted(GRIM_KEYS)}")
        for k in ("label", "mean", "n"):
            if k not in e:
                raise InputError(f"{w}.{k}: required")
        label = e["label"]
        if not isinstance(label, str) or isinstance(label, _JNum) or not label.strip():
            raise InputError(f"{w}.label: expected a non-empty string")
        key = label.strip().casefold()
        if key in seen:
            raise InputError(f"{w}.label: {_short(label)} repeats [{seen[key]}].label")
        seen[key] = i
        mean = e["mean"]
        if not isinstance(mean, str) or len(mean) > MAX_DIGITS + 2:
            raise InputError(f"{w}.mean: expected a number as printed (e.g. 3.48 or \"3.48\"), "
                             f"got {_short(mean)}")
        mtxt = mean.strip().replace("·", ".")
        if not re.fullmatch(r"-?(?:\d+(?:\.\d*)?|\.\d+)", mtxt):
            raise InputError(f"{w}.mean: {_short(mean)} is not a plain decimal number")
        mdec = Decimal(mtxt if not mtxt.lstrip("-").startswith(".") else mtxt.replace(".", "0.", 1))
        printed = max(0, -mdec.as_tuple().exponent)
        n = _pos_int(e["n"], f"{w}.n", 1)
        items = _pos_int(e["items"], f"{w}.items", 1) if "items" in e else 1
        if "decimals" in e:
            dec = _pos_int(e["decimals"], f"{w}.decimals", 0)
            if dec > 15:
                raise InputError(f"{w}.decimals: {dec} is more than 15")
            if dec < printed:
                raise InputError(f"{w}.decimals: {dec} is fewer than the {printed} decimals "
                                 f"written in mean {mtxt}")
        else:
            dec = printed
            if dec > 15:
                raise InputError(f"{w}.mean: more than 15 decimals")
        out.append({"label": label.strip(), "mean": mdec, "mean_text": mtxt, "n": n,
                    "items": items, "decimals": dec})
    return out


def check_grim(entries: list[dict]) -> tuple[list[dict], int]:
    claims: list[dict] = []
    n_checked = 0
    for e in entries:
        total = e["n"] * e["items"]
        where = f"grim:{e['label']}"
        what = (f"'{e['label']}': mean {e['mean_text']} (as {e['decimals']} decimals) of n = {e['n']}"
                + (f" × {e['items']} items" if e["items"] != 1 else ""))
        if total >= 10 ** e["decimals"]:
            claims.append(_claim("GRIM_NOT_ASSESSED", "Minor", where,
                                 f"{what}: n·items = {total} >= 10^{e['decimals']}, so every mean at "
                                 "this precision is reachable; GRIM cannot test it."))
            continue
        n_checked += 1
        m = Fraction(e["mean"])
        h = Fraction(1, 2 * 10 ** e["decimals"])
        lo, hi = (m - h) * total, (m + h) * total
        s_lo, s_hi = math.ceil(lo), math.floor(hi)
        if s_lo > s_hi:
            near = [s for s in (s_hi, s_lo)]
            alt = ", ".join(f"{s}/{total} = {float(Fraction(s, total)):.{e['decimals'] + 2}f}" for s in near)
            claims.append(_claim("GRIM_INCONSISTENT", "Major", where,
                                 f"{what}: no integer sum over {total} responses gives this mean at "
                                 f"its printed precision (nearest: {alt})."))
    return claims, n_checked


# --- driver --------------------------------------------------------------------------------

def run(manuscript: str | None, text: str | None, grim_path: str | None,
        grim: list[dict] | None, alpha: Decimal) -> dict:
    claims: list[dict] = []
    n_text = n_found = n_grim = 0
    if text is not None:
        c, n_text, n_found = check_text(text, alpha)
        claims += c
    if grim is not None:
        c, n_grim = check_grim(grim)
        claims += c
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    n_minor = len(claims) - n_major
    if n_major:
        verdict = "MAJOR_CANDIDATE"
    elif n_text + n_grim == 0:
        verdict = "NOT_ASSESSED"
    else:
        verdict = "OK"
    basis = ("declared" if text is None else "manuscript+declared" if grim is not None else "manuscript")
    return {"detector": DETECTOR, "source": manuscript, "grim": grim_path, "basis": basis,
            "alpha": str(alpha), "claims": claims,
            "summary": {"n_statistics_found": n_found, "n_statistics_checked": n_text,
                        "n_grim_checked": n_grim, "n_major": n_major, "n_minor": n_minor,
                        "verdict": verdict}}


def render(res: dict) -> str:
    s = res["summary"]
    out = ["== Test statistic vs P (self-review) ==",
           f"source: {res['source'] or '-'}  grim: {res['grim'] or '-'}  alpha: {res['alpha']}",
           f"statistics found: {s['n_statistics_found']}  recomputed: {s['n_statistics_checked']}  "
           f"GRIM entries checked: {s['n_grim_checked']}"]
    for c in res["claims"]:
        out.append(f"[{c['severity']}] {c['verdict']} {c['where']}  {c['detail']}")
    tag = " (as declared)" if res["basis"] == "declared" else ""
    if s["verdict"] == "MAJOR_CANDIDATE":
        out.append(f"MAJOR candidate: {s['n_major']} Major, {s['n_minor']} Minor.")
    elif s["verdict"] == "NOT_ASSESSED":
        out.append("NOT ASSESSED: no test statistic with a P in the same sentence and no GRIM entry with "
                   "power; write results as t(df) = x, P = y, or declare means with --grim.")
    elif s["n_minor"]:
        out.append(f"No Major issue{tag}: {s['n_minor']} Minor (see above).")
    else:
        out.append(f"OK{tag}: every recomputed P and declared mean is consistent at its printed precision.")
    return "\n".join(out)


def _parse_alpha(s: str) -> Decimal:
    try:
        a = Decimal(s)
    except InvalidOperation:
        raise InputError(f"--alpha: {_short(s)} is not a number")
    if not a.is_finite() or not (0 < a < 1):
        raise InputError(f"--alpha: {_short(s)} must be greater than 0 and less than 1")
    return a


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manuscript", help="manuscript markdown/text")
    ap.add_argument("--grim", help="grim.json: declared means to test for GRIM consistency")
    ap.add_argument("--alpha", default="0.05", help="significance level (default 0.05)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on a Major claim; exit 2 when nothing could be assessed")
    ap.add_argument("--quiet", action="store_true", help="suppress the report; exit code only")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a text report")
    args = ap.parse_args(argv)
    if args.manuscript is None and args.grim is None:
        print("error: pass --manuscript, --grim, or both", file=sys.stderr)
        return 2
    try:
        alpha = _parse_alpha(args.alpha)
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    text = None
    if args.manuscript is not None:
        try:
            with open(args.manuscript, encoding="utf-8-sig") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError) as e:
            print(f"error: cannot read manuscript: {e}", file=sys.stderr)
            return 2
    grim = None
    if args.grim is not None:
        try:
            grim = load_grim(args.grim)
        except (InputError, ValueError, OverflowError, RecursionError, ArithmeticError) as e:
            print(f"error: {args.grim}: {e}", file=sys.stderr)
            return 2
    res = run(args.manuscript, text, args.grim, grim, alpha)
    if not args.quiet:
        print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else render(res))
    v = res["summary"]["verdict"]
    if args.strict and v == "MAJOR_CANDIDATE":
        return 1
    if args.strict and v == "NOT_ASSESSED":
        print("error: --strict and nothing could be assessed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

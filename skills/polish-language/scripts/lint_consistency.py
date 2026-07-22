#!/usr/bin/env python3
"""
Deterministic consistency linter for medical manuscripts (polish-language).

Flags mechanical, style-guide-level inconsistencies that copy-editors catch and
that AI-tell removal (`/humanize`) deliberately does NOT touch:

  1. Abbreviations   — defined-once, used-before-defined, defined-but-unused,
                       used-but-never-defined
  2. Spelling        — mixed US/UK variants (analyze/analyse, tumor/tumour, …)
  3. Numeric ranges  — hyphen between numbers where an en-dash belongs (5-10)
  4. p-values        — mixed P/p case; impossible "P = 0.000"
  5. Hyphenation     — variant forms of the same term (follow-up/followup/…)
  6. Small numbers   — single digits 1–9 written as digits in prose
  7. Units           — missing space between value and unit (5mg)

It NEVER rewrites text, changes numbers, edits citations, or judges scientific
content — it only reports. All output is deterministic (stable ordering), so it
doubles as a reproducible challenge-card verifier.

Usage:
    python3 lint_consistency.py manuscript.md
    python3 lint_consistency.py manuscript.md --strict   # exit 1 if any issue
"""

import argparse
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Config (fixed, deterministic)
# --------------------------------------------------------------------------- #
# Abbreviations so ubiquitous they need no in-text definition.
ABBR_WHITELIST = {
    "AI", "DNA", "RNA", "USA", "UK", "EU", "WHO", "FDA", "HIV", "AIDS",
    "ID", "OK", "PDF", "URL", "HTML", "API", "AND", "OR", "NOT", "ROC",
}

# US ↔ UK spelling families: canonical "us" form -> regex matching both.
SPELLING_FAMILIES = [
    ("analyze", r"\banalys[ei]([sdz]|zing|sing|zed|sed)?\b", r"analy(s)"),
    ("organize", r"\borganis[ei]?\w*\b", r"organis"),
    ("characterize", r"\bcharacteris\w*\b", r"characteris"),
    ("optimize", r"\boptimis\w*\b", r"optimis"),
    ("randomize", r"\brandomis\w*\b", r"randomis"),
    ("standardize", r"\bstandardis\w*\b", r"standardis"),
    ("tumor", r"\btumour(s)?\b", r"tumour"),
    ("color", r"\bcolour(s|ed|ing)?\b", r"colour"),
    ("behavior", r"\bbehaviour(s|al)?\b", r"behaviour"),
    ("favor", r"\bfavour(s|ed|able)?\b", r"favour"),
    ("center", r"\bcentre(s|d)?\b", r"centre"),
    ("labeled", r"\blabelled\b", r"labelled"),
    ("modeling", r"\bmodelling\b", r"modelling"),
    ("fetal", r"\bfoetal\b", r"foetal"),
]
# For each family we also need the US-variant regex to count it.
SPELLING_US = {
    "analyze": r"\banaly(z|ze|zed|zing|zes)\w*\b",
    "organize": r"\borganiz\w*\b",
    "characterize": r"\bcharacteriz\w*\b",
    "optimize": r"\boptimiz\w*\b",
    "randomize": r"\brandomiz\w*\b",
    "standardize": r"\bstandardiz\w*\b",
    "tumor": r"\btumor(s)?\b",
    "color": r"\bcolor(s|ed|ing)?\b",
    "behavior": r"\bbehavior(s|al)?\b",
    "favor": r"\bfavor(s|ed|able)?\b",
    "center": r"\bcenter(s|ed)?\b",
    "labeled": r"\blabeled\b",
    "modeling": r"\bmodeling\b",
    "fetal": r"\bfetal\b",
}

# Hyphenation/terminology variant families (all lowercase match, word-ish).
HYPHEN_FAMILIES = [
    ("follow-up", [r"\bfollow-up\b", r"\bfollowup\b", r"\bfollow up\b"]),
    ("health care", [r"\bhealthcare\b", r"\bhealth care\b", r"\bhealth-care\b"]),
    ("long-term", [r"\blong-term\b", r"\blongterm\b", r"\blong term\b"]),
    ("well-being", [r"\bwell-being\b", r"\bwellbeing\b"]),
    ("decision-making", [r"\bdecision-making\b", r"\bdecision making\b"]),
    ("COVID-19", [r"\bCOVID-19\b", r"\bCOVID19\b", r"\bCovid-19\b"]),
]

UNIT_TOKENS = (
    "mg", "kg", "mL", "ml", "mm", "cm", "mcg", "ug", "mmHg", "mGy", "mSv",
    "mmol", "mol", "IU", "mGy", "Gy", "Sv", "Hz", "kPa",
)
UNIT_RE = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)(" + "|".join(sorted(UNIT_TOKENS, key=len, reverse=True)) + r")(?![\w])"
)

ABBR_DEF_RE = re.compile(r"\(([A-Z][A-Z0-9]{1,5})\)")            # (CT), (MRI), (DKA), (COVID)
ABBR_USE_RE = re.compile(r"(?<![A-Za-z])([A-Z]{2,6})(?![A-Za-z])")  # standalone caps token
NUM_RANGE_RE = re.compile(r"(?<![\w/.\-])(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)(?![\w/.\-])")
PVAL_RE = re.compile(r"(?<![A-Za-z])([Pp])\s*([=<>])\s*(0?\.\d+|\d+\.\d+|\.\d+)")
SMALL_NUM_RE = re.compile(r"(?<![\w.=<>+\-/])([1-9])\s+([a-z]{3,})")


# --------------------------------------------------------------------------- #
# Checks (each returns list[(line, message)])
# --------------------------------------------------------------------------- #
def check_abbreviations(lines):
    out = []
    defs = {}          # abbr -> first definition line
    uses = {}          # abbr -> list of (line) excluding the def-parenthesis line
    def_lines = {}     # abbr -> set of lines where defined
    for i, line in enumerate(lines, 1):
        for m in ABBR_DEF_RE.finditer(line):
            ab = m.group(1)
            defs.setdefault(ab, i)
            def_lines.setdefault(ab, set()).add(i)
    for i, line in enumerate(lines, 1):
        # mask the "(ABBR)" definition spans so they don't count as bare uses
        masked = ABBR_DEF_RE.sub(lambda m: " " * len(m.group(0)), line)
        for m in ABBR_USE_RE.finditer(masked):
            ab = m.group(1)
            uses.setdefault(ab, []).append(i)

    all_abbr = set(defs) | {a for a in uses}
    for ab in sorted(all_abbr):
        if ab in ABBR_WHITELIST:
            continue
        u = uses.get(ab, [])
        d = defs.get(ab)
        if d is None:
            if len(u) >= 2:
                out.append((min(u), f'"{ab}" used {len(u)}x but never defined'))
            continue
        if len(def_lines.get(ab, set())) > 1:
            out.append((sorted(def_lines[ab])[1], f'"{ab}" defined more than once'))
        before = [ln for ln in u if ln < d]
        if before:
            out.append((min(before), f'"{ab}" used before its definition (defined L{d})'))
        if not u:
            out.append((d, f'"{ab}" defined but never used'))
    return out


def check_spelling(lines):
    out = []
    text = "\n".join(lines)
    us_total = 0
    uk_total = 0
    fam_hits = []  # (line, msg, side)
    for us_form, uk_re, _ in SPELLING_FAMILIES:
        us_re = SPELLING_US[us_form]
        uk_count = len(re.findall(uk_re, text, re.I))
        us_count = len(re.findall(us_re, text, re.I))
        us_total += us_count
        uk_total += uk_count
        for i, line in enumerate(lines, 1):
            for _m in re.finditer(uk_re, line, re.I):
                fam_hits.append((i, f'"{us_form}" family: UK spelling here', "uk"))
            for _m in re.finditer(us_re, line, re.I):
                fam_hits.append((i, f'"{us_form}" family: US spelling here', "us"))
    if us_total == 0 and uk_total == 0:
        return out
    dominant = "US" if us_total >= uk_total else "UK"
    minority = "uk" if dominant == "US" else "us"
    for line, msg, side in fam_hits:
        if side == minority:
            out.append((line, f"{msg} (document is predominantly {dominant})"))
    return out, dominant, us_total, uk_total


def check_numeric_ranges(lines):
    out = []
    for i, line in enumerate(lines, 1):
        for m in NUM_RANGE_RE.finditer(line):
            out.append((i, f'"{m.group(0)}" — use en-dash for numeric range ({m.group(1)}–{m.group(2)})'))
    return out


def check_pvalues(lines):
    out = []
    cap = low = 0
    hits = []
    for i, line in enumerate(lines, 1):
        for m in PVAL_RE.finditer(line):
            letter, op, val = m.group(1), m.group(2), m.group(3)
            if letter == "P":
                cap += 1
            else:
                low += 1
            hits.append((i, letter, op, val, m.group(0)))
    if not hits:
        return out, None
    dominant = "P" if cap >= low else "p"
    for i, letter, op, val, raw in hits:
        try:
            num = float(val)
        except ValueError:
            num = None
        if num is not None and num == 0:
            out.append((i, f'"{raw}" — a p-value cannot be exactly 0; report as {letter} < .001'))
        if letter != dominant:
            out.append((i, f'"{raw}" — inconsistent case (document uses "{dominant}")'))
    return out, dominant


def check_hyphenation(lines):
    out = []
    for canon, variants in HYPHEN_FAMILIES:
        present = []
        per_variant = {}
        for vre in variants:
            vlines = [i for i, line in enumerate(lines, 1) if re.search(vre, line, re.I)]
            if vlines:
                present.append(vre)
                per_variant[vre] = vlines
        if len(present) >= 2:
            first_line = min(min(v) for v in per_variant.values())
            out.append((first_line, f'inconsistent forms of "{canon}" (multiple variants present)'))
    return out


def check_small_numbers(lines):
    out = []
    for i, line in enumerate(lines, 1):
        for m in SMALL_NUM_RE.finditer(line):
            word = m.group(2)
            if word in UNIT_TOKENS:
                continue
            out.append((i, f'"{m.group(1)} {word}" — spell out single-digit numbers in prose'))
    return out


def check_units(lines):
    out = []
    for i, line in enumerate(lines, 1):
        for m in UNIT_RE.finditer(line):
            out.append((i, f'"{m.group(0)}" — insert a space between value and unit ({m.group(1)} {m.group(2)})'))
    return out


# A float title/caption line: "**Table 2.** ...", "Figure 1 ...".
FLOAT_TITLE_RE = re.compile(r"^\s*\*{0,2}\s*(?:Table|Figure)\s+\d+", re.IGNORECASE)
# Thousands-grouped integers: comma style (3,681) and period/European style (3.681).
COMMA_GROUP_RE = re.compile(r"\b\d{1,3}(?:,\d{3})+\b")
PERIOD_GROUP_RE = re.compile(r"\b\d{1,3}(?:\.\d{3})+\b")


def check_thousands_separator(lines):
    """Float-title thousands-separator drift. High-precision: only flags when the
    SAME integer appears comma-grouped somewhere (e.g. "3,681" in the body) AND
    period-grouped inside a float title/caption (e.g. "n = 3.681"). This avoids the
    decimal ambiguity — a genuine 3-decimal number never also appears comma-grouped."""
    out = []
    comma_vals = {}  # normalized digits -> first line it appears comma-grouped
    for i, line in enumerate(lines, 1):
        for m in COMMA_GROUP_RE.finditer(line):
            comma_vals.setdefault(m.group(0).replace(",", ""), i)
    if not comma_vals:
        return out
    for i, line in enumerate(lines, 1):
        if not FLOAT_TITLE_RE.match(line):
            continue
        for m in PERIOD_GROUP_RE.finditer(line):
            norm = m.group(0).replace(".", "")
            if norm in comma_vals:
                out.append((i, f'"{m.group(0)}" in a float title uses a period thousands-separator '
                               f'while the body writes it "{int(norm):,}" (L{comma_vals[norm]}) — '
                               f'harmonize the thousands separator across titles and body'))
    return out


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def section(title, items):
    lines = [f"## {title}"]
    if items:
        for ln, msg in sorted(items, key=lambda x: (x[0], x[1])):
            lines.append(f"- L{ln}: {msg}")
    else:
        lines.append("- OK: no issues")
    lines.append("")
    return lines, len(items)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic manuscript consistency linter.")
    ap.add_argument("path", help="manuscript markdown/text file")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any issue found")
    args = ap.parse_args(argv)

    lines = Path(args.path).read_text(errors="ignore").splitlines()

    abbr = check_abbreviations(lines)
    spell_res = check_spelling(lines)
    spell = spell_res[0] if isinstance(spell_res, tuple) else spell_res
    ranges = check_numeric_ranges(lines)
    pval_res = check_pvalues(lines)
    pvals = pval_res[0]
    hyph = check_hyphenation(lines)
    small = check_small_numbers(lines)
    units = check_units(lines)
    thousands = check_thousands_separator(lines)

    report = ["# Consistency Lint Report", ""]
    total = 0
    cats_hit = 0
    for title, items in [
        ("Abbreviations", abbr),
        ("Spelling (US/UK consistency)", spell),
        ("Numeric ranges", ranges),
        ("p-values", pvals),
        ("Hyphenation / terminology", hyph),
        ("Small numbers in prose", small),
        ("Units", units),
        ("Thousands separator (title vs body)", thousands),
    ]:
        sec, n = section(title, items)
        report += sec
        total += n
        cats_hit += 1 if n else 0

    report.append("---")
    report.append(f"Summary: {total} issue(s) across {cats_hit} category(ies).")
    sys.stdout.write("\n".join(report) + "\n")

    if args.strict and total > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

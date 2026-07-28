#!/usr/bin/env python3
"""Title-page author/affiliation builder + checker (write-paper).

Most journals — and every Nature Portfolio / npj technical check — require the
title-page affiliations to be **numbered in the order the authors first introduce
them**: affiliation 1 belongs to the first author, and each new affiliation gets
the next number the first time it appears as you read the author list left to
right. Each affiliation must also carry its city and country. An LLM hand-numbering
this gets the order wrong (it groups by institution, or lets a late author's
affiliation keep a low number), which the technical check bounces.

This script makes that numbering deterministic.

BUILD (default): read an authors YAML and emit the correctly-numbered author line
+ affiliation block + corresponding-author footnotes.

  python3 build_title_page_affiliations.py --authors authors.yaml [--out title_page_affiliations.md]

CHECK: parse an existing title page and verify the numbering is by first
appearance (affiliation 1 == first author's first affiliation), with no gaps,
orphans, or out-of-order definitions, and a city+country on every affiliation.

  python3 build_title_page_affiliations.py --check title_page.md [--strict]

authors.yaml
------------
    authors:
      - name: "Jane Doe"
        affiliations: [uh_rad, uh_convergence]      # ordered; keys into `affiliations`
        corresponding: false                         # optional -> appends "*"
        equal_contribution: false                    # optional -> appends "†"
      - name: "John Roe"
        affiliations: [uh_rad]
        corresponding: true
    affiliations:
      uh_rad: "Department of Radiology, University Hospital, City, Country"
      uh_convergence: "Department of Convergence Medicine, University Hospital, City, Country"

Exit codes: 0 clean (build, or check with no violations / report-only); 1 a check
violation under --strict; 2 input/usage error. Stdlib-only except PyYAML (already a
repo dependency); a JSON authors file also works.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A country token a city+country affiliation tail is expected to end with. Not
# exhaustive — used as a soft "looks like it has a country" heuristic.
COUNTRY_RE = re.compile(
    r"(Republic of Korea|South Korea|\bKorea\b|United States|\bUSA\b|\bU\.?S\.?A?\.?\b|"
    r"United Kingdom|\bUK\b|\bChina\b|\bJapan\b|\bGermany\b|\bFrance\b|\bItaly\b|\bSpain\b|"
    r"\bCanada\b|\bAustralia\b|\bIndia\b|\bSingapore\b|\bTaiwan\b|\bNetherlands\b|"
    r"\bSwitzerland\b|\bSweden\b|\bBelgium\b|\bBrazil\b|\bIsrael\b|\bAustria\b|\bDenmark\b|"
    r"\bNorway\b|\bFinland\b|\bPoland\b|\bTurkey\b|\bIreland\b|\bPortugal\b|\bGreece\b)\.?\s*$"
)


def _err(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 2


def load_authors(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".json",):
        return json.loads(text)
    try:
        import yaml  # type: ignore
    except ImportError:
        raise SystemExit("PyYAML required for YAML input (or pass a .json file).")
    return yaml.safe_load(text)


# ---------------------------------------------------------------- build --------

def assign_numbers(authors: list[dict]) -> dict[str, int]:
    """First-appearance numbering across the ordered author list."""
    order: dict[str, int] = {}
    nxt = 1
    for a in authors:
        for key in a.get("affiliations", []):
            if key not in order:
                order[key] = nxt
                nxt += 1
    return order


def build(data: dict) -> tuple[str, list[str]]:
    authors = data.get("authors") or []
    affil = data.get("affiliations") or {}
    problems: list[str] = []
    if not authors:
        problems.append("no authors")
    order = assign_numbers(authors)

    # validate keys + city/country
    for key in order:
        if key not in affil:
            problems.append(f"affiliation key '{key}' used by an author but not defined")
    for key in affil:
        if key not in order:
            problems.append(f"affiliation '{key}' is defined but no author uses it")
    for key, num in sorted(order.items(), key=lambda kv: kv[1]):
        text = affil.get(key, "")
        if text and not COUNTRY_RE.search(text):
            problems.append(f"affiliation {num} ('{key}') has no recognizable city+country tail")

    # author line
    names: list[str] = []
    for a in authors:
        nums = [str(order[k]) for k in a.get("affiliations", []) if k in order]
        marks = "".join(nums and [",".join(nums)] or [])
        suffix = ""
        if a.get("equal_contribution"):
            suffix += ",†" if marks else "†"
        if a.get("corresponding"):
            suffix += ",\\*" if (marks or suffix) else "\\*"
        sup = (marks + suffix).lstrip(",")
        names.append(f"{a['name']}^{sup}^" if sup else a["name"])
    author_line = "; ".join(names)

    # affiliation block (numeric = first-appearance order)
    block = [
        f"^{num}^ {affil.get(key, '[MISSING AFFILIATION TEXT]')}"
        for key, num in sorted(order.items(), key=lambda kv: kv[1])
    ]

    out = [author_line, ""]
    out += block
    footnotes = []
    if any(a.get("equal_contribution") for a in authors):
        footnotes.append("† These authors contributed equally to this work.")
    corr = [a for a in authors if a.get("corresponding")]
    if corr:
        footnotes.append("\\* Corresponding author" + ("s" if len(corr) > 1 else "") + ".")
    if footnotes:
        out += [""] + footnotes
    return "\n".join(out) + "\n", problems


# ---------------------------------------------------------------- check --------

SUP_RE = re.compile(r"\^([0-9,\\\*†‡§ ]+)\^")
AFFIL_LINE_RE = re.compile(r"^\s*\^(\d+)\^\s+(.*\S)\s*$")
# An author token: a name followed by a ^...^ superscript, separated by ; or ,
AUTHOR_TOKEN_RE = re.compile(r"([^;]+?)\^([0-9,\\\*†‡§ ]+)\^")


def parse_author_line(text: str) -> list[list[int]]:
    """Return, per author (in order), the list of affiliation numbers they cite.
    Looks at the densest superscript-bearing line (the author byline)."""
    best_line, best_count = "", 0
    for ln in text.splitlines():
        c = len(SUP_RE.findall(ln))
        if c > best_count:
            best_line, best_count = ln, c
    per_author: list[list[int]] = []
    for _name, sup in AUTHOR_TOKEN_RE.findall(best_line):
        nums = [int(n) for n in re.findall(r"\d+", sup)]
        per_author.append(nums)
    return per_author


def parse_affil_block(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for ln in text.splitlines():
        m = AFFIL_LINE_RE.match(ln.replace("\\", ""))
        if m:
            out.append((int(m.group(1)), m.group(2).rstrip(" \\")))
    return out


def check_title_page(text: str) -> list[dict]:
    findings: list[dict] = []
    per_author = parse_author_line(text)
    block = parse_affil_block(text)
    if not per_author:
        return [{"severity": "hard", "rule": "author_line", "detail": "no author byline with ^superscripts^ found"}]
    if not block:
        return [{"severity": "hard", "rule": "affil_block", "detail": "no '^N^ affiliation' block found"}]

    defined = [n for n, _ in block]
    defined_set = set(defined)

    # 1. affiliation 1 == first author's first affiliation
    first_nums = per_author[0]
    if not first_nums or first_nums[0] != 1:
        findings.append({"severity": "hard", "rule": "first_author_is_1",
                         "detail": f"affiliation 1 must be the first author's first affiliation; first author cites {first_nums or '∅'}"})

    # 2. first-appearance order == 1,2,3,... (a new number may only be the next integer)
    seen: list[int] = []
    expected_next = 1
    for ai, nums in enumerate(per_author, 1):
        for n in nums:
            if n not in seen:
                if n != expected_next:
                    findings.append({"severity": "hard", "rule": "first_appearance_order",
                                     "detail": f"affiliation {n} first appears at author #{ai} but {expected_next} has not appeared yet — numbering is not in author order"})
                seen.append(n)
                expected_next = max(expected_next, n) + 1 if n == expected_next else expected_next

    # 3. block defined in ascending order, contiguous, no dup
    if defined != sorted(defined):
        findings.append({"severity": "hard", "rule": "block_ascending", "detail": f"affiliation block is not in ascending numeric order: {defined}"})
    if len(defined) != len(defined_set):
        findings.append({"severity": "hard", "rule": "block_duplicate", "detail": f"duplicate affiliation number(s) in the block: {defined}"})
    if defined_set and sorted(defined_set) != list(range(1, max(defined_set) + 1)):
        findings.append({"severity": "hard", "rule": "block_gaps", "detail": f"affiliation numbers are not contiguous 1..N: {sorted(defined_set)}"})

    # 4. cross-reference: every cited number defined, every defined number cited
    cited = {n for nums in per_author for n in nums}
    for n in sorted(cited - defined_set):
        findings.append({"severity": "hard", "rule": "undefined_affiliation", "detail": f"author cites affiliation {n} but the block does not define it"})
    for n in sorted(defined_set - cited):
        findings.append({"severity": "soft", "rule": "orphan_affiliation", "detail": f"affiliation {n} is defined but no author cites it"})

    # 5. city + country on each affiliation
    for n, t in block:
        if not COUNTRY_RE.search(t):
            findings.append({"severity": "soft", "rule": "city_country", "detail": f"affiliation {n} has no recognizable city+country tail: '{t[:60]}...'"})
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Build or check title-page author/affiliation numbering (first-appearance order).")
    ap.add_argument("--authors", help="authors YAML/JSON (build mode)")
    ap.add_argument("--check", help="existing title page (.md/.qmd) to verify")
    ap.add_argument("--out", help="write the built block here (build mode)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on a hard check violation")
    args = ap.parse_args()

    if not args.authors and not args.check:
        return _err("pass --authors (build) or --check <title_page> (verify)")

    rc = 0
    if args.authors:
        p = Path(args.authors)
        if not p.is_file():
            return _err(f"authors file not found: {p}")
        rendered, problems = build(load_authors(p))
        if args.out:
            Path(args.out).write_text(rendered, encoding="utf-8")
            print(f"wrote {args.out}")
        else:
            print(rendered)
        for pr in problems:
            print(f"  [warn] {pr}", file=sys.stderr)

    if args.check:
        p = Path(args.check)
        if not p.is_file():
            return _err(f"title page not found: {p}")
        findings = check_title_page(p.read_text(encoding="utf-8"))
        print("=" * 41)
        print(" Title-Page Affiliation Order")
        print("=" * 41)
        hard = [f for f in findings if f["severity"] == "hard"]
        if not findings:
            print("OK: affiliations are numbered by author first-appearance, contiguous, with city+country.")
        for f in findings:
            print(f"  [{f['severity']}] {f['rule']}: {f['detail']}")
        if hard and args.strict:
            print("\nTITLE_PAGE_AFFILIATION_ORDER_VIOLATION", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Catalog-count consistency check (codex Improvement A).

Counts cited in public docs (skill count, reporting-guideline count, journal-
profile counts) were hand-maintained in multiple places and drifted (README once
said "22 guidelines" while orchestrate said "15"; more recently every doc said
"33 reporting guidelines" while only 32 are enumerated and vendored). This makes
the counts a single source of truth and fails CI on drift.

Three layers:
  1. Recompute every count from disk (the real ground truth).
  2. Assert metadata/catalog_counts.json matches disk — the SSOT cannot lie.
     Exception: the journal-profile counts (``AUTO_DERIVED_KEYS``) are recomputed
     from disk but never asserted against the JSON, so that adding one profile —
     the single-file change the "add a journal profile" good-first-issue (#115)
     invites from a first-time contributor — can never fail on a count bump they
     have no reason to know about. Those counts are cited in no checked doc claim,
     so disk is their sole source of truth.
  3. Assert the count claims in README / orchestrate / check-reporting match the
     SSOT. Guideline claims are matched (case-insensitively, so a "### 33 Reporting
     Guidelines" heading is caught) by the word "guideline"; the skill self-count by
     both the "skills that actually work" tagline and the README shields badge
     (img.shields.io/badge/Skills-N-). The badge regex is scoped to the shields URL so
     arbitrary prose never trips it, and comparison/marketing lines about *other* repos
     ("400-900 skills", "869 skills") are never touched.

Exit 0 when everything agrees; non-zero on any drift. Stdlib-only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SSOT = ROOT / "metadata" / "catalog_counts.json"

# Counts that a drive-by contributor legitimately changes with a single-file PR
# (adding one journal profile). These are AUTO-DERIVED from disk and deliberately
# NOT asserted against catalog_counts.json — otherwise the flagship "add a journal
# profile" good-first-issue (#115) would fail CATALOG_COUNT_DRIFT for the exact
# newcomer it targets, who has no reason to touch the SSOT JSON. No public doc
# cross-checks these counts, so disk is their sole source of truth. Maintainer-
# scoped counts (skills, reporting_guidelines, integrity_detectors) stay hard-
# asserted below and in catalog_counts.json.
# `plugins` is derived from the marketplace SSOT (.claude-plugin/marketplace.json),
# not from catalog_counts.json, so it is not asserted against the JSON here — but
# unlike the journal-profile keys it IS cross-checked against the README plugin
# claim in Layer 3 (doc_claims).
AUTO_DERIVED_KEYS = ("journal_profiles_find", "journal_profiles_write", "plugins")


def disk_counts() -> dict[str, int]:
    skills = sum(1 for p in (ROOT / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").exists())
    checklists = len(list((ROOT / "skills" / "check-reporting" / "references" / "checklists").glob("*.md")))
    find_prof = len(list((ROOT / "skills" / "find-journal" / "references" / "journal_profiles").glob("*.md")))
    write_prof = len(list((ROOT / "skills" / "write-paper" / "references" / "journal_profiles").glob("*.md")))
    # Deterministic, stdlib-only analysis-integrity detectors living inside skills/
    # (check_*/detect_*/derive_*/verify_refs). Excludes top-level repo-CI validators
    # (validate_*.py in scripts/) and host/format validators (validate_schema.py,
    # validate_pptx_mac_compat.py), which are not manuscript-integrity gates.
    detector_globs = ("check_*.py", "detect_*.py", "derive_*.py", "verify_refs.py")
    detectors = len({
        str(p) for g in detector_globs for p in (ROOT / "skills").glob(f"*/scripts/{g}")
    })
    # medsci-* category plugins in the plugin marketplace SSOT
    mp = ROOT / ".claude-plugin" / "marketplace.json"
    plugins = 0
    if mp.exists():
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
            plugins = sum(1 for p in data.get("plugins", [])
                          if str(p.get("name", "")).startswith("medsci-"))
        except (ValueError, OSError):
            plugins = 0
    return {
        "skills": skills,
        "reporting_guidelines": checklists,
        "journal_profiles_find": find_prof,
        "journal_profiles_write": write_prof,
        "integrity_detectors": detectors,
        "plugins": plugins,
    }


# Files that carry the catalog-total guideline claim. Scoped explicitly rather
# than scanning all .md: phrases like "PRISMA 2020 guidelines" (version year) or
# "4 reporting guidelines in one tool" (a flow-diagram subset in figure_specs.md)
# are NOT catalog totals and would false-positive a blanket scan. A new doc that
# cites the catalog total must be added here. CHANGELOG is deliberately absent —
# it is a dated record that legitimately quotes superseded counts.
GUIDELINE_CLAIM_FILES = [
    "README.md",
    "skills/orchestrate/SKILL.md",
    "skills/check-reporting/SKILL.md",
    "skills/make-figures/references/reporting_guideline_figure_map.md",
]
SKILLS_TAGLINE_FILES = ["README.md"]
# README shields badge (img.shields.io/badge/Skills-N-...). Scoped to the badge URL so
# only the literal badge count is checked, never arbitrary "Skills" prose.
SKILLS_BADGE_FILES = ["README.md"]

# Files carrying the catalog-total DETECTOR claim. MEDSCI_AUDIT.md drifted once
# (lead said 27 while the SSOT was 28) because no gate watched it. The patterns
# below are anchored to the *current-total* phrasings ONLY — they must never match
# historical/evaluation numbers in the same file (e.g. "brought the catalog to 24",
# "19 DefectSpec rows", "n=21", or the per-family sub-counts in the family table),
# which are legitimately different facts. A new doc citing the detector total must
# be added here with an anchored pattern.
#
# paper.md (the JOSS submission) states the total in its Summary and was ungated
# until the suite grew past it — a paper whose headline number disagrees with the
# software it describes is exactly the drift this file exists to prevent.
DETECTOR_CLAIM_FILES = ["MEDSCI_AUDIT.md", "paper.md"]
DETECTOR_CLAIM_PATTERNS = [
    r"\b(\d{1,3})\s+stdlib-only detectors\b",
    r"\bThe\s+(\d{1,3})\s+detectors\s+fall into\b",
    r"Current detector catalog:\s*(\d{1,3})\b",
    r'"(\d{1,3})\s+detectors,\s*validated\b',
    r"\bcover all\s+(\d{1,3})\s+detectors\b",
]

# Files carrying the plugin-marketplace count claim (the `medsci-*` category
# plugins). Drifted once (README said "eight" while marketplace.json had nine)
# because no gate watched it. The number is written as an English word, so a small
# word->int map is needed; only a number token immediately preceding
# "category plugins" is treated as a claim.
PLUGIN_CLAIM_FILES = ["README.md"]
NUM_WORDS = {w: i for i, w in enumerate(
    ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
     "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
     "sixteen", "seventeen", "eighteen", "nineteen", "twenty"])}


def doc_claims() -> list[tuple[str, int, int, str]]:
    """Return (file, claimed, expected, context) for every count claim found.

    Guideline claims use a 1-2 digit count (4-digit version years like "2020" are
    excluded) followed by "[reporting] guidelines". The skill self-count is matched
    only by the README "skills that actually work" tagline, so comparison lines
    about other repos ("400-900 skills") are never touched.
    """
    out: list[tuple[str, int, int, str]] = []
    truth = disk_counts()
    g = truth["reporting_guidelines"]
    s = truth["skills"]

    guide_re = re.compile(r"\b(\d{1,2})\s+(?:reporting\s+)?guidelines\b", re.IGNORECASE)
    skills_re = re.compile(r"\*\*(\d+)\s+skills that actually work")
    badge_re = re.compile(r"img\.shields\.io/badge/Skills-(\d+)-")

    for rel in GUIDELINE_CLAIM_FILES:
        f = ROOT / rel
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in guide_re.finditer(line):
                out.append((rel, int(m.group(1)), g, f"L{i} guidelines"))

    for rel in SKILLS_TAGLINE_FILES:
        f = ROOT / rel
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in skills_re.finditer(line):
                out.append((rel, int(m.group(1)), s, f"L{i} skills tagline"))

    for rel in SKILLS_BADGE_FILES:
        f = ROOT / rel
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in badge_re.finditer(line):
                out.append((rel, int(m.group(1)), s, f"L{i} skills badge"))

    d = truth["integrity_detectors"]
    det_res = [re.compile(p, re.IGNORECASE) for p in DETECTOR_CLAIM_PATTERNS]
    for rel in DETECTOR_CLAIM_FILES:
        f = ROOT / rel
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for rx in det_res:
                for m in rx.finditer(line):
                    out.append((rel, int(m.group(1)), d, f"L{i} detector total"))

    # Plugin marketplace count: a number word or digit shortly before "category
    # plugins". The capture group is constrained to number tokens so an ordinary
    # word (e.g. "of", "medsci") that happens to sit before the phrase is not
    # mistaken for the count.
    pl = truth["plugins"]
    _num_alt = "|".join(NUM_WORDS)
    plugin_re = re.compile(rf"\b({_num_alt}|\d+)\b[^.\n]{{0,20}}?\bcategory plugins\b", re.IGNORECASE)
    for rel in PLUGIN_CLAIM_FILES:
        f = ROOT / rel
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in plugin_re.finditer(line):
                tok = m.group(1).lower()
                n = NUM_WORDS.get(tok, int(tok) if tok.isdigit() else None)
                if n is not None:
                    out.append((rel, n, pl, f"L{i} plugin count"))
    return out


def main() -> int:
    truth = disk_counts()

    print("=" * 41)
    print(" Catalog-Count Consistency")
    print("=" * 41)
    for k, v in truth.items():
        print(f"  disk: {k} = {v}")

    failures = 0

    # Layer 2 — SSOT must match disk.
    if not SSOT.exists():
        print(f"\nFAIL: SSOT missing: {SSOT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    ssot = json.loads(SSOT.read_text(encoding="utf-8"))
    for key, val in truth.items():
        if key in AUTO_DERIVED_KEYS:
            continue  # disk is truth; a profile-add PR must never need a JSON bump
        if ssot.get(key) != val:
            print(f"\nFAIL: SSOT {key}={ssot.get(key)} != disk {val}", file=sys.stderr)
            failures += 1

    # Layer 3 — doc claims must match disk.
    for rel, claimed, expected, ctx in doc_claims():
        if claimed != expected:
            print(f"\nFAIL: {rel} {ctx}: claims {claimed}, expected {expected}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"\nCATALOG_COUNT_DRIFT: {failures} mismatch(es).", file=sys.stderr)
        return 1
    print("\nOK: SSOT and all doc count claims agree with disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

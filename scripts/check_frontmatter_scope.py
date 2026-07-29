#!/usr/bin/env python3
"""A manuscript detector that reads YAML front matter as body prose.

A pandoc manuscript opens with a `---`-fenced YAML block, and projects keep real sentences
in it: `status:` notes, `changelog:` entries, build annotations. Every detector in this repo
that scans `--manuscript` rolls its own body extractor, and those extractors filter lines
starting with `#`, `|`, `>`, `!`, list markers and code fences. **A YAML front-matter block
matches none of those**, so its prose is read as the manuscript's own text.

This is not hypothetical. Three shipped detectors have fired on it:

  check_citation_order      reported floats "cited out of order" from a `status:` block
                            narrating a display-item renumber
  check_aphorism_density    listed build notes among the manuscript's short declaratives
  check_claim_artifact      returned PRIMARY_REASSIGNED — a **P0** — when a `changelog:`
                            entry said the primary endpoint was changed. A Major that fires
                            harder the more openly a project records its own history is the
                            Major most likely to get waved through, and estimand provenance
                            is precisely the gate that must not be.

`skills/self-review/scripts/_frontmatter.py` (and `sync-submission`'s `_yaml_frontmatter.py`)
solve it. The problem was never the fix; it was that nothing made the gap visible, so the fix
reached 4 of 41 detectors over several months.

WHAT THIS GATE DOES

Every `skills/*/scripts/check_*.py` that accepts `--manuscript` must either strip front matter
-- directly, or through a same-directory helper it imports -- or appear in ALLOWLIST below with
a reason. The allowlist is seeded with the detectors that did not strip it on the day this gate
landed, and it exists to be **emptied**: a name leaves it when that detector is fixed, and
nothing may be added without a reason. New detectors get no grace period.

This is deliberately a list rather than a count. "37 detectors do not strip front matter" is a
number nobody acts on; a name is a piece of work. It is the same reason a scanner that skips
unmapped items has to print what it skipped.

Repo-CI validator, so it lives in scripts/ and is NOT an analysis-integrity detector: the
catalog glob is `skills/*/scripts/{check_,detect_,derive_,verify_refs}*.py`, and this file is
outside it. `integrity_detectors` is unchanged.

Usage:  python3 scripts/check_frontmatter_scope.py [--strict]
Exit:   0 clean (or advisory without --strict); 1 a detector strips nothing and is not listed.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TAKES_MANUSCRIPT = re.compile(r'["\']--manuscript["\']')
# Direct evidence that the module removes front matter before analysing prose.
STRIPS = re.compile(
    r"from\s+_(?:yaml_)?frontmatter\s+import"
    r"|import\s+_(?:yaml_)?frontmatter\b"
    r"|strip_frontmatter\s*\("
    r"|strip_yaml_frontmatter\s*\("
)
# A same-directory private helper import: `from _prose import ...`. Resolved one level,
# because check_aphorism_density and check_rhetorical_density strip through _prose, and a
# gate that called those two "debt" would be inventing work.
SIBLING_IMPORT = re.compile(r"^\s*(?:from|import)\s+(_\w+)", re.M)

# path -> why it does not strip yet. EMPTY THIS LIST. Every entry is a detector that will
# read a `status:` or `changelog:` block as manuscript prose the first time a project puts
# one there. They are listed rather than counted so each is a piece of work with a name.
ALLOWLIST: dict[str, str] = {
    # -- self-review: the largest family, and where the P0s live -------------------------
    "skills/self-review/scripts/check_analysis_definitions.py": "not yet swept",
    "skills/self-review/scripts/check_artifact_coverage.py": "not yet swept",
    "skills/self-review/scripts/check_baseline_drift.py": "not yet swept",
    "skills/self-review/scripts/check_classical_style.py": "not yet swept",
    "skills/self-review/scripts/check_cohort_arithmetic.py": "not yet swept",
    "skills/self-review/scripts/check_cv_leakage.py": "not yet swept",
    "skills/self-review/scripts/check_dta_denominators.py": "not yet swept",
    "skills/self-review/scripts/check_editorial_impression.py": "not yet swept",
    "skills/self-review/scripts/check_effect_stability.py": "not yet swept",
    "skills/self-review/scripts/check_emphasis_density.py": "not yet swept",
    "skills/self-review/scripts/check_figure_citation.py": "not yet swept",
    "skills/self-review/scripts/check_incorporation_bias.py": "not yet swept",
    "skills/self-review/scripts/check_nested_group_comparison.py": "not yet swept",
    "skills/self-review/scripts/check_null_calibration.py": "not yet swept",
    "skills/self-review/scripts/check_paired_difference_estimator.py": "not yet swept",
    "skills/self-review/scripts/check_paren_spans.py": "not yet swept",
    "skills/self-review/scripts/check_reference_adequacy.py": "not yet swept",
    "skills/self-review/scripts/check_reported_p_from_counts.py": "not yet swept",
    "skills/self-review/scripts/check_reviewer_team_consistency.py": "not yet swept",
    "skills/self-review/scripts/check_rounded_delta.py": "not yet swept",
    "skills/self-review/scripts/check_scope_coherence.py": "not yet swept",
    "skills/self-review/scripts/check_supplement_hygiene.py": "not yet swept",
    "skills/self-review/scripts/check_table_percentages.py": "not yet swept",
    # -- other skills: each needs its own helper, since skills are self-contained --------
    "skills/academic-aio/scripts/check_summary_box.py": "not yet swept",
    "skills/check-reporting/scripts/check_checklist_version.py": "not yet swept",
    "skills/check-reporting/scripts/check_framework_naming.py": "not yet swept",
    "skills/humanize/scripts/check_sentence_variety.py": "not yet swept",
    "skills/peer-review/scripts/check_self_improvement_claims.py": "not yet swept",
    "skills/revise/scripts/check_response_claims.py": "not yet swept",
    "skills/sync-submission/scripts/check_credit_integrity.py": "not yet swept",
    "skills/sync-submission/scripts/check_cross_artifact_stale.py": "not yet swept",
    "skills/sync-submission/scripts/check_disclosure_availability.py": "not yet swept",
    "skills/sync-submission/scripts/check_portal_mirror.py": "not yet swept",
    "skills/verify-refs/scripts/check_claim_fidelity.py": "not yet swept",
    "skills/write-paper/scripts/check_placeholders.py": "not yet swept",
}


def _strips(path: Path, seen: set[Path] | None = None) -> bool:
    """True if `path`, or a same-directory `_helper` it imports, removes front matter."""
    seen = seen if seen is not None else set()
    if path in seen or not path.is_file():
        return False
    seen.add(path)
    src = path.read_text(encoding="utf-8", errors="replace")
    if STRIPS.search(src):
        return True
    return any(
        _strips(path.parent / f"{name}.py", seen)
        for name in SIBLING_IMPORT.findall(src)
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on any unlisted detector (CI uses this)")
    a = ap.parse_args()

    detectors, stripping, unlisted, listed = [], [], [], []
    for p in sorted(ROOT.glob("skills/*/scripts/check_*.py")):
        rel = p.relative_to(ROOT).as_posix()
        if not TAKES_MANUSCRIPT.search(p.read_text(encoding="utf-8", errors="replace")):
            continue
        detectors.append(rel)
        if _strips(p):
            stripping.append(rel)
        elif rel in ALLOWLIST:
            listed.append(rel)
        else:
            unlisted.append(rel)

    stale = sorted(set(ALLOWLIST) - set(detectors) - set(stripping) | (set(ALLOWLIST) & set(stripping)))

    print(f"--manuscript detectors: {len(detectors)} | strip front matter: {len(stripping)} "
          f"| known debt: {len(listed)} | unlisted: {len(unlisted)}")

    if stale:
        print("\nSTALE ALLOWLIST -- these now strip front matter (or no longer exist). "
              "Delete them from ALLOWLIST:")
        for rel in stale:
            print(f"  {rel}")

    if unlisted:
        print("\nFRONTMATTER_SCOPE: a --manuscript detector that does not strip YAML front matter\n"
              "and is not listed as known debt. A `status:` or `changelog:` block in the manuscript\n"
              "will be read as body prose:\n")
        for rel in unlisted:
            print(f"  {rel}")
        print("\n  Fix: `from _frontmatter import strip_frontmatter` (a same-directory helper --\n"
              "  skills are self-contained, so each skill needs its own copy) and apply it to the\n"
              "  manuscript text before any pattern runs. Add a regression fixture whose front\n"
              "  matter contains the phrase the detector looks for, and assert it stays silent\n"
              "  while the same phrase in the body still fires.")

    if listed and not unlisted and not stale:
        print(f"\nOK: no unlisted detector. {len(listed)} known-debt entries remain -- this list\n"
              "exists to be emptied; see ALLOWLIST in this file.")

    failed = bool(unlisted) or bool(stale)
    if failed and a.strict:
        return 1
    if failed:
        print("\n(advisory: re-run with --strict to fail)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

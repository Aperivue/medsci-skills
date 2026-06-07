"""Deterministic defect injectors for the E1 seeded-defect benchmark.

Each injector reads a target file *inside a temp copy*, applies a deterministic
transform (first-match-in-document-order, no RNG), writes it back via
``safe_write``, and returns an ``Outcome`` describing what changed. If the
required anchor is absent the injector returns status SKIPPED (excluded from the
recall denominator) rather than silently producing a no-op.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.workspace import safe_write  # noqa: E402


@dataclass
class Outcome:
    status: str            # INJECTED | SKIPPED
    reason: str = ""
    before_excerpt: str = ""
    after_excerpt: str = ""


def _excerpt(s: str, n: int = 100) -> str:
    return re.sub(r"\s+", " ", s).strip()[:n]


# --- style (check_classical_style) -----------------------------------------

def inject_section_symbol(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    if "§" in txt:
        return Outcome("SKIPPED", "manuscript already contains §")
    safe_write(p, txt + "\n\nThe primary outcome was defined in §2 of the protocol.\n")
    return Outcome("INJECTED", after_excerpt="appended 'in §2 of the protocol'")


def inject_inbody_ai_disclosure(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    if re.search(r"generative ai was not used|artificial intelligence disclosure", txt, re.I):
        return Outcome("SKIPPED", "AI-disclosure phrase already present")
    safe_write(p, txt + "\n\nGenerative AI was not used in the preparation of this manuscript.\n")
    return Outcome("INJECTED", after_excerpt="appended in-body AI disclosure sentence")


def inject_em_dashes(p: Path, args: dict) -> Outcome:
    n = int(args.get("n", 40))
    txt = p.read_text(encoding="utf-8")
    payload = " ".join(["clause — clause"] * n)
    safe_write(p, txt + "\n\n" + payload + "\n")
    return Outcome("INJECTED", after_excerpt=f"appended {n} em-dashes")


# --- scope (check_scope_coherence) -----------------------------------------

def inject_prognostic_conclusion(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    if not re.search(r"cross[-\s]?sectional|point[-\s]prevalence|prevalence (?:study|survey)", txt, re.I):
        return Outcome("SKIPPED", "no cross-sectional design statement to make this incoherent")
    add = ("\n\n## Conclusions\n\nWe recommend annual surveillance and longitudinal "
           "follow-up to monitor disease progression over time.\n")
    safe_write(p, txt + add)
    return Outcome("INJECTED", after_excerpt="appended prognostic/surveillance conclusion")


# --- cohort arithmetic (check_cohort_arithmetic) ---------------------------

def inject_cascade_sum(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    # complete-case contradiction: 5010 - 1000 = 4010, but states 4500
    sent = ("\n\nOf 5,010 participants, 1,000 had missing covariate data, "
            "leaving a final analytic sample of 4,500.\n")
    safe_write(p, txt + sent)
    return Outcome("INJECTED", after_excerpt="appended complete-case arithmetic contradiction")


def inject_rate_backcalc(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    # 250 / 100000 * 1000 = 2.5, but states 5.0 per 1,000 PY
    sent = ("\n\nThe incidence rate was 5.0 per 1,000 person-years "
            "(250 events over 100,000 person-years of follow-up).\n")
    safe_write(p, txt + sent)
    return Outcome("INJECTED", after_excerpt="appended rate that does not back-calculate")


# --- artifact coverage (check_artifact_coverage) ---------------------------

_METHODS_HEADING = re.compile(r"(?im)^#{1,4}\s+.*(method|statistical analys|analysis plan).*$")


def inject_promised_absent(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    # 'landmark' is used (vs E-value, whose regex spuriously matches 'the value')
    if re.search(r"\blandmark\b", txt, re.I):
        return Outcome("SKIPPED", "a landmark analysis is already mentioned")
    m = _METHODS_HEADING.search(txt)
    if not m:
        return Outcome("SKIPPED", "no Methods / Statistical analysis heading")
    # insert into the section BODY (after the heading line's newline), not on the
    # heading line itself
    nl = txt.find("\n", m.end())
    idx = (nl + 1) if nl != -1 else len(txt)
    insert = ("\nA landmark analysis was performed to address potential "
              "immortal-time bias in the primary comparison.\n")
    new = txt[:idx] + insert + txt[idx:]
    safe_write(p, new)
    return Outcome("INJECTED", after_excerpt="promised a landmark analysis in Methods (absent from Results)")


# --- reporting framework (check_framework_naming) --------------------------

def inject_base_missing(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    if re.search(r"\bPROBAST\b", txt, re.I):
        return Outcome("SKIPPED", "PROBAST already named (base present)")
    safe_write(p, txt + "\n\nRisk of bias was assessed using PROBAST-AI.\n")
    return Outcome("INJECTED", after_excerpt="used PROBAST-AI without naming base PROBAST")


def inject_hyphen_mix(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    if re.search(r"TRIPOD\s*\+\s*AI", txt, re.I):
        return Outcome("SKIPPED", "TRIPOD+AI already present")
    # name base TRIPOD standalone so BASE_MISSING does NOT fire; mix +AI and -AI
    add = ("\n\nReporting followed TRIPOD [1]; AI-specific items were drawn from "
           "TRIPOD+AI and TRIPOD-AI guidance.\n")
    safe_write(p, txt + add)
    return Outcome("INJECTED", after_excerpt="mixed TRIPOD+AI and TRIPOD-AI hyphenation")


# --- generated code (check_generated_code) ---------------------------------

def inject_abs_path(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    # generic placeholder username (no maintainer PII); still triggers ABS_PATH
    line = '\nINJECTED_DATA = "/Users/researcher/private/raw_cohort.csv"\n'
    safe_write(p, txt + line)
    return Outcome("INJECTED", after_excerpt="appended absolute /Users path literal")


def inject_inplace_overwrite(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".r":
        block = ('\n_inj <- read.csv("inj_inplace.csv")\n'
                 'write.csv(_inj, "inj_inplace.csv")\n')
    else:
        block = ('\nimport pandas as _pd\n'
                 '_inj = _pd.read_csv("inj_inplace.csv")\n'
                 '_inj.to_csv("inj_inplace.csv")\n')
    safe_write(p, txt + block)
    return Outcome("INJECTED", after_excerpt="read and overwrite the same path")


def inject_missing_seed(p: Path, args: dict) -> Outcome:
    txt = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".r":
        new = re.sub(r"(?m)^.*\bset\.seed\s*\(.*$", "", txt)
        new = new + "\n_inj <- sample(1:10)\n"
    else:
        new = re.sub(r"random_state\s*=\s*[\w.]+", "shuffle=True", txt)
        new = re.sub(r"(?m)^.*\bnp\.random\.seed\s*\(.*$", "", new)
        new = re.sub(r"(?m)^.*\brandom\.seed\s*\(.*$", "", new)
        new = new + "\n_inj = np.random.permutation(5)\n"
    safe_write(p, new)
    return Outcome("INJECTED", after_excerpt="stripped seed(s) and added unseeded randomness")


# --- citation (verify_refs offline / check_citation_keys) ------------------

def inject_pagination_placeholder(p: Path, args: dict) -> Outcome:
    bib = p.read_text(encoding="utf-8")
    new = re.sub(r"pages\s*=\s*\{[^}]*\}", "pages = {e000--e000}", bib, count=1)
    if new == bib:
        return Outcome("SKIPPED", "no pages field to rewrite")
    safe_write(p, new)
    return Outcome("INJECTED", after_excerpt="first entry pages -> e000--e000")


def inject_duplicate_ref(p: Path, args: dict) -> Outcome:
    bib = p.read_text(encoding="utf-8")
    m = re.search(r"@\w+\{[^@]*?\n\}", bib, re.S)
    if not m:
        return Outcome("SKIPPED", "could not isolate a bib entry to duplicate")
    entry = m.group(0)
    # change only the citekey so it is a separate entry with the SAME doi
    dup = re.sub(r"(@\w+\{)([^,]+)", r"\1\2_dup", entry, count=1)
    safe_write(p, bib + "\n\n" + dup + "\n")
    return Outcome("INJECTED", after_excerpt="duplicated first entry (same DOI, new key)")


def inject_undefined_citekey(p: Path, args: dict) -> Outcome:
    md = p.read_text(encoding="utf-8")
    safe_write(p, md + "\n\nThis claim cites a missing key [@ghost_missing_key].\n")
    return Outcome("INJECTED", after_excerpt="added [@ghost_missing_key] (not in bib)")


def inject_fake_doi(p: Path, args: dict) -> Outcome:
    bib = p.read_text(encoding="utf-8")
    new = re.sub(r"doi\s*=\s*\{[^}]*\}", "doi = {10.9999/this.doi.does.not.exist.000000}", bib, count=1)
    if new == bib:
        return Outcome("SKIPPED", "no doi field to corrupt")
    safe_write(p, new)
    return Outcome("INJECTED", after_excerpt="first entry DOI -> fabricated")


def inject_wrong_author(p: Path, args: dict) -> Outcome:
    bib = p.read_text(encoding="utf-8")
    new = re.sub(r"author\s*=\s*\{[^}]*\}",
                 "author = {Nonexistent, Q. Z. and Imaginary, A. B.}", bib, count=1)
    if new == bib:
        return Outcome("SKIPPED", "no author field to corrupt")
    safe_write(p, new)
    return Outcome("INJECTED", after_excerpt="first entry authors -> wrong")


INJECTORS = {
    "inject_section_symbol": inject_section_symbol,
    "inject_inbody_ai_disclosure": inject_inbody_ai_disclosure,
    "inject_em_dashes": inject_em_dashes,
    "inject_prognostic_conclusion": inject_prognostic_conclusion,
    "inject_cascade_sum": inject_cascade_sum,
    "inject_rate_backcalc": inject_rate_backcalc,
    "inject_promised_absent": inject_promised_absent,
    "inject_base_missing": inject_base_missing,
    "inject_hyphen_mix": inject_hyphen_mix,
    "inject_abs_path": inject_abs_path,
    "inject_inplace_overwrite": inject_inplace_overwrite,
    "inject_missing_seed": inject_missing_seed,
    "inject_pagination_placeholder": inject_pagination_placeholder,
    "inject_duplicate_ref": inject_duplicate_ref,
    "inject_undefined_citekey": inject_undefined_citekey,
    "inject_fake_doi": inject_fake_doi,
    "inject_wrong_author": inject_wrong_author,
}

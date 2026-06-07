"""Deterministic adjudication for the E2 LLM comparator.

Given a seeded defect and a free-text LLM review, decide whether the review
named the *specific* injected defect (not merely produced some unrelated
finding). Adjudication keys on the injected signature tokens so it is
reproducible; a human_adjudication column is left for optional manual review.
"""

from __future__ import annotations

import re

# defect_id -> signature tokens; a hit requires the LLM to mention the specific
# injected artefact (any-of for some, all-of where a single token is ambiguous).
SIGNATURES = {
    "STY_SECTION_SYMBOL": {"any": ["§", "section symbol", "section sign"]},
    "STY_AI_DISCLOSURE": {"any": ["ai disclosure", "generative ai", "ai-use", "ai use disclosure", "in the body"]},
    "STY_EM_DASH": {"any": ["em dash", "em-dash", "dash"]},
    "SCO_PROGNOSTIC": {"any": ["cross-sectional", "prognostic", "surveillance", "causal", "longitudinal"]},
    "COH_CASCADE_SUM": {"any": ["4,500", "4500", "5,010", "does not", "arithmetic", "do not add", "sum"]},
    "COH_RATE_BACKCALC": {"any": ["5.0 per", "incidence rate", "does not", "2.5", "recompute", "person-years"]},
    "ART_PROMISED_ABSENT": {"any": ["landmark", "not reported", "promised", "absent from results", "not in the results"]},
    "FRM_BASE_MISSING": {"any": ["probast", "base instrument", "without", "not defined", "acronym"]},
    "FRM_HYPHEN_MIX": {"any": ["tripod+ai", "tripod-ai", "hyphen", "inconsistent", "+ai", "-ai"]},
    "GEN_MISSING_SEED_PY": {"any": ["seed", "reproducib", "random"]},
    "GEN_MISSING_SEED_R": {"any": ["seed", "reproducib", "random"]},
    "GEN_ABS_PATH_PY": {"any": ["absolute path", "/users/", "hard-coded path", "hardcoded path", "hard coded"]},
    "GEN_ABS_PATH_R": {"any": ["absolute path", "/users/", "hard-coded path", "hardcoded path", "hard coded"]},
    "GEN_INPLACE_OVERWRITE_PY": {"any": ["overwrit", "same path", "in-place", "in place", "source data"]},
    "CIT_PAGINATION": {"any": ["pagination", "e000", "placeholder", "page", "in press"]},
    "CIT_DUPLICATE": {"any": ["duplicate", "same doi", "repeated reference", "twice"]},
    "CIT_UNDEFINED_KEY": {"any": ["ghost_missing_key", "undefined", "missing reference", "not in", "citation key"]},
    "CIT_FAKE_DOI": {"any": ["doi", "fabricat", "does not exist", "invalid doi", "10.9999"]},
    "CIT_WRONG_AUTHOR": {"any": ["author", "wrong author", "nonexistent", "mismatch"]},
}


def adjudicate(defect_id: str, llm_text: str) -> bool:
    sig = SIGNATURES.get(defect_id)
    if not sig:
        return False
    t = llm_text.lower()
    anys = [s.lower() for s in sig.get("any", [])]
    return any(s in t for s in anys)

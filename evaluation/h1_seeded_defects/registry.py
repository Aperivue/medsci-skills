"""Defect registry for the E1 seeded-defect benchmark.

One DefectSpec per defect type. ``demos`` lists the input sources the defect can
be cleanly attributed in ("fixture" = the synthetic citation fixture). One
defect is injected per temp copy, one detector judged per defect, so attribution
is unambiguous. Network-required citation defects (FABRICATED/MISMATCH) are
marked and recorded NOT_RUN unless --online is passed.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DefectSpec:
    defect_id: str
    defect_class: str
    detector_id: str
    injector: str
    expected_codes: tuple
    demos: tuple
    target_file: str            # relative to demo root; fixture file for "fixture"
    network_required: bool = False
    injector_args: dict = field(default_factory=dict)


MANUSCRIPT = "manuscript/manuscript.md"
ALL_DEMOS = ("01_wisconsin_bc", "02_metafor_bcg", "03_nhanes_obesity")

REGISTRY: list[DefectSpec] = [
    # --- style ---
    DefectSpec("STY_SECTION_SYMBOL", "style", "classical_style",
               "inject_section_symbol", ("SECTION_SYMBOL",), ALL_DEMOS, MANUSCRIPT),
    DefectSpec("STY_AI_DISCLOSURE", "style", "classical_style",
               "inject_inbody_ai_disclosure", ("INBODY_AI_DISCLOSURE",), ALL_DEMOS, MANUSCRIPT),
    DefectSpec("STY_EM_DASH", "style", "classical_style",
               "inject_em_dashes", ("EM_DASH_OVERUSE",), ALL_DEMOS, MANUSCRIPT),

    # --- scope ---
    DefectSpec("SCO_PROGNOSTIC", "scope", "scope_coherence",
               "inject_prognostic_conclusion", ("CROSS_SECTIONAL_PROGNOSTIC",),
               ("03_nhanes_obesity",), MANUSCRIPT),

    # --- cohort / arithmetic ---
    DefectSpec("COH_CASCADE_SUM", "cohort", "cohort_arithmetic",
               "inject_cascade_sum", ("CASCADE_SUM",), ("03_nhanes_obesity",), MANUSCRIPT),
    DefectSpec("COH_RATE_BACKCALC", "cohort", "cohort_arithmetic",
               "inject_rate_backcalc", ("RATE_BACKCALC",), ("03_nhanes_obesity",), MANUSCRIPT),

    # --- artifact coverage (synthetic fixture: demos place Results under
    #     sub-headings, so the forward check cannot isolate Results there) ---
    DefectSpec("ART_PROMISED_ABSENT", "artifact_coverage", "artifact_coverage",
               "inject_promised_absent", ("PROMISED_ABSENT",), ("fixture_artifact",), "clean.md"),

    # --- reporting framework ---
    DefectSpec("FRM_BASE_MISSING", "framework", "framework_naming",
               "inject_base_missing", ("BASE_MISSING",), ALL_DEMOS, MANUSCRIPT),
    DefectSpec("FRM_HYPHEN_MIX", "framework", "framework_naming",
               "inject_hyphen_mix", ("HYPHEN_MIX",), ALL_DEMOS, MANUSCRIPT),

    # --- generated code (py + R) ---
    DefectSpec("GEN_MISSING_SEED_PY", "generated_code", "generated_code",
               "inject_missing_seed", ("MISSING_SEED",), ("01_wisconsin_bc",),
               "analysis/analyze.py"),
    DefectSpec("GEN_MISSING_SEED_R", "generated_code", "generated_code",
               "inject_missing_seed", ("MISSING_SEED",), ("02_metafor_bcg",),
               "analysis/meta_analysis.R"),
    DefectSpec("GEN_ABS_PATH_PY", "generated_code", "generated_code",
               "inject_abs_path", ("HARDCODED_ABS_PATH",), ("01_wisconsin_bc",),
               "analysis/analyze.py"),
    DefectSpec("GEN_ABS_PATH_R", "generated_code", "generated_code",
               "inject_abs_path", ("HARDCODED_ABS_PATH",), ("02_metafor_bcg",),
               "analysis/meta_analysis.R"),
    DefectSpec("GEN_INPLACE_OVERWRITE_PY", "generated_code", "generated_code",
               "inject_inplace_overwrite", ("INPLACE_SOURCE_OVERWRITE",),
               ("01_wisconsin_bc",), "analysis/analyze.py"),

    # --- citation (synthetic fixture; offline-detectable) ---
    DefectSpec("CIT_PAGINATION", "citation", "verify_refs",
               "inject_pagination_placeholder", ("PAGINATION_PLACEHOLDER",),
               ("fixture",), "clean.bib"),
    DefectSpec("CIT_DUPLICATE", "citation", "verify_refs",
               "inject_duplicate_ref", ("DUPLICATE",), ("fixture",), "clean.bib"),
    DefectSpec("CIT_UNDEFINED_KEY", "citation", "citation_keys",
               "inject_undefined_citekey", ("UNDEFINED",), ("fixture",), "clean.md"),

    # --- citation (network-required; NOT_RUN unless --online) ---
    DefectSpec("CIT_FAKE_DOI", "citation", "verify_refs",
               "inject_fake_doi", ("FABRICATED",), ("fixture",), "clean.bib",
               network_required=True),
    DefectSpec("CIT_WRONG_AUTHOR", "citation", "verify_refs",
               "inject_wrong_author", ("MISMATCH",), ("fixture",), "clean.bib",
               network_required=True),
]

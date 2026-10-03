#!/usr/bin/env python3
"""Every detector's JSON output must name the detector that produced it.

A verification layer whose artifacts cannot be traced back to the check that produced
them is only half a verification layer. Until now the qc/*.json envelopes carried the
findings but not the finding's author: a consumer aggregating a project's qc directory —
a dashboard, an audit trail, the review-harvest precision ledger — had to infer the
detector from the *filename*, which is chosen freely at the call site (`--out qc/cs3.json`,
`--out qc/v13_scope.json`). Two runs of one detector under different filenames read as two
detectors; one detector run under an unexpected filename read as none.

So the contract is: any detector that emits JSON emits `"detector": "<its own id>"` in the
envelope. This gate enforces it statically, so a new detector cannot ship without it.

It is deliberately a source check rather than an execution check: detectors need fixtures,
credentials, and sometimes a network to run, but the envelope key is a literal in the
source and can be verified without any of that.

Second contract — the verdict vocabulary (docs/detector-conventions.md). A detector's
`summary.verdict` is one of VERDICT_VOCAB, so that "not checked" (NOT_ASSESSED) can never be
spelled like "no problem" (OK), and a consumer does not need a per-detector dictionary of
synonyms. This is a ratchet, not a rewrite: detectors that did not conform when the contract
was written are listed in GRANDFATHERED with what they emit today, so the gate passes on the
current tree and fails for
  * a new detector whose summary.verdict is outside the vocabulary or cannot be read,
  * a grandfathered detector that starts emitting a value its entry does not record, and
  * a stale entry (the detector conforms now, emits fewer outliers, or no longer exists) —
    so the list can only shrink.

What the verdict check can see, stated rather than implied: it reads SOURCE, not output.
It finds `summary.verdict` written as
  * `"summary": {..., "verdict": <expr>}` in a dict literal,
  * `summary = {..., "verdict": <expr>}`, or
  * `summary["verdict"] = <expr>` / `<x>["summary"]["verdict"] = <expr>`,
and resolves <expr> through string literals, `a if c else b`, `a or b`, and a local name whose
assignments in the same function are themselves resolvable. It does NOT see a verdict computed
any other way (a report-object property, a lookup table, a value read from input), a verdict at
the envelope top level, the stdout final line, or the exit code. A detector whose verdict it
cannot read is not counted as conforming: it fails unless it is grandfathered with a reason.

Exit 0 when every JSON-emitting detector self-identifies and every summary.verdict conforms or
is grandfathered exactly. With --strict, exit 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Same discovery globs as validate_catalog_consistency.py / gen_detectors_catalog_json.py,
# so this gate covers exactly the counted detector suite.
DETECTOR_GLOBS = ("check_*.py", "detect_*.py", "derive_*.py", "verify_refs.py")

# A detector that never writes JSON has no envelope to label. Listed explicitly rather
# than inferred, so that adding a JSON output to one of them trips this gate.
NO_JSON_OUTPUT = {
    "check_checklist_exists",
    "check_citation_keys",
}

# The summary.verdict vocabulary. OK and MAJOR_CANDIDATE are what the conforming majority
# already emits; NOT_ASSESSED is the established spelling (check_exclusion_code_validity) for a
# run that could not check its input. A Minor-only run is OK with summary.n_minor > 0 — the
# majority's existing behaviour — so no fourth value is introduced.
VERDICT_VOCAB = ("OK", "MAJOR_CANDIDATE", "NOT_ASSESSED")

# path -> (out-of-vocabulary summary.verdict values the gate reads today, reason).
# None = the gate reads no summary.verdict in this detector at all; the reason then says what
# it emits instead. Remove an entry when its detector conforms; the gate fails until you do.
_TOP = "verdict at the envelope top level, not summary.verdict: "
_PROP = "verdict is a report-object property at the envelope top level: "
_NONE = "no envelope verdict; the outcome is per-claim verdicts, counts and the exit code"
GRANDFATHERED: dict[str, tuple[frozenset[str] | None, str]] = {
    # -- summary.verdict readable, values outside the vocabulary --------------------------
    "skills/check-reporting/scripts/check_framework_naming.py": (frozenset({"FLAG"}), "Minor-only run reports FLAG instead of OK"),
    "skills/imaging-data/scripts/check_normalizer_domain.py": (frozenset({"FLAG", "MAJOR"}), "MAJOR instead of MAJOR_CANDIDATE; Minor-only run reports FLAG"),
    "skills/model-scaffold/scripts/check_training_hygiene.py": (frozenset({"INCOMPLETE"}), "partial coverage reported as INCOMPLETE rather than NOT_ASSESSED"),
    "skills/self-review/scripts/check_baseline_drift.py": (frozenset({"DRIFT_FLAGS"}), "any finding reports DRIFT_FLAGS; no Major/Minor split in the verdict"),
    "skills/self-review/scripts/check_claim_artifact.py": (frozenset({"REVIEW"}), "Minor-only run reports REVIEW instead of OK"),
    "skills/self-review/scripts/check_classical_style.py": (frozenset({"FLAG"}), "Minor-only run reports FLAG instead of OK"),
    "skills/self-review/scripts/check_editorial_impression.py": (frozenset({"IMPRESSION_FLAGS"}), "any finding reports IMPRESSION_FLAGS; no Major/Minor split in the verdict"),
    "skills/self-review/scripts/check_emphasis_density.py": (frozenset({"REVIEW"}), "any finding reports REVIEW; no Major/Minor split in the verdict"),
    "skills/self-review/scripts/check_figure_citation.py": (frozenset({"REVIEW"}), "Minor-only run reports REVIEW instead of OK"),
    "skills/self-review/scripts/check_rounded_delta.py": (frozenset({"REVIEW"}), "any finding reports REVIEW; no Major/Minor split in the verdict"),
    # -- verdict present, but not where the gate reads it ---------------------------------
    "skills/academic-aio/scripts/check_summary_box.py": (None, _TOP + "CONFORMANT / ADVISORY / NONCONFORMANT"),
    "skills/clean-data/scripts/check_reverse_coding.py": (None, _TOP + "OK / REVERSE_CODING_SUSPECT / REVERSE_CODING_LIKELY"),
    "skills/make-figures/scripts/derive_figure_legend_counts.py": (None, _TOP + "OK / NOT_CHECKED / MISMATCH"),
    "skills/revise/scripts/check_density_complaint.py": (None, _TOP + "OK / DENSITY_COMPLAINT_UNADDRESSED"),
    "skills/self-review/scripts/check_confounding_completeness.py": (None, _TOP + "OK / MAJOR_CANDIDATE (values conform, placement does not)"),
    "skills/sync-submission/scripts/check_disclosure_availability.py": (None, _TOP + "CLEAN / ADVISORY / BLOCKER"),
    "skills/sync-submission/scripts/check_wordcount_cap.py": (None, _TOP + "OK / WORDCOUNT_NEAR_CAP / WORDCOUNT_OVER_CAP"),
    "skills/sync-submission/scripts/detect_copy_divergence.py": (None, _TOP + "OK / DIVERGENT"),
    "skills/peer-review/scripts/check_pdf_injection.py": (None, _PROP + "CLEAN / SUSPICIOUS / INJECTION DETECTED"),
    "skills/peer-review/scripts/check_review_request_types.py": (None, _PROP + "OK / REQUEST-TYPE VIOLATIONS"),
    "skills/self-review/scripts/check_analysis_definitions.py": (None, _PROP + "OK / UNDEFINED ANALYSES"),
    "skills/self-review/scripts/check_dta_denominators.py": (None, _PROP + "OK / DENOMINATOR MISMATCH"),
    "skills/self-review/scripts/check_nested_group_comparison.py": (None, _PROP + "OK / NESTED COMPARISON FOUND"),
    "skills/self-review/scripts/check_paired_difference_estimator.py": (None, _PROP + "OK / ESTIMATOR PROBLEM"),
    "skills/self-review/scripts/check_reported_p_from_counts.py": (None, _PROP + "OK / P ALPHA CROSSING / NON-REPRODUCIBLE P"),
    "skills/self-review/scripts/check_table_percentages.py": (None, _PROP + "OK / MISMATCH FOUND"),
    # -- no envelope-level verdict ---------------------------------------------------------
    "skills/analyze-stats/scripts/check_separation.py": (None, "per-predictor status clear / separated / not_run; summary holds counts per finding verdict"),
    "skills/check-reporting/scripts/check_checklist_version.py": (None, _NONE),
    "skills/check-reporting/scripts/check_prisma_figure.py": (None, "per-row status PRESENT / MISMATCH / MISSING; no envelope verdict"),
    "skills/clean-data/scripts/check_structural_zero.py": (None, _NONE),
    "skills/contribute/scripts/check_contribution_safety.py": (None, "summary holds counts per severity; no verdict field"),
    "skills/humanize/scripts/check_rewrite_fidelity.py": (None, _NONE),
    "skills/humanize/scripts/check_sentence_variety.py": (None, _NONE),
    "skills/imaging-data/scripts/check_dataset_profile.py": (None, "summary holds counts only; no verdict field"),
    "skills/lit-sync/scripts/check_citekey_provenance.py": (None, "per-entry verdict OK / FILENAME / INVENTED / ...; no envelope verdict"),
    "skills/manage-refs/scripts/check_bib_title_markup.py": (None, "summary holds counts only; no verdict field"),
    "skills/manage-refs/scripts/check_csl_render.py": (None, _NONE + "; exit 1 also covers checks that could not run"),
    "skills/manage-refs/scripts/check_xref.py": (None, "summary holds counts only; no verdict field"),
    "skills/meta-analysis/scripts/check_pool_consistency.py": (None, _NONE),
    "skills/model-selection/scripts/check_model_provenance.py": (None, "summary holds major/minor counts only; no verdict field"),
    "skills/peer-review/scripts/check_review_boxes.py": (None, "summary holds counts only; no verdict field"),
    "skills/peer-review/scripts/check_review_length.py": (None, "summary holds counts only; no verdict field"),
    "skills/peer-review/scripts/check_self_improvement_claims.py": (None, "summary holds counts only; no verdict field"),
    "skills/present-paper/scripts/check_deck_budget.py": (None, _NONE),
    "skills/present-paper/scripts/check_diagram_edges.py": (None, _NONE),
    "skills/present-paper/scripts/check_font_portability.py": (None, _NONE),
    "skills/present-paper/scripts/check_slide_tells.py": (None, "summary holds counts only; no verdict field"),
    "skills/present-paper/scripts/check_text_overflow.py": (None, _NONE),
    "skills/revise/scripts/check_response_claims.py": (None, "summary holds counts only; no verdict field"),
    "skills/search-lit/scripts/check_doi_record_match.py": (None, _NONE),
    "skills/self-review/scripts/check_aphorism_density.py": (None, _NONE),
    "skills/self-review/scripts/check_perspective_structure.py": (None, _NONE),
    "skills/self-review/scripts/check_reference_adequacy.py": (None, "summary holds counts only; no verdict field"),
    "skills/self-review/scripts/check_reviewer_team_consistency.py": (None, _NONE),
    "skills/self-review/scripts/check_rhetorical_density.py": (None, _NONE),
    "skills/sync-submission/scripts/check_asset_anonymization.py": (None, "summary holds counts only; no verdict field"),
    "skills/sync-submission/scripts/check_checklist_dump_leak.py": (None, "summary holds counts only; no verdict field"),
    "skills/sync-submission/scripts/check_credit_integrity.py": (None, _NONE),
    "skills/sync-submission/scripts/check_cross_artifact_stale.py": (None, "summary holds counts only; no verdict field"),
    "skills/sync-submission/scripts/check_marked_manuscript.py": (None, "summary holds counts only; no verdict field"),
    "skills/sync-submission/scripts/check_portal_field_residue.py": (None, "summary holds counts only; no verdict field"),
    "skills/sync-submission/scripts/check_portal_mirror.py": (None, _NONE),
    "skills/verify-refs/scripts/check_claim_fidelity.py": (None, _NONE),
    "skills/verify-refs/scripts/verify_refs.py": (None, _NONE),
    "skills/write-paper/scripts/check_placeholders.py": (None, "summary holds counts only; no verdict field"),
}


def _resolve(expr: ast.AST, scope: ast.AST, depth: int = 0) -> tuple[set[str], bool]:
    """String values `expr` can take, and whether some branch could not be read."""
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return {expr.value}, False
    if isinstance(expr, ast.IfExp):
        branches = [expr.body, expr.orelse]
    elif isinstance(expr, ast.BoolOp):
        branches = list(expr.values)
    elif isinstance(expr, ast.Name) and depth < 3:
        branches = []
        for n in ast.walk(scope):
            if not isinstance(n, (ast.Assign, ast.AnnAssign)) or n.value is None:
                continue
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                if isinstance(t, ast.Name) and t.id == expr.id:
                    branches.append(n.value)
                elif isinstance(t, ast.Tuple) and isinstance(n.value, ast.Tuple):
                    for el, v in zip(t.elts, n.value.elts):
                        if isinstance(el, ast.Name) and el.id == expr.id:
                            branches.append(v)
        if not branches:
            return set(), True
        values, unread = set(), False
        for b in branches:
            v, u = _resolve(b, scope, depth + 1)
            values |= v
            unread |= u
        return values, unread
    else:
        return set(), True
    values, unread = set(), False
    for b in branches:
        v, u = _resolve(b, scope, depth)
        values |= v
        unread |= u
    return values, unread


def summary_verdicts(src: str) -> tuple[int, set[str], bool]:
    """(number of summary.verdict sites, values read, whether any site was unreadable)."""
    tree = ast.parse(src)
    scope_of: dict[ast.AST, ast.AST] = {}

    def visit(node: ast.AST, scope: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            scope_of[child] = scope
            visit(child, child if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else scope)

    visit(tree, tree)

    def verdict_in(d: ast.Dict) -> list[ast.AST]:
        return [v for k, v in zip(d.keys, d.values)
                if isinstance(k, ast.Constant) and k.value == "verdict"]

    def is_summary(e: ast.AST) -> bool:
        return (isinstance(e, ast.Name) and e.id == "summary") or (
            isinstance(e, ast.Subscript) and isinstance(e.slice, ast.Constant)
            and e.slice.value == "summary")

    sites: list[tuple[ast.AST, ast.AST]] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "summary" and isinstance(v, ast.Dict):
                    sites += [(e, n) for e in verdict_in(v)]
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "summary" and isinstance(n.value, ast.Dict):
                    sites += [(e, n) for e in verdict_in(n.value)]
                if (isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
                        and t.slice.value == "verdict" and is_summary(t.value)):
                    sites.append((n.value, n))

    values, unread = set(), False
    for expr, at in sites:
        v, u = _resolve(expr, scope_of.get(at, tree))
        values |= v
        unread |= u
    return len(sites), values, unread


def audit_verdicts(paths: list[Path], grandfathered: dict | None = None) -> list[str]:
    gf = GRANDFATHERED if grandfathered is None else grandfathered
    problems: list[str] = []
    seen: set[str] = set()
    vocab = ", ".join(VERDICT_VOCAB)
    for p in paths:
        if p.stem in NO_JSON_OUTPUT:
            continue
        rel = p.relative_to(ROOT).as_posix()
        seen.add(rel)
        n_sites, values, unread = summary_verdicts(p.read_text(encoding="utf-8"))
        outliers = values - set(VERDICT_VOCAB)
        readable = n_sites > 0 and not unread
        if rel in gf:
            recorded, _ = gf[rel]
            if recorded is None:
                if n_sites:
                    problems.append(
                        f"{rel}: grandfathered as having no readable summary.verdict, but the gate "
                        f"now reads one {sorted(values)}"
                        + (" (partly unreadable)" if unread else "")
                        + " — if it conforms, remove the GRANDFATHERED entry; otherwise make it conform.")
            elif not readable:
                problems.append(f"{rel}: grandfathered with {sorted(recorded)}, but the gate can no longer "
                                "read its summary.verdict — make it readable and conforming.")
            elif outliers - recorded:
                problems.append(f"{rel}: summary.verdict gained {sorted(outliers - recorded)}, outside "
                                f"the vocabulary ({vocab}). A grandfathered detector may not add values.")
            elif not outliers:
                problems.append(f"{rel}: now conforms ({sorted(values)}) — remove its stale GRANDFATHERED entry.")
            elif outliers != recorded:
                problems.append(f"{rel}: no longer emits {sorted(recorded - outliers)} — shrink its "
                                f"GRANDFATHERED entry to {sorted(outliers)}.")
            continue
        if not n_sites:
            problems.append(f"{rel}: no summary.verdict the gate can read. Emit "
                            f'"summary": {{..., "verdict": <one of {vocab}>}} '
                            "(docs/detector-conventions.md).")
        elif unread:
            problems.append(f"{rel}: summary.verdict is computed in a way the gate cannot read "
                            f"statically; write it from literals in {vocab}.")
        elif outliers:
            problems.append(f"{rel}: summary.verdict uses {sorted(outliers)}, outside the vocabulary "
                            f"({vocab}) — docs/detector-conventions.md.")
    for rel in sorted(set(gf) - seen):
        problems.append(f"{rel}: GRANDFATHERED entry names no current JSON-emitting detector — remove it.")
    return problems


def detectors() -> list[Path]:
    return sorted(
        p for g in DETECTOR_GLOBS for p in (ROOT / "skills").glob(f"*/scripts/{g}")
    )


def audit() -> list[str]:
    problems: list[str] = []
    for p in detectors():
        stem = p.stem
        src = p.read_text(encoding="utf-8")
        writes_json = "json.dump" in src

        # The contract is about the ARTIFACT: the qc JSON must name the detector that wrote it.
        # This check reads source, which is a proxy — so it has to accept both honest ways of
        # satisfying the contract, or it fails a detector that does the right thing:
        #
        #   "detector": "check_x"        written as a literal, or
        #   DETECTOR = "check_x"  …  {"detector": DETECTOR, …}   named once, used everywhere
        #
        # The second is better practice (the id appears in the envelope AND on each finding without
        # being retyped). Rejecting it would push authors toward copy-pasted string literals to
        # appease a checker, which is how a gate starts making the code worse.
        literal = re.search(rf'"detector"\s*:\s*"{re.escape(stem)}"', src) is not None
        via_const = (
            re.search(rf'^DETECTOR\s*=\s*"{re.escape(stem)}"\s*$', src, re.MULTILINE) is not None
            and re.search(r'"detector"\s*:\s*DETECTOR\b', src) is not None
        )
        identifies = literal or via_const

        if stem in NO_JSON_OUTPUT:
            if writes_json:
                problems.append(
                    f"{p.relative_to(ROOT)}: listed as emitting no JSON, but it calls json.dump* — "
                    'remove it from NO_JSON_OUTPUT and add "detector": "%s" to the envelope' % stem
                )
            continue

        if not writes_json:
            problems.append(
                f"{p.relative_to(ROOT)}: emits no JSON. If that is intended, add '{stem}' to "
                "NO_JSON_OUTPUT in this script (with a reason); otherwise give it a JSON envelope."
            )
        elif not identifies:
            problems.append(
                f'{p.relative_to(ROOT)}: JSON envelope does not carry "detector": "{stem}". '
                "A qc artifact must name the detector that wrote it — the filename is chosen by "
                "the caller and cannot be trusted to identify it."
            )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="exit 1 on any violation (CI gate)")
    a = ap.parse_args()

    found = detectors()
    problems = audit() + audit_verdicts(found)
    if problems:
        print(f"DETECTOR_ENVELOPE_DRIFT: {len(problems)} problem(s) across {len(found)} detectors\n")
        for p in problems:
            print(f"  - {p}")
        return 1 if a.strict else 0

    labeled = len(found) - len(NO_JSON_OUTPUT)
    print(f"OK: all {labeled} JSON-emitting detectors self-identify ({len(found)} detectors scanned); "
          f"summary.verdict within {{{', '.join(VERDICT_VOCAB)}}} for {labeled - len(GRANDFATHERED)}, "
          f"{len(GRANDFATHERED)} grandfathered exactly as recorded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

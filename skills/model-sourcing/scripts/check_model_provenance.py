#!/usr/bin/env python3
"""Model-provenance gate for a third-party model you are about to build a study on.

Choosing an architecture is a literature question and `/architecture-zoo` answers it. Choosing a
*concrete artifact* — this repository, this checkpoint, this revision — is a provenance question,
and the two facts a researcher usually checks (the licence, the citation count) are the two that
cannot answer it.

The failure this gate exists for is the quietest one. A method developed and tuned against a
benchmark family will be evaluated by the next person *on that same benchmark*, and the resulting
number will read like validation while being closer to a training-set score. Nothing in the
repository says so: the licence is clean, the paper is highly cited, the task matches, the code
runs. The conflict lives in the relationship between two facts that sit in different documents —
what the model was developed on, and what you are about to evaluate it on — and it is visible
only when they are written down side by side. That is what the dossier is for.

The gate reads a declarative **model dossier** and decides each finding by set arithmetic over
it. It never fetches a repository, never resolves a licence from the network, and never infers a
fact the dossier does not state: an unstated fact is a finding, not something to guess at.

CHECKS (verdicts):
  MAJOR
  1. BENCHMARK_PROVENANCE_CONFLICT  a dataset the model was developed/tuned/competed on also
                                    appears among your evaluation arms. That arm does not
                                    independently test the model, however held-out it is for you.
  2. EVAL_DATA_IN_TRAINING          an evaluation arm's dataset appears in the model's own
                                    training corpus — the strong form of the same problem.
  3. LICENCE_UNSTATED               no licence recorded. Not "probably permissive": unstated.
  4. LICENCE_INCOMPATIBLE           the licence forbids the declared intended use (a
                                    non-commercial or research-only licence under commercial or
                                    deployment intent).
  5. WEIGHTS_PROVENANCE_UNKNOWN     pretrained weights are used and the corpus they were trained
                                    on is not stated — so what is in them cannot be reasoned
                                    about, including whether your evaluation set is.

  MINOR (each is a fact to record, not necessarily a defect)
  6. TASK_MISMATCH                  the model's declared task differs from the study's.
  7. NO_VERSION_PIN                 no commit, tag or revision — "we used nnU-Net" is not a
                                    reproducible statement.
  8. VALIDATION_UNREPORTED          no reported validation (dataset + metric) recorded.
  9. HARDWARE_UNVERIFIED            hardware compatibility claimed but never executed.
 10. LICENCE_UNVERIFIED             a licence is named but its source file is not, so it came
                                    from a badge or a memory rather than from the artifact.

DOSSIER (JSON)
  {
    "model": "nnU-Net v2",
    "source": {"kind": "github", "url": "...", "version": "v2.5.1", "commit": "abc1234"},
    "licence": {"spdx": "Apache-2.0", "verified_from": "LICENSE at the pinned commit"},
    "intended_use": "research",              // research | commercial | clinical_deployment
    "weights": {"pretrained": false},        // if true, add "trained_on": [...]
    "task": {"model": "3d_ct_organ_segmentation", "study": "3d_ct_organ_segmentation"},
    "reported_validation": [{"dataset": "MSD", "metric": "Dice", "source": "Nat Methods 2021"}],
    "developed_on": ["Medical Segmentation Decathlon"],
    "evaluation_arms": [{"name": "internal", "dataset": "MSD Task09 Spleen"},
                        {"name": "external", "dataset": "AMOS22"}],
    "hardware": {"claimed": "any CUDA GPU", "verified_on": "GTX 1080 Ti", "verified": true}
  }

  Dataset names are matched as **token sequences**, so "MSD Task09 Spleen" matches "MSD" while
  "MS" does not match "MSD", plus a small alias table for families that are routinely written
  two ways (MSD / Decathlon). Matching never falls back to substring search.

INPUTS
  --dossier   model dossier JSON (required).

OUTPUT
  A findings table (stdout) and, with --out, a JSON artifact.
  Exit 1 under --strict when any Major finding exists. Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Families routinely written more than one way. Values are canonical token sequences.
DATASET_ALIASES = {
    "decathlon": ["msd"],
    "medicalsegmentationdecathlon": ["msd"],
    "medical": ["msd"],  # only via the multi-token form below
}
MULTI_TOKEN_ALIASES = {
    ("medical", "segmentation", "decathlon"): ["msd"],
    ("the", "medical", "segmentation", "decathlon"): ["msd"],
}
NONCOMMERCIAL_MARKERS = ("-nc-", "-nc", "noncommercial", "non-commercial",
                         "research-only", "researchonly", "cc-by-nc")
RESTRICTED_USES = {"commercial", "clinical_deployment", "clinical-deployment", "deployment",
                   "product"}


def _tokens(name: str) -> tuple[str, ...]:
    toks = tuple(t for t in re.split(r"[^a-z0-9]+", str(name).strip().lower()) if t)
    if toks in MULTI_TOKEN_ALIASES:
        return tuple(MULTI_TOKEN_ALIASES[toks])
    if len(toks) == 1 and toks[0] in DATASET_ALIASES and toks[0] != "medical":
        return tuple(DATASET_ALIASES[toks[0]])
    return toks


def datasets_match(a: str, b: str) -> bool:
    """True when two dataset names denote the same corpus (or one is a family of the other).

    Token-sequence prefix, never substring: ('msd','task09','spleen') matches ('msd',), and
    ('ms',) does not match ('msd',).
    """
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    short, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return long_[:len(short)] == short


def _norm(s) -> str:
    return str(s).strip().lower() if s is not None else ""


def analyze(dossier_path: str) -> dict:
    d = json.loads(Path(dossier_path).read_text(encoding="utf-8"))
    claims: list[dict] = []

    def claim(verdict: str, severity: str, detail: str, where: list[str] | None = None) -> None:
        claims.append({"verdict": verdict, "severity": severity, "detail": detail,
                       "where": sorted(where or [])[:12], "n_where": len(where or [])})

    arms = d.get("evaluation_arms") or []
    arm_datasets = [(a.get("name") or "?", a.get("dataset") or "") for a in arms]

    # ---- the conflict neither the licence nor the citation count reveals ------
    developed_on = d.get("developed_on") or []
    hits = [f"{nm} ({ds}) <- developed on {dev}"
            for nm, ds in arm_datasets for dev in developed_on if datasets_match(ds, dev)]
    if hits:
        claim("BENCHMARK_PROVENANCE_CONFLICT", "Major",
              "an evaluation arm uses a dataset the model was developed or tuned on; that arm "
              "does not independently test the model, no matter how held-out the split is for "
              "you. Report it as a demonstration of the pipeline and put the evidence on an arm "
              "whose data post-dates the model", hits)

    # ---- the strong form: your eval set is in the weights ---------------------
    weights = d.get("weights") or {}
    pretrained = bool(weights.get("pretrained"))
    trained_on = weights.get("trained_on") or []
    leaks = [f"{nm} ({ds}) in the training corpus ({tr})"
             for nm, ds in arm_datasets for tr in trained_on if datasets_match(ds, tr)]
    if leaks:
        claim("EVAL_DATA_IN_TRAINING", "Major",
              "an evaluation arm's dataset appears in the corpus the weights were trained on; "
              "the resulting number is a training-set score", leaks)
    if pretrained and not trained_on:
        claim("WEIGHTS_PROVENANCE_UNKNOWN", "Major",
              "pretrained weights are used and the corpus behind them is not stated, so it "
              "cannot be established whether your evaluation data is inside them")

    # ---- licence -------------------------------------------------------------
    lic = d.get("licence") or d.get("license") or {}
    spdx = _norm(lic.get("spdx") or lic.get("name"))
    use = _norm(d.get("intended_use"))
    if not spdx:
        claim("LICENCE_UNSTATED", "Major",
              "no licence recorded. An unstated licence is not a permissive one — it is an "
              "unanswered question about whether the work may be used or redistributed at all")
    else:
        if not lic.get("verified_from"):
            claim("LICENCE_UNVERIFIED", "Minor",
                  f"licence '{spdx}' is named but the file it was read from is not recorded; "
                  "a badge in a README is not the licence")
        if use in RESTRICTED_USES and any(m in spdx for m in NONCOMMERCIAL_MARKERS):
            claim("LICENCE_INCOMPATIBLE", "Major",
                  f"licence '{spdx}' restricts use to non-commercial or research purposes while "
                  f"the declared intended use is '{use}'")

    # ---- task, pin, validation, hardware -------------------------------------
    task = d.get("task") or {}
    tm, ts = _norm(task.get("model")), _norm(task.get("study"))
    if tm and ts and tm != ts:
        claim("TASK_MISMATCH", "Minor",
              f"the model's task ('{tm}') is not the study's task ('{ts}'); a transfer step and "
              "its own validation are required, not just a checkpoint")

    src = d.get("source") or {}
    if not (src.get("commit") or src.get("version") or src.get("revision") or src.get("tag")):
        claim("NO_VERSION_PIN", "Minor",
              "no commit, tag or revision recorded; 'we used <model>' does not identify what ran "
              "and cannot be reproduced once the default branch moves")

    if not (d.get("reported_validation") or []):
        claim("VALIDATION_UNREPORTED", "Minor",
              "no reported validation (dataset + metric + source) recorded for the model as "
              "published; there is then no prior expectation to compare your own numbers against")

    hw = d.get("hardware") or {}
    if hw.get("claimed") and not hw.get("verified"):
        claim("HARDWARE_UNVERIFIED", "Minor",
              f"hardware support is claimed ('{hw.get('claimed')}') but never executed; support "
              "matrices and what the stack actually runs on are different statements")

    majors = [c for c in claims if c["severity"] == "Major"]
    return {
        # the artifact names its own author: a qc filename is chosen by the caller and
        # cannot be trusted to identify what wrote it
        "detector": "check_model_provenance",
        "dossier": dossier_path,
        "model": d.get("model", ""),
        "n_arms": len(arms),
        "claims": claims,
        "summary": {"major": len(majors), "minor": len(claims) - len(majors)},
    }


def render(result: dict) -> str:
    lines = [f"Model provenance — {result['model'] or '(unnamed)'}  "
             f"({result['n_arms']} evaluation arm(s))", ""]
    if not result["claims"]:
        lines.append("  no findings — every provenance fact the gate checks is stated and consistent")
    for c in result["claims"]:
        lines.append(f"  [{c['severity']:<5}] {c['verdict']}")
        lines.append(f"           {c['detail']}")
        for w in c["where"]:
            lines.append(f"           - {w}")
    lines.append("")
    lines.append(f"  Major {result['summary']['major']}   Minor {result['summary']['minor']}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a third-party model's provenance dossier.")
    ap.add_argument("--dossier", required=True)
    ap.add_argument("--out")
    ap.add_argument("--strict", action="store_true", help="exit 1 when a Major finding exists")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not Path(a.dossier).exists():
        print(f"input error: dossier not found: {a.dossier}", file=sys.stderr)
        return 2
    try:
        result = analyze(a.dossier)
    except json.JSONDecodeError as exc:
        print(f"input error: dossier is not valid JSON: {exc}", file=sys.stderr)
        return 2

    if not a.quiet:
        print(render(result))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    return 1 if (a.strict and result["summary"]["major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

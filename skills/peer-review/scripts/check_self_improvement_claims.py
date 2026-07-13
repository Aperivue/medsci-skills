#!/usr/bin/env python3
"""A self-improvement claim is a claim about a *signal*. This checks the signal exists.

A growing class of medical-AI manuscripts reports that a system improved itself: an agent that
critiques and rewrites its own output, a pipeline trained on data it generated, an LLM used as
the judge that scores the training signal. The loop looks like a method — but every improvement
loop is a claim that some signal can substitute for human judgment, and the paper often never
says which signal that was.

Two failures are decidable by reading the text, and both are reviewed badly:

  1. THE SELF-CONFIRMING LOOP. When the generator and the evaluator are the same model, their
     biases correlate: the loop reinforces the errors the model is most *confident* about, and a
     self-critique "inherits the blind spots that produce confident fabrication". A reported gain
     may be the judge and the generator agreeing with each other, which is not evidence about the
     world. Naming GPT-4o as the system and GPT-4o as the judge, with no external validation of
     the judge, is that failure on the page.

  2. THE UNGROUNDED LOOP. Ungrounded self-critique converges to rewording, not correction — ten
     rounds across three providers produced a 55% decline in informational change, while a single
     verification step restored forward movement (DeVilling 2025, arXiv:2510.21861). A manuscript
     that claims improvement from a self-refinement loop and never names an external signal has
     reported evidence of *change*, not of improvement.

This is a lexical check, and it is deliberately conservative: it fires only when a self-improvement
claim is explicit AND the grounding vocabulary is absent from the entire text. A paper that
validates its LLM judge against human experts, or scores against held-out labels, does not fire —
even if it also self-refines, because then the signal exists and the rest is judgment (see the
`self_improving_system.md` domain probe, SI1-SI7).

Verdicts:
  SELF_CONFIRMING_EVALUATOR (major)  the system and the judge are the same model; the judge is
                                     never validated against anything outside the loop
  UNGROUNDED_SELF_LOOP (major)       an explicit self-refinement / self-critique / self-training
                                     claim, with no external verification vocabulary anywhere
  SELF_TRAINING_NO_REAL_DATA (minor) trained on model-generated data with no real-data mixing and
                                     no exogenous fraction reported (collapse risk)

Usage:
    check_self_improvement_claims.py --manuscript paper.md [--out qc/self_improvement.json] [--strict]

Exit 0 unless --strict and a major fires. Stdlib only; .docx read via python-docx when available.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- what a self-improvement loop is called, in the wild -------------------------------------
SELF_LOOP = re.compile(
    r"\bself[- ](?:refine|refinement|critique|criticism|correct|correction|improve|improvement|"
    r"improving|evolve|evolving|evolution|reward|rewarding|training|train|distill|distillation|"
    r"play|consistency|verification|evaluate|evaluation)\b"
    r"|\biterative(?:ly)? (?:refine|refines|refining|critiqu\w+|revis\w+|improv\w+)\b"
    r"|\brecursive(?:ly)? (?:improv\w+|refin\w+|train\w+)\b"
    r"|\bthe (?:model|agent|system) (?:critiques?|revises?|corrects?|improves?) its own\b",
    re.IGNORECASE,
)

# An LLM sitting in the judge seat.
JUDGE_CTX = re.compile(
    r"\b(?:llm[- ]as[- ]a?[- ]?judge|as (?:the |a )?judge|judge model|evaluator model|"
    r"reward model|used .{0,40}to (?:score|rate|judge|evaluate)|"
    r"(?:scored|rated|judged|evaluated|graded) by)\b",
    re.IGNORECASE,
)

# Model identifiers, coarse but specific enough not to catch prose.
MODEL = re.compile(
    r"\b(?:gpt[- ]?[0-9o][\w.-]*|chatgpt|claude[- ][\w.]+|claude[- ]?[0-9][\w.-]*|gemini[- ][\w.]+|"
    r"llama[- ]?[0-9][\w.-]*|mistral[\w.-]*|mixtral[\w.-]*|qwen[\w.-]*|deepseek[\w.-]*|"
    r"palm[- ]?2|med[- ]?palm[\w.-]*|phi[- ]?[0-9][\w.-]*|gemma[\w.-]*|grok[\w.-]*)\b",
    re.IGNORECASE,
)

# The system under study (as opposed to the judge).
SYSTEM_CTX = re.compile(
    r"\b(?:our (?:model|system|agent|pipeline|method|framework)|we (?:use|used|employ|employed|"
    r"fine[- ]?tun\w+|prompt\w*|built|develop\w+)|the (?:proposed|underlying|base|backbone) "
    r"(?:model|system|agent)|was (?:implemented|built) (?:with|using|on))\b",
    re.IGNORECASE,
)

# Any signal from outside the loop. If ANY of these appear, the paper has named a grounding
# signal and the rest is a judgment call for the reviewer, not a deterministic finding.
EXTERNAL_SIGNAL = re.compile(
    r"\b(?:ground[- ]truth|gold[- ]standard|reference standard|held[- ]?out|"
    r"human (?:expert|rater|reader|annotat\w+|evaluat\w+|review\w+)|expert (?:rater|reader|panel|"
    r"annotat\w+|review\w+|consensus)|radiologist\w*|clinician[- ]rated|physician[- ]rated|"
    r"inter[- ]rater|independent (?:test|validation|evaluation|annotation)|external validation|"
    r"labell?ed (?:test|validation) set|manual (?:annotation|review|validation)|"
    r"agreement with (?:human|expert|clinician)|validated against|"
    r"unit test\w*|test suite|execution feedback|compiler|formal verif\w+|"
    r"chart review|adjudicat\w+|registry[- ]linked outcome)\b",
    re.IGNORECASE,
)

# Training on model-generated data.
SELF_DATA = re.compile(
    r"\b(?:synthetic (?:data|cases?|examples?|samples?)|(?:model|self|llm)[- ]generated (?:data|"
    r"cases?|examples?|labels?|annotations?)|pseudo[- ]labell?\w+|self[- ]train\w+|"
    r"generated (?:its own|our own) training)\b",
    re.IGNORECASE,
)
REAL_DATA_MIX = re.compile(
    r"\b(?:real[- ]data|mixed with (?:real|human|original)|exogenous|human[- ]written|"
    r"replay|original (?:training )?(?:corpus|data)|held[- ]?out real|"
    r"fraction of (?:real|authentic)|combined with the original)\b",
    re.IGNORECASE,
)

WINDOW = 200  # chars around a match, when locating the model named in a role


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        try:
            from docx import Document  # type: ignore
        except ImportError:
            raise SystemExit(f"python-docx required to read {path}")
        return "\n".join(p.text for p in Document(str(path)).paragraphs)
    return path.read_text(encoding="utf-8", errors="replace")


def models_in_role(text: str, role: re.Pattern[str]) -> set[str]:
    """Model names appearing near a role cue (judge, or system-under-study)."""
    found: set[str] = set()
    for m in role.finditer(text):
        lo, hi = max(0, m.start() - WINDOW), min(len(text), m.end() + WINDOW)
        for mm in MODEL.finditer(text[lo:hi]):
            found.add(mm.group(0).lower())
    return found


def family(name: str) -> str:
    """gpt-4o and gpt-4-turbo are the same family: the biases that matter correlate."""
    return re.split(r"[- .]", name, maxsplit=1)[0]


def audit(path: Path) -> dict:
    text = read_text(path)
    findings: list[dict] = []

    loop_hits = [m.group(0) for m in SELF_LOOP.finditer(text)]
    grounded = EXTERNAL_SIGNAL.search(text) is not None

    if loop_hits and not grounded:
        findings.append(
            {
                "verdict": "UNGROUNDED_SELF_LOOP",
                "severity": "major",
                "evidence": sorted({h.lower() for h in loop_hits})[:6],
                "detail": (
                    "The manuscript claims improvement from a self-refinement / self-evaluation loop "
                    f"({', '.join(sorted({h.lower() for h in loop_hits})[:3])}) but names no signal from "
                    "outside that loop anywhere in the text — no ground truth, no held-out labels, no "
                    "human expert, no executable check. Ungrounded self-critique converges to rewording: "
                    "informational change fell 55% over ten rounds in a controlled study, while a single "
                    "verification step restored forward movement. What is reported is evidence of change, "
                    "not of improvement. Name the signal, and report the per-iteration trajectory."
                ),
            }
        )

    judges = models_in_role(text, JUDGE_CTX)
    systems = models_in_role(text, SYSTEM_CTX)
    shared = {j for j in judges if any(family(j) == family(s) for s in systems)}
    if shared and JUDGE_CTX.search(text) and not grounded:
        findings.append(
            {
                "verdict": "SELF_CONFIRMING_EVALUATOR",
                "severity": "major",
                "evidence": {"judge": sorted(judges), "system": sorted(systems),
                             "shared_family": sorted(shared)},
                "detail": (
                    f"The judge and the system under study are the same model family "
                    f"({', '.join(sorted(shared))}), and the judge is never validated against anything "
                    "outside the loop (no human expert, no ground truth, no held-out labels). When the "
                    "generator and the evaluator share weights their biases correlate: the loop "
                    "reinforces the errors the model is most confident about, and the reported gain may "
                    "be the judge and the generator agreeing with each other. Validate the judge against "
                    "an external standard and report the agreement, or use an independent evaluator."
                ),
            }
        )

    if SELF_DATA.search(text) and re.search(r"\btrain\w*|fine[- ]?tun\w+", text, re.I) \
            and not REAL_DATA_MIX.search(text):
        findings.append(
            {
                "verdict": "SELF_TRAINING_NO_REAL_DATA",
                "severity": "minor",
                "evidence": sorted({m.group(0).lower() for m in SELF_DATA.finditer(text)})[:5],
                "detail": (
                    "The system is trained on model-generated data with no mention of real-data mixing "
                    "or an exogenous fraction. If the externally grounded share of the training signal "
                    "goes to zero, degenerative dynamics follow — the distribution's tails are lost "
                    "first, which in a clinical model means the rare presentations. State the real-data "
                    "fraction and check the tail classes across rounds, not only aggregate accuracy."
                ),
            }
        )

    return {
        "detector": "check_self_improvement_claims",
        "manuscript": str(path),
        "self_improvement_claimed": bool(loop_hits),
        "external_signal_named": grounded,
        "findings": findings,
        "summary": {
            "major": sum(1 for f in findings if f["severity"] == "major"),
            "minor": sum(1 for f in findings if f["severity"] == "minor"),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manuscript", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--strict", action="store_true", help="exit 1 if a major verdict fires")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not a.manuscript.is_file():
        raise SystemExit(f"not found: {a.manuscript}")

    rep = audit(a.manuscript)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not a.quiet:
        claimed = "yes" if rep["self_improvement_claimed"] else "no"
        signal = "yes" if rep["external_signal_named"] else "NO"
        print(f"{a.manuscript.name}: self-improvement claimed: {claimed} | external signal named: {signal}")
        for f in rep["findings"]:
            print(f"  [{f['severity'].upper()}] {f['verdict']}: {f['detail']}")
        if not rep["findings"]:
            print("  OK — no ungrounded or self-confirming improvement claim detected")

    return 1 if (a.strict and rep["summary"]["major"]) else 0


if __name__ == "__main__":
    sys.exit(main())

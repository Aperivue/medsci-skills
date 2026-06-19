#!/usr/bin/env python3
"""Render references/trajectory_archetypes.md from the canonical YAML rubric.

The YAML (references/trajectory_archetypes.yaml) is the single source of truth.
This script regenerates the human-readable Markdown narrative from it so the two
can never drift. CI / the skill test runs `--check` to assert they are in sync.

Usage:
  python3 render_archetype_doc.py            # write the .md
  python3 render_archetype_doc.py --check     # exit 1 if the .md is stale
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is a declared dependency
    sys.stderr.write("ERROR: PyYAML is required (pip install pyyaml).\n")
    sys.exit(2)

HERE = Path(__file__).resolve().parent
YAML_PATH = HERE / "references" / "trajectory_archetypes.yaml"
MD_PATH = HERE / "references" / "trajectory_archetypes.md"

PROV_LABEL = {
    "source-derived": "`source-derived`",
    "rule-derived": "`rule-derived`",
    "unavailable": "`unavailable` [VERIFY]",
}


def _signal_line(sig: dict) -> str:
    prov = PROV_LABEL.get(sig.get("provenance", ""), sig.get("provenance", ""))
    weight = sig.get("weight", 0.0)
    narrative = sig.get("narrative", "").strip()
    line = f"- **{sig['id']}** ({prov}, weight {weight}) — {narrative}"
    note = sig.get("verify_note")
    if note:
        line += f" _{note.strip()}_"
    return line


def render(data: dict) -> str:
    out: list[str] = []
    out.append("<!-- GENERATED FILE — do not edit by hand.")
    out.append("     Source of truth: trajectory_archetypes.yaml")
    out.append("     Regenerate: python3 render_archetype_doc.py -->")
    out.append("")
    out.append("# Trajectory-Archetype Rubric")
    out.append("")
    out.append(f"Rubric version: **{data['rubric_version']}**")
    out.append("")
    out.append(
        "Classification output is an **explainable, multi-label heuristic — NOT an "
        "objective verdict**. Each surfaced label carries a score, a confidence band, "
        "and evidence drawn from the queried author's OWN fetched PMIDs. Below the "
        "minimum sample, below the score threshold, or with a negative rule firing, the "
        "archetype is reported as `insufficient evidence`."
    )
    out.append("")
    out.append("## Provenance tags")
    out.append("")
    out.append("- `source-derived` — a raw PubMed record field (n_authors, year, pub_types, study_type).")
    out.append("- `rule-derived` — a threshold / share / fraction / term-match computed over raw fields.")
    out.append(
        "- `unavailable` [VERIFY] — cannot be computed in the PubMed-only MVP "
        "(h-index, citation counts/half-life, venue-impact tier, repository/preprint "
        "links, cross-platform divergence). Weight 0; excluded from the score denominator; never fabricated."
    )
    out.append("")
    out.append("## Scoring")
    out.append("")
    out.append("- A signal is *computable for a dataset* iff its provenance is `source-derived` or `rule-derived` AND all its required columns are present.")
    out.append("- `score = (sum of weights of fired computable signals) / (sum of weights of all computable signals)`, clamped to [0, 1].")
    out.append("- `unavailable` signals never enter the numerator or denominator — they surface only as [VERIFY] notes.")
    out.append("- A **negative** rule firing suppresses the label (`insufficient evidence`) regardless of score.")
    out.append("- A label is surfaced iff: no negative fired, sample `n >= min_sample`, `score >= score_threshold`, and at least one computable signal fired.")
    out.append("")
    out.append("## Confidence (capped at each archetype's `max_confidence_mvp`)")
    out.append("")
    out.append("- **high** — >= 3 distinct computable signals fired AND `n >= min_sample`")
    out.append("- **med** — >= 2 distinct computable signals fired")
    out.append("- **low** — >= 1 computable signal fired")
    out.append("")
    out.append("## Author position caveat")
    out.append("")
    out.append(
        "Author position is a positional heuristic (`first` / `middle` / `last` / "
        "`unknown`, plus real `EqualContrib` metadata when PubMed marks it). It is NOT "
        "authoritative leadership or corresponding-author metadata, which are "
        "`unavailable` in this MVP."
    )
    out.append("")
    out.append("## Archetypes (multi-label; an author may score on several)")
    out.append("")

    for key in sorted(data["archetypes"].keys()):
        arc = data["archetypes"][key]
        out.append(f"### {key} — {arc['name']}")
        out.append("")
        out.append(arc["summary"].strip())
        out.append("")
        out.append(
            f"_min_sample: {arc['min_sample']} · score_threshold: {arc['score_threshold']} "
            f"· max_confidence_mvp: {arc['max_confidence_mvp']}_"
        )
        out.append("")
        if arc.get("flag"):
            out.append(f"> **Flag.** {arc['flag'].strip()}")
            out.append("")
        out.append("Signals:")
        out.append("")
        for sig in arc["signals"]:
            out.append(_signal_line(sig))
        out.append("")
        negs = arc.get("negatives") or []
        if negs:
            out.append("Negatives (rule the archetype OUT):")
            out.append("")
            for neg in negs:
                out.append(f"- **{neg['id']}** — {neg.get('narrative', '').strip()}")
            out.append("")

    composites = data.get("composites") or {}
    if composites:
        out.append("## Composite patterns (computed combinations, not independent labels)")
        out.append("")
        for key in sorted(composites.keys()):
            comp = composites[key]
            out.append(f"### {key} — {comp['name']}")
            out.append("")
            out.append(comp["summary"].strip())
            out.append("")
            out.append(f"- Requires all of: {', '.join(comp['requires_all'])}")
            extra = comp.get("extra_condition", {})
            if extra:
                out.append(f"- Extra condition — {extra.get('narrative', '').strip()}")
            out.append(f"- {comp.get('narrative', '').strip()}")
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Render trajectory_archetypes.md from the YAML rubric")
    ap.add_argument("--check", action="store_true", help="verify the .md is in sync; exit 1 on drift")
    args = ap.parse_args()

    if not YAML_PATH.exists():
        sys.stderr.write(f"ERROR: missing {YAML_PATH}\n")
        return 2
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    rendered = render(data)

    if args.check:
        current = MD_PATH.read_text(encoding="utf-8") if MD_PATH.exists() else ""
        if current != rendered:
            sys.stderr.write(
                f"DRIFT: {MD_PATH.name} is out of sync with the YAML rubric. "
                "Run: python3 render_archetype_doc.py\n"
            )
            return 1
        print(f"OK: {MD_PATH.name} matches the rubric YAML.")
        return 0

    MD_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {MD_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

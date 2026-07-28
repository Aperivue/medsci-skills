#!/usr/bin/env python3
"""Semantics-preserving perturbations of a held-out corpus — the severity probe.

WHAT THIS IS FOR
    Every other measurement here needs to know the right answer before it can call a detector wrong.
    This one does not. If a detector's verdict changes when the manuscript is rewritten in a way
    that cannot change what the manuscript SAYS, then the detector was reading surface form, and it
    is wrong on one side of the pair regardless of which side. That is a severity test in Mayo's
    sense: it constructs the case in which the checker would be caught, and it needs no labeler.

    It is also ledger Class C turned into a systematic probe. C1 and C2 were exactly this: a
    detector that recognised "Data Availability" and not JAMA's "Data Sharing Statement", found by
    accident on twelve papers. The house-vocabulary perturbation looks for the rest of that class on
    purpose.

WHY THERE IS NO PARAPHRASE PERTURBATION
    The obvious fourth perturbation is "reword the prose without changing the claims", and it is
    omitted deliberately. A machine paraphrase is not verifiably meaning-preserving: certifying that
    a rewritten sentence still says the same thing is a human judgement, per sentence, at corpus
    scale. That is a bigger labeling burden than the study this probe was promoted to replace. A
    perturbation whose validity cannot be checked mechanically cannot support an argument that a
    changed verdict is the detector's fault.

    So all three perturbations here are ones a script can PROVE it applied correctly, and each run
    ships a validity report saying so.

THE PERTURBATIONS

  house-vocab       Rewrite section labels and disclosure headings into a different publisher's
                    house wording ("Data Availability" -> "Data Sharing Statement", "Competing
                    interests" -> "Declaration of competing interest"). Meaning-preserving because
                    the pairs are recognised synonyms across journals; a reader loses nothing.
                    The sharpest probe of the five ledger Class C defects.

  rename-abbrev     Rename in-document abbreviations consistently ("MRI (magnetic resonance
                    imaging)" everywhere becomes "QZT (magnetic resonance imaging)"). Meaning-
                    preserving because the abbreviation is DEFINED in the document: the expansion
                    travels with it. Probes detectors keyed to specific token strings.

  reorder-sections  Permute sibling sections within the body, seeded. Meaning-preserving for every
                    claim in the paper. NOT meaning-preserving for order itself, so detectors whose
                    documented job is order or position are exempt (see EXEMPT below) — a changed
                    verdict there is the detector working, not failing.

VALIDITY GUARD
    A perturbation that damages the document is not semantics-preserving, and a probe that cannot
    tell the difference would report our own corruption as a detector defect — which is precisely
    what happened to the first corpus renderer (ledger B1-B4). So every run asserts, per paper:

      - the multiset of numbers is unchanged
      - the multiset of citation markers is unchanged
      - no content is lost: the word count outside the intended edits is unchanged
      - the intended edit actually happened at least once (a no-op perturbation measures nothing)

    A paper failing any of these is excluded from that perturbation and named in the report.

Usage:
    perturb_corpus.py --corpus _corpus/heldout --out _corpus/perturbed/house-vocab \\
        --perturbation house-vocab [--seed 42] [--report path.json]

Exit: 0 written, 1 a paper failed the validity guard (still writes the rest, names the failures),
      2 usage error. Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- house vocabulary rings -------------------------------------------------------------------
# Each ring is a set of wordings that different publishers use for THE SAME THING. Rotating one
# step around a ring changes the house, never the meaning. Longest-first at match time, so
# "Conflict of Interest Disclosures" is not eaten by "Conflict of Interest".
VOCAB_RINGS: Tuple[Tuple[str, ...], ...] = (
    ("Data Availability Statement", "Data Sharing Statement", "Availability of data and materials",
     "Data Availability"),
    ("Conflict of Interest Disclosures", "Declaration of competing interest", "Competing interests",
     "Conflicts of Interest", "Conflict of Interest"),
    ("Funding/Support", "Funding Statement", "Funding"),
    ("CRediT authorship contribution statement", "Author Contributions", "Authors' contributions"),
    ("Acknowledgements", "Acknowledgments"),
    ("Ethics approval and consent to participate", "Ethical approval", "Ethics Statement"),
)

# Detectors exempt from a given perturbation because order or position is their documented subject.
# A verdict that moves here is the detector doing its job. Named explicitly rather than inferred:
# an inferred exemption list is a place to hide a real failure.
EXEMPT: Dict[str, Tuple[str, ...]] = {
    "reorder-sections": (
        "check_citation_order",        # float citation order IS the check
        "check_figure_citation",       # first-citation position
        "check_perspective_structure",  # section sequence is the subject
        "check_classical_style",       # heading order / house structure
        "check_summary_box",           # box placement
    ),
    "house-vocab": (),
    "rename-abbrev": (),
}

NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")
CITE_RE = re.compile(r"\[\d+(?:[–\-,;\s]*\d+)*\]")
# "magnetic resonance imaging (MRI)" — a definition that makes the abbreviation renameable.
#
# Two or more capitals, no trailing digit, deliberately. A first version accepted a single capital and so
# treated figure panel labels "(A)", "(B)" and the statistic "(P)" as abbreviations, then renamed
# every standalone A and P in the document — 400+ words in some papers. The validity guard caught
# it and refused to write the corpus, which is what the guard is for; this is the fix behind it.
ABBREV_DEF_RE = re.compile(r"\(([A-Z]{2,6})\)")

# Capitalised tokens that are not abbreviations of anything, or whose renaming would change meaning.
ABBREV_STOPLIST = frozenset({
    "AND", "OR", "NOT", "THE", "ALL", "NEW", "TWO", "ONE", "SD", "SE", "CI", "IQR", "NA", "ID",
})
WORD_RE = re.compile(r"[A-Za-z]+")


def farthest_in_ring(word: str, ring: Tuple[str, ...]) -> str:
    """The ring member sharing the FEWEST words with `word`.

    Rotating to the neighbour is a weak probe: "Data Availability" -> "Data Availability Statement"
    differs by one appended token, and a detector keyed on the substring never notices. The point of
    this perturbation is to hand the detector a wording it has genuinely never met, so it goes to
    the most distant member of the ring — "Data Sharing Statement" or "Availability of data and
    materials". Deterministic: ties break on ring order.
    """
    src = set(word.lower().split())
    return min(
        (w for w in ring if w != word),
        key=lambda w: (len(src & set(w.lower().split())), ring.index(w)),
    )


def rotate_vocab(text: str) -> Tuple[str, int]:
    """Rewrite each house wording as another house's. Longest match first, so a long phrase is not
    swallowed by a shorter one it contains ("Conflict of Interest Disclosures" vs "Conflict of
    Interest")."""
    pairs: List[Tuple[str, str]] = []
    for ring in VOCAB_RINGS:
        for word in ring:
            pairs.append((word, farthest_in_ring(word, ring)))
    pairs.sort(key=lambda p: -len(p[0]))

    # Two passes with a sentinel, so a rewritten string is not rewritten again by a later rule.
    n = 0
    holder: Dict[str, str] = {}
    for i, (src, dst) in enumerate(pairs):
        token = f"\x00VOCAB{i}\x00"
        new, k = re.subn(re.escape(src), token, text)
        if k:
            holder[token] = dst
            text = new
            n += k
    for token, dst in holder.items():
        text = text.replace(token, dst)
    return text, n


def rename_abbreviations(text: str, rng: random.Random) -> Tuple[str, int]:
    """Rename abbreviations that the document itself defines, consistently, everywhere."""
    defined = [m.group(1) for m in ABBREV_DEF_RE.finditer(text)]
    # Only abbreviations that recur — a one-off is not worth perturbing and risks a false rename.
    counts = Counter(re.findall(r"\b[A-Z]{2,6}\b", text))
    targets = sorted({a for a in defined if a not in ABBREV_STOPLIST and counts.get(a, 0) >= 2})
    if not targets:
        return text, 0
    n = 0
    for i, abbr in enumerate(targets):
        # Deterministic, obviously-synthetic, and LETTERS ONLY. A digit in the replacement token
        # lands in the document's number multiset, which the validity guard reads as "the numbers
        # changed" — correctly, and it refused to write the corpus until this was fixed.
        new = "ZQX" + chr(ord("A") + i // 26) + chr(ord("A") + i % 26)
        text, k = re.subn(rf"\b{re.escape(abbr)}\b", new, text)
        n += k
    return text, n


def reorder_sections(text: str, rng: random.Random) -> Tuple[str, int]:
    """Permute sibling `##` sections, keeping the title block and the first section in place."""
    lines = text.splitlines(keepends=True)
    idx = [i for i, ln in enumerate(lines) if re.match(r"^## (?!#)", ln)]
    if len(idx) < 3:
        return text, 0
    head = lines[: idx[0]]
    blocks: List[List[str]] = []
    for a, b in zip(idx, idx[1:] + [len(lines)]):
        blocks.append(lines[a:b])
    # Keep the first block anchored (usually Abstract) so the document still opens like a paper.
    first, rest = blocks[0], blocks[1:]
    order = list(range(len(rest)))
    rng.shuffle(order)
    if order == sorted(order) and len(order) > 1:  # a shuffle that changed nothing measures nothing
        order.reverse()
    out = head + first + [ln for i in order for ln in rest[i]]
    return "".join(out), len(order)


PERTURBATIONS = {
    "house-vocab": lambda t, rng: rotate_vocab(t),
    "rename-abbrev": rename_abbreviations,
    "reorder-sections": reorder_sections,
}


def validity(before: str, after: str, kind: str, edits: int) -> List[str]:
    """What must be true for a changed verdict to be the DETECTOR's fault and not ours.

    The word budget is DERIVED from the edits actually made, not a constant. A first version used a
    flat cap and excluded 6 of 12 pilot papers for the crime of containing many abbreviations —
    a guard that rejects the perturbation working as designed is a guard that measures nothing.
    """
    problems: List[str] = []
    if Counter(NUM_RE.findall(before)) != Counter(NUM_RE.findall(after)):
        problems.append("numbers changed")
    if Counter(CITE_RE.findall(before)) != Counter(CITE_RE.findall(after)):
        problems.append("citation markers changed")
    wb, wa = Counter(WORD_RE.findall(before)), Counter(WORD_RE.findall(after))
    if kind == "reorder-sections" and wb != wa:
        problems.append("word multiset changed under a pure reordering")
    delta = sum((wb - wa).values()) + sum((wa - wb).values())
    if kind == "rename-abbrev":
        # Each rename removes exactly one token and adds exactly one. Anything else is collateral.
        if delta != 2 * edits:
            problems.append(f"rewrote {delta} words for {edits} renames (expected {2 * edits}) — "
                            "the rename touched something it did not name")
    elif kind == "house-vocab":
        # A ring phrase is at most six words, so a swap moves at most twelve.
        if delta > 12 * edits:
            problems.append(f"rewrote {delta} words for {edits} swaps — beyond the intended edit")
    if before == after:
        problems.append("no-op: nothing was perturbed, so this paper measures nothing")
    return problems


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--perturbation", choices=sorted(PERTURBATIONS), required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--report", type=Path)
    a = ap.parse_args(argv)

    if not a.corpus.is_dir():
        print(f"perturb: no corpus at {a.corpus}", file=sys.stderr)
        return 2
    papers = sorted(p for p in a.corpus.iterdir() if p.suffix.lower() in (".md", ".txt"))
    if not papers:
        print(f"perturb: no papers in {a.corpus}", file=sys.stderr)
        return 2

    a.out.mkdir(parents=True, exist_ok=True)
    fn = PERTURBATIONS[a.perturbation]
    written, excluded, edits = [], [], 0

    for p in papers:
        before = p.read_text(encoding="utf-8")
        rng = random.Random(f"{a.seed}:{p.stem}")  # per paper, so one paper cannot shift another
        after, n = fn(before, rng)
        problems = validity(before, after, a.perturbation, n)
        if problems:
            excluded.append({"paper": p.stem, "problems": problems})
            continue
        (a.out / p.name).write_text(after, encoding="utf-8")
        written.append({"paper": p.stem, "edits": n})
        edits += n

    report = {
        "perturbation": a.perturbation,
        "seed": a.seed,
        "source": str(a.corpus),
        "out": str(a.out),
        "n_written": len(written),
        "n_excluded": len(excluded),
        "total_edits": edits,
        "exempt_detectors": list(EXEMPT.get(a.perturbation, ())),
        "written": written,
        "excluded": excluded,
    }
    print(f"perturb {a.perturbation}: {len(written)} paper(s), {edits} edit(s) -> {a.out}")
    for e in excluded:
        print(f"  EXCLUDED {e['paper']}: {'; '.join(e['problems'])}")
    if EXEMPT.get(a.perturbation):
        print(f"  exempt from invariance (order/position IS their subject): "
              f"{', '.join(EXEMPT[a.perturbation])}")
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  report: {a.report}")
    return 1 if excluded else 0


if __name__ == "__main__":
    sys.exit(main())

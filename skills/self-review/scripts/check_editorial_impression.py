#!/usr/bin/env python3
"""Editorial-impression / defensiveness gate (self-review §L) — the counterweight pass.

The rest of the MedSci-Audit stack minimizes *rejection-for-cause* (the floor):
fabricated citations, drifting numbers, overclaims, missing checklist items. Several
of those gates raise the floor by *adding* material — a hedge, a caveat, a disclosure,
a checklist row — and nothing in the stack pushes back. Iterated, a manuscript
monotonically over-hardens: a confident narrative turns into a defensive audit that an
editor reads as a risk signal even when every individual gate finding was correct.

This gate is the missing opposite force. It does not relax any integrity gate; it scans
the *manuscript as a whole* for editorial-impression risks and recommends SUBTRACTION —
REMOVE, MOVE, or TIGHTEN — so the accurate content the gates secured is also read
confidently. Every finding is advisory (Minor / impression) and NON-BLOCKING: this gate
never returns a submission blocker. It raises the ceiling; it does not gate the floor.

  HEDGE_DENSITY         defensive-caveat tokens per 1,000 body-narrative words exceed a
                        threshold — the prose hedges faster than it asserts. TIGHTEN.
  HEDGE_REPEAT          one caveat motif ("no deployable claim", "not generalizable",
                        "none evaluated here") repeats >=N times across body + abstract.
                        Say it once, firmly. TIGHTEN.
  AUDIT_IN_BODY         provenance/audit minutiae (SHA / git commit / unit-test /
                        post-lock timeline / manifest / seed=N / audit trail) appear in
                        the Introduction / Results / Discussion narrative rather than a
                        Methods reproducibility statement or a supplement. MOVE.
  LIMITATIONS_VOLUME    the Limitations passage enumerates more than N discrete items;
                        a wall of limitations reads as a rebuttal letter. TIGHTEN.
  ABSTRACT_CAVEAT_LOAD  the Abstract carries >=N caveat clauses; the headline result is
                        buried under qualifiers before a reader reaches it. TIGHTEN.
  BURIED_DEFENSE        a strong numeric robustness / sensitivity result sits only in the
                        Limitations / supplement, with no robustness mention in Results.
                        This is the inverse of the scope-coherence gate: scope-coherence
                        pushes a *weak* analysis out of Results; BURIED_DEFENSE pulls a
                        *strong* confound rebuttal back into Results. MOVE (promote).

Conservative by construction: each probe fires only on an explicit, locatable signal, to
keep false positives low on a widely-used skill. The gate needs IMRAD-style headings to
locate sections; with none it degrades to a whole-document density read.

INPUTS
  --manuscript  manuscript markdown/text (required).
  thresholds    --hedge-per-1k (10.0), --repeat-threshold (3), --limitations-max (6),
                --abstract-caveat-max (2). A probe fires when its count exceeds the max.

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manuscript, claims[{verdict, severity, action, detail, where}], summary}
  Every claim is severity "Minor" with an action of REMOVE / MOVE / TIGHTEN. Exit code is
  always 0 for the findings themselves (advisory); --strict is accepted for CLI parity
  with the other gates but never blocks, since this gate emits no Major.

Stdlib-only (json / re / argparse / pathlib). Exit codes: 0 clean or advisory findings,
2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Section segmentation
# --------------------------------------------------------------------------- #

HEADING_RE = re.compile(r"^(#{1,6})\s*\*{0,2}(.+?)\*{0,2}\s*$", re.MULTILINE)

# Narrative regions where defensive prose and out-of-place audit minutiae read worst.
# Methods is deliberately excluded (a reproducibility statement belongs there), as is
# any supplement / availability / declarations region.
BODY_NARRATIVE = {"introduction", "results", "discussion", "conclusion", "limitations"}


def classify_heading(h: str) -> str:
    t = h.lower().strip()
    if "abstract" in t or t == "summary":
        return "abstract"
    if any(k in t for k in (
        "data availability", "code availability", "availability", "supplement",
        "appendix", "acknowledg", "funding", "declaration", "competing interest",
        "conflict of interest", "reproducibility", "references", "author contribution",
    )):
        return "supplement"
    if "limitation" in t:
        return "limitations"
    if "introduction" in t or "background" in t:
        return "introduction"
    if any(k in t for k in (
        "method", "material", "statistical analys", "study design",
        "patients and", "data collection", "study population",
    )):
        return "methods"
    if "result" in t or "finding" in t:
        return "results"
    if "discussion" in t:
        return "discussion"
    if "conclusion" in t:
        return "conclusion"
    return "other"


def segment(text: str) -> list[tuple[str, str]]:
    """Return an ordered list of (region, body_text) pairs. Text before the first
    heading is a 'preamble' region. Region names follow classify_heading()."""
    matches = list(HEADING_RE.finditer(text))
    regions: list[tuple[str, str]] = []
    if not matches:
        return [("preamble", text)]
    if matches[0].start() > 0:
        pre = text[: matches[0].start()].strip()
        if pre:
            regions.append(("preamble", pre))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        regions.append((classify_heading(m.group(2)), body))
    return regions


def region_text(regions: list[tuple[str, str]], names: set[str]) -> str:
    return "\n".join(b for r, b in regions if r in names)


def abstract_text(regions: list[tuple[str, str]], full: str) -> str:
    """The Abstract region; fall back to the text before the first Introduction/Methods
    heading (a structured abstract without its own heading), capped to ~350 words."""
    abs_regions = [b for r, b in regions if r == "abstract"]
    if abs_regions:
        return "\n".join(abs_regions)
    # Fallback: preamble + everything up to the first intro/methods region.
    out: list[str] = []
    for r, b in regions:
        if r in ("introduction", "methods", "results", "discussion"):
            break
        if r in ("preamble", "other"):
            out.append(b)
    joined = "\n".join(out)
    words = joined.split()
    return " ".join(words[:350]) if len(words) > 350 else joined


def word_count(text: str) -> int:
    return sum(1 for w in text.split() if any(c.isalpha() for c in w))


def sentences(text: str) -> list[str]:
    # Lightweight sentence split on ., !, ? followed by whitespace.
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if s.strip()]


# --------------------------------------------------------------------------- #
# Lexicons
# --------------------------------------------------------------------------- #

# Defensive caveats — explicitly hedging phrases, not ordinary modal verbs. Stacking
# these is the defensiveness tell HEDGE_DENSITY measures.
CAVEAT = re.compile(
    r"\bcaveats?\b|should be interpreted with caution|with caution\b|"
    r"must be interpreted|interpreted? with care|"
    r"cannot be (?:inferred|established|excluded|determined|generaliz\w+|ruled out|drawn|assumed)|"
    r"no (?:causal|deployable|clinical|definitive) (?:claim|inference|conclusion|relationship)|"
    r"not (?:be )?(?:generaliz\w+|definitive|conclusive|deployable|warranted)|"
    r"\bpreliminary\b|\bexploratory\b|hypothesis[-\s]generating|"
    r"warrants? (?:caution|further (?:study|validation|research|investigation))|"
    r"remains? (?:unclear|uncertain|to be (?:established|determined|confirmed))|"
    r"\blimited (?:by|generaliz\w+|sample|to|in scope)|"
    r"single[-\s](?:cent(?:er|re)|institution|site)|retrospective (?:design|nature)|"
    r"should not be (?:used|interpreted|construed)|"
    r"do(?:es)? not (?:establish|imply|permit|support|prove)|"
    r"not (?:yet )?(?:ready|validated|intended) for (?:clinical|deployment|practice)|"
    r"\bunderpowered\b|\bmodest\b|no (?:firm|strong) (?:conclusion|inference)",
    re.IGNORECASE)

# Repeated caveat motifs (HEDGE_REPEAT): family key -> regex. A family repeating across
# body + abstract above the threshold should be stated once, firmly.
MOTIFS: dict[str, re.Pattern] = {
    "no_deployable_claim": re.compile(
        r"no (?:deployable|deployment|clinical|practice|diagnostic) (?:claim|use|recommendation)|"
        r"not (?:ready|intended|validated) for (?:clinical|deployment|practice)",
        re.IGNORECASE),
    "not_generalizable": re.compile(r"not (?:be )?generaliz\w+|limited generaliz\w+", re.IGNORECASE),
    "none_evaluated_here": re.compile(
        r"(?:none|not|no \w+) (?:were |was |are |is )?evaluated (?:here|in this (?:study|work|analysis))|"
        r"not (?:assessed|examined|tested) (?:here|in this (?:study|work))", re.IGNORECASE),
    "no_causal": re.compile(r"no causal (?:claim|inference|relationship|conclusion|interpretation)", re.IGNORECASE),
    "hypothesis_generating": re.compile(r"hypothesis[-\s]generating", re.IGNORECASE),
    "interpret_with_caution": re.compile(
        r"interpret\w* with caution|should be interpreted with caution|with caution", re.IGNORECASE),
    "single_center": re.compile(r"single[-\s](?:cent(?:er|re)|institution|site)", re.IGNORECASE),
    "retrospective_design": re.compile(r"retrospective (?:design|nature|study|cohort)", re.IGNORECASE),
    "preliminary": re.compile(r"\bpreliminary\b", re.IGNORECASE),
}

# Motifs that are factual study-design descriptors rather than defensive caveats. A
# single-centre / retrospective study must state its design in Methods, and naming it
# again in the Abstract and Limitations is normal, not over-hedging. Count these only
# in the non-Methods narrative so an honestly-written single-centre retrospective study
# (the most common observational design) is not flagged for stating a true fact.
FACTUAL_DESCRIPTOR_MOTIFS = {"single_center", "retrospective_design"}

# Provenance / audit minutiae that belong in Methods or a supplement, not the narrative.
AUDIT = re.compile(
    r"\bsha-?256\b|\bmd5\b|\bchecksum\b|(?:git\s+)?(?:commit|hash|sha)\s*[:=]?\s*[0-9a-f]{7,40}\b|"
    r"\bcommit\s+[0-9a-f]{7,40}\b|\bunit[-\s]?test(?:s|ing|ed)?\b|\bpost[-\s]?lock\b|"
    r"seed\s*=\s*\d+|\brandom seed\s+\d+\b|\baudit trail\b|"
    r"reproducibility (?:manifest|hash|record)|data lock(?:ed)? on|\bcontent[-\s]hash\b",
    re.IGNORECASE)

# Robustness / sensitivity vocabulary (for BURIED_DEFENSE).
ROBUST = re.compile(
    r"sensitivity analys\w+|robustness|leave[-\s]one[-\s]out|leave[-\s]pair[-\s]out|"
    r"\bE[-\s]?value\b|remained (?:significant|robust|consistent|unchanged|stable)|"
    r"did not (?:materially |substantially |meaningfully )?(?:change|alter|differ)|"
    r"results were (?:similar|consistent|robust|unchanged)|consistent across|"
    r"after (?:excluding|adjusting for|accounting for)|tipping[-\s]point", re.IGNORECASE)

# A strong numeric token next to a robustness statement makes it Results-worthy.
NUMERIC = re.compile(
    r"\b\d+\.\d+\b|\b\d{1,3}%|95%\s*ci|(?:OR|HR|RR|AUC|aHR|aOR)\s*[=:]?\s*\d|"
    r"p\s*[<=>]\s*0?\.\d+", re.IGNORECASE)

ORDINALS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh",
            "eighth", "ninth", "tenth"]


# --------------------------------------------------------------------------- #
# Probes
# --------------------------------------------------------------------------- #

def probe_hedge_density(regions, body, threshold) -> list[dict]:
    words = word_count(body)
    if words < 80:  # too little narrative to judge density reliably
        return []
    n = len(CAVEAT.findall(body))
    density = n / words * 1000
    if density > threshold:
        return [{
            "verdict": "HEDGE_DENSITY", "severity": "Minor", "action": "TIGHTEN",
            "detail": (f"defensive-caveat density is {density:.1f} per 1,000 body words "
                       f"({n} caveat tokens / {words} words; threshold {threshold:.0f}); the "
                       f"prose hedges faster than it asserts — keep the load-bearing caveats, "
                       f"cut the reflexive ones"),
            "where": f"body narrative ({words} words)",
        }]
    return []


def probe_hedge_repeat(regions, full, threshold) -> list[dict]:
    non_methods = "\n".join(b for r, b in regions if r != "methods")
    claims = []
    for key, rx in MOTIFS.items():
        # Factual design descriptors are not over-hedging when stated in Methods;
        # count them only in the non-Methods narrative.
        hay = non_methods if key in FACTUAL_DESCRIPTOR_MOTIFS else full
        n = len(rx.findall(hay))
        if n >= threshold:
            m = rx.search(hay)
            phrase = m.group(0).strip() if m else key
            claims.append({
                "verdict": "HEDGE_REPEAT", "severity": "Minor", "action": "TIGHTEN",
                "detail": (f"the caveat '{phrase}' (motif: {key}) appears {n} times across "
                           f"the narrative; state it once, firmly, and remove the repeats"),
                "where": phrase[:120],
            })
    return claims


def probe_audit_in_body(regions) -> list[dict]:
    body = region_text(regions, BODY_NARRATIVE)
    claims = []
    seen = set()
    for m in AUDIT.finditer(body):
        tok = m.group(0).strip().lower()
        norm = re.sub(r"[0-9a-f]{7,40}", "<hash>", tok)
        if norm in seen:
            continue
        seen.add(norm)
        claims.append({
            "verdict": "AUDIT_IN_BODY", "severity": "Minor", "action": "MOVE",
            "detail": (f"provenance/audit token '{m.group(0).strip()}' appears in the "
                       f"Introduction/Results/Discussion narrative; move reproducibility "
                       f"detail to a Methods statement or a supplement"),
            "where": body[max(0, m.start() - 40):m.end() + 40].strip()[:160],
        })
    return claims


def probe_limitations_volume(regions, full, max_items) -> list[dict]:
    lim = region_text(regions, {"limitations"})
    if not lim:
        # Inline limitations paragraph inside Discussion.
        disc = region_text(regions, {"discussion", "conclusion"})
        m = re.search(r"(?:our |this )?stud(?:y|ies) (?:has|have)[^.]{0,40}limitations?|"
                      r"several (?:important )?limitations|limitations? (?:of this|warrant)",
                      disc, re.IGNORECASE)
        if not m:
            return []
        lim = disc[m.start():]
    # Count discrete items: max of ordinal markers, (N) enumerators, bullet lines.
    low = lim.lower()
    n_ord = sum(1 for o in ORDINALS if re.search(rf"(?:^|[\s(,;])\b{o}\b\s*,", low))
    n_enum = len(set(re.findall(r"\((\d{1,2})\)", lim)))
    n_bullet = len(re.findall(r"^\s*[-*]\s+\S", lim, re.MULTILINE))
    n = max(n_ord, n_enum, n_bullet)
    if n > max_items:
        return [{
            "verdict": "LIMITATIONS_VOLUME", "severity": "Minor", "action": "TIGHTEN",
            "detail": (f"the Limitations passage enumerates {n} discrete items "
                       f"(threshold {max_items}); consolidate related items so the section "
                       f"reads as honest disclosure, not a rebuttal letter"),
            "where": f"Limitations ({n} items)",
        }]
    return []


def probe_abstract_caveat_load(regions, full, max_caveats) -> list[dict]:
    abs_t = abstract_text(regions, full)
    if word_count(abs_t) < 40:
        return []
    caveat_sents = [s for s in sentences(abs_t) if CAVEAT.search(s)]
    n = len(caveat_sents)
    if n > max_caveats:
        return [{
            "verdict": "ABSTRACT_CAVEAT_LOAD", "severity": "Minor", "action": "TIGHTEN",
            "detail": (f"the Abstract carries {n} caveat-bearing clauses (threshold "
                       f"{max_caveats}); lead with the result and keep at most one or two "
                       f"essential qualifiers so the headline is not buried"),
            "where": (caveat_sents[0][:140] if caveat_sents else "Abstract"),
        }]
    return []


def probe_buried_defense(regions) -> list[dict]:
    results = region_text(regions, {"results"})
    buried_src = region_text(regions, {"limitations", "supplement"})
    if not buried_src:
        return []
    # If Results already discusses robustness, nothing is buried.
    if ROBUST.search(results):
        return []
    claims = []
    for s in sentences(buried_src):
        if ROBUST.search(s) and NUMERIC.search(s):
            claims.append({
                "verdict": "BURIED_DEFENSE", "severity": "Minor", "action": "MOVE",
                "detail": ("a numeric robustness/sensitivity result sits in the "
                           "Limitations/supplement with no robustness mention in Results; "
                           "promote it into Results — it is evidence for the finding, not a "
                           "caveat against it"),
                "where": s[:160],
            })
            break  # one promotion recommendation is enough
    return claims


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def check(text: str, *, hedge_per_1k: float, repeat_threshold: int,
          limitations_max: int, abstract_caveat_max: int) -> list[dict]:
    regions = segment(text)
    body = region_text(regions, BODY_NARRATIVE)
    if not body:  # no IMRAD headings — degrade to a whole-document read (minus supplement)
        body = region_text(regions, {"preamble", "other"}) or text
    claims: list[dict] = []
    claims += probe_hedge_density(regions, body, hedge_per_1k)
    claims += probe_hedge_repeat(regions, text, repeat_threshold)
    claims += probe_audit_in_body(regions)
    claims += probe_limitations_volume(regions, text, limitations_max)
    claims += probe_abstract_caveat_load(regions, text, abstract_caveat_max)
    claims += probe_buried_defense(regions)
    return claims


def analyze(manuscript: str, **kw) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"), **kw)
    by_action = {"REMOVE": 0, "MOVE": 0, "TIGHTEN": 0}
    for c in claims:
        by_action[c["action"]] = by_action.get(c["action"], 0) + 1
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "by_action": by_action,
            "verdict": "IMPRESSION_FLAGS" if claims else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Action | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['action']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | narrative reads confidently; no subtraction needed |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Editorial-impression / defensiveness gate (§L) — advisory, non-blocking.")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true",
                    help="accepted for CLI parity; this gate emits no Major, so it never blocks")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    ap.add_argument("--hedge-per-1k", type=float, default=10.0,
                    help="HEDGE_DENSITY: caveat tokens per 1,000 body words before firing (default 10)")
    ap.add_argument("--repeat-threshold", type=int, default=3,
                    help="HEDGE_REPEAT: motif occurrences across body+abstract before firing (default 3)")
    ap.add_argument("--limitations-max", type=int, default=6,
                    help="LIMITATIONS_VOLUME: discrete Limitations items allowed (default 6)")
    ap.add_argument("--abstract-caveat-max", type=int, default=2,
                    help="ABSTRACT_CAVEAT_LOAD: caveat clauses allowed in the Abstract (default 2)")
    args = ap.parse_args()

    result = analyze(
        args.manuscript,
        hedge_per_1k=args.hedge_per_1k,
        repeat_threshold=args.repeat_threshold,
        limitations_max=args.limitations_max,
        abstract_caveat_max=args.abstract_caveat_max,
    )

    if not args.quiet:
        print("=" * 41)
        print(" Editorial Impression / Defensiveness (§L)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_claims"]:
            ba = s["by_action"]
            print(f"IMPRESSION flags: {s['n_claims']} advisory finding(s) "
                  f"(REMOVE {ba['REMOVE']} / MOVE {ba['MOVE']} / TIGHTEN {ba['TIGHTEN']}). "
                  f"Non-blocking — these raise the ceiling, they do not gate submission.")
        else:
            print("OK: narrative reads confidently; no subtraction recommended.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_editorial_impression", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    # Advisory: never blocks. --strict is accepted for parity but this gate has no Major.
    return 0


if __name__ == "__main__":
    sys.exit(main())

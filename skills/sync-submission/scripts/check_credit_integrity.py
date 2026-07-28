#!/usr/bin/env python3
"""CRediT integrity — a contribution taxonomy is a factual claim, published with the paper.

WHY THIS EXISTS

CRediT terms are printed in the published record and every co-author sees them, but nothing
ties a term to anything. During one byline negotiation three terms were requested for an
author in sequence — Visualization, then Methodology, then Formal analysis — each after the
previous was checked against the project record and found unsupported: the author's
tracked-changes file contained zero embedded images and left the figure legends untouched,
the analysis protocol was frozen two days before they joined, and the coding was recorded as
two named coders whose blind passes predated their arrival. A fourth term, Conceptualization,
turned out to be *entirely* legitimate — it rested on work that happens off-repo, in email
and meetings. The pattern was a taxonomy expanding to justify a position rather than to
describe work, and the honest version of it is indistinguishable from the legitimate one
without evidence.

WHAT IS DELIBERATELY OUT OF SCOPE

**Author order and equal-contribution designation are not gated here and never will be.**
Those are negotiated, and negotiation is legitimate. Only the taxonomy — a factual claim
about who did what — is checked. Conflating the two is why they get edited as one block.

WHAT IS CHECKED, AND WHY EACH IS SAFE

Three of the four verdicts need nothing but the manuscript, so they hold on any project:

  CREDIT_TERM_INVALID (major)
      A section that calls itself CRediT uses a term outside the official fourteen.
      "Statistical analysis", "Manuscript writing" and "Study design" are the usual ones —
      they read as CRediT and are not, and a journal that asks for CRediT wants the fourteen.

  CREDIT_INITIALS_UNRESOLVED (major)
      Initials in the contributions section that match no author, or match two. This is what
      a byline change actually leaves behind: an author is removed or reordered and their
      initials keep working somewhere in the paragraph.

  CREDIT_AUTHOR_UNLISTED (major)
      A byline author with no contribution attributed anywhere. Under ICMJE every author must
      have contributed; a name with no term is either an authorship problem or an edit that
      dropped a clause.

  CREDIT_UNCORROBORATED (prompt — never a blocker)
      A term whose footprint is absent. Two sources, both optional and neither invented:
      the manuscript itself (Visualization claimed on a paper with no figures; Software with
      no code availability statement) and, if the project keeps one, a contribution record
      passed with --contribution-record. A missing record simply means this half does not run.

WHY THE LAST ONE CANNOT BE A BLOCKER

Real contributions happen off-repo. The one term in the incident above that WAS supported —
Conceptualization — had no artifact in the repository at all; it lived in email and in a
critique that drove a restructure. A gate that failed the build on that would be wrong, and
would teach its user to disable it. So it asks for the artifact or an attestation, and gets
out of the way.

WHAT IS NOT BUILT, AND WHY

The original proposal wanted Visualization corroborated against a *figure provenance table*
and Formal analysis against an *analysis record*. Neither convention exists in this toolkit.
Building against them would mean inventing the convention and then gating against our own
invention. Instead --contribution-record accepts a record if the project already keeps one,
and asserts nothing when it does not.

Usage:
    check_credit_integrity.py --manuscript m.md [--contribution-record contributions.yaml]
        [--out qc/credit_integrity.json] [--quiet]

Exit 0 clean, 1 any finding (majors and prompts alike — the caller decides severity from the
JSON), 2 no CRediT section to check. Stdlib only; .docx via python-docx when available.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DETECTOR = "check_credit_integrity"

# The fourteen. https://credit.niso.org/ — this list is the standard, not a house style.
CREDIT_TERMS = {
    "conceptualization": "Conceptualization",
    "data curation": "Data curation",
    "formal analysis": "Formal analysis",
    "funding acquisition": "Funding acquisition",
    "investigation": "Investigation",
    "methodology": "Methodology",
    "project administration": "Project administration",
    "resources": "Resources",
    "software": "Software",
    "supervision": "Supervision",
    "validation": "Validation",
    "visualization": "Visualization",
    "writing original draft": "Writing – original draft",
    "writing review editing": "Writing – review & editing",
}
# Near-misses that read as CRediT but are not, mapped to what was meant. Naming them is the
# difference between "invalid" and a usable message.
NEAR_MISS = {
    "statistical analysis": "Formal analysis",
    "statistics": "Formal analysis",
    "analysis": "Formal analysis",
    "study design": "Conceptualization or Methodology",
    "design": "Conceptualization or Methodology",
    "manuscript writing": "Writing – original draft",
    "writing": "Writing – original draft or Writing – review & editing",
    "drafting": "Writing – original draft",
    "revision": "Writing – review & editing",
    "critical revision": "Writing – review & editing",
    "data collection": "Investigation or Data curation",
    "data analysis": "Formal analysis",
    "interpretation": "Formal analysis or Validation",
    "literature search": "Investigation",
    "figure preparation": "Visualization",
    "final approval": "Writing – review & editing",
}

CREDIT_HEADING_RE = re.compile(
    r"^#{1,6}\s*\*{0,2}\s*(?:Authors?[’'\s]*\s*[Cc]ontributions?|CRediT[^\n]*)\*{0,2}\s*:?\s*$",
    re.M)
IMG_LINK_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
FIGURE_CAPTION_RE = re.compile(r"^\s*\**\s*(?:Figure|Fig\.?)\s*\d+\b", re.M | re.I)
CODE_AVAIL_RE = re.compile(r"^#{1,6}\s*\*{0,2}\s*Code Availability", re.M | re.I)
# "J.D.", "Y.N.", "A.B.C." — the form contributions sections are written in.
INITIALS_RE = re.compile(r"\b(?:[A-Z]\.){2,4}")
# A byline name: "Jane Doe", "Jane A. Doe", "Mary Anne Roe" — two to four capitalised words,
# optionally carrying a superscript/affiliation marker.
NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+){1,2})\b")


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        try:
            import docx  # type: ignore
        except ImportError:
            print(f"ERROR: reading {path.name} needs python-docx", file=sys.stderr)
            raise SystemExit(2)
        return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)
    return path.read_text(encoding="utf-8", errors="replace")


def credit_section(md: str) -> str | None:
    m = CREDIT_HEADING_RE.search(md)
    if not m:
        return None
    rest = md[m.end():]
    nxt = re.search(r"^#{1,6}\s", rest, re.M)
    return (rest[: nxt.start()] if nxt else rest).strip()


def norm_term(t: str) -> str:
    n = re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", t.lower())).strip()
    # "Writing—original draft preparation" is MDPI's rendering of "Writing – original draft", not a
    # fifteenth term. The trailing noun is house style, so it is normalised away rather than
    # reported as a near miss.
    return re.sub(r" preparation$", "", n)


def initials_of(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    return "".join(p[0].upper() + "." for p in parts)


def byline_names(md: str) -> list[str]:
    """Author names from the manuscript head — before the first section heading.

    Confidence matters more than recall here: the bijection checks are skipped entirely when
    fewer than two names are found, because a wrong byline produces wrong accusations about
    every author at once.
    """
    head = md[: md.index("\n## ")] if "\n## " in md else md[:1500]
    head = re.sub(r"^#\s+.*$", "", head, count=1, flags=re.M)   # drop the title line
    head = re.sub(r"[*_`^~†‡§¶\d]", " ", head)
    stop = {"Abstract", "Keywords", "Background", "Methods", "Results", "Conclusion",
            "Introduction", "Discussion", "Synthetic", "Not", "Corresponding", "Author"}
    out: list[str] = []
    for m in NAME_RE.finditer(head):
        n = re.sub(r"\s+", " ", m.group(1)).strip()
        if n.split()[0] in stop or n in out:
            continue
        out.append(n)
    return out


def load_record(path: Path) -> dict[str, set[str]]:
    """Optional contribution record: {initials or name: [artifact, ...]}.

    Accepts JSON, or the trivial `key: a, b` YAML subset, so a project can keep one without
    taking a dependency. Absent -> this half of the check simply does not run.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
        for line in raw.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line or line.startswith("-"):
                continue
            k, v = line.split(":", 1)
            data[k.strip().strip("'\"")] = [x.strip() for x in v.split(",") if x.strip()]
    return {str(k).upper(): {str(x).lower() for x in (v if isinstance(v, list) else [v])}
            for k, v in data.items()}


# Terms whose absence the MANUSCRIPT alone can speak to. Anything else needs a record.
def manuscript_footprint(md: str) -> dict[str, bool]:
    has_figure = bool(IMG_LINK_RE.search(md) or FIGURE_CAPTION_RE.search(md))
    return {
        "Visualization": has_figure,
        "Software": bool(CODE_AVAIL_RE.search(md)),
    }


def build_report(manuscript: Path, record_path: Path | None) -> dict | None:
    md = read_text(manuscript)
    body = credit_section(md)
    if body is None:
        return None

    findings: list[dict] = []
    # "CRediT" may be declared in the heading ("## CRediT authorship statement") or in the
    # body ("CRediT: J.D. Conceptualization…"). Scoping the test to the heading alone made a
    # section that says CRediT in its first word grade its invalid terms as merely minor.
    heading_text = md[CREDIT_HEADING_RE.search(md).start(): CREDIT_HEADING_RE.search(md).end()]
    section_says_credit = bool(re.search(r"CRediT", heading_text + "\n" + body, re.I))

    # --- 1. terms outside the fourteen
    #
    # Only for a section that IS a CRediT block. The docstring above already says so — "a section
    # that calls itself CRediT" — and the code had drifted from it: the scan ran on any
    # "Authors' Contributions" heading and merely graded the result `minor`. A minor finding still
    # exits non-zero, so a free-prose contributions paragraph fired.
    #
    # Measured against 12 accepted papers, that is exactly what happened: "analysis" and "writing"
    # reported as invalid CRediT terms in papers carrying NO CRediT statement at all — zero of the
    # fourteen present. A journal that never asked for CRediT has not asked its authors to use the
    # fourteen. A challenge card always contains the block being validated, so no fixture in this
    # repo could have shown it.
    #
    # A block counts as CRediT if it says so, or carries at least three of the official terms.
    # Three, not one: "Investigation", "Validation" and "Software" are ordinary English words that
    # turn up in prose by accident; three of them together do not.
    # Count against the NORMALISED body, because CREDIT_TERMS is keyed normalised: the key is
    # "writing original draft" and the page says "Writing – original draft". Matching the raw text
    # undercounts every hyphenated term and lets a real CRediT block fall below the bar.
    body_norm = norm_term(body)
    official_present = {t for t in CREDIT_TERMS if t and t in body_norm}
    is_credit_block = section_says_credit or len(official_present) >= 3

    # The em dash belongs in this class. MDPI renders the taxonomy as "Writing—original draft
    # preparation"; without U+2014 the term is shredded at the dash and the fragment "writing" is
    # reported as an invalid CRediT term — against a block that had written the term correctly for
    # its publisher. Two accepted MDPI papers failed this way.
    used_raw = re.findall(r"[A-Za-z][A-Za-z—–\-&' ]{3,40}", body) if is_credit_block else []
    seen: set[str] = set()
    for raw in used_raw:
        n = norm_term(raw)
        if n in CREDIT_TERMS or not n or n in seen:
            continue
        if n in NEAR_MISS:
            seen.add(n)
            findings.append({
                "verdict": "CREDIT_TERM_INVALID",
                "severity": "major" if section_says_credit else "minor",
                "term": raw.strip(),
                "suggest": NEAR_MISS[n],
                "message": (
                    f"\"{raw.strip()}\" is not a CRediT term; the taxonomy has fourteen and "
                    f"this is not one of them. The closest is {NEAR_MISS[n]}."
                ),
            })

    # --- 2/3. initials <-> byline
    names = byline_names(md)
    used_initials = sorted(set(INITIALS_RE.findall(body)))
    if len(names) >= 2 and used_initials:
        by_init: dict[str, list[str]] = {}
        for n in names:
            by_init.setdefault(initials_of(n), []).append(n)
        for ini in used_initials:
            owners = by_init.get(ini, [])
            if len(owners) == 1:
                continue
            findings.append({
                "verdict": "CREDIT_INITIALS_UNRESOLVED",
                "severity": "major",
                "initials": ini,
                "matches": owners,
                "message": (
                    f"\"{ini}\" in the contributions section matches "
                    + (f"{len(owners)} authors ({', '.join(owners)})" if owners
                       else "no author in the byline")
                    + ". A byline edit leaves initials behind that still read as valid."
                ),
            })
        for ini, owners in sorted(by_init.items()):
            if ini in used_initials:
                continue
            findings.append({
                "verdict": "CREDIT_AUTHOR_UNLISTED",
                "severity": "major",
                "author": owners[0],
                "initials": ini,
                "message": (
                    f"{owners[0]} ({ini}) is in the byline but has no contribution attributed. "
                    f"Under ICMJE every author must have contributed — this is either an "
                    f"authorship question or an edit that dropped a clause."
                ),
            })

    # --- 4. corroboration (prompt only)
    footprint = manuscript_footprint(md)
    claimed = {CREDIT_TERMS[norm_term(r)] for r in used_raw if norm_term(r) in CREDIT_TERMS}
    for term, present in footprint.items():
        if term in claimed and not present:
            why = ("the manuscript has no figures — no image embeds and no figure captions"
                   if term == "Visualization" else
                   "the manuscript has no Code Availability statement")
            findings.append({
                "verdict": "CREDIT_UNCORROBORATED",
                "severity": "minor",
                "term": term,
                "message": (
                    f"{term} is claimed, but {why}. Point at the artifact, or record an "
                    f"explicit attestation — contributions do happen off-repo."
                ),
            })

    record = load_record(record_path) if record_path and record_path.is_file() else None
    if record is not None:
        for ini in used_initials:
            artifacts = record.get(ini)
            if artifacts is None:
                findings.append({
                    "verdict": "CREDIT_UNCORROBORATED",
                    "severity": "minor",
                    "initials": ini,
                    "message": (
                        f"{ini} is credited in the manuscript but appears nowhere in the "
                        f"contribution record. Add the artifact, or an attestation that the "
                        f"contribution was off-repo."
                    ),
                })

    return {
        "detector": DETECTOR,
        "manuscript": str(manuscript),
        "contribution_record": str(record_path) if record is not None else None,
        "byline_authors": names,
        "initials_used": used_initials,
        "credit_terms_claimed": sorted(claimed),
        "bijection_checked": bool(len(names) >= 2 and used_initials),
        "findings": findings,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="CRediT taxonomy integrity (not author order).")
    ap.add_argument("--manuscript", required=True, type=Path)
    ap.add_argument("--contribution-record", type=Path,
                    help="optional {initials: [artifact, ...]} JSON/simple-YAML; absent = that "
                         "half of the check does not run")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="accepted for call-site symmetry; a finding exits 1 either way")
    args = ap.parse_args()

    if not args.manuscript.is_file():
        print(f"ERROR: manuscript not found: {args.manuscript}", file=sys.stderr)
        return 2

    report = build_report(args.manuscript, args.contribution_record)
    if report is None:
        if not args.quiet:
            print(f"{DETECTOR}: no author-contributions / CRediT section — skipped.")
        return 2

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print(f"{DETECTOR}: {len(report['credit_terms_claimed'])} CRediT term(s), "
              f"{len(report['initials_used'])} contributor initial(s)"
              + ("" if report["bijection_checked"]
                 else "; byline not resolvable, author/initials cross-check skipped"))
        for f in report["findings"]:
            print(f"  [{f['severity']}] {f['verdict']}: {f['message']}")
        if not report["findings"]:
            print("OK: the taxonomy is CRediT, resolves to the byline, and nothing is "
                  "claimed against an absent footprint.")

    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())

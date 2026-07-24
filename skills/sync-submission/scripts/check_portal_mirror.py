#!/usr/bin/env python3
"""Portal-field mirror gate — the portal field REPLACES the manuscript section, so a
sentence that never reaches the field is never published.

WHAT THIS IS NOT

`check_portal_field_residue.py` asks whether what you paste is *clean* (markdown leaking
into a plain-text field). This asks the opposite question: whether what you did *not* paste
is quietly lost. A residue-clean portal field can still be missing the one sentence that
mattered.

THE CONTRACT THAT MAKES THIS A DEFECT AND NOT A STYLE NOTE

Springer Nature's SNAPP states it on the submission form itself, at four fields — Author
Contributions, Competing Interests, Data Availability, Acknowledgements:

    "This replaces any statement written within the manuscript and is the one that we will
     publish."

So the manuscript file is the copy the reviewers read, and the portal box is the copy the
world gets. A statement that lives only in the manuscript is not a redundant duplicate; it
is a statement that will not exist in the published record. Nothing warns you, because
nothing is wrong with either document on its own.

TWO SENTENCES THIS WAS BUILT FROM, BOTH ONE CLICK FROM VANISHING

  * **Equal contribution.** The title page carried a † footnote naming two co-first authors.
    The author page has no equal-contribution checkbox. Unless "X and Y contributed equally
    to this work" is typed into the Author Contributions box, the published paper has no
    co-first authors — and the people it was negotiated for never see it.
  * **"The funder had no role in study design…"** It sat in the manuscript's
    Acknowledgements. The portal's structured *Research funding* field takes a funder name
    and a grant ID and has nowhere to put a role disclaimer, so pasting only an AI-use note
    into the Acknowledgements box drops it.

Both are invisible to every other gate: the manuscript is complete, the portal fields are
clean, and the loss only appears in the galley.

VERDICTS

  PORTAL_FIELD_NOT_MIRRORED (major)   a sentence in a replacing manuscript section has no
                                      home in that field's portal artifact.
  PORTAL_FIELD_MISSING (major)        the manuscript has the section, the journal says the
                                      field replaces it, and no portal artifact exists at
                                      all — the published field will be empty or whatever
                                      the portal's auto-extraction guessed.
  EQUAL_CONTRIBUTION_NOT_IN_PORTAL (major)
                                      the manuscript asserts equal / co-first contribution
                                      somewhere, and the Author Contributions portal text
                                      does not. There is no checkbox for this.

WHY MATCHING IS GRADED, NOT LITERAL

Comparison runs through `_quote_match.py`, which grades EXACT / INTERLEAVED / PARTIAL /
ABSENT rather than answering yes/no. An author legitimately re-flows sentences when pasting,
and a manuscript read out of .docx arrives with its own extraction noise; only ABSENT — not
one ordered run of the sentence's words — is called a loss. The alternative, a substring
test, reports a sentence the author *did* paste (differently punctuated) as dropped, and a
gate that cries wolf about pasted text is a gate that gets ignored at exactly the moment it
finally has something true to say.

WHICH FIELDS REPLACE IS A JOURNAL FACT, NOT A GUESS

Read from the journal profile's `## Portal Mechanics` block (`Fields that REPLACE the
manuscript: ...`), or given explicitly with `--fields`. With neither, this exits 2 (skipped)
and asserts nothing — a portal contract that has not been recorded is not a contract this
gate may invent.

Usage:
    check_portal_mirror.py --manuscript m.md --portal-dir portal_fields/ \\
        --profile .../npj_Digital_Medicine.md [--out qc/portal_mirror.json] [--strict]
    check_portal_mirror.py --manuscript m.md --profile P --emit portal_fields/   # scaffold

Exit 0 clean, 1 finding (with --strict), 2 inputs absent / no portal contract recorded.
Stdlib only; .docx via python-docx when available.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _quote_match import match_quality, tokens  # noqa: E402  (vendored, same-dir)

DETECTOR = "check_portal_mirror"

# A fragment shorter than this ("None.", "Not applicable.") carries too few tokens for an
# ordered-run match to mean anything, so it is counted rather than judged.
MIN_SENTENCE_TOKENS = 5

# Canonical field id -> heading synonyms in the manuscript. The id is also the artifact stem
# the portal directory is searched for.
FIELDS: dict[str, tuple[str, ...]] = {
    "author_contributions": ("author contributions", "authors' contributions",
                             "authors contributions", "contributions", "credit"),
    "competing_interests": ("competing interests", "competing financial interests",
                            "conflict of interest", "conflicts of interest",
                            "declaration of interests", "declaration of competing interest"),
    "data_availability": ("data availability", "data availability statement",
                          "availability of data", "availability of data and materials"),
    "code_availability": ("code availability", "code availability statement"),
    "acknowledgements": ("acknowledgements", "acknowledgments", "acknowledgement",
                         "acknowledgment"),
    "funding": ("funding", "funding statement", "financial support", "research funding"),
}
# Accepted spellings of a field name as it may be written in a journal profile.
ALIAS_TO_ID = {syn: fid for fid, syns in FIELDS.items() for syn in syns}

EQUAL_CONTRIB = re.compile(
    r"\b(contributed equally|equal contribution|equally to this work|"
    r"co-?first author|joint first author|share[d]? first authorship)\b",
    re.IGNORECASE,
)

HEADING = re.compile(r"^(#{1,6})\s*\**\s*([^*#\n]+?)\s*\**\s*$", re.M)
ABBREV = re.compile(r"\b(?:et al|e\.g|i\.e|cf|vs|Fig|No|Dr|Prof|approx)\.$", re.IGNORECASE)
# Author initials are not sentence ends — and Author Contributions is the one section
# guaranteed to be written in them. Without this, "J.D. and A.R. designed the study" splits
# into "J.D.", "and A.R.", "designed the study…": three fragments, two of them too short to
# judge, and a real omission would be reported against a clause with no subject.
INITIALS = re.compile(r"(?:\b[A-Z]\.){1,4}\s*$")


# ------------------------------------------------------------------------------- reading

def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        try:
            import docx  # type: ignore
        except ImportError:
            print(f"ERROR: reading {path.name} needs python-docx", file=sys.stderr)
            raise SystemExit(2)
        d = docx.Document(str(path))
        return "\n".join(p.text for p in d.paragraphs)
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_heading(t: str) -> str:
    return re.sub(r"[^a-z ]", "", t.lower()).strip()


def sections(md: str) -> list[tuple[str, str]]:
    """(normalized heading, body) for every heading, body running to the next heading."""
    out: list[tuple[str, str]] = []
    marks = list(HEADING.finditer(md))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(md)
        out.append((normalize_heading(m.group(2)), md[m.end(): end].strip()))
    return out


def find_section(md: str, field_id: str) -> str | None:
    wanted = FIELDS[field_id]
    for head, body in sections(md):
        if head in wanted:
            return body
    # a heading like "Data availability statement" that carries extra words
    for head, body in sections(md):
        if any(head.startswith(w) or w.startswith(head) for w in wanted if len(head) > 6):
            return body
    return None


LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


def blocks(body: str) -> list[str]:
    """Paragraphs and list items, each with its wrapped lines rejoined.

    Splitting on newlines first is wrong and was: a sentence hard-wrapped across two lines
    ("The funder had no role in study" / "design, data collection…") becomes two fragments,
    which the gate then reports as two separate losses with both halves truncated mid-clause.
    Markdown separates paragraphs by blank lines, so a block ends at a blank line or at the
    start of a list item — a CRediT block is written as a list, and losing one item loses one
    author's credit, so items stay individual.
    """
    out: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            out.append(" ".join(buf).strip())
            buf.clear()

    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith(("|", ">", "```", "#")):
            flush()
            continue
        if LIST_ITEM.match(raw):
            flush()
            buf.append(LIST_ITEM.sub("", raw).strip())
        else:
            buf.append(line)
    flush()
    return [b for b in out if b]


def statements(body: str) -> list[str]:
    """Sentence-ish units of a declaration section, over rejoined blocks."""
    out: list[str] = []
    for block in blocks(body):
        buf = ""
        for piece in re.split(r"(?<=[.!?])\s+", block):
            buf = f"{buf} {piece}".strip() if buf else piece
            if ABBREV.search(buf) or INITIALS.search(buf):
                continue
            out.append(buf)
            buf = ""
        if buf:
            out.append(buf)
    return [s for s in out if s.strip()]


# ---------------------------------------------------------------- the journal's contract

def replacing_fields_from_profile(path: Path) -> list[str]:
    """Read `## Portal Mechanics` -> `Fields that REPLACE the manuscript: A · B · C`.

    Unrecognised names are dropped rather than guessed at; a profile naming a field this
    gate has no heading synonyms for would otherwise silently assert nothing.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^##\s*Portal Mechanics\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return []
    line = re.search(r"Fields that REPLACE the manuscript\**\s*:\s*(.+)$", m.group(1), re.M)
    if not line:
        return []
    out: list[str] = []
    for part in re.split(r"[·,;|]", re.sub(r"[*_`]", "", line.group(1))):
        fid = ALIAS_TO_ID.get(normalize_heading(part))
        if fid and fid not in out:
            out.append(fid)
    return out


def portal_artifact(portal_dir: Path, field_id: str) -> Path | None:
    """Find this field's paste artifact by stem, tolerating the names authors actually use."""
    if not portal_dir.is_dir():
        return None
    wanted = {field_id} | {normalize_heading(s).replace(" ", "_") for s in FIELDS[field_id]}
    for p in sorted(portal_dir.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in (".txt", ".md"):
            continue
        stem = re.sub(r"[^a-z0-9]+", "_", p.stem.lower()).strip("_")
        if stem in wanted or any(stem.startswith(w) for w in wanted):
            return p
    return None


# --------------------------------------------------------------------------------- check

def build_report(manuscript: Path, portal_dir: Path | None, fields: list[str]) -> dict:
    md = read_text(manuscript)
    findings: list[dict] = []
    checked = skipped_short = 0
    examined: list[str] = []

    for fid in fields:
        body = find_section(md, fid)
        if body is None:
            continue  # the manuscript has no such section: nothing to lose
        examined.append(fid)
        art = portal_artifact(portal_dir, fid) if portal_dir else None
        if art is None:
            findings.append({
                "verdict": "PORTAL_FIELD_MISSING",
                "severity": "major",
                "field": fid,
                "message": (
                    f"The manuscript has a {fid.replace('_', ' ')} section and this journal "
                    f"publishes the PORTAL field in its place, but no paste artifact for it "
                    f"exists. Whatever is typed into that box — or left empty — is what gets "
                    f"published. Generate one with --emit and check it."
                ),
            })
            continue

        portal_text = read_text(art)
        for sent in statements(body):
            if len(tokens(sent)) < MIN_SENTENCE_TOKENS:
                skipped_short += 1
                continue
            checked += 1
            if match_quality(sent, portal_text)["grade"] != "ABSENT":
                continue
            findings.append({
                "verdict": "PORTAL_FIELD_NOT_MIRRORED",
                "severity": "major",
                "field": fid,
                "portal_artifact": art.name,
                "sentence": sent[:300],
                "message": (
                    f"This sentence is in the manuscript's {fid.replace('_', ' ')} section but "
                    f"not in {art.name}, which replaces it in the published record: "
                    f"\"{sent[:120]}\". Copy the section rather than re-composing it."
                ),
            })

    # Equal contribution has no checkbox anywhere in the portal; if it is not typed into the
    # contributions box it does not survive, so it is checked against the WHOLE manuscript
    # rather than against one section (it is usually a title-page footnote, not a sentence in
    # Author Contributions at all).
    if "author_contributions" in fields and EQUAL_CONTRIB.search(md):
        art = portal_artifact(portal_dir, "author_contributions") if portal_dir else None
        portal_text = read_text(art) if art else ""
        if not EQUAL_CONTRIB.search(portal_text):
            findings.append({
                "verdict": "EQUAL_CONTRIBUTION_NOT_IN_PORTAL",
                "severity": "major",
                "field": "author_contributions",
                "portal_artifact": art.name if art else None,
                "message": (
                    "The manuscript states that authors contributed equally, but the Author "
                    "Contributions portal text does not. There is no equal-contribution "
                    "checkbox on the author page: if this sentence is not in that box, the "
                    "published paper has no co-first authors."
                ),
            })

    return {
        "detector": DETECTOR,
        "manuscript": str(manuscript),
        "portal_dir": str(portal_dir) if portal_dir else None,
        "replacing_fields": fields,
        "fields_examined": examined,
        "sentences_checked": checked,
        "fragments_too_short_to_judge": skipped_short,
        "findings": findings,
    }


def do_emit(manuscript: Path, out_dir: Path, fields: list[str], force: bool) -> int:
    """Write one paste-ready .txt per replacing field, straight from the manuscript.

    The point is that the author never hand-composes the box. Both sentences this gate was
    built from were lost to re-composition, not to carelessness.
    """
    md = read_text(manuscript)
    out_dir.mkdir(parents=True, exist_ok=True)
    wrote = 0
    for fid in fields:
        body = find_section(md, fid)
        if body is None:
            continue
        dest = out_dir / f"{fid}.txt"
        if dest.exists() and not force:
            print(f"  exists, left alone: {dest.name} (use --force to overwrite)")
            continue
        text = re.sub(r"[*_`]", "", body).strip()
        # The equal-contribution sentence is a TITLE-PAGE footnote, not part of the
        # contributions section, so copying the section alone reproduces exactly the omission
        # this gate exists to catch. Lift it in, since the portal box is the only place it can
        # survive: there is no checkbox for it.
        if fid == "author_contributions" and not EQUAL_CONTRIB.search(text):
            lifted = next((s for s in statements(md) if EQUAL_CONTRIB.search(s)), None)
            if lifted:
                lifted = re.sub(r"^[\W_]+", "", re.sub(r"[*_`]", "", lifted)).strip()
                text = f"{lifted}\n\n{text}"
                print(f"  lifted equal-contribution statement into {dest.name}")
        dest.write_text(text + "\n", encoding="utf-8")
        print(f"  wrote {dest.name}  ({len(text.split())} words)")
        wrote += 1
    print(f"{DETECTOR}: emitted {wrote} paste-ready field(s) into {out_dir}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Portal fields replace the manuscript — mirror gate.")
    ap.add_argument("--manuscript", required=True, type=Path)
    ap.add_argument("--portal-dir", type=Path, help="directory of portal paste artifacts")
    ap.add_argument("--profile", type=Path, help="journal profile .md with a Portal Mechanics block")
    ap.add_argument("--fields", help="comma-separated field names, overriding the profile")
    ap.add_argument("--emit", type=Path, metavar="DIR",
                    help="write paste-ready field files from the manuscript instead of checking")
    ap.add_argument("--force", action="store_true", help="with --emit, overwrite existing files")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="accepted for call-site symmetry; every verdict here is major, so a "
                         "finding exits 1 with or without it")
    args = ap.parse_args()

    if not args.manuscript.is_file():
        print(f"ERROR: manuscript not found: {args.manuscript}", file=sys.stderr)
        return 2

    if args.fields:
        fields = [f for f in (ALIAS_TO_ID.get(normalize_heading(x))
                              for x in args.fields.split(",")) if f]
    elif args.profile and args.profile.is_file():
        fields = replacing_fields_from_profile(args.profile)
    else:
        fields = []
    if not fields:
        if not args.quiet:
            print(f"{DETECTOR}: no replacing-field contract for this journal "
                  "(profile has no 'Portal Mechanics' block and --fields not given) — skipped.")
        return 2

    if args.emit:
        return do_emit(args.manuscript, args.emit, fields, args.force)

    if not args.portal_dir or not args.portal_dir.is_dir():
        if not args.quiet:
            print(f"{DETECTOR}: --portal-dir absent — skipped.")
        return 2

    report = build_report(args.manuscript, args.portal_dir, fields)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print(f"{DETECTOR}: {len(report['fields_examined'])} replacing field(s) present in the "
              f"manuscript; checked {report['sentences_checked']} sentence(s)")
        if report["fragments_too_short_to_judge"]:
            print(f"  {report['fragments_too_short_to_judge']} fragment(s) too short to judge")
        for f in report["findings"]:
            print(f"  [{f['severity']}] {f['verdict']}: {f['message']}")
        if not report["findings"]:
            print("OK: every manuscript declaration has a home in the field that replaces it.")

    # Exit 1 on ANY finding, NOT only under --strict. preflight_gate drives its halt decision
    # from this exit code and does not pass --strict, so a --strict-gated exit would report a
    # dropped declaration as a clean check — which it did, until this line.
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())

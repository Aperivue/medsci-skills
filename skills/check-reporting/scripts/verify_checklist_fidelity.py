#!/usr/bin/env python3
"""A bundled checklist must match the official instrument it claims to be.

Issue #352 (an external report, 2026-07-21): the file labelled "TRIPOD+AI 2024" was actually TRIPOD
2015 with separately-numbered `-AI` additions — the older section sequence, non-canonical item
identifiers (`1-AI`, `10-AI-a`, …), and no Open Science or Patient-and-Public-Involvement items. The
official TRIPOD+AI 2024 (Collins et al., BMJ 2024;385:e078378) is a **rewrite**: 27 main items, 52
subitems, with Open science (18) and PPI (19) as first-class items.

Nothing caught it. `check_checklist_exists` verifies the file is *present*; `check_framework_naming`
verifies it *names* its base instrument. Neither compares the file's item inventory against the
official one — so a checklist could silently drift from the guideline it claims to reproduce, and an
audit could report "TRIPOD+AI compliant" while checking a different, older instrument.

This is that check. It is manifest-driven, so it generalises: each entry states the official
inventory (item count, required sections, forbidden structures, a source token) and this script holds
the bundled file to it. Add a guideline by adding an EXPECTED entry, not code.

The same audit (2026-07-21) found two more of the #352 class and they are covered here: CLEAR had been
regrouped into seven invented topical "domains" (item 1 = "Study hypothesis") when the official
instrument is numbered by manuscript section (item 1 = Title, item 44 = baseline demographics), and
MI-CLEAR-LLM carried the 2024 six-item body under a "Version 2025" label when the official 2025 update
has eight item categories.

Text mode. Item counts and headings do not catch a checklist whose items are all present but
reworded: a model transcribing a statement drops an example, a clause or a whole bullet, or carries
the next section's heading into an item, and the inventory still matches. For open-licence statements
the published item text is extracted mechanically into `skills/check-reporting/tests/checklist_sources/`
(see `refresh_from_europepmc.py` there), and every item in the vendored file must match it after
typographic normalisation (quotes, dashes, "e.g."/"eg", a trailing full stop, list bullets). Those
sources are not shipped, so an installed copy skips this mode and says so.

Not named `check_*` on purpose — it is a fidelity regression, run in CI, not one of the manuscript
integrity detectors in the published count.

Usage:
    verify_checklist_fidelity.py [--strict] [--root PATH]

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKLISTS = "skills/check-reporting/references/checklists"

# The official inventory each bundled checklist must reproduce. Sourced from the published statement,
# not from the file being checked — that is the whole point.
EXPECTED = {
    "TRIPOD_AI.md": {
        "official_section_start": "## Checklist Items",
        "official_section_end": "## MedSci supplemental",   # supplemental checks are ours, exempt
        "main_items": list(range(1, 28)),                    # 1..27
        "subitem_rows": 52,
        "required_headings": ["### Open science", "### Patient and public involvement"],
        "forbidden_in_official": r"\b\d+-AI\b",              # non-canonical identifiers
        "must_contain": ["10.1136/bmj-2023-078378", "supersedes and replaces TRIPOD 2015"],
        "source": "Collins GS et al. BMJ 2024;385:e078378 (TRIPOD+AI 2024)",
    },
    # Issue-#352 class, found by the same fidelity audit (2026-07-21): the bundled CLEAR invented a
    # 7-topical-domain taxonomy (item 1 = "Study hypothesis") — but official CLEAR is numbered by
    # MANUSCRIPT SECTION (item 1 = Title, 2 = Abstract, 44 = baseline demographics), and its only two
    # non-essential items are 53 and 58 (the file wrongly said 17 and 57). Every cited item number was wrong.
    "CLEAR.md": {
        "official_section_start": "## Checklist Items",
        "official_section_end": "## Notes for assessors",
        "main_items": list(range(1, 59)),                    # 1..58
        "subitem_rows": 58,
        "required_headings": ["### Title", "### Abstract", "### Results", "### Discussion"],
        "forbidden_in_official": r"Domain \d",               # the topical-domain regrouping tell
        "must_contain": ["10.1186/s13244-023-01415-8", "specifying the radiomic methodology"],
        "source": "Kocak B et al. Insights Imaging 2023;14(1):75 (CLEAR 2023)",
    },
    # Issue-#352 class (2026-07-21): the file was labelled "Version 2025" but carried the 2024 SIX-item
    # body. The official 2025 update has EIGHT item categories, promoting Access mode, Input data type,
    # and Adaptation strategy to first-class items.
    "MI_CLEAR_LLM.md": {
        "official_section_start": "## Checklist Items",
        "official_section_end": "## Notes for assessors",
        "main_items": list(range(1, 9)),                     # 1..8
        "subitem_rows": 8,
        "required_headings": ["### 2. Access mode", "### 3. Input data type", "### 4. Adaptation strategy used"],
        "must_contain": ["10.3348/kjr.2025.1522", "8 item categories"],
        "source": "Park SH et al. Korean J Radiol 2025;26(12):1123-1132 (MI-CLEAR-LLM 2025)",
    },
    # GATHER 2016 (Stevens et al.): 18 items in four sections (Objectives and funding;
    # Data inputs; Data analysis; Results and discussion). Registered so the burden-of-disease
    # reporting checklist cannot silently drift from the 18-item statement.
    "GATHER.md": {
        "official_section_start": "## Checklist Items",
        "official_section_end": "## MedSci application notes",
        "main_items": list(range(1, 19)),                    # 1..18
        "subitem_rows": 18,
        "required_headings": ["### Objectives and funding", "### Data inputs",
                              "### Data analysis", "### Results and discussion"],
        "must_contain": ["10.1371/journal.pmed.1002056", "Health Estimates Reporting"],
        "source": "Stevens GA et al. Lancet 2016;388:e19-23 / PLoS Med 2016;13(6):e1002056 (GATHER)",
    },
}


TEXT_SOURCES = "skills/check-reporting/tests/checklist_sources"
ITEM_ID = re.compile(r"\d+[a-z]?")


def normalise(s: str) -> str:
    """Typographic differences only; any change of words still differs."""
    s = unicodedata.normalize("NFKC", s)
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u2013", "-"),
                 ("\u2014", "-"), ("\u2010", "-"), ("\u00a0", " ")):
        s = s.replace(a, b)
    s = re.sub(r"\*\*|__|`", "", s)
    s = re.sub(r"\s*[\u25cf\u2022]\s*", "; ", s)          # published list bullets vs "; " in a table cell
    s = re.sub(r"\be\.g\.,?", "eg,", s)
    s = re.sub(r"\bi\.e\.,?", "ie,", s)
    s = s.replace("eg,,", "eg,").replace("ie,,", "ie,").replace(":;", ":")
    s = re.sub(r"\s+", " ", s).strip()
    return s.rstrip(".").strip().lower()


def vendored_items(text: str) -> dict[str, str]:
    """Item id (first cell) -> item text (last cell) for every checklist table row."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and ITEM_ID.fullmatch(cells[0].strip("*")) and len(cells[-1]) > 8:
            out.setdefault(cells[0].strip("*"), cells[-1])
    return out


def check_text(root: Path) -> tuple[list[str], int, bool]:
    """Returns (problems, statements checked, sources present)."""
    src_dir = root / TEXT_SOURCES
    sources = sorted(src_dir.glob("*.json")) if src_dir.is_dir() else []
    if not sources:
        return [], 0, False
    out: list[str] = []
    for sp in sources:
        spec = json.loads(sp.read_text(encoding="utf-8"))
        md = root / CHECKLISTS / spec["vendored_file"]
        if not md.is_file():
            out.append(f"{spec['vendored_file']}: file missing (text source {sp.name})")
            continue
        want, have = spec["items"], vendored_items(md.read_text(encoding="utf-8"))
        cite = f"{spec['source']['citation']}, {spec['source']['table']}"
        for k in sorted(set(want) - set(have), key=_key):
            out.append(f"{md.name} item {k}: missing — the statement has it ({cite}).")
        for k in sorted(set(have) - set(want), key=_key):
            out.append(f"{md.name} item {k}: not in the statement ({cite}).")
        for k in sorted(set(want) & set(have), key=_key):
            if normalise(want[k]) != normalise(have[k]):
                out.append(f"{md.name} item {k}: text differs from {cite}\n"
                           f"        published: {want[k]}\n        vendored:  {have[k]}")
    return out, len(sources), True


def _key(k: str) -> tuple[int, str]:
    return (int(re.match(r"\d+", k).group()), k)


def official_slice(text: str, spec: dict) -> str:
    s = text.find(spec["official_section_start"])
    e = text.find(spec["official_section_end"])
    if s < 0:
        return text
    return text[s : e if e > s else len(text)]


def check_one(path: Path, spec: dict) -> list[str]:
    out: list[str] = []
    if not path.is_file():
        return [f"{path.name}: file missing"]
    text = path.read_text(encoding="utf-8")
    official = official_slice(text, spec)

    # main item numbers present in the official section
    nums = sorted({int(m) for m in re.findall(r"^\|\s*(\d+)[a-g]?\s*\|", official, re.MULTILINE)})
    want = spec["main_items"]
    if nums != want:
        missing = [n for n in want if n not in nums]
        extra = [n for n in nums if n not in want]
        out.append(f"{path.name}: main items are {nums or '[]'} — "
                   f"expected {want[0]}..{want[-1]}"
                   + (f"; missing {missing}" if missing else "")
                   + (f"; unexpected {extra}" if extra else ""))

    rows = len(re.findall(r"^\|\s*\d+[a-g]?\s*\|", official, re.MULTILINE))
    if rows != spec["subitem_rows"]:
        out.append(f"{path.name}: {rows} checklist rows in the official section — expected "
                   f"{spec['subitem_rows']} subitems ({spec['source']}).")

    for h in spec["required_headings"]:
        if h not in text:
            out.append(f"{path.name}: missing required section '{h}' — it is an official item, not optional.")

    forbidden = spec.get("forbidden_in_official")
    if forbidden:
        bad = re.findall(forbidden, official)
        if bad:
            out.append(f"{path.name}: forbidden pattern in the official section: "
                       f"{sorted(set(bad))} — this marks a structure the official instrument does not use "
                       f"(non-canonical identifiers, or a grouping the guideline does not have).")

    for tok in spec["must_contain"]:
        if tok not in text:
            out.append(f"{path.name}: missing required marker {tok!r} (source DOI / version / framing).")

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--root", type=Path, default=ROOT)
    a = ap.parse_args()

    problems: list[str] = []
    for name, spec in EXPECTED.items():
        problems += check_one(a.root / CHECKLISTS / name, spec)
    text_problems, n_text, have_sources = check_text(a.root)
    problems += text_problems

    if not problems:
        print(f"OK: {len(EXPECTED)} bundled checklist(s) match their official item inventory.")
        if have_sources:
            print(f"OK: {n_text} checklist(s) match the published item text word for word.")
        else:
            print(f"NOTE: no text sources under {TEXT_SOURCES} (an installed copy) — text mode skipped.")
        return 0

    print(f"CHECKLIST_FIDELITY: {len(problems)} discrepanc(ies) — a bundled checklist does not match "
          f"the official instrument it claims to be.\n")
    for p in problems:
        print(f"  - {p}")
    print(
        "\nA checklist labelled with an official guideline's name must reproduce that guideline's item\n"
        "inventory, or a compliance audit checks a different instrument than the one it reports.\n"
    )
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())

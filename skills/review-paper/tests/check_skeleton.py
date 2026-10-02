#!/usr/bin/env python3
"""Structural check of review-paper's macro skeleton against the bundled PRISMA checklists.

For each IMRaD format (scoping -> PRISMA-ScR, systematic -> PRISMA 2020), every applicable
Methods and Results item in the check-reporting checklist must have a slot tagged
`[<checklist> <item>]` under the skeleton's top-level `- Methods` / `- Results` bullet.
The narrative section must keep the 7-part skeleton and carry no PRISMA slot.

Exit 0 = clean, 1 = structural gap (listed), 2 = input not recognised (named).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CHECKLISTS = {
    "scoping": ("PRISMA-ScR", REPO / "skills/check-reporting/references/checklists/PRISMA_ScR.md"),
    "systematic": ("PRISMA 2020", REPO / "skills/check-reporting/references/checklists/PRISMA_2020.md"),
}
ITEM_ROW = re.compile(r"^\|\s*\**(\d+[a-z]?)\**\s*\|([^|]*)\|([^|]*)\|")


def required_items(path: Path) -> dict[str, set[str]]:
    """Applicable item numbers under the checklist's ### Methods and ### Results headings."""
    out: dict[str, set[str]] = {"Methods": set(), "Results": set()}
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            section = line[4:].strip()
            continue
        m = ITEM_ROW.match(line)
        if m and section in out:
            if m.group(3).strip().startswith("**Not applicable"):
                continue
            out[section].add(m.group(1))
    return out


def split_formats(text: str) -> dict[str, str]:
    parts = re.split(r"^## Format:\s*(\w+)\s*$", text, flags=re.M)
    return {parts[i].lower(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def slots_by_section(body: str, label: str) -> dict[str, set[str]]:
    tag = re.compile(r"\[" + re.escape(label) + r" (\d+[a-z]?)\]")
    out: dict[str, set[str]] = {}
    section = None
    for line in body.splitlines():
        top = re.match(r"^- (\w+)", line)
        if top:
            section = top.group(1)
        if section is not None:
            out.setdefault(section, set()).update(tag.findall(line))
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_skeleton.py <macro_skeleton.md>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"ENV-ERR: skeleton not found: {path}", file=sys.stderr)
        return 2
    for _, cl in CHECKLISTS.values():
        if not cl.is_file():
            print(f"ENV-ERR: checklist not found: {cl}", file=sys.stderr)
            return 2
    formats = split_formats(path.read_text(encoding="utf-8"))
    problems: list[str] = []
    for fmt in ("narrative", "scoping", "systematic"):
        if fmt not in formats:
            problems.append(f"no '## Format: {fmt}' section")
    if "narrative" in formats:
        body = formats["narrative"]
        if "[PRISMA" in body:
            problems.append("narrative: carries PRISMA slots (narrative is SANRA, not PRISMA)")
        parts = re.findall(r"(?:^|\s)([1-7])\.\s", body)
        if sorted(set(parts)) != [str(i) for i in range(1, 8)]:
            problems.append("narrative: 7-part skeleton not intact")
    for fmt, (label, cl) in CHECKLISTS.items():
        if fmt not in formats:
            continue
        need = required_items(cl)
        if not need["Methods"] or not need["Results"]:
            print(f"ENV-ERR: no Methods/Results items parsed from {cl}", file=sys.stderr)
            return 2
        have = slots_by_section(formats[fmt], label)
        for sec in ("Methods", "Results"):
            missing = sorted(need[sec] - have.get(sec, set()))
            if missing:
                problems.append(f"{fmt}: {sec} lacks slots for {label} items {', '.join(missing)}")
    for p in problems:
        print(f"GAP: {p}")
    if problems:
        return 1
    print("OK: narrative 7-part; scoping and systematic carry every PRISMA Methods/Results slot")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""Rebuild a checklist's item-text source from the published statement, without a model in the loop.

A vendored checklist that claims to reproduce an open-licence statement is checked against this
file by `scripts/verify_checklist_fidelity.py` (text mode). The text here is extracted mechanically
from the statement's JATS XML on Europe PMC (the table rows that carry an item number), so nothing
between the publisher and the comparison was retyped, summarised or "cleaned up" by a model. That is
the step where vendored checklists went wrong before: items were invented, merged, truncated, or
carried a neighbouring section heading, while their headers said "verified".

Needs the network; CI never runs it. Run it when a statement is added or revised, review the diff of
the JSON, and commit it together with any correction to the vendored `.md`.

Usage:
    python3 refresh_from_europepmc.py STARD CONSORT SPIRIT     # rebuild those sources
    python3 refresh_from_europepmc.py --list                   # show the registered statements
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
ID = re.compile(r"\d+[a-z]?")

# name -> where the statement's checklist table lives. Open licence only: the extracted text is
# committed, so a statement whose licence does not allow redistribution does not belong here.
STATEMENTS = {
    "STARD": {"md": "STARD.md", "pmcid": "PMC4623764", "table": "Table 1", "licence": "CC BY 4.0",
              "citation": "Bossuyt PM et al. STARD 2015. BMJ 2015;351:h5527", "doi": "10.1136/bmj.h5527"},
    "CONSORT": {"md": "CONSORT.md", "pmcid": "PMC11995449", "table": "Table 1", "licence": "CC BY 4.0",
                "citation": "Hopewell S et al. CONSORT 2025 statement. BMJ 2025;389:e081123",
                "doi": "10.1136/bmj-2024-081123"},
    "SPIRIT": {"md": "SPIRIT.md", "pmcid": "PMC12035670", "table": "Table 1", "licence": "CC BY 4.0",
               "citation": "Chan AW et al. SPIRIT 2025 statement. BMJ 2025;389:e081477",
               "doi": "10.1136/bmj-2024-081477"},
}

URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"


def extract(xml: bytes, table_label: str) -> dict[str, str]:
    root = ET.fromstring(xml)
    for tw in root.iter("table-wrap"):
        if (tw.findtext("label") or "").strip() != table_label:
            continue
        items: dict[str, str] = {}
        for tr in tw.iter("tr"):
            cells = [" ".join("".join(td.itertext()).split()) for td in tr]
            for i, cell in enumerate(cells):
                if ID.fullmatch(cell) and i + 1 < len(cells) and cells[i + 1]:
                    items.setdefault(cell, cells[i + 1])
                    break
        return items
    raise SystemExit(f"{table_label} not found in the XML")


def refresh(name: str) -> Path:
    spec = STATEMENTS[name]
    req = urllib.request.Request(URL.format(pmcid=spec["pmcid"]),
                                 headers={"User-Agent": "medsci-skills checklist-source refresh"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                xml = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 502, 503, 504) or attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
    items = extract(xml, spec["table"])
    out = HERE / f"{name}.json"
    out.write_text(json.dumps({
        "guideline": name,
        "vendored_file": spec["md"],
        "source": {**{k: spec[k] for k in ("citation", "doi", "pmcid", "table", "licence")},
                   "url": URL.format(pmcid=spec["pmcid"]),
                   "xml_sha256": hashlib.sha256(xml).hexdigest(),
                   "retrieved": dt.date.today().isoformat()},
        "items": items,
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("names", nargs="*")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list or not a.names:
        for k, v in STATEMENTS.items():
            print(f"{k:8} {v['pmcid']:12} {v['table']:8} -> {v['md']}")
        return 0
    for name in a.names:
        if name not in STATEMENTS:
            print(f"unknown statement {name!r}; known: {', '.join(STATEMENTS)}", file=sys.stderr)
            return 2
        p = refresh(name)
        print(f"wrote {p.name}: {len(json.loads(p.read_text())['items'])} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())

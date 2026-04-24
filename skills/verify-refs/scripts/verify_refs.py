#!/usr/bin/env python3
"""Reference verification helper for medsci-skills.

The script is deliberately stdlib-only. It extracts reference-like entries from
Markdown, DOCX, BibTeX, plain text, or TSV, verifies DOI/PMID when possible, and
writes a single audit artifact: qc/reference_audit.json. Per v1.1.1 artifact
contract, this skill is sole writer of that file and MUST NOT touch references/.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from xml.etree import ElementTree as ET


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
PMID_RE = re.compile(r"\bPMID\s*:?\s*(\d{5,9})\b", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


@dataclass
class RefRecord:
    ref_id: str
    raw: str
    title_guess: str = ""
    doi: str = ""
    pmid: str = ""
    year_guess: str = ""
    status: str = "UNVERIFIED"
    evidence: str = ""
    note: str = ""


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_doi(doi: str) -> str:
    return doi.rstrip(".,;)].").lower()


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for p in root.findall(".//w:p", ns):
        parts = [t.text or "" for t in p.findall(".//w:t", ns)]
        if parts:
            paragraphs.append("".join(parts))
    return "\n".join(paragraphs)


def read_input(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        return read_docx(path)
    return path.read_text(encoding="utf-8", errors="replace")


def parse_bib(text: str) -> list[RefRecord]:
    records: list[RefRecord] = []
    entries = re.split(r"\n(?=@\w+\{)", "\n" + text)
    for entry in entries:
        entry = entry.strip()
        if not entry.startswith("@"):
            continue
        key_match = re.match(r"@\w+\{([^,]+),", entry)
        title_match = re.search(r"title\s*=\s*[\{\"](.+?)[\}\"]\s*,", entry, re.I | re.S)
        doi_match = re.search(r"doi\s*=\s*[\{\"](.+?)[\}\"]\s*,", entry, re.I | re.S)
        pmid_match = re.search(r"pmid\s*=\s*[\{\"]?(\d{5,9})", entry, re.I)
        year_match = re.search(r"year\s*=\s*[\{\"]?((?:19|20)\d{2})", entry, re.I)
        raw = normalize_space(entry)
        records.append(
            RefRecord(
                ref_id=key_match.group(1) if key_match else f"ref_{len(records)+1}",
                raw=raw,
                title_guess=normalize_space(title_match.group(1)) if title_match else "",
                doi=clean_doi(doi_match.group(1)) if doi_match else "",
                pmid=pmid_match.group(1) if pmid_match else "",
                year_guess=year_match.group(1) if year_match else "",
            )
        )
    return records


def parse_tsv(text: str) -> list[RefRecord]:
    rows = list(csv.DictReader(text.splitlines(), delimiter="\t"))
    records: list[RefRecord] = []
    for i, row in enumerate(rows, 1):
        joined = " ".join(str(v) for v in row.values() if v)
        doi = ""
        pmid = ""
        for key, value in row.items():
            lk = (key or "").lower()
            if lk == "doi" and value:
                doi = clean_doi(value)
            if lk == "pmid" and value:
                pmid = re.sub(r"\D", "", value)
        title = row.get("title") or row.get("Title") or ""
        records.append(RefRecord(ref_id=f"ref_{i}", raw=normalize_space(joined), title_guess=title, doi=doi, pmid=pmid))
    return records


def reference_section(text: str) -> str:
    match = re.search(r"(?im)^\s*(references|bibliography|reference list)\s*$", text)
    if match:
        return text[match.end() :]
    return text


def parse_reference_lines(text: str) -> list[RefRecord]:
    section = reference_section(text)
    lines = [normalize_space(line) for line in section.splitlines()]
    candidates: list[str] = []
    current = ""
    for line in lines:
        if not line:
            continue
        starts_ref = bool(re.match(r"^(\[\d+\]|\d+[\.\)]|\-\s+)", line))
        if starts_ref and current:
            candidates.append(current)
            current = line
        else:
            current = f"{current} {line}".strip() if current else line
    if current:
        candidates.append(current)

    if len(candidates) < 2:
        candidates = [line for line in lines if DOI_RE.search(line) or PMID_RE.search(line) or len(line) > 60]

    records: list[RefRecord] = []
    for i, raw in enumerate(candidates, 1):
        raw = normalize_space(raw)
        doi_match = DOI_RE.search(raw)
        pmid_match = PMID_RE.search(raw)
        year_match = YEAR_RE.search(raw)
        records.append(
            RefRecord(
                ref_id=f"ref_{i}",
                raw=raw,
                title_guess=guess_title(raw),
                doi=clean_doi(doi_match.group(0)) if doi_match else "",
                pmid=pmid_match.group(1) if pmid_match else "",
                year_guess=year_match.group(0) if year_match else "",
            )
        )
    return records


def guess_title(raw: str) -> str:
    no_prefix = re.sub(r"^(\[\d+\]|\d+[\.\)]|\-\s+)\s*", "", raw)
    parts = [p.strip() for p in re.split(r"\.\s+", no_prefix) if p.strip()]
    for part in parts:
        words = part.split()
        if 4 <= len(words) <= 30 and not re.search(r"\b(doi|pmid|journal|vol)\b", part, re.I):
            return part.strip('"')
    return ""


def http_json(url: str, timeout: int) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": "medsci-skills/verify-refs (mailto:example@example.com)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except Exception:
        return None


def verify_crossref(doi: str, timeout: int) -> tuple[str, str]:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    data = http_json(url, timeout)
    if not data or data.get("status") != "ok":
        return "UNVERIFIED", "CrossRef DOI lookup failed"
    msg = data.get("message", {})
    title = " ".join(msg.get("title") or [])
    year_parts = (((msg.get("issued") or {}).get("date-parts") or [[None]])[0])
    year = str(year_parts[0]) if year_parts and year_parts[0] else ""
    evidence = f"CrossRef DOI OK"
    if title:
        evidence += f"; title={title[:120]}"
    if year:
        evidence += f"; year={year}"
    return "OK", evidence


def verify_pubmed_pmid(pmid: str, timeout: int) -> tuple[str, str]:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "retmode": "json"}
    )
    data = http_json(url, timeout)
    if not data:
        return "UNVERIFIED", "PubMed PMID lookup failed"
    result = data.get("result", {})
    item = result.get(pmid)
    if not item:
        return "FABRICATED", "PMID not found in PubMed"
    title = html.unescape(item.get("title", ""))
    return "OK", f"PubMed PMID OK; title={title[:120]}"


def verify_pubmed_title(title: str, timeout: int) -> tuple[str, str]:
    if not title:
        return "UNVERIFIED", "No DOI, PMID, or usable title"
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "term": title, "retmode": "json", "retmax": "3"}
    )
    data = http_json(url, timeout)
    if not data:
        return "UNVERIFIED", "PubMed title search failed"
    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return "UNVERIFIED", "No PubMed title match"
    return "OK", f"PubMed title match; PMID candidates={','.join(ids)}"


def verify_record(record: RefRecord, offline: bool, timeout: int) -> RefRecord:
    if offline:
        if record.doi or record.pmid:
            record.status = "UNVERIFIED"
            record.evidence = "Identifier extracted; offline mode"
        else:
            record.status = "UNVERIFIED"
            record.evidence = "No identifier; offline mode"
        return record

    checks: list[tuple[str, str]] = []
    if record.doi:
        checks.append(verify_crossref(record.doi, timeout))
        time.sleep(0.2)
    if record.pmid:
        checks.append(verify_pubmed_pmid(record.pmid, timeout))
        time.sleep(0.2)
    if not checks:
        checks.append(verify_pubmed_title(record.title_guess, timeout))
        time.sleep(0.2)

    statuses = [s for s, _ in checks]
    evidence = " | ".join(e for _, e in checks)
    if "OK" in statuses and "FABRICATED" in statuses:
        record.status = "MISMATCH"
    elif "OK" in statuses:
        record.status = "OK"
    elif "FABRICATED" in statuses:
        record.status = "FABRICATED"
    else:
        record.status = "UNVERIFIED"
    record.evidence = evidence
    return record


def write_outputs(records: list[RefRecord], project_root: Path, source: Path) -> None:
    """Audit-only writer (v1.1.1 Phase 1A.2).

    Per docs/artifact_contract.md, /verify-refs is sole writer of qc/reference_audit.json
    only. It MUST NOT write to references/ (that directory is owned by /search-lit and
    /lit-sync). All per-record details live inside reference_audit.json.
    """
    qc_dir = project_root / "qc"
    qc_dir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    for rec in records:
        counts[rec.status] = counts.get(rec.status, 0) + 1
    audit = {
        "schema_version": 2,
        "source": str(source),
        "total_references": len(records),
        "counts": counts,
        "submission_safe": counts.get("FABRICATED", 0) == 0 and counts.get("MISMATCH", 0) == 0,
        "fully_verified": counts.get("UNVERIFIED", 0) == 0 and counts.get("FABRICATED", 0) == 0 and counts.get("MISMATCH", 0) == 0,
        "requires_manual_reference_check": counts.get("UNVERIFIED", 0) > 0,
        "records": [asdict(rec) for rec in records],
    }
    (qc_dir / "reference_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify manuscript references.")
    parser.add_argument("input", help="Input .md, .docx, .bib, .txt, or .tsv file")
    parser.add_argument("--project-root", default=".", help="Project root for output artifacts")
    parser.add_argument("--offline", action="store_true", help="Do not call PubMed/CrossRef APIs")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP timeout seconds")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    project_root = Path(args.project_root).resolve()
    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 2

    text = read_input(input_path)
    suffix = input_path.suffix.lower()
    if suffix == ".bib":
        records = parse_bib(text)
    elif suffix == ".tsv":
        records = parse_tsv(text)
    else:
        records = parse_reference_lines(text)

    if not records:
        print("No references detected.", file=sys.stderr)
        return 3

    verified = [verify_record(rec, args.offline, args.timeout) for rec in records]
    write_outputs(verified, project_root, input_path)

    counts: dict[str, int] = {}
    for rec in verified:
        counts[rec.status] = counts.get(rec.status, 0) + 1
    print(json.dumps({"total": len(verified), "counts": counts}, indent=2))
    return 1 if counts.get("FABRICATED", 0) or counts.get("MISMATCH", 0) else 0


if __name__ == "__main__":
    sys.exit(main())

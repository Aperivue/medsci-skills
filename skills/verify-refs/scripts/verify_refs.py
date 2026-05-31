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
from dataclasses import dataclass, asdict, field
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
    first_author_guess: str = ""  # back-compat (= cited_authors[0] when available)
    # v1.3.0: full author cross-check (AI-assisted-drafting hallucination motivation)
    cited_authors: list = field(default_factory=list)        # family names parsed from bib/tsv/text
    actual_authors: list = field(default_factory=list)        # family names from authoritative source
    cited_author_count: int = 0
    actual_author_count: int = 0
    # v1.3.0: intentional truncate marker. Set via BibTeX field `_audit_truncated = N`
    # (any non-empty value); when present, count mismatch is downgraded to a note
    # and does not trigger MISMATCH status. Use when CSL renders first-1 or first-5
    # + et al. and the trailing authors are deliberately omitted from the bib.
    audit_truncated: bool = False
    status: str = "UNVERIFIED"
    evidence: str = ""
    note: str = ""


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_doi(doi: str) -> str:
    return doi.rstrip(".,;)].").lower()


def normalize_doi_for_dup(doi: str) -> str:
    """Strict DOI normalization for duplicate detection.

    Beyond clean_doi(): strips common URL prefixes and trailing slashes so that
    `https://doi.org/10.1234/abc/` and `10.1234/abc` collapse to the same key.
    """
    if not doi:
        return ""
    s = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/",
                   "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    s = s.strip().rstrip("/")
    return clean_doi(s)


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
        # Balanced-brace aware author capture (handles "\~{n}" LaTeX escapes that
        # would otherwise terminate a non-greedy {.+?} match prematurely).
        author_field = ""
        am = re.search(r"author\s*=\s*\{", entry, re.I)
        if am:
            start = am.end()
            depth = 1
            j = start
            while j < len(entry) and depth > 0:
                if entry[j] == "{":
                    depth += 1
                elif entry[j] == "}":
                    depth -= 1
                j += 1
            author_field = entry[start : j - 1]
        cited = parse_bib_authors(author_field)
        # v1.3.0: intentional truncate marker (any non-empty `_audit_truncated`)
        trunc_match = re.search(r"_audit_truncated\s*=\s*[\{\"]?([^,}\"]+)", entry, re.I)
        records.append(
            RefRecord(
                ref_id=key_match.group(1) if key_match else f"ref_{len(records)+1}",
                raw=raw,
                title_guess=normalize_space(title_match.group(1)) if title_match else "",
                doi=clean_doi(doi_match.group(1)) if doi_match else "",
                pmid=pmid_match.group(1) if pmid_match else "",
                year_guess=year_match.group(1) if year_match else "",
                first_author_guess=cited[0] if cited else (parse_first_author(author_field) if author_field else ""),
                cited_authors=cited,
                cited_author_count=len(cited),
                audit_truncated=bool(trunc_match and trunc_match.group(1).strip().lower() not in ("", "false", "0", "no")),
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
        author_field = row.get("author") or row.get("authors") or row.get("Author") or row.get("Authors") or ""
        records.append(
            RefRecord(
                ref_id=f"ref_{i}",
                raw=normalize_space(joined),
                title_guess=title,
                doi=doi,
                pmid=pmid,
                first_author_guess=parse_first_author(author_field) if author_field else "",
            )
        )
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
                first_author_guess=parse_first_author(raw),
            )
        )
    return records


_NAME_PARTICLES = {"von", "van", "de", "del", "della", "dos", "da", "le", "la", "du", "den", "der", "ten"}


def parse_bib_authors(author_field: str) -> list:
    """Parse BibTeX author field into a list of family-name strings.

    Handles "Last, First and Last, First" and "First Last and First Last" forms.
    Strips simple LaTeX accents and braces.
    """
    if not author_field:
        return []
    raw = re.sub(r"\s+", " ", author_field).strip()
    parts = re.split(r"\s+and\s+", raw)
    families: list[str] = []
    for name in parts:
        n = name.strip()
        if not n:
            continue
        if "," in n:
            family = n.split(",", 1)[0].strip()
        else:
            toks = n.split()
            family = toks[-1] if toks else ""
        # Strip simple LaTeX accents: \~{n}, \"{o}, \`{a} → underlying char
        family = re.sub(r"\\[\"'`~^=.]?\{?([A-Za-zà-ÿ])\}?", r"\1", family)
        family = re.sub(r"[{}]", "", family).strip()
        if family and family != "others":
            families.append(family)
    return families


def parse_first_author(raw: str) -> str:
    """Extract first-author surname from a Vancouver/AMA/BibTeX-style citation.

    Conservative: returns "" when the format is ambiguous so author-mismatch
    checks degrade gracefully rather than firing false MISMATCH alerts.
    """
    text = re.sub(r"^\s*(\[\d+\]|\d+[\.\)])\s*", "", raw).strip()
    bib_m = re.search(r"author\s*=\s*[{\"]([^}\"]+)", text, re.I)
    if bib_m:
        text = bib_m.group(1)
    text = re.split(r"\s+and\s+", text, maxsplit=1)[0]
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return ""
    # "Lastname, Firstname H." style (BibTeX expanded)
    if len(parts) >= 2 and re.match(r"^[A-Z][a-zA-Z .\-']*$", parts[1]) and not re.search(r"\d", parts[1]):
        if re.match(r"^[A-Z][a-zA-Zà-ÿ'\- ]+$", parts[0]):
            return parts[0].strip()
    first = parts[0]
    # "Surname Initials" — strip trailing initials block (e.g., "DH", "J", "F.D.")
    m = re.match(
        r"^((?:(?:" + "|".join(_NAME_PARTICLES) + r")\s+)?[A-Zà-ÿ][\wà-ÿ'\-]*(?:\s+[A-Zà-ÿ][\wà-ÿ'\-]*)?)\s+(?:[A-Z]\.?\s*){1,4}$",
        first,
    )
    if m:
        return m.group(1).strip()
    tokens = first.split()
    if tokens and tokens[0].lower() in _NAME_PARTICLES and len(tokens) >= 2:
        return f"{tokens[0]} {tokens[1]}"
    return tokens[0] if tokens else ""


def _normalize_surname(name: str) -> str:
    """Strip diacritics + lowercase for surname comparison.

    Coverage (v1.3.0): Latin-with-accents (NFKD decomposes), Turkish
    (ş→s, ğ→g, ı→i), Polish/Czech (ł, đ — not NFKD-decomposable, handled below),
    German ß→ss, Nordic ø/æ/œ → o/ae/oe. Motivation: a Turkish surname
    `Çolakoğlu` vs PubMed `Colakoglu` false-positive MISMATCH.
    """
    import unicodedata
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().strip()
    # Multi-char + non-NFKD-decomposable mappings
    multi = {
        "ß": "ss", "þ": "th", "ł": "l", "đ": "d", "ı": "i",
        "ø": "o", "æ": "ae", "œ": "oe",
    }
    for k, v in multi.items():
        n = n.replace(k, v)
    n = re.sub(r"[^a-z\s\-]", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def author_surnames_match(cited: str, actual: str) -> bool:
    """Tolerant comparison: handles particle variants and hyphenation."""
    if not cited or not actual:
        return True  # cannot judge → do not flag
    a = _normalize_surname(cited)
    b = _normalize_surname(actual)
    if not a or not b:
        return True
    if a == b:
        return True
    # Particle-stripped variants ("von elm" vs "elm")
    a_core = re.sub(r"^(?:" + "|".join(_NAME_PARTICLES) + r")\s+", "", a)
    b_core = re.sub(r"^(?:" + "|".join(_NAME_PARTICLES) + r")\s+", "", b)
    if a_core and b_core and (a_core == b_core or a_core in b_core or b_core in a_core):
        return True
    # Hyphen vs space ("Abd-alrazaq" vs "abd alrazaq")
    if a.replace("-", " ") == b.replace("-", " "):
        return True
    return False


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


def verify_crossref(doi: str, timeout: int) -> tuple[str, str, list]:
    """Returns (status, evidence, family_names).

    v1.3.0: returns full author family list instead of first-author only.
    CrossRef API is not authoritative for given names (documented case: CrossRef
    returned "Vasileios", PubMed efetch & the curated record = "Victoria").
    Use verify_pubmed_efetch as the truth source when PMID is available.
    """
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    data = http_json(url, timeout)
    if not data or data.get("status") != "ok":
        return "UNVERIFIED", "CrossRef DOI lookup failed", []
    msg = data.get("message", {})
    title = " ".join(msg.get("title") or [])
    year_parts = (((msg.get("issued") or {}).get("date-parts") or [[None]])[0])
    year = str(year_parts[0]) if year_parts and year_parts[0] else ""
    authors_raw = msg.get("author") or []
    families: list[str] = []
    for a in authors_raw:
        fam = (a.get("family") or a.get("name") or "").strip()
        if fam:
            families.append(fam)
    evidence = "CrossRef DOI OK"
    if title:
        evidence += f"; title={title[:120]}"
    if year:
        evidence += f"; year={year}"
    if families:
        evidence += f"; authors={len(families)} (first={families[0]})"
    return "OK", evidence, families


def verify_pubmed_pmid(pmid: str, timeout: int) -> tuple[str, str, list]:
    """Returns (status, evidence, family_names).

    Uses esummary (fast). Returns family-name approximation by stripping trailing
    initial block from "Surname Initials" form. Authoritative names → call
    verify_pubmed_efetch().
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "retmode": "json"}
    )
    data = http_json(url, timeout)
    if not data:
        return "UNVERIFIED", "PubMed PMID lookup failed", []
    result = data.get("result", {})
    item = result.get(pmid)
    if not item:
        return "FABRICATED", "PMID not found in PubMed", []
    if item.get("error"):
        return "FABRICATED", f"PubMed PMID error: {item['error']}", []
    title = html.unescape(item.get("title", ""))
    authors_raw = item.get("authors") or []
    families: list[str] = []
    for a in authors_raw:
        if a.get("authtype") not in (None, "Author"):
            continue
        full = (a.get("name") or "").strip()
        # esummary "name" is "Surname Initials" e.g. "Reichheld FF"
        m = re.match(r"^(.+?)\s+[A-Z]{1,4}$", full)
        fam = m.group(1).strip() if m else full
        if fam:
            families.append(fam)
    evidence = f"PubMed PMID OK; title={title[:120]}; authors={len(families)}"
    if families:
        evidence += f" (first={families[0]})"
    return "OK", evidence, families


def verify_pubmed_efetch(pmid: str, timeout: int) -> tuple[str, str, list, list]:
    """Authoritative PubMed full author record via efetch.fcgi (XML).

    Returns (status, evidence, family_names, given_names). Use given_names for
    given-name cross-check (CrossRef-vs-PubMed disagreement, e.g. a documented
    case: CrossRef "Vasileios" vs PubMed "Victoria" — PubMed is authoritative).
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "retmode": "xml"}
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "medsci-skills/verify-refs (mailto:example@example.com)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml_text = resp.read().decode("utf-8", "replace")
    except Exception:
        return "UNVERIFIED", "PubMed efetch failed", [], []
    families: list[str] = []
    givens: list[str] = []
    # Per-Author block: <Author ValidYN="Y"><LastName>X</LastName><ForeName>Y</ForeName>...
    for am in re.finditer(
        r'<Author\s+ValidYN="Y"[^>]*>(.*?)</Author>', xml_text, re.S
    ):
        block = am.group(1)
        lm = re.search(r"<LastName>([^<]+)</LastName>", block)
        fm = re.search(r"<ForeName>([^<]+)</ForeName>", block)
        if lm:
            families.append(html.unescape(lm.group(1)).strip())
            givens.append(html.unescape(fm.group(1)).strip() if fm else "")
    if not families:
        return "UNVERIFIED", "PubMed efetch returned no author elements", [], []
    return (
        "OK",
        f"PubMed efetch OK; authors={len(families)} (first={families[0]})",
        families,
        givens,
    )


def verify_pubmed_title(title: str, timeout: int) -> tuple[str, str, list]:
    """Title-only search returns no confident author list."""
    if not title:
        return "UNVERIFIED", "No DOI, PMID, or usable title", []
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "term": title, "retmode": "json", "retmax": "3"}
    )
    data = http_json(url, timeout)
    if not data:
        return "UNVERIFIED", "PubMed title search failed", []
    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return "UNVERIFIED", "No PubMed title match", []
    return "OK", f"PubMed title match; PMID candidates={','.join(ids)}", []


def verify_record(record: RefRecord, offline: bool, timeout: int) -> RefRecord:
    """v1.3.0: full-author cross-check.

    Authoritative source priority for the actual author list:
      1. PubMed efetch (XML full-record) — best (motivation: CrossRef returned a
         wrong given name "Vasileios" vs PubMed efetch authoritative "Victoria";
         also catches AI-generated bib entries with hallucinated #2..#N family
         names — a real AI-assembled bib registered 7 of 10 fabricated co-author names).
      2. CrossRef DOI (fallback when no PMID).
      3. PubMed esummary (fast count check; family-name approximation only).
    All cited authors (BibTeX) are compared family-by-family against the
    authoritative list AND total counts are compared. Any cited author beyond
    the actual list, any per-index family mismatch, and any count mismatch are
    each reported. When no full cited list was parsed (TSV / plain text), the
    check degrades to the first-author surname comparison (Gate 4 behaviour).
    """
    if offline:
        if record.doi or record.pmid:
            record.status = "UNVERIFIED"
            record.evidence = "Identifier extracted; offline mode"
        else:
            record.status = "UNVERIFIED"
            record.evidence = "No identifier; offline mode"
        return record

    statuses: list[str] = []
    evidence_parts: list[str] = []
    actual_authors: list[str] = []
    actual_givens: list[str] = []
    sources_consulted: list[str] = []

    # Step 1 — PubMed efetch (authoritative) when PMID present.
    if record.pmid:
        st, ev, fams, givens = verify_pubmed_efetch(record.pmid, timeout)
        time.sleep(0.2)
        statuses.append(st)
        evidence_parts.append(ev)
        if st == "OK" and fams:
            actual_authors = fams
            actual_givens = givens
            sources_consulted.append("pubmed_efetch")
        # also run esummary for FABRICATED detection (efetch returns valid XML even for
        # unknown PMIDs in some edge cases; esummary's "error" field is decisive).
        st_es, ev_es, fams_es = verify_pubmed_pmid(record.pmid, timeout)
        time.sleep(0.2)
        statuses.append(st_es)
        evidence_parts.append(ev_es)
        if not actual_authors and st_es == "OK" and fams_es:
            actual_authors = fams_es
            sources_consulted.append("pubmed_esummary")

    # Step 2 — CrossRef DOI (used only when efetch did not provide a list).
    if record.doi:
        st_cr, ev_cr, fams_cr = verify_crossref(record.doi, timeout)
        time.sleep(0.2)
        statuses.append(st_cr)
        evidence_parts.append(ev_cr)
        if not actual_authors and st_cr == "OK" and fams_cr:
            actual_authors = fams_cr
            sources_consulted.append("crossref")

    # Step 3 — title-only fallback (no confident author list).
    if not statuses:
        st_t, ev_t, _ = verify_pubmed_title(record.title_guess, timeout)
        time.sleep(0.2)
        statuses.append(st_t)
        evidence_parts.append(ev_t)

    # Full-author cross-check
    record.actual_authors = actual_authors
    record.actual_author_count = len(actual_authors)
    if record.cited_authors and not record.cited_author_count:
        record.cited_author_count = len(record.cited_authors)

    mismatches: list[str] = []
    if record.cited_authors and actual_authors:
        compare_n = min(len(record.cited_authors), len(actual_authors))
        for i in range(compare_n):
            cited = record.cited_authors[i]
            if not author_surnames_match(cited, actual_authors[i]):
                mismatches.append(
                    f"#{i+1} family: cited='{cited}' vs source='{actual_authors[i]}'"
                )
        # cited has more authors than source — always flag (cannot be intentional)
        for i in range(compare_n, len(record.cited_authors)):
            mismatches.append(
                f"#{i+1} extra cited='{record.cited_authors[i]}' (source has only {len(actual_authors)} authors)"
            )
        # source has more authors than cited — count mismatch, suppressed under
        # `_audit_truncated` marker (intentional CSL et-al truncation).
        if record.cited_author_count != record.actual_author_count:
            if record.audit_truncated and record.cited_author_count < record.actual_author_count:
                evidence_parts.append(
                    f"NOTE: intentional truncate ({record.cited_author_count} of {record.actual_author_count}; "
                    f"`_audit_truncated` marker set)"
                )
            else:
                mismatches.append(
                    f"AUTHOR COUNT: cited={record.cited_author_count} vs source={record.actual_author_count}"
                )
    elif record.first_author_guess and actual_authors:
        # No parsed cited author list (TSV / plain-text input) — degrade to the
        # first-author surname cross-check (Gate 4 behaviour).
        if not any(author_surnames_match(record.first_author_guess, a) for a in actual_authors):
            mismatches.append(
                f"#1 family: cited='{record.first_author_guess}' vs source='{actual_authors[0]}'"
            )

    author_mismatch = bool(mismatches)
    if author_mismatch:
        evidence_parts.append("AUTHOR MISMATCH | " + " | ".join(mismatches))

    # Status precedence
    if "OK" in statuses and "FABRICATED" in statuses:
        record.status = "MISMATCH"
    elif "OK" in statuses:
        record.status = "MISMATCH" if author_mismatch else "OK"
    elif "FABRICATED" in statuses:
        record.status = "FABRICATED"
    else:
        record.status = "UNVERIFIED"

    # Note classification (most informative wins)
    if author_mismatch and not record.note:
        # Distinguish first-author hallucination (high reviewer salience)
        first_cited = record.cited_authors[0] if record.cited_authors else record.first_author_guess
        first_bad = (
            first_cited
            and actual_authors
            and not author_surnames_match(first_cited, actual_authors[0])
        )
        if first_bad:
            record.note = "first-author hallucination suspected (DOI/PMID correct, family differs)"
        else:
            record.note = "non-first-author hallucination or count mismatch (DOI/PMID correct)"
    record.evidence = " | ".join(p for p in evidence_parts if p)
    if sources_consulted:
        record.evidence += f" | source={'+'.join(sources_consulted)}"
    return record


def detect_duplicates(records: list[RefRecord]) -> list[dict]:
    """Detect verbatim PMID or DOI duplicates within the reference list.

    Verbatim duplicates (same PMID or normalized DOI) are a common LLM
    citation-compilation artifact and require cite renumbering before
    submission.
    """
    seen_pmids: dict[str, str] = {}
    seen_dois: dict[str, str] = {}
    findings: list[dict] = []
    for rec in records:
        rec_id = rec.ref_id or "<unknown>"
        pmid = (rec.pmid or "").strip()
        if pmid:
            if pmid in seen_pmids:
                findings.append({
                    "severity": "MAJOR",
                    "category": "duplicate_pmid",
                    "ref_ids": [seen_pmids[pmid], rec_id],
                    "pmid": pmid,
                    "note": "Verbatim duplicate reference. Cite renumbering required.",
                })
            else:
                seen_pmids[pmid] = rec_id
        doi = normalize_doi_for_dup(rec.doi or "")
        if doi:
            if doi in seen_dois:
                findings.append({
                    "severity": "MAJOR",
                    "category": "duplicate_doi",
                    "ref_ids": [seen_dois[doi], rec_id],
                    "doi": doi,
                    "note": "Verbatim duplicate reference. Cite renumbering required.",
                })
            else:
                seen_dois[doi] = rec_id
    return findings


def write_outputs(records: list[RefRecord], project_root: Path, source: Path,
                  duplicate_findings: list[dict]) -> None:
    """Audit-only writer (v1.3.0).

    Per docs/artifact_contract.md, /verify-refs is sole writer of qc/reference_audit.json
    only. It MUST NOT write to references/ (that directory is owned by /search-lit and
    /lit-sync). All per-record details live inside reference_audit.json.

    v1.2.0 (2026-05): adds duplicate_findings[] for PMID/DOI duplicate detection
    (Gate 5; resolves /peer-review Phase 2A P7). submission_safe and fully_verified
    both require duplicate_findings to be empty.

    v1.3.0 (2026-05): full-author cross-check. records[] now carry cited_authors[],
    actual_authors[], and author counts; schema_version bumps to 4. MISMATCH now
    fires on any #2..#N family hallucination or author-count mismatch, not just the
    first author (motivation: a bib entry with a real first author but 7/10
    fabricated co-author given names previously passed audit).
    """
    qc_dir = project_root / "qc"
    qc_dir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    for rec in records:
        counts[rec.status] = counts.get(rec.status, 0) + 1
    audit = {
        "schema_version": 4,
        "source": str(source),
        "total_references": len(records),
        "counts": counts,
        "duplicate_findings": duplicate_findings,
        "submission_safe": (
            counts.get("FABRICATED", 0) == 0
            and counts.get("MISMATCH", 0) == 0
            and len(duplicate_findings) == 0
        ),
        "fully_verified": (
            counts.get("UNVERIFIED", 0) == 0
            and counts.get("FABRICATED", 0) == 0
            and counts.get("MISMATCH", 0) == 0
            and len(duplicate_findings) == 0
        ),
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
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on any UNVERIFIED row, and forbid --offline")
    args = parser.parse_args()

    if args.strict and args.offline:
        print("--strict is incompatible with --offline", file=sys.stderr)
        return 2

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
    duplicate_findings = detect_duplicates(verified)
    write_outputs(verified, project_root, input_path, duplicate_findings)

    counts: dict[str, int] = {}
    for rec in verified:
        counts[rec.status] = counts.get(rec.status, 0) + 1
    print(json.dumps({
        "total": len(verified),
        "counts": counts,
        "duplicate_findings_count": len(duplicate_findings),
    }, indent=2))
    if counts.get("FABRICATED", 0) or counts.get("MISMATCH", 0) or duplicate_findings:
        return 1
    if args.strict and counts.get("UNVERIFIED", 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

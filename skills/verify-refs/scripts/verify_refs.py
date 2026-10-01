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
import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, asdict, field
from pathlib import Path
from xml.etree import ElementTree as ET


# `<>` belong to legacy SICI DOIs (10.1002/(SICI)...17:8<857::AID-SIM777>3.0.CO;2-E), whose
# check character after `;2-` can also be `#`. Without them a text reference's DOI was cut
# short, and a cut DOI is not registered anywhere, which the doi.org check below would
# report as FABRICATED.
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:<>A-Z0-9]+(?:(?<=;2-)#|\b)", re.I)
WELL_FORMED_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
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
    #
    # It is ALSO set by the standard BibTeX `and others` sentinel. `_audit_truncated`
    # is a field this toolkit invented; `and others` is the one every reference
    # manager already writes and BibTeX/CSL already render as "et al.". Treating it
    # as a count mismatch fired MISMATCH — the render-aborting verdict — on any
    # consortium or multisociety-guideline reference, which is the class clinical
    # manuscripts cite most.
    audit_truncated: bool = False
    # Collective / corporate author (EASL, KDIGO, AHA/ACC, WHO, a named working
    # group / consortium). BibTeX convention double-braces these
    # (`author = {{KDIGO Working Group}}`) and PubMed returns them as
    # <CollectiveName>; the personal-name family cross-check does not apply and
    # must not fire MISMATCH (which would abort render on every guideline-citing
    # cohort manuscript).
    corporate_author: bool = False
    # True when title_guess came from a title field (BibTeX `title`, a TSV title column). Only
    # such a title is compared with the record a DOI/PMID resolves to: a title guessed from a
    # plain-text reference line is often the author list, and comparing it would turn clean
    # references into MISMATCH.
    title_from_field: bool = False
    status: str = "UNVERIFIED"
    evidence: str = ""
    note: str = ""


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# Organization / collective-author signal in an author field. Used (a) when a
# brace survives in the parsed BibTeX author field (double-brace convention) and
# (b) as a keyword fallback for single-braced or plain-text collective names.
_ORG_AUTHOR_RE = re.compile(
    r"\b(?:Group|Committee|Society|Association|Collaborat\w+|Consortium|Network|"
    r"Panel|Initiative|Organization|Organisation|Investigators|Trialists|Task\s+Force|"
    r"Working\s+Group|Study\s+Group|Foundation|Institute|Council|Federation|College|"
    r"WHO|EASL|EASD|EASO|KDIGO|AHA|ACC|ESC|NICE|AASLD|KASL)\b", re.IGNORECASE)


def is_corporate_author_field(author_field: str) -> bool:
    """A collective/corporate author (a guideline body, working group, consortium)
    rather than a list of people.

    Braces alone do NOT make an author corporate. Better BibTeX brace-protects a
    hyphenated or particle SURNAME so BibTeX will not re-case or re-split it —
    `author = {{Eckel-Passow}, Jeanette E. and {von Deimling}, Andreas}` — and the
    old brace-only rule read those as organizations and *skipped* the author
    cross-check entirely. That is a false PASS, not a false alarm: the check this
    tool exists to perform was silently not performed, and nothing said so.

    A field is corporate when it carries an organizational keyword, or when it is a
    single braced blob with no personal-name structure at all (no comma separating a
    surname from a given name, no `and`-joined list).
    """
    if not author_field:
        return False
    if _ORG_AUTHOR_RE.search(author_field):
        return True

    braced = "{" in author_field or "}" in author_field
    if not braced:
        return False

    # Personal-name structure survives brace-stripping -> these are people.
    bare = author_field.replace("{", "").replace("}", "")
    if "," in bare or re.search(r"\band\b", bare):
        return False

    # A lone braced blob with no keyword and no name structure (e.g. `{{ADNI}}`):
    # still treat as collective — skipping is the conservative outcome there.
    return True


def clean_doi(doi: str) -> str:
    return doi.rstrip(".,;)].").lower()


def normalize_doi_for_dup(doi: str, keep_trailing_slash: bool = False) -> str:
    """Strict DOI normalization for duplicate detection.

    Beyond clean_doi(): strips common URL prefixes and trailing slashes so that
    `https://doi.org/10.1234/abc/` and `10.1234/abc` collapse to the same key.
    A trailing slash is legal in a DOI, so a registry lookup also needs the form
    that keeps it (`keep_trailing_slash=True`).
    """
    if not doi:
        return ""
    s = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/",
                   "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    s = s.strip()
    if not keep_trailing_slash:
        s = s.rstrip("/")
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


def brace_field(entry: str, name: str) -> str:
    """Read a brace-delimited BibTeX field by counting braces, not by regex.

    A non-greedy `{(.+?)}` stops at the first `}`, which truncates any brace-protected inner group
    (`title = {A multisociety {Delphi} consensus}`). Anchoring the match on a trailing comma avoids
    that but silently returns nothing when the field is the entry's LAST one, where BibTeX makes the
    comma optional. Counting depth is correct in both cases. Returns "" when the field is absent or
    is not brace-delimited.
    """
    m = re.search(rf"(?<![\w-]){name}\s*=\s*\{{", entry, re.I)
    if not m:
        return ""
    start = m.end()
    depth, j = 1, start
    while j < len(entry) and depth > 0:
        if entry[j] == "{":
            depth += 1
        elif entry[j] == "}":
            depth -= 1
        j += 1
    return entry[start : j - 1]


def parse_bib(text: str) -> list[RefRecord]:
    records: list[RefRecord] = []
    entries = re.split(r"\n(?=@\w+\{)", "\n" + text)
    for entry in entries:
        entry = entry.strip()
        if not entry.startswith("@"):
            continue
        key_match = re.match(r"@\w+\{([^,]+),", entry)
        # Field names are matched whole (`(?<![\w-])`): `title` also matched inside `booktitle`,
        # so a proceedings paper whose booktitle came first was read with the proceedings name.
        title_match = (re.search(r"(?<![\w-])title\s*=\s*[\{\"](.+?)[\}\"]\s*,", entry, re.I | re.S)
                       or re.search(r'(?<![\w-])title\s*=\s*"([^"]+)"', entry, re.I))
        # The trailing comma is OPTIONAL: BibTeX does not require one after an entry's LAST field,
        # and `doi` is very often that last field. Requiring it left `record.doi` empty for those
        # entries, which skips the CrossRef check outright and drops the record onto the soft-flagged
        # OpenAlex title path where the author cross-check is disabled — so the anti-fabrication
        # check this skill exists for was silently off for exactly those references. Unlike `title`
        # on the line above, a DOI never carries brace-protected inner groups (`{Delphi}`), so
        # stopping at the first `}` is correct here and would truncate there.
        doi_match = re.search(r"(?<![\w-])doi\s*=\s*[\{\"](.+?)[\}\"]\s*,?", entry, re.I | re.S)
        pmid_match = re.search(r"(?<![\w-])pmid\s*=\s*[\{\"]?(\d{5,9})", entry, re.I)
        year_match = re.search(r"(?<![\w-])year\s*=\s*[\{\"]?((?:19|20)\d{2})", entry, re.I)
        raw = normalize_space(entry)
        author_field = brace_field(entry, "author")
        # `title` needs the same balanced-brace read, and for the same reason `doi` needed an
        # optional comma: the regex above requires a trailing comma, so a title that is the entry's
        # LAST field came back empty. It cannot simply take `,?` — the non-greedy match would then
        # stop at the inner `}` of a brace-protected group and return "A multisociety {Delphi".
        # Prefer the balanced read whenever the field is brace-delimited; keep the regex for the
        # quote-delimited form it already handled.
        title_braced = brace_field(entry, "title")
        if title_braced:
            title_match = None
            title_text = title_braced
        else:
            title_text = title_match.group(1) if title_match else ""
        cited = parse_bib_authors(author_field)
        # v1.3.0: intentional truncate marker (any non-empty `_audit_truncated`)
        trunc_match = re.search(r"_audit_truncated\s*=\s*[\{\"]?([^,}\"]+)", entry, re.I)
        records.append(
            RefRecord(
                ref_id=key_match.group(1) if key_match else f"ref_{len(records)+1}",
                raw=raw,
                title_guess=normalize_space(title_text),
                title_from_field=bool(title_text.strip()),
                doi=clean_doi(doi_match.group(1)) if doi_match else "",
                pmid=pmid_match.group(1) if pmid_match else "",
                year_guess=year_match.group(1) if year_match else "",
                first_author_guess=cited[0] if cited else (parse_first_author(author_field) if author_field else ""),
                cited_authors=cited,
                cited_author_count=len(cited),
                audit_truncated=(
                    bool(trunc_match and trunc_match.group(1).strip().lower() not in ("", "false", "0", "no"))
                    or has_bibtex_et_al(author_field)
                ),
                corporate_author=is_corporate_author_field(author_field),
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
                title_from_field=bool(title.strip()),
                doi=doi,
                pmid=pmid,
                first_author_guess=parse_first_author(author_field) if author_field else "",
                corporate_author=is_corporate_author_field(author_field),
            )
        )
    return records


# A bare "References" line, or a Markdown heading ("## References", "**References**",
# Quarto's "# References {.unnumbered}"). Missing the heading form parsed the whole .md/.qmd,
# so body paragraphs and bullets became references (all UNVERIFIED; --strict never passed).
REFERENCE_HEADING_RE = re.compile(
    r"(?im)^[ \t]*(#{1,6})?[ \t]*\**[ \t]*(?:references|bibliography|reference list)"
    r"[ \t]*\**[ \t]*:?[ \t]*(?:\{[^}\n]*\})?[ \t]*$"
)


def reference_section(text: str) -> str:
    match = REFERENCE_HEADING_RE.search(text)
    if not match:
        return text
    section = text[match.end() :]
    # The list ends at the next heading of the same or a higher level (Tables, Figure
    # Legends); after a bare "References" line, at any Markdown heading.
    level = len(match.group(1) or "") or 6
    end = re.search(rf"(?m)^[ \t]*#{{1,{level}}}[ \t]", section)
    return section[: end.start()] if end else section


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


def has_bibtex_et_al(author_field: str) -> bool:
    """True when the author field ends in the BibTeX `and others` sentinel.

    `and others` is BibTeX's own way of saying "et al." — it is what Zotero,
    Mendeley, JabRef and a hand-written .bib all emit for a list the author chose
    not to type out, and what BibTeX and CSL both render as an et-al. It is a
    declaration that the list is deliberately short, so a cited-vs-source count
    difference is expected and must not be reported as a mismatch.

    Matched only in the trailing position, where BibTeX defines it. A real surname
    "Others" mid-list (or a first name "Others") is not this sentinel and is left
    to the ordinary family cross-check.
    """
    if not author_field:
        return False
    return bool(re.search(r"\s+and\s+others\s*$", re.sub(r"\s+", " ", author_field).strip(), re.I))


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

    Unicode dashes are folded to ASCII `-` FIRST. The final filter keeps `[a-z\\s-]`
    and deletes everything else, so a publisher-supplied U+2010 in a hyphenated
    surname was *deleted* rather than matched: CrossRef `Foltyn‐Dumitru` normalized
    to `foltyndumitru` while the identical ASCII bib entry gave `foltyn-dumitru`,
    and the audit fired MISMATCH — its loudest verdict — on a clean reference.
    """
    import unicodedata
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().strip()
    # Unicode dash/hyphen variants -> ASCII hyphen. Publisher metadata uses these
    # freely in hyphenated surnames (U+2010 HYPHEN, U+2011 NON-BREAKING HYPHEN,
    # U+2012 FIGURE DASH, U+2013 EN DASH, U+2014 EM DASH, U+2212 MINUS).
    n = re.sub(r"[‐‑‒–—―−﹘﹣－]", "-", n)
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


def _contact_email() -> str:
    """User-supplied contact email (courtesy for NCBI/CrossRef), never a credential."""
    return (os.environ.get("MEDSCI_CONTACT_EMAIL")
            or os.environ.get("NCBI_EMAIL")
            or "medsci-skills@users.noreply.github.com")


def _user_agent() -> str:
    return f"medsci-skills/verify-refs (mailto:{_contact_email()})"


def _ncbi_extras() -> dict:
    """Optional NCBI E-utilities etiquette / rate-limit params, all from env.
    Setting NCBI_API_KEY raises the PubMed rate limit from 3 to 10 requests/s;
    absent it, the calls stay keyless. `tool`/`email` are NCBI-recommended courtesy."""
    extra = {"tool": "medsci-skills", "email": _contact_email()}
    key = os.environ.get("NCBI_API_KEY")
    if key:
        extra["api_key"] = key
    return extra


def http_json(url: str, timeout: int) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except Exception:
        return None


def http_fetch(url: str, timeout: int) -> tuple[int | None, dict | None]:
    """(HTTP status, parsed JSON body) — unlike http_json, an error status is returned.

    A registry's 404 is an answer ("no such DOI"), not a failed lookup, so the DOI path
    needs to tell it apart from a timeout. Status is None when no HTTP response arrived;
    the body is None when it is not JSON.
    """
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, body = resp.status, resp.read()
    except urllib.error.HTTPError as err:
        status = err.code
        try:
            body = err.read()
        except Exception:
            body = b""
    except Exception:
        return None, None
    try:
        return status, json.loads(body.decode("utf-8", "replace"))
    except ValueError:
        return status, None


def crossref_year(msg: dict) -> str:
    """The year to show for a CrossRef record: print, then online, then issued.

    `issued` is the EARLIEST publication date, so an article published online in December
    and in a print issue the next January reports the online year there, while journals
    cite the issue year. Showing `issued` alone invites "correcting" a bib year that was
    right. When the candidates disagree, both are shown, e.g. "2023 (print; online 2022)".
    """
    years: list[tuple[str, str]] = []
    for field_name, label in (("published-print", "print"), ("published-online", "online"),
                              ("issued", "issued")):
        parts = ((msg.get(field_name) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            years.append((label, str(parts[0])))
    if not years:
        return ""
    primary_label, primary = years[0]
    others: list[tuple[str, str]] = []
    for label, value in years[1:]:
        if value != primary and all(value != seen for _, seen in others):
            others.append((label, value))
    if not others:
        return primary
    return f"{primary} ({primary_label}; " + "; ".join(f"{l} {v}" for l, v in others) + ")"


def verify_crossref(doi: str, timeout: int, titles: list | None = None) -> tuple[str, str, list]:
    """Returns (status, evidence, family_names); on OK, the record's titles go into `titles`.

    v1.3.0: returns full author family list instead of first-author only.
    CrossRef API is not authoritative for given names (documented case: CrossRef
    returned "Vasileios", PubMed efetch & the curated record = "Victoria").
    Use verify_pubmed_efetch as the truth source when PMID is available.
    """
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    status, data = http_fetch(url, timeout)
    if status == 404:
        return verify_doi_handle(doi, timeout)
    if not isinstance(data, dict) or data.get("status") != "ok":
        return "UNVERIFIED", "CrossRef DOI lookup failed", []
    msg = data.get("message", {})
    title = " ".join(msg.get("title") or [])
    year = crossref_year(msg)
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
    if titles is not None:
        titles.extend(crossref_titles(msg))
    return "OK", evidence, families


def crossref_titles(msg: dict) -> list:
    """Every title a CrossRef record answers to.

    CrossRef keeps a subtitle in its own field, so the cited "Main: Sub" is matched against
    the joined form as well as the bare title; a translated work carries `original-title`; and
    a chapter DOI cited by its book's title is not a different work.
    """
    main = [t for t in (msg.get("title") or []) if t]
    out = list(main)
    out += [f"{m}: {sub}" for m in main for sub in (msg.get("subtitle") or []) if sub]
    out += [t for t in (msg.get("original-title") or []) + (msg.get("short-title") or []) if t]
    if msg.get("type") in ("book-chapter", "book-section", "book-part", "reference-entry"):
        out += [t for t in (msg.get("container-title") or []) if t]
    return out


def verify_doi_handle(doi: str, timeout: int) -> tuple[str, str, list]:
    """A DOI CrossRef answered 404 for: ask the DOI handle registry whether it exists at all.

    CrossRef is one of several registration agencies (DataCite, mEDRA, JaLC, ...), so its 404
    alone proves nothing. doi.org's handle API resolves across all of them: HTTP 404 with
    responseCode 100 means the DOI is registered nowhere, i.e. it does not exist -> FABRICATED,
    the same meaning as a PMID PubMed has no record of (verify_record turns it into MISMATCH
    when a title search then finds the work: a real paper cited with a wrong DOI). A registered
    DOI (a DataCite one, say) stays UNVERIFIED for the later indexes to confirm; any other
    answer (5xx, unexpected JSON), a network error, or a string that is not a well-formed DOI
    (a placeholder such as "n/a") is UNVERIFIED as before. A DOI may legally end in "/", which
    normalization strips, so the cited form is looked up too: FABRICATED only when every form is
    registered nowhere. A legacy SICI DOI that is not found stays UNVERIFIED: its punctuation is
    easily cut in extraction. Returns (status, evidence, family_names).
    """
    handle = normalize_doi_for_dup(doi)
    if not WELL_FORMED_DOI_RE.match(handle):
        return "UNVERIFIED", "CrossRef 404; not a well-formed DOI, doi.org not consulted", []
    answers = []
    for form in dict.fromkeys([handle, normalize_doi_for_dup(doi, keep_trailing_slash=True)]):
        status, data = http_fetch("https://doi.org/api/handles/" + urllib.parse.quote(form), timeout)
        code = data.get("responseCode") if isinstance(data, dict) else None
        answers.append("found" if (status, code) == (200, 1)
                       else "not_found" if (status, code) == (404, 100) else "failed")
    if "found" in answers:
        return "UNVERIFIED", "CrossRef 404; DOI registered with another agency (doi.org handle found)", []
    if "failed" in answers:
        return "UNVERIFIED", "CrossRef 404; doi.org handle lookup failed", []
    if "(sici)" in handle:
        # A SICI DOI's punctuation (<>, #, ;) is easily cut in extraction; not-found is not proof.
        return "UNVERIFIED", "CrossRef 404; doi.org handle not found, but a legacy SICI DOI; extraction may be incomplete", []
    return "FABRICATED", "DOI does not exist in any registry (CrossRef 404; doi.org handle not found)", []


def verify_pubmed_pmid(pmid: str, timeout: int, titles: list | None = None) -> tuple[str, str, list]:
    """Returns (status, evidence, family_names); on OK, the record's titles go into `titles`.

    Uses esummary (fast). Returns family-name approximation by stripping trailing
    initial block from "Surname Initials" form. Authoritative names → call
    verify_pubmed_efetch().
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "retmode": "json", **_ncbi_extras()}
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
    if titles is not None:
        titles.extend(t for t in (title, html.unescape(item.get("vernaculartitle") or ""),
                                  html.unescape(item.get("booktitle") or "")) if t)
    return "OK", evidence, families


def verify_pubmed_efetch(pmid: str, timeout: int,
                         titles: list | None = None) -> tuple[str, str, list, list]:
    """Authoritative PubMed full author record via efetch.fcgi (XML).

    On OK, the article's titles (a translated ArticleTitle and its VernacularTitle, or a
    BookTitle) go into `titles`.

    Returns (status, evidence, family_names, given_names). Use given_names for
    given-name cross-check (CrossRef-vs-PubMed disagreement, e.g. a documented
    case: CrossRef "Vasileios" vs PubMed "Victoria" — PubMed is authoritative).
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "retmode": "xml", **_ncbi_extras()}
    )
    req = urllib.request.Request(
        url,
        headers={"User-Agent": _user_agent()},
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
    # Titles are kept even when there are no personal authors: a collective-author record
    # (a guideline group) has none, and its VernacularTitle is only here, not in esummary.
    if titles is not None:
        for tag in ("ArticleTitle", "VernacularTitle", "BookTitle"):
            for tm in re.finditer(rf"<{tag}\b[^>]*>(.*?)</{tag}>", xml_text, re.S):
                titles.append(html.unescape(tm.group(1)))
    if not families:
        return "UNVERIFIED", "PubMed efetch returned no author elements", [], []
    return (
        "OK",
        f"PubMed efetch OK; authors={len(families)} (first={families[0]})",
        families,
        givens,
    )


def verify_pubmed_title(title: str, timeout: int) -> tuple[str, str, list]:
    """Title-only search returns no confident author list.

    esearch matches the words of a title, not the title, so a made-up title still returns
    PMIDs and a hit proves nothing on its own. The candidates' titles are fetched and the best
    one must pass the same similarity guard as the OpenAlex title search; otherwise the row
    stays UNVERIFIED. Returning OK on the bare hit let a reference with a fabricated DOI and a
    fabricated title end OK and fully verified.
    """
    if not title:
        return "UNVERIFIED", "No DOI, PMID, or usable title", []
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "term": title, "retmode": "json", "retmax": "3", **_ncbi_extras()}
    )
    data = http_json(url, timeout)
    if not data:
        return "UNVERIFIED", "PubMed title search failed", []
    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return "UNVERIFIED", "No PubMed title match", []
    time.sleep(0.2)
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(ids), "retmode": "json", **_ncbi_extras()}
    )
    summary = http_json(url, timeout)
    if not summary:
        return "UNVERIFIED", f"PubMed title candidates could not be fetched; PMID candidates={','.join(ids)}", []
    result = summary.get("result", {})
    best_id, best_sim = "", 0.0
    for pmid in ids:
        sim = _title_similarity(title, html.unescape((result.get(pmid) or {}).get("title", "")))
        if sim > best_sim:
            best_id, best_sim = pmid, sim
    if best_sim >= TITLE_MATCH_MIN:
        return "OK", f"PubMed title match; PMID={best_id} (sim={best_sim:.2f})", []
    return (
        "UNVERIFIED",
        f"No confident PubMed title match (best sim={best_sim:.2f}); PMID candidates={','.join(ids)}",
        [],
    )


# Minimum _title_similarity for a title-search hit to count as the cited work (OpenAlex and
# the PubMed title fallback share it).
TITLE_MATCH_MIN = 0.8


# Connective words ignored by _title_similarity. Other short tokens stay: CT, MR, US, AI, HR
# and single digits are what tells two otherwise identical titles apart.
_TITLE_STOPWORDS = frozenset(
    "a an the of in on to for and or by with at as is vs from".split())


def _title_similarity(a: str, b: str) -> float:
    """Token Jaccard on normalized titles (stdlib-only).

    Guards title-search matches (OpenAlex, PubMed fallback): a fabricated title must not
    earn a spurious OK just because a search returned some unrelated work. Connective
    stopwords are dropped so they do not inflate similarity, and a possessive "'s" is
    removed first so "Alzheimer's" and "Alzheimer" agree. Every other token counts, however
    short: dropping tokens of <=2 characters made "... in CT" match "... in MR", and dropping
    single letters made "hepatitis B" match "hepatitis C".
    """
    def toks(s: str) -> set:
        s = re.sub(r"['\u2019]s\b", "", s.lower())
        s = re.sub(r"[^a-z0-9 ]", " ", s)
        return {w for w in s.split() if w not in _TITLE_STOPWORDS}
    ta, tb = toks(a), toks(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# A DOI or PMID that resolves verifies the work it resolves to, not the title cited with it. The
# cited title is compared with every title the record answers to: fewer than half of the cited
# title's words found in any of them is a different work. Measuring the cited side tolerates a
# cited title that leaves out the record's subtitle, without letting a short title of a related
# paper match a longer cited one because most of its few words are in it.
IDENTIFIER_TITLE_MIN = 0.5


def _us_spelling(w: str) -> str:
    """Fold British spellings onto American ones, so that a title differing only in spelling
    (paediatric/pediatric, tumour/tumor, randomised/randomized, centre/center) is not counted
    as a different title."""
    if len(w) > 4 and w.endswith("our"):
        w = w[:-3] + "or"
    if len(w) >= 5:  # an acronym (MAE, OE) is not a spelling
        w = w.replace("ae", "e").replace("oe", "e")
    w = re.sub(r"(?<=[a-z]{3})is(e|ed|ing|ation)$", r"iz\1", w)
    w = re.sub(r"(?<=[a-z]{2})yse$", "yze", w)
    w = re.sub(r"(?<=[a-z]{3}[aeiou])ll(ed|ing|er)$", r"l\1", w)  # modelled, labelling
    w = re.sub(r"(?<=[a-z]{2})(t|b)red$", r"\1ered", w)  # centred -> centered
    return re.sub(r"(?<=[a-z]{2})(t|b)re$", r"\1er", w)  # centre, metre, theatre, fibre


def _title_words(s: str) -> set | None:
    """Content words of a title, or None when it is not readable as Latin script.

    The tokenizer folds to ASCII, so a title mostly in another script (Chinese, Korean,
    Cyrillic) would shrink to its few Latin acronyms and be compared on those alone.
    """
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)          # publisher markup: <i>, <sub>, MathML
    s = re.sub(r"\\[a-zA-Z]+", " ", s)      # LaTeX commands in a BibTeX title
    letters = sum(ch.isalpha() for ch in s)
    s = re.sub(r"['\u2019]s\b", "", s.lower())
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    if not letters or sum(ch.isalpha() for ch in s) < letters / 2:
        return None
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    words = set()
    for w in s.split():
        if w in _TITLE_STOPWORDS:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "is", "us")):
            w = w[:-1]
        words.add(_us_spelling(w))
    return words or None


def _same_title(a: str, b: str) -> bool:
    """Near-identical titles (Jaccard >= TITLE_MATCH_MIN): the same title in two records."""
    wa, wb = _title_words(a), _title_words(b)
    return bool(wa and wb) and len(wa & wb) / len(wa | wb) >= TITLE_MATCH_MIN


def cited_title_agrees(cited: str, resolved: list) -> bool | None:
    """Does the cited title name the record its DOI/PMID resolved to?

    True when some resolved title contains at least IDENTIFIER_TITLE_MIN of the cited title's
    words, False when none does, None when there is nothing to compare: no cited title, or no
    title on either side readable as Latin script.
    """
    cited_words = _title_words(cited)
    if not cited_words:
        return None
    verdict = None
    for title in resolved:
        words = _title_words(title)
        if not words:
            continue
        if len(cited_words & words) / len(cited_words) >= IDENTIFIER_TITLE_MIN:
            return True
        verdict = False
    return verdict


# A reference line also carries author and journal words, which can supply half of a short
# title by chance ("Cancer research priorities" in a line citing the journal Cancer Research),
# so a line must contain most of the resolved title, or of its part before a colon.
LINE_TITLE_MIN = 0.8


def _non_latin_letters(s: str) -> int:
    """Letters outside the Latin and Greek scripts (CJK, Hangul, Cyrillic, ...). Greek is common
    in scientific titles (beta-amyloid), and accented Latin letters (o-slash, sharp s) are Latin."""
    return sum(1 for ch in s if ch.isalpha()
               and not unicodedata.name(ch, "").startswith(("LATIN", "GREEK")))


def resolved_title_in_text(text: str, resolved: list) -> bool | None:
    """Is the resolved title written in a plain-text reference line?

    A line's guessed title is often its author list, so the line itself is searched: True when
    at least LINE_TITLE_MIN of the words of some resolved title (or of its main title before a
    colon) occur in it, False when none does, None when there is nothing to compare: a line
    holding a letter of another script (its title may be written in it), or no resolved title
    readable as Latin script. A record title of two or three words that happen to stand in the
    line's journal name or author list still matches; the check cannot tell them apart.
    """
    if _non_latin_letters(text):
        return None
    text_words = _title_words(text)
    if not text_words:
        return None
    verdict = None
    for title in resolved:
        for candidate in dict.fromkeys([title, title.split(":")[0]]):
            words = _title_words(candidate)
            if not words or (candidate != title and len(words) < 3):
                continue
            if len(words & text_words) / len(words) >= LINE_TITLE_MIN:
                return True
            verdict = False
    return verdict


def _openalex_families(work: dict) -> list:
    """Best-effort family-name list from an OpenAlex work's authorships.

    OpenAlex exposes only `author.display_name` with NO structured family/given
    split, and the live data mixes "First Last" and "Last, First" forms within a
    single record (observed: 'Noah Shinn' alongside 'Cassano, Federico'). This list
    is therefore informational only — it is NOT used to drive the authoritative
    family-by-family MISMATCH cross-check (that stays reserved for PubMed efetch /
    CrossRef, which carry a structured family field). See verify_record.
    """
    families: list[str] = []
    for au in work.get("authorships") or []:
        name = ((au.get("author") or {}).get("display_name") or "").strip()
        if not name:
            continue
        if "," in name:
            # "Last, First" → family is the part before the comma.
            fam = name.split(",", 1)[0].strip()
        else:
            toks = name.split()
            fam = toks[-1] if toks else ""
            # Strip a trailing initials block ("Madaan A").
            if fam and re.match(r"^[A-Z]{1,4}$", fam) and len(toks) >= 2:
                fam = toks[-2]
        if fam:
            families.append(fam)
    return families


def verify_openalex(doi: str, title: str, timeout: int,
                    titles: list | None = None) -> tuple[str, str, list]:
    """Tertiary index for conference proceedings / non-DOI / non-biomedical works.

    PubMed covers only biomedical literature and CrossRef's proceedings coverage is
    spotty, so NeurIPS / ICLR / ACL-style citations (common in medical-AI papers)
    fall through both. OpenAlex (https://api.openalex.org) is free and key-less and
    ingests those venues, so it recovers them — the free analogue of the second
    index (e.g. Scopus) that journal portals use alongside CrossRef.

    Resolves by DOI when available (exact); otherwise by title.search with a
    similarity guard so a fabricated title cannot earn a spurious OK. Returns
    (status, evidence, family_names). Never returns FABRICATED: an OpenAlex miss is
    a coverage gap, not proof of fabrication.
    """
    work = None
    via = ""
    if doi:
        data = http_json(
            "https://api.openalex.org/works/https://doi.org/" + urllib.parse.quote(doi),
            timeout,
        )
        if data and data.get("id"):
            work = data
            via = "doi"
    if work is None and title:
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
            {"filter": "title.search:" + title, "per-page": "5"}
        )
        data = http_json(url, timeout)
        results = (data or {}).get("results") or []
        best, best_sim = None, 0.0
        for w in results:
            sim = _title_similarity(title, w.get("title") or w.get("display_name") or "")
            if sim > best_sim:
                best, best_sim = w, sim
        if best is not None and best_sim >= TITLE_MATCH_MIN:
            work = best
            via = f"title(sim={best_sim:.2f})"
    if work is None:
        return "UNVERIFIED", "OpenAlex: no confident match", []
    families = _openalex_families(work)
    wtitle = (work.get("title") or work.get("display_name") or "")[:120]
    year = work.get("publication_year")
    ev = f"OpenAlex OK via {via}; title={wtitle}"
    if year:
        ev += f"; year={year}"
    if families:
        ev += f"; authors={len(families)} (first={families[0]})"
    if titles is not None and via == "doi":
        titles.extend(t for t in (work.get("title"), work.get("display_name")) if t)
    return "OK", ev, families


def author_cross_check(
    cited_authors: list,
    actual_authors: list,
    cited_author_count: int,
    actual_author_count: int,
    *,
    corporate: bool = False,
    soft: bool = False,
    audit_truncated: bool = False,
    first_author_guess: str = "",
) -> tuple[list, list]:
    """Pure family-by-family + author-count cross-check (no network, no RefRecord).

    Compares every cited author family against the authoritative list positionally,
    flags any cited author beyond the source list, and compares total counts (a count
    mismatch is downgraded to a note when ``audit_truncated`` and cited < actual — an
    intentional CSL et-al truncation). When no cited list was parsed (TSV / plain
    text) it degrades to a first-author surname check. Corporate/collective authors
    and OpenAlex-``soft`` lists are exempt (they must never fire MISMATCH).

    Returns ``(mismatches, notes)``: ``mismatches`` — human-readable mismatch strings
    (empty = clean); ``notes`` — non-mismatch evidence strings (the truncation note).
    This is the sole decision surface behind an AUTHOR MISMATCH status, extracted so
    the fabricated-co-author path has a network-free regression test
    (``tests/test_fabricated_author.sh``). Behaviour is identical to the inline logic
    it replaced in ``verify_record``.
    """
    mismatches: list = []
    notes: list = []
    if not corporate and cited_authors and actual_authors and not soft:
        compare_n = min(len(cited_authors), len(actual_authors))
        for i in range(compare_n):
            cited = cited_authors[i]
            if not author_surnames_match(cited, actual_authors[i]):
                mismatches.append(
                    f"#{i+1} family: cited='{cited}' vs source='{actual_authors[i]}'"
                )
        # cited has more authors than source — always flag (cannot be intentional)
        for i in range(compare_n, len(cited_authors)):
            mismatches.append(
                f"#{i+1} extra cited='{cited_authors[i]}' (source has only {len(actual_authors)} authors)"
            )
        # source has more authors than cited — count mismatch, suppressed when the
        # bib declares the truncation, either with the `_audit_truncated` marker or
        # with BibTeX's own `and others` sentinel (intentional CSL et-al truncation).
        if cited_author_count != actual_author_count:
            if audit_truncated and cited_author_count < actual_author_count:
                notes.append(
                    f"NOTE: intentional truncate ({cited_author_count} of {actual_author_count}; "
                    f"declared by `and others` or `_audit_truncated`)"
                )
            else:
                mismatches.append(
                    f"AUTHOR COUNT: cited={cited_author_count} vs source={actual_author_count}"
                )
    elif not corporate and first_author_guess and actual_authors:
        # No parsed cited author list (TSV / plain-text input) — degrade to the
        # first-author surname cross-check (Gate 4 behaviour).
        if not any(author_surnames_match(first_author_guess, a) for a in actual_authors):
            mismatches.append(
                f"#1 family: cited='{first_author_guess}' vs source='{actual_authors[0]}'"
            )
    return mismatches, notes


def verify_record(record: RefRecord, offline: bool, timeout: int,
                  use_openalex: bool = True) -> RefRecord:
    """v1.3.0: full-author cross-check.

    Authoritative source priority for the actual author list:
      1. PubMed efetch (XML full-record) — best (motivation: CrossRef returned a
         wrong given name "Vasileios" vs PubMed efetch authoritative "Victoria";
         also catches AI-generated bib entries with hallucinated #2..#N family
         names).
      2. CrossRef DOI (fallback when no PMID).
      3. OpenAlex (tertiary; conference proceedings / non-DOI / non-biomedical works
         that PubMed and CrossRef miss — the free analogue of a portal's Scopus pass).
      4. PubMed esummary (fast count check; family-name approximation only).
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
        if record.corporate_author:
            record.note = "corporate/collective author — personal-name cross-check skipped"
            record.evidence += " | CORPORATE AUTHOR (collective/organization)"
        return record

    statuses: list[str] = []
    evidence_parts: list[str] = []
    actual_authors: list[str] = []
    actual_givens: list[str] = []
    sources_consulted: list[str] = []
    # True when the actual_authors list came from OpenAlex, whose display names carry
    # no structured family field and mix "First Last" / "Last, First" forms. Such a
    # list can support a tolerant first-author membership check but NOT the strict
    # positional + author-count cross-check (which would mis-fire on the format noise).
    actual_authors_soft = False
    # The titles each identifier resolved to; the reference must carry a title of each one, so a
    # wrong DOI is caught even when the PMID beside it is right.
    resolved_titles: dict[str, list[str]] = {"PMID": [], "DOI": []}

    # Step 1 — PubMed efetch (authoritative) when PMID present.
    if record.pmid:
        st, ev, fams, givens = verify_pubmed_efetch(record.pmid, timeout, titles=resolved_titles["PMID"])
        time.sleep(0.2)
        statuses.append(st)
        evidence_parts.append(ev)
        if st == "OK" and fams:
            actual_authors = fams
            actual_givens = givens
            sources_consulted.append("pubmed_efetch")
        # also run esummary for FABRICATED detection (efetch returns valid XML even for
        # unknown PMIDs in some edge cases; esummary's "error" field is decisive).
        st_es, ev_es, fams_es = verify_pubmed_pmid(record.pmid, timeout, titles=resolved_titles["PMID"])
        time.sleep(0.2)
        statuses.append(st_es)
        evidence_parts.append(ev_es)
        if not actual_authors and st_es == "OK" and fams_es:
            actual_authors = fams_es
            sources_consulted.append("pubmed_esummary")

    # Step 2 — CrossRef DOI (used only when efetch did not provide a list).
    if record.doi:
        st_cr, ev_cr, fams_cr = verify_crossref(record.doi, timeout, titles=resolved_titles["DOI"])
        time.sleep(0.2)
        statuses.append(st_cr)
        evidence_parts.append(ev_cr)
        if not actual_authors and st_cr == "OK" and fams_cr:
            actual_authors = fams_cr
            sources_consulted.append("crossref")

    # Step 3 — OpenAlex tertiary index. Fires only when no authoritative author list
    # was obtained yet (no PMID/DOI, or those lookups returned no authors), so a
    # biomedical reference already resolved by PubMed/CrossRef incurs no extra call.
    # Recovers conference proceedings and non-biomedical works (NeurIPS/ICLR/ACL) and
    # retries DOIs that CrossRef missed.
    if use_openalex and not actual_authors:
        st_oa, ev_oa, fams_oa = verify_openalex(record.doi, record.title_guess, timeout,
                                                titles=resolved_titles["DOI"])
        time.sleep(0.2)
        statuses.append(st_oa)
        evidence_parts.append(ev_oa)
        if st_oa == "OK":
            sources_consulted.append("openalex")
            if fams_oa:
                actual_authors = fams_oa
                actual_authors_soft = True

    # Step 4 — PubMed title-only final fallback when nothing confident resolved.
    if "OK" not in statuses and not actual_authors:
        st_t, ev_t, _ = verify_pubmed_title(record.title_guess, timeout)
        time.sleep(0.2)
        statuses.append(st_t)
        evidence_parts.append(ev_t)

    # Full-author cross-check
    record.actual_authors = actual_authors
    record.actual_author_count = len(actual_authors)
    if record.cited_authors and not record.cited_author_count:
        record.cited_author_count = len(record.cited_authors)

    # Collective/corporate author (guideline body, working group): PubMed returns
    # it as <CollectiveName> and the BibTeX double-braces it, so the personal-name
    # family cross-check does not apply. Detect it on the source side too (no parsed
    # personal authors but a title/DOI verified, or the source author looks like an
    # organization), so a guideline cite is VERIFIED, never a render-aborting MISMATCH.
    source_corporate = bool(actual_authors) and any(_ORG_AUTHOR_RE.search(a) for a in actual_authors)
    if record.corporate_author or source_corporate:
        if not record.note:
            record.note = "corporate/collective author — personal-name cross-check skipped"
        evidence_parts.append("CORPORATE AUTHOR (collective/organization; family cross-check skipped)")

    mismatches, xcheck_notes = author_cross_check(
        record.cited_authors,
        actual_authors,
        record.cited_author_count,
        record.actual_author_count,
        corporate=(record.corporate_author or source_corporate),
        soft=actual_authors_soft,
        audit_truncated=record.audit_truncated,
        first_author_guess=record.first_author_guess,
    )
    evidence_parts.extend(xcheck_notes)

    author_mismatch = bool(mismatches)
    if author_mismatch:
        evidence_parts.append("AUTHOR MISMATCH | " + " | ".join(mismatches))

    # A resolving identifier with agreeing authors used to be OK whatever title was cited with
    # it. A title read from a title field is compared as a title; a plain-text reference line
    # (Markdown, DOCX, text) is searched for the resolved title instead, because the title
    # guessed from such a line is often its author list (see RefRecord.title_from_field).
    wrong_ids = []
    if "OK" in statuses:
        verdicts = {
            ident: (cited_title_agrees(record.title_guess, titles) if record.title_from_field
                    else resolved_title_in_text(record.raw, titles))
            for ident, titles in resolved_titles.items() if titles
        }
        for ident, agrees in verdicts.items():
            other = "DOI" if ident == "PMID" else "PMID"
            # A CrossRef record may hold only the original-language title of a paper PubMed lists
            # in English: when this identifier's title matches the other identifier's record
            # (whose titles include PubMed's VernacularTitle), both name the same work.
            same_work = verdicts.get(other) is True and any(
                _same_title(a, b) for a in resolved_titles[ident] for b in resolved_titles[other])
            if agrees is False and not same_work:
                wrong_ids.append(ident)
    title_mismatch = bool(wrong_ids)
    if title_mismatch:
        evidence_parts.append(f"TITLE MISMATCH | the {'/'.join(wrong_ids)} resolves to a work whose "
                              "title shares under half its words with the cited reference")

    # Status precedence
    if "OK" in statuses and "FABRICATED" in statuses:
        record.status = "MISMATCH"
    elif "OK" in statuses:
        record.status = "MISMATCH" if (author_mismatch or title_mismatch) else "OK"
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
    if title_mismatch and not record.note:
        record.note = (f"title mismatch: the {'/'.join(wrong_ids)} resolves to a work with a "
                       "different title")
    if "OK" in statuses and "FABRICATED" in statuses and not record.note:
        record.note = "wrong identifier: the cited DOI/PMID does not exist, but the work itself was found"
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


# Pagination / publication-stage placeholders. A reference whose pages or status is
# still "e000–e000", "in press", "TBD", or "forthcoming" is not yet a fully citable
# record. verify-refs is manuscript-agnostic, so it only flags these as UNVERIFIED
# with note="pagination_placeholder"; the centrality call (is this a method- or
# headline-load-bearing cite, hence a P0 blocker?) is made by /self-review Phase 2.5c,
# which has the manuscript in hand. (Gate 6, added 2026-06.)
PAGINATION_PLACEHOLDER_RE = re.compile(
    r"e0{3}.{0,3}e0{3}|in[ .]?press|\bTBD\b|forthcoming", re.I)


def flag_pagination_placeholder(record: RefRecord) -> None:
    """If the raw entry carries a pagination/publication-stage placeholder, attach a
    note and downgrade a resolved (OK) record to UNVERIFIED (an in-press/e000
    citation is not yet locatable to the page). Worse statuses are left unchanged."""
    if not PAGINATION_PLACEHOLDER_RE.search(record.raw or ""):
        return
    tag = "pagination_placeholder"
    record.note = f"{record.note} | {tag}".strip(" |") if record.note else tag
    if record.status == "OK":
        record.status = "UNVERIFIED"
        ev = "identifier resolved but pagination/publication-stage placeholder unresolved"
        record.evidence = f"{record.evidence} | {ev}".strip(" |") if record.evidence else ev


def portable_source(source: Path, project_root: Path) -> str:
    """Render the audited file's path so the audit can travel with the manuscript.

    `source` was written with `str()`, i.e. whatever the caller passed — and the caller
    resolves it, so on a real run that is an absolute path. On a maintainer's machine an
    absolute path contains the home directory, and therefore a username, inside
    `qc/reference_audit.json`, which is a COMMITTED artifact. The public-surface PII gate
    caught exactly that three times between 2026-07-31 and 2026-08-01; the field is
    rewritten on every render, so hand-scrubbing it lost twice.

    Nothing consumes the absolute form. The audit file lives beside the manuscript and
    moves with it, so a path relative to the project root is not merely PII-free, it is
    the correct referent. Falls back to the CWD, then to the bare filename, so a source
    outside the project (a shared .bib) still yields something readable and still carries
    no home directory.
    """
    for base in (project_root, Path.cwd()):
        try:
            return source.resolve().relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return source.name


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
    first author. A correct lead author does not verify the remaining author list.

    The audit also records WHAT it audited: `source_sha256` (the input file's hash) and
    `audited_ref_ids`. Without them a green `submission_safe` outlives the file it
    describes — the bib gains a reference, nobody reruns the audit, and the new entry is
    shipped never having been checked. A consumer reading the audit later compares both
    against the current bib (see check_claim_fidelity.py --reference-audit).
    """
    qc_dir = project_root / "qc"
    qc_dir.mkdir(parents=True, exist_ok=True)

    try:
        source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    except OSError:
        source_sha256 = ""
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec.status] = counts.get(rec.status, 0) + 1
    audit = {
        "schema_version": 4,
        "source": portable_source(source, project_root),
        "source_sha256": source_sha256,
        "audited_ref_ids": [rec.ref_id.strip() for rec in records],
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
    (qc_dir / "reference_audit.json").write_text(json.dumps({"detector": "verify_refs", **audit}, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify manuscript references.")
    parser.add_argument("input", help="Input .md, .docx, .bib, .txt, or .tsv file")
    parser.add_argument("--project-root", default=".", help="Project root for output artifacts")
    parser.add_argument("--offline", action="store_true", help="Do not call PubMed/CrossRef/doi.org/OpenAlex APIs")
    parser.add_argument("--no-openalex", action="store_true",
                        help="Disable the OpenAlex tertiary index (restrict to PubMed + CrossRef)")
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

    verified = [
        verify_record(rec, args.offline, args.timeout, use_openalex=not args.no_openalex)
        for rec in records
    ]
    for rec in verified:
        flag_pagination_placeholder(rec)
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

#!/usr/bin/env python3
"""
Cohort Overlap Detection — flag included-study pairs sharing same data source.

Motivation: recent SR-MA peer-review cycles found included studies using
overlapping public ICU/EHR cohorts (MIMIC-IV, eICU, KNHIS, UK Biobank) without
explicit acknowledgment. Independent-cohort assumption for MA pooling is then
violated. This script reads a study list with PMID + extracted cohort metadata,
fetches missing fields from PubMed efetch when needed, and reports clusters by
(a) shared public database, (b) shared institution + overlapping enrollment
period, (c) shared author surname + year proximity.

Usage:
    python3 cohort_overlap_check.py --input studies.csv --out overlap_report.md

Input CSV schema (recommended columns):
    study_id, pmid, country, institution, database_source, enrollment_period_start,
    enrollment_period_end, first_author, year, sample_n

`database_source` examples: "MIMIC-IV", "eICU", "KNHIS", "UK Biobank", "institutional",
"multi-center prospective". Use empty string if unknown — script will attempt PubMed
fetch to infer.

Outputs a Markdown report listing:
- HIGH-CONFIDENCE OVERLAP pairs (same database + overlapping period)
- MEDIUM-CONFIDENCE candidates (same institution OR same author surname + year ±2)
- UNDETERMINED (insufficient metadata)
"""
import argparse
import csv
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Optional

PUBLIC_DBS = [
    "MIMIC-IV", "MIMIC-III", "eICU", "MIMIC", "MarketScan", "Optum",
    "NHANES", "KNHANES", "KNHIS", "UK Biobank", "Biobank Japan",
    "TriNetX", "All of Us", "VA Corporate Data Warehouse", "PCORnet",
    "SEER", "NSQIP",
]


def fetch_pubmed_affiliation(pmid: str, timeout: int = 10) -> dict:
    """Fetch first-author affiliation + abstract Methods snippet via efetch."""
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={pmid}&retmode=xml"
    )
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = resp.read()
    except Exception as e:
        return {"pmid": pmid, "error": str(e)}

    root = ET.fromstring(data)
    art = root.find(".//Article")
    if art is None:
        return {"pmid": pmid, "error": "no Article element"}

    title = art.findtext("ArticleTitle", "") or ""
    aff = root.findtext(".//Author/AffiliationInfo/Affiliation", "") or ""
    abstract = " ".join(
        (ab.text or "") for ab in root.findall(".//AbstractText")
    )

    # Heuristic database detection from abstract
    db_hit = ""
    for db in PUBLIC_DBS:
        if db.lower() in abstract.lower():
            db_hit = db
            break

    return {
        "pmid": pmid,
        "title": title,
        "affiliation": aff,
        "database_hit": db_hit,
    }


def periods_overlap(s1: str, e1: str, s2: str, e2: str) -> Optional[bool]:
    """Return True/False/None (None = insufficient data). YYYY-MM strings."""
    if not (s1 and e1 and s2 and e2):
        return None
    try:
        return not (e1 < s2 or e2 < s1)
    except Exception:
        return None


def cluster_by_db(rows: list[dict]) -> dict[str, list[dict]]:
    """Group rows by database_source (non-empty)."""
    clusters = defaultdict(list)
    for r in rows:
        db = (r.get("database_source") or "").strip()
        if db and db.lower() != "institutional":
            clusters[db].append(r)
    return {k: v for k, v in clusters.items() if len(v) >= 2}


def cluster_by_institution(rows: list[dict]) -> dict[str, list[dict]]:
    clusters = defaultdict(list)
    for r in rows:
        inst = (r.get("institution") or "").strip()
        if inst:
            # Normalize: lowercase, strip "Department of X, " prefix
            key = inst.lower().split(",")[0].strip()
            clusters[key].append(r)
    return {k: v for k, v in clusters.items() if len(v) >= 2}


def cluster_by_author_year(rows: list[dict]) -> dict[str, list[dict]]:
    clusters = defaultdict(list)
    for r in rows:
        surname = (r.get("first_author") or "").strip().split()[0].lower() if r.get("first_author") else ""
        if surname:
            clusters[surname].append(r)
    return {k: v for k, v in clusters.items() if len(v) >= 2}


def write_report(out_path: Path, db_clusters, inst_clusters, author_clusters,
                 enriched: list[dict]) -> None:
    lines = ["# Cohort Overlap Report", ""]

    lines.append(f"Total studies analyzed: **{len(enriched)}**")
    lines.append("")

    lines.append("## HIGH-CONFIDENCE: Same public database")
    if db_clusters:
        for db, rows in db_clusters.items():
            lines.append(f"\n### Database: **{db}** ({len(rows)} studies)")
            for r in rows:
                period = (
                    f"{r.get('enrollment_period_start','?')}"
                    f"-{r.get('enrollment_period_end','?')}"
                )
                lines.append(
                    f"- {r.get('study_id','?')} (PMID {r.get('pmid','?')}, "
                    f"N={r.get('sample_n','?')}, period {period})"
                )
            # Period overlap check (pairwise)
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    o = periods_overlap(
                        rows[i].get("enrollment_period_start", ""),
                        rows[i].get("enrollment_period_end", ""),
                        rows[j].get("enrollment_period_start", ""),
                        rows[j].get("enrollment_period_end", ""),
                    )
                    if o is True:
                        lines.append(
                            f"  - WARN Period overlap: {rows[i]['study_id']} <-> {rows[j]['study_id']}"
                        )
                    elif o is None:
                        lines.append(
                            f"  - QUERY Period overlap undetermined: "
                            f"{rows[i]['study_id']} <-> {rows[j]['study_id']}"
                        )
    else:
        lines.append("None.")

    lines.append("\n## MEDIUM: Same institution (single-center cluster)")
    if inst_clusters:
        for inst, rows in inst_clusters.items():
            lines.append(f"\n### Institution: **{inst}** ({len(rows)} studies)")
            for r in rows:
                lines.append(f"- {r.get('study_id','?')} (PMID {r.get('pmid','?')})")
    else:
        lines.append("None.")

    lines.append("\n## LOWER: Same author surname +/-2y year")
    if author_clusters:
        for surname, rows in author_clusters.items():
            years = [int(r["year"]) for r in rows if str(r.get("year","")).isdigit()]
            year_span = max(years) - min(years) if years else None
            tag = "(within +/-2y)" if year_span is not None and year_span <= 2 else "(>2y span)"
            lines.append(f"\n### Surname: **{surname}** {tag} - {len(rows)} studies")
            for r in rows:
                lines.append(f"- {r.get('study_id','?')} ({r.get('year','?')})")
    else:
        lines.append("None.")

    lines.append("\n## Recommendation")
    lines.append(
        "- For HIGH-CONFIDENCE overlap pairs: sensitivity analysis excluding one, "
        "explicit Limitations acknowledgment, cohort-source column in Table 1."
    )
    lines.append(
        "- For MEDIUM: request author institution + ORCID to verify cohort independence."
    )

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Cohort overlap detector for SR-MA")
    p.add_argument("--input", required=True, type=Path, help="Input CSV")
    p.add_argument("--out", required=True, type=Path, help="Output Markdown report")
    p.add_argument("--enrich", action="store_true",
                   help="Fetch PubMed efetch for missing database/affiliation")
    args = p.parse_args()

    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 1

    with args.input.open(newline="", encoding="utf-8") as fin:
        rows = list(csv.DictReader(fin))

    if args.enrich:
        for r in rows:
            if not r.get("database_source") and r.get("pmid"):
                info = fetch_pubmed_affiliation(r["pmid"])
                if info.get("database_hit"):
                    r["database_source"] = info["database_hit"]
                if not r.get("institution") and info.get("affiliation"):
                    r["institution"] = info["affiliation"][:80]

    db_clusters = cluster_by_db(rows)
    inst_clusters = cluster_by_institution(rows)
    author_clusters = cluster_by_author_year(rows)

    write_report(args.out, db_clusters, inst_clusters, author_clusters, rows)

    n_db = sum(len(v) for v in db_clusters.values())
    n_inst = sum(len(v) for v in inst_clusters.values())
    print(
        f"Cohort overlap: {len(db_clusters)} DB clusters ({n_db} studies), "
        f"{len(inst_clusters)} institution clusters ({n_inst} studies)"
    )
    print(f"Report: {args.out}")

    return 1 if db_clusters else 0


if __name__ == "__main__":
    sys.exit(main())

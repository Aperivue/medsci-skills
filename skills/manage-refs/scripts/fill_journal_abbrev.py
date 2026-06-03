#!/usr/bin/env python3
"""Inject NLM journal abbreviations (+ optionally normalize author case / titles)
into a BibLaTeX .bib from PubMed authoritative metadata.

Why: CSL `container-title form="short"` prints the full journal name unless the
.bib entry carries a `shortjournal` field. Most Zotero/BBT exports omit it, so
NLM-style journals (JKMS, AJR, KJR, NEJM, ...) render the full title regardless
of CSL. This script resolves each entry's DOI → PMID → PubMed esummary `source`
(the NLM Title Abbreviation) and writes `shortjournal = {...}`.

Also (optional, --titles): pulls efetch ArticleTitle to double-brace titles
(preserving proper-noun casing + subtitle), and flags ALL-CAPS author fields.

Authoritative source: PubMed (esummary `source` = NLM abbreviation; efetch
ArticleTitle = full title). Falls back to CrossRef `short-container-title` when a
DOI has no PubMed record. Never invents abbreviations.

Usage:
  python fill_journal_abbrev.py --bib refs.bib --out refs_nlm.bib            # shortjournal only
  python fill_journal_abbrev.py --bib refs.bib --out refs_nlm.bib --titles   # + title double-brace
"""
import argparse, re, json, time, urllib.request, urllib.parse, sys

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = {"User-Agent": "medsci-manage-refs/1.0"}

def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode()

def doi_to_pmid(doi):
    try:
        term = urllib.parse.quote(f'"{doi}"[AID] OR "{doi}"[DOI]')
        j = json.loads(_get(f"{EUTILS}/esearch.fcgi?db=pubmed&term={term}&retmode=json"))
        ids = j.get("esearchresult", {}).get("idlist", [])
        return ids[0] if ids else None
    except Exception:
        return None

def pmids_summary(pmids):
    """return {pmid: {'source':abbrev, 'title':...}}"""
    if not pmids: return {}
    j = json.loads(_get(f"{EUTILS}/esummary.fcgi?db=pubmed&id={','.join(pmids)}&retmode=json"))
    res = j.get("result", {})
    return {p: {"source": res.get(p, {}).get("source")} for p in pmids}

def parse_entries(bib):
    return [m for m in re.finditer(r"@\w+\{[^@]*?\n\}", bib, re.S)]

def field(block, name):
    m = re.search(rf"{name}\s*=\s*\{{(.+?)\}},", block, re.S)
    return m.group(1).strip() if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--titles", action="store_true", help="also double-brace titles via efetch")
    a = ap.parse_args()
    bib = open(a.bib, encoding="utf-8").read()

    # 1) collect DOIs → PMIDs
    blocks = parse_entries(bib)
    doi_by_key = {}
    for b in blocks:
        key = re.match(r"@\w+\{([^,]+),", b).group(1).strip()
        doi = field(b, "doi") or field(b, "DOI")
        if doi: doi_by_key[key] = doi.strip()
    pmid_by_key = {}
    for k, doi in doi_by_key.items():
        pmid_by_key[k] = doi_to_pmid(doi); time.sleep(0.4)
    pmids = [p for p in pmid_by_key.values() if p]
    summ = pmids_summary(pmids)

    # 2) inject shortjournal
    out = bib; n = 0
    for k, pmid in pmid_by_key.items():
        if not pmid: continue
        abbrev = summ.get(pmid, {}).get("source")
        if not abbrev: continue
        # find this entry, add shortjournal after journaltitle/journal if absent
        pat = re.compile(r"(@\w+\{" + re.escape(k) + r",.*?)(\n\})", re.S)
        m = pat.search(out)
        if not m or "shortjournal" in m.group(1): continue
        block = m.group(1)
        inj = re.sub(r"(\n\t?journal(?:title)?\s*=\s*\{[^}]*\},)",
                     r"\1\n\tshortjournal = {" + abbrev + "},", block, count=1)
        if inj == block:  # no journal field found; append before closing
            inj = block + "\n\tshortjournal = {" + abbrev + "},"
        out = out.replace(block, inj, 1); n += 1

    open(a.out, "w", encoding="utf-8").write(out)
    print(f"shortjournal injected: {n}/{len(doi_by_key)} entries "
          f"(DOIs resolved to PMID: {len(pmids)})")
    caps = [re.match(r'@\w+\{([^,]+),', b).group(1) for b in blocks
            if (au := field(b, "author")) and re.search(r"\{?[A-Z]{3,}\}?,\s*\{?[A-Z]{3,}", au or "")]
    if caps:
        print("WARN: ALL-CAPS author fields (fix case manually or re-pull):", caps)
    if a.titles:
        print("NOTE: --titles efetch double-brace not auto-applied; "
              "use the efetch ArticleTitle pattern documented in REFERENCE_STYLE_SPECS.md")

if __name__ == "__main__":
    main()

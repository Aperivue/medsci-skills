#!/usr/bin/env python3
"""Stdlib-only PubMed XML parsing + target-author attribution + record classifiers.

Split out of fetch_pubmed.py so the safety-critical logic — which author on a paper
is the *target* author, and what metadata is attributed to them — is unit-tested in CI
WITHOUT requiring Biopython (fetch_pubmed.py keeps the Bio.Entrez network dependency).

Design rules:
- Target-author attribution never borrows a co-author's ORCID/affiliation. When two
  same-surname authors appear on one paper and initials/ORCID cannot disambiguate, the
  record's target metadata (and position) is `unknown` — never guessed.
- Author position is a positional heuristic only: first / middle / last / unknown, plus
  the real `EqualContrib` flag when PubMed marks it. It is NOT leadership metadata.

Only the standard library is imported here.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Target-author attribution
# ---------------------------------------------------------------------------


def _norm_initials(s: str) -> str:
    """Normalize initials to uppercase letters only (e.g., 'D. K.' -> 'DK')."""
    return re.sub(r"[^A-Za-z]", "", s or "").upper()


def _norm_orcid(s: str) -> str:
    """Normalize an ORCID to the 16 hex-ish chars (strip URL prefix, dashes)."""
    s = (s or "").strip()
    s = re.sub(r"^https?://orcid\.org/", "", s, flags=re.I)
    return re.sub(r"[^0-9Xx]", "", s).upper()


def match_target_author(
    authors: list[dict],
    target_last: str,
    target_initials: str = "",
    target_orcid: str = "",
) -> tuple[int | None, str]:
    """Return (index_of_target_author, match_basis).

    match_basis is one of: orcid, initials, surname-unique, ambiguous-initials,
    ambiguous-surname, no-surname-match. The two `ambiguous-*` bases mean the target
    could not be uniquely identified on this paper -> callers must NOT attribute
    co-author metadata.
    """
    tl = (target_last or "").lower()
    surname_cands = [i for i, a in enumerate(authors) if a.get("LastName", "").lower() == tl]
    if not surname_cands:
        # fallback: substring (handles compound surnames / encoding quirks)
        surname_cands = [i for i, a in enumerate(authors) if tl and tl in a.get("LastName", "").lower()]
    if not surname_cands:
        return None, "no-surname-match"

    # 1. ORCID is authoritative.
    if target_orcid:
        tgt = _norm_orcid(target_orcid)
        orcid_matches = [i for i in surname_cands if _norm_orcid(authors[i].get("ORCID", "")) == tgt and tgt]
        if len(orcid_matches) >= 1:
            return orcid_matches[0], "orcid"
        # provided ORCID matched no surname candidate -> fall through to initials/surname.

    # 2. Initials.
    if target_initials:
        ti = _norm_initials(target_initials)
        init_matches = [i for i in surname_cands if _norm_initials(authors[i].get("Initials", "")) == ti and ti]
        if len(init_matches) == 1:
            return init_matches[0], "initials"
        if len(init_matches) > 1:
            return init_matches[0], "ambiguous-initials"
        # no initials match -> fall through to surname.

    # 3. Surname only.
    if len(surname_cands) == 1:
        return surname_cands[0], "surname-unique"
    return surname_cands[0], "ambiguous-surname"


def classify_author_position(idx: int | None, n_authors: int) -> str:
    """Positional heuristic only: first / middle / last / unknown."""
    if idx is None or n_authors <= 0:
        return "unknown"
    if idx == 0:
        return "first"
    if idx == n_authors - 1:
        return "last"
    return "middle"


# ---------------------------------------------------------------------------
# Content classifiers (unchanged logic, stdlib-only)
# ---------------------------------------------------------------------------


def classify_study_type(title: str, abstract: str, mesh_terms: list[str], pub_types: list[str]) -> str:
    text = (title + " " + abstract).lower()
    pub_lower = " ".join(pub_types).lower()

    if "global burden" in text or "gbd" in text:
        return "GBD"
    if ("systematic review" in text or "meta-analysis" in text or
            "systematic review" in pub_lower or "meta-analysis" in pub_lower):
        return "SR/MA"
    if ("national health insurance" in text or "nhis" in text or
            "claims database" in text or "nationwide cohort" in text):
        return "NHIS/Claims"
    if ("cross-national" in text or "binational" in text or
            ("korea" in text and ("united states" in text or "japan" in text or
             "france" in text or "american" in text))):
        return "Cross-national"
    if ("knhanes" in text or "nhanes" in text or "national health and nutrition" in text or
            "kchs" in text or "national survey" in text):
        return "National survey"
    if "biobank" in text:
        return "Biobank"
    if ("machine learning" in text or "deep learning" in text or
            "artificial intelligence" in text or "neural network" in text):
        return "AI/ML"
    if "randomized" in text or "clinical trial" in pub_lower:
        return "Clinical trial"
    if "case report" in text or "case report" in pub_lower:
        return "Case report"
    if "letter" in pub_lower or "comment" in pub_lower or "editorial" in pub_lower:
        return "Letter/Commentary"
    return "Other"


def classify_topic(title: str, abstract: str, mesh_terms: list[str]) -> str:
    text = (title + " " + abstract).lower()
    topics = {
        "Allergy/Respiratory": ["allergy", "allergic", "asthma", "respiratory", "atopic",
                                 "rhinitis", "eczema", "copd", "pneumonia", "lung disease"],
        "Cardiovascular": ["cardiovascular", "coronary", "heart", "myocardial", "hypertension",
                            "stroke", "atherosclerosis", "arrhythmia"],
        "Mental health": ["depression", "anxiety", "mental health", "psychiatric", "suicide",
                          "adhd", "autism", "bipolar", "schizophrenia"],
        "Infectious": ["covid", "sars-cov", "infection", "vaccine", "vaccination", "herpes zoster",
                       "influenza", "hepatitis", "tuberculosis"],
        "Oncology": ["cancer", "tumor", "malignant", "neoplasm", "carcinoma", "leukemia",
                     "lymphoma"],
        "Metabolic": ["diabetes", "obesity", "metabolic", "lipid", "cholesterol", "fatty liver",
                      "bmi", "insulin"],
        "Nutrition/Lifestyle": ["diet", "nutrition", "physical activity", "exercise", "sleep",
                                "sedentary", "alcohol", "smoking"],
        "Musculoskeletal": ["osteoporosis", "fracture", "arthritis", "bone", "sarcopenia",
                            "musculoskeletal", "spine", "joint"],
        "Neurological": ["dementia", "alzheimer", "parkinson", "epilepsy", "migraine",
                         "cerebrovascular", "brain", "cognitive", "aneurysm"],
        "Radiology/Imaging": ["radiolog", "imaging", "ct ", "mri", "ultrasound", "x-ray",
                              "mammograph", "pet", "contrast"],
        "GI/Hepatology": ["gastro", "liver", "hepat", "pancrea", "colon", "bowel",
                          "endoscop", "cirrhosis"],
        "Ophthalmology": ["ophthalm", "vision", "macular", "retinal", "eye", "glaucoma"],
        "Pediatrics": ["child", "pediatric", "adolescent", "infant", "neonatal", "prenatal",
                       "offspring"],
    }
    scores = {}
    for topic, keywords in topics.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[topic] = score
    if not scores:
        return "Other"
    return max(scores, key=scores.get)


def classify_journal_tier(journal: str) -> str:
    j = (journal or "").lower()
    if any(x in j for x in ["lancet"]):
        return "Lancet family"
    if any(x in j for x in ["nature", "nat med", "nat rev", "nat commun"]):
        return "Nature family"
    if any(x in j for x in ["n engl j med", "bmj", "jama"]):
        return "NEJM/BMJ/JAMA"
    high_if = ["circulation", "eur heart j", "allergy", "j allergy clin immunol",
               "ebiomedic", "sci adv", "cell", "ann oncol", "gut", "radiology",
               "eur radiol", "invest radiol"]
    if any(x in j for x in high_if):
        return "IF>=10"
    return "Other"


# ---------------------------------------------------------------------------
# Article parsing
# ---------------------------------------------------------------------------

CSV_FIELDNAMES = [
    "pmid", "title", "journal", "journal_abbrev", "year",
    "n_authors", "author_position", "equal_contrib", "match_basis",
    "target_initials", "target_orcid", "target_affiliation",
    "study_type", "topic", "journal_tier", "pub_types", "mesh_terms", "abstract",
]


def _extract_authors(art) -> list[dict]:
    authors: list[dict] = []
    author_list = art.find(".//AuthorList") if art is not None else None
    if author_list is None:
        return authors
    for auth_el in author_list.findall("Author"):
        last = auth_el.find("LastName")
        fore = auth_el.find("ForeName")
        initials = auth_el.find("Initials")
        collective = auth_el.find("CollectiveName")
        orcid = ""
        for ident in auth_el.findall("Identifier"):
            if (ident.get("Source") or "").upper() == "ORCID":
                orcid = (ident.text or "").strip()
                break
        affiliation = ""
        aff_el = auth_el.find(".//AffiliationInfo/Affiliation")
        if aff_el is not None and aff_el.text:
            affiliation = aff_el.text.strip()
        authors.append({
            "LastName": last.text if last is not None else "",
            "ForeName": fore.text if fore is not None else "",
            "Initials": initials.text if initials is not None else "",
            "CollectiveName": collective.text if collective is not None else "",
            "ORCID": orcid,
            "Affiliation": affiliation,
            "EqualContrib": (auth_el.get("EqualContrib") or "").upper(),
        })
    return authors


def parse_article(article, target_last: str, target_initials: str = "", target_orcid: str = "") -> dict:
    """Parse one <PubmedArticle> element into a flat record dict.

    Target-author metadata (ORCID/affiliation/initials/position/equal_contrib) is
    attributed ONLY when the target author is uniquely identified on the paper.
    """
    medline = article.find(".//MedlineCitation")
    art = medline.find(".//Article") if medline is not None else None

    pmid = ""
    pmid_el = medline.find(".//PMID") if medline is not None else None
    if pmid_el is not None:
        pmid = pmid_el.text or ""

    title = ""
    title_el = art.find(".//ArticleTitle") if art is not None else None
    if title_el is not None:
        title = "".join(title_el.itertext()).strip()

    journal = ""
    journal_el = art.find(".//Journal/Title") if art is not None else None
    if journal_el is not None:
        journal = journal_el.text or ""

    journal_abbrev = ""
    ja_el = art.find(".//Journal/ISOAbbreviation") if art is not None else None
    if ja_el is not None:
        journal_abbrev = ja_el.text or ""

    year = ""
    year_el = art.find(".//Journal/JournalIssue/PubDate/Year") if art is not None else None
    if year_el is not None:
        year = year_el.text or ""
    else:
        medline_date = art.find(".//Journal/JournalIssue/PubDate/MedlineDate") if art is not None else None
        if medline_date is not None and medline_date.text:
            match = re.search(r"(20\d{2}|19\d{2})", medline_date.text)
            if match:
                year = match.group(1)

    authors = _extract_authors(art)
    n_authors = len(authors)

    idx, match_basis = match_target_author(authors, target_last, target_initials, target_orcid)
    ambiguous = match_basis in ("ambiguous-initials", "ambiguous-surname")

    if idx is None or ambiguous:
        # Cannot uniquely attribute -> never borrow a co-author's metadata.
        author_position = "unknown"
        equal_contrib = ""
        t_initials = t_orcid = t_affiliation = ""
    else:
        author_position = classify_author_position(idx, n_authors)
        tgt = authors[idx]
        equal_contrib = "Y" if tgt.get("EqualContrib") == "Y" else ""
        t_initials = tgt.get("Initials", "")
        t_orcid = tgt.get("ORCID", "")
        t_affiliation = tgt.get("Affiliation", "")

    abstract = ""
    abstract_el = art.find(".//Abstract") if art is not None else None
    if abstract_el is not None:
        parts = ["".join(at.itertext()).strip() for at in abstract_el.findall("AbstractText")]
        abstract = " ".join(parts)

    mesh_terms = []
    mesh_list = medline.find(".//MeshHeadingList") if medline is not None else None
    if mesh_list is not None:
        for mh in mesh_list.findall("MeshHeading"):
            desc = mh.find("DescriptorName")
            if desc is not None:
                mesh_terms.append(desc.text or "")

    pub_types = []
    pt_list = art.find(".//PublicationTypeList") if art is not None else None
    if pt_list is not None:
        for pt in pt_list.findall("PublicationType"):
            pub_types.append(pt.text or "")

    study_type = classify_study_type(title, abstract, mesh_terms, pub_types)
    topic = classify_topic(title, abstract, mesh_terms)
    journal_tier = classify_journal_tier(journal_abbrev or journal)

    return {
        "pmid": pmid,
        "title": title,
        "journal": journal,
        "journal_abbrev": journal_abbrev,
        "year": year,
        "n_authors": n_authors,
        "author_position": author_position,
        "equal_contrib": equal_contrib,
        "match_basis": match_basis,
        "target_initials": t_initials,
        "target_orcid": t_orcid,
        "target_affiliation": t_affiliation,
        "study_type": study_type,
        "topic": topic,
        "journal_tier": journal_tier,
        "pub_types": "; ".join(pub_types),
        "mesh_terms": "; ".join(mesh_terms),
        "abstract": abstract[:500],
    }


def records_from_xml(xml_data, target_last: str, target_initials: str = "", target_orcid: str = "") -> list[dict]:
    """Parse a PubmedArticleSet XML (bytes or str) into records. Used by tests + fetch."""
    if isinstance(xml_data, bytes):
        root = ET.fromstring(xml_data)
    else:
        root = ET.fromstring(xml_data)
    return [parse_article(a, target_last, target_initials, target_orcid)
            for a in root.findall(".//PubmedArticle")]

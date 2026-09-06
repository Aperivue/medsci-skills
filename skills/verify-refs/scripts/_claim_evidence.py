"""Report helpers for claim fidelity; no clinical verdicts or network calls.

An assessment is an attributed review record, not a mechanically verified fact.
The helpers bind that record to inputs and render a view of the existing JSON.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re

DIMENSIONS = ("metric", "unit", "denominator", "population", "direction")
VERDICTS = ("supported", "contradicted", "unresolved", "not_assessed")


def sha256(path: Path | None) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else None


def normalized_doi(value: str) -> str:
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value.strip(),
                  flags=re.I).lower().rstrip(".,;")


def prose_spans(raw: str, abbrev: re.Pattern):
    """Prose sentence offsets in the read_text representation, not PDF coordinates.

    Mask excluded regions without shifting positions. As with the existing probes,
    prose inventory excludes code, blockquotes, markdown tables and references.
    """
    def mask(match):
        return re.sub(r"[^\n]", " ", match.group())

    body = re.sub(r"\A---[^\n]*\n.*?\n(?:---|\.\.\.)[^\n]*(?:\n|$)", mask, raw, flags=re.S)
    body = re.sub(r"(?m)^[ \t]*(```|~~~)[^\n]*\n.*?^[ \t]*\1[^\n]*(?:\n|$)",
                  mask, body, flags=re.S)
    cut = re.search(r"(?im)^#{1,3}\s*\**\s*(references|bibliography|works cited)\b", body)
    if cut:
        body = body[:cut.start()]
    body = re.sub(r"(?m)^[ \t]*(?:>|\||#{1,6}\s)[^\n]*", mask, body)
    bracket_spans = [(m.start(), m.end()) for m in re.finditer(r"\[[^\]]*\]", body)]
    start = 0
    for boundary in re.finditer(r"(?<=[.!?])\s+|\n[ \t]*\n|\Z", body):
        end = boundary.start()
        if any(a < end < b for a, b in bracket_spans):
            continue  # e.g. a page locator inside [see @key, p. 3]
        if abbrev.search(body[start:end].strip()) and "\n\n" not in boundary.group():
            continue
        part = body[start:end]
        left = len(part) - len(part.lstrip())
        right = len(part.rstrip())
        if right > left:
            yield start + left, start + right
        start = boundary.end()


def blank_assessment() -> dict:
    return {"verdict": "not_assessed", "assessor": "", "assessed_at": "", "method": "",
            "source_scope": "unknown", "identity_checked": False,
            "source_pages": [], "source_excerpt": "", "rationale": "",
            "claim": {key: "" for key in DIMENSIONS},
            "source": {key: "" for key in DIMENSIONS}}


def binding_hash(binding: dict) -> str:
    return hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()


def reference_record(audit: dict | None, token: str, doi: str) -> dict:
    """Metadata audit is contextual, never proof of source identity or claim support."""
    records = (audit or {}).get("records", [])
    matches = [r for r in records if r.get("ref_id") == token]
    if not matches and doi:
        matches = [r for r in records if normalized_doi(r.get("doi", "")) == doi]
    if len(matches) != 1:
        return {"link": "ambiguous" if matches else "not_available", "recorded_status": None}
    row = matches[0]
    same_doi = not doi or normalized_doi(row.get("doi", "")) == doi
    return {"link": "matched_identifier" if same_doi else "identifier_conflict",
            "recorded_status": row.get("status"), "doi": row.get("doi", ""),
            "input_binding": "not_recorded_by_reference_audit"}


def pdf_record(retrieval: dict | None, pdf_dir: Path | None, doi: str) -> dict:
    rows = [r for r in (retrieval or {}).get("items", [])
            if doi and normalized_doi(r.get("doi", "")) == doi]
    result = {"file": None, "sha256": None, "report_sha256": None,
              "hash_status": "not_available", "identity": {"status": "unavailable"},
              "text_derivation": "not_recorded; equal filenames do not establish PDF-to-text provenance"}
    if len(rows) != 1:
        result["hash_status"] = "ambiguous_report" if rows else "not_available"
        return result
    row = rows[0]
    identity = row.get("source_identity")
    if not isinstance(identity, dict) or identity.get("status") not in {"consistent", "conflict", "unresolved", "unavailable"}:
        identity = {"status": "unavailable", "reason": "missing_or_invalid_identity_record"}
    result["identity"] = copy.deepcopy(identity)
    result["report_sha256"] = row.get("file_sha256") or None
    name = row.get("file", "")
    # Retrieval reports contain basenames, not arbitrary local read instructions.
    if not name or Path(name).name != name or "/" in name or "\\" in name or not pdf_dir:
        result["hash_status"] = "invalid_or_missing_filename"
        return result
    path = pdf_dir / name
    if not path.resolve().is_relative_to(pdf_dir.resolve()):
        result["hash_status"] = "path_outside_pdf_directory"
        return result
    result["file"] = name
    result["sha256"] = sha256(path)
    if result["sha256"] is None:
        result["hash_status"] = "file_missing"
    elif result["report_sha256"] is None:
        result["hash_status"] = "report_hash_missing"
    elif result["sha256"] != result["report_sha256"]:
        result["hash_status"] = "changed_since_retrieval"
    else:
        result["hash_status"] = "matched"
    return result


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def assessment_state(assessment: dict, row: dict, binding_matches: bool) -> tuple[str, str]:
    """Validate record completeness and freshness, not scientific interpretation."""
    verdict = assessment.get("verdict")
    if verdict == "not_assessed":
        return "not_assessed", "not_assessed"
    if not binding_matches:
        return "unresolved", "stale_inputs"
    if verdict not in VERDICTS:
        return "unresolved", "invalid_verdict"
    if not all(nonempty(assessment.get(key)) for key in ("assessor", "assessed_at", "method", "rationale")):
        return "unresolved", "incomplete_assessment"
    if verdict == "unresolved":
        return verdict, "recorded"
    if row["source"]["text_sha256"] is None:
        return "unresolved", "source_not_available"
    if row["source"]["pdf"]["hash_status"] != "matched":
        return "unresolved", "pdf_not_bound"
    if row["source"]["pdf"]["identity"].get("status") == "conflict":
        return "unresolved", "source_identity_conflict"
    if assessment.get("source_scope") != "full_text" or assessment.get("identity_checked") is not True:
        return "unresolved", "source_review_incomplete"
    pages = assessment.get("source_pages")
    if not isinstance(pages, list) or not pages or any(type(p) is not int or p < 1 for p in pages):
        return "unresolved", "missing_pdf_pages"
    if not nonempty(assessment.get("source_excerpt")):
        return "unresolved", "missing_source_excerpt"
    for side in ("claim", "source"):
        values = assessment.get(side)
        if not isinstance(values, dict) or not all(nonempty(values.get(key)) for key in DIMENSIONS):
            return "unresolved", "incomplete_comparison"
    return verdict, "recorded"


def build_evidence(raw: str, manuscript: Path, fulltext_dir: Path, resolver,
                   abbrev: re.Pattern, *, binding: dict, retrieval: dict | None = None,
                   pdf_dir: Path | None = None, reference_audit: dict | None = None,
                   reviewed_report: dict | None = None) -> dict:
    previous_rows = (reviewed_report or {}).get("evidence_rows", [])
    previous = {r["id"]: r for r in previous_rows}
    if len(previous) != len(previous_rows):
        raise ValueError("duplicate evidence row IDs in reviewed report")
    rows = []
    occurrences = Counter()
    pdf_cache = {}
    for start, end in prose_spans(raw, abbrev):
        sentence = raw[start:end]
        for token in dict.fromkeys(resolver.citations_in(sentence)):
            sentence_hash = hashlib.sha256(sentence.encode()).hexdigest()
            base = hashlib.sha256((sentence + "\0" + token).encode()).hexdigest()[:20]
            occurrences[base] += 1
            ident = f"claim-{base}-{occurrences[base]}"
            doi = normalized_doi(resolver.key_doi.get(token) or resolver.num_doi.get(token) or "")
            mapped = resolver.refmap.get(token, "")
            if not doi and normalized_doi(mapped).startswith("10."):
                doi = normalized_doi(mapped)
            source = resolver.resolve(token)
            if doi not in pdf_cache:
                pdf_cache[doi] = pdf_record(retrieval, pdf_dir, doi)
            pdf = copy.deepcopy(pdf_cache[doi])
            source_hash = resolver._source_hashes[source[0]] if source else None
            current_binding = {**binding, "sentence_sha256": sentence_hash, "citation": token,
                               "doi": doi, "text_sha256": source_hash, "pdf_sha256": pdf["sha256"]}
            row = {"id": ident, "citation": token, "doi": doi or None,
                   "manuscript": {"file": manuscript.name, "text": sentence,
                                  "line_start": raw.count("\n", 0, start) + 1,
                                  "line_end": raw.count("\n", 0, end) + 1,
                                  "char_start": start, "char_end": end,
                                  "coordinate_system": "read_text character offsets; lines are not rendered pages"},
                   "source": {"text_file": source[0].relative_to(fulltext_dir).as_posix() if source else None,
                              "text_sha256": source_hash, "pdf": pdf},
                   "reference_audit": reference_record(reference_audit, token, doi),
                   "binding": current_binding, "assessment": blank_assessment(),
                   "verdict": "not_assessed", "review_state": "not_assessed"}
            row["binding_sha256"] = binding_hash(current_binding)
            row["assessment"]["binding_sha256"] = row["binding_sha256"]
            prior = previous.get(ident)
            if prior:
                assessment = prior.get("assessment")
                if not isinstance(assessment, dict):
                    raise ValueError("assessment must be an object")
                row["assessment"] = copy.deepcopy(assessment)
                # Preserve the assessment's original binding through repeated reruns.
                # Comparing only the prior report's current inputs would make a stale
                # assessment look current on the second rerun.
                matches = assessment.get("binding_sha256") == binding_hash(current_binding)
                row["verdict"], row["review_state"] = assessment_state(assessment, row, matches)
                if not matches:
                    row["previous_binding"] = prior.get("binding")
            rows.append(row)
    present = {r["id"] for r in rows}
    # Do not silently drop a review when its sentence/citation disappears on rerun.
    orphaned = [copy.deepcopy(r) for r in previous_rows if r["id"] not in present]
    orphaned += copy.deepcopy((reviewed_report or {}).get("orphaned_evidence_reviews", []))
    return {"evidence_rows": rows, "orphaned_evidence_reviews": orphaned,
            "evidence_counts": {"sentence_citation_pairs": len(rows),
                                "verdicts": dict(Counter(r["verdict"] for r in rows)),
                                "orphaned_reviews": len(orphaned)},
            "evidence_scope": "Recognized prose citations only; tables, blockquotes, code, bibliography and uncited claims are not inventoried. Recorded assessments are attributed judgments, not automatically verified facts. PDF pages and excerpts require assessor inspection; PDF-to-text derivation is not inferred."}


def render_table(report: dict) -> str:
    def cell(value):
        # Literal user/source text must not become HTML, links or multiline table syntax.
        import html
        value = html.escape(str(value), quote=False)
        value = re.sub(r"([\\`*\[\]_])", r"\\\1", value)
        return value.replace("|", "&#124;").replace("\n", " ").replace("\r", " ")

    lines = ["# Claim-source evidence table", "",
             "Derived from claim_fidelity.json. Recorded judgments are not automatic source verification.",
             "Automated findings and manual assessments are separate. Unknown or stale evidence remains visible.",
             "", "| ID / citation | Manuscript location and claim | Source / PDF SHA256 / identity | Pages and excerpt | Claim vs source | Assessment |",
             "|---|---|---|---|---|---|"]
    for row in report["evidence_rows"]:
        assessment = row["assessment"]; source = row["source"]; pdf = source["pdf"]
        comparison = "; ".join(f"{k}: {assessment.get('claim', {}).get(k, '')} / {assessment.get('source', {}).get(k, '')}" for k in DIMENSIONS)
        columns = [f"{row['id']} / {row['citation']}",
                   f"{row['manuscript']['file']} L{row['manuscript']['line_start']}: {row['manuscript']['text']}",
                   f"Text: {source['text_file'] or 'missing'}; PDF: {pdf['file'] or 'missing'} / {pdf['sha256'] or 'unbound'} / {pdf['identity'].get('status', 'unavailable')} ({pdf['hash_status']})",
                   f"{assessment.get('source_pages', [])}: {assessment.get('source_excerpt', '')}",
                   comparison,
                   f"{row['verdict']} ({row['review_state']}); {assessment.get('assessor', '')}; {assessment.get('assessed_at', '')}; {assessment.get('method', '')}; {assessment.get('rationale', '')}"]
        lines.append("| " + " | ".join(cell(c) for c in columns) + " |")
    lines += ["", report["evidence_scope"], "",
              f"Orphaned review records retained in JSON: {len(report['orphaned_evidence_reviews'])}.",
              f"Automated findings retained in JSON: {len(report['findings'])}.", ""]
    return "\n".join(lines)

#!/usr/bin/env python3
"""Classify a queried author's publication trajectory into archetypes A1-A6 (+ composite).

EXPLAINABLE MULTI-LABEL HEURISTIC, NOT AN OBJECTIVE VERDICT. Each surfaced label carries
a score, a confidence band, and evidence drawn from the queried author's OWN PMIDs.

The rubric (signals, weights, thresholds, provenance) is the canonical YAML
references/trajectory_archetypes.yaml. The score formula, confidence bands, negative
rule, and evidence shapes are documented there and implemented here verbatim.

A corpus_manifest.json with review_status == "approved" whose hashes match the CSV is
REQUIRED — surname-alone resolution is forbidden, so an unreviewed corpus cannot be
classified (see SKILL.md Step 6/7).

Stdlib + PyYAML only (no pandas/Biopython).

Usage:
  python3 classify_archetypes.py publications.csv --manifest corpus_manifest.json \
      --rubric references/trajectory_archetypes.yaml -o report_dir/
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write("ERROR: PyYAML is required (pip install pyyaml).\n")
    sys.exit(2)

HERE = Path(__file__).resolve().parent
DEFAULT_RUBRIC = HERE / "references" / "trajectory_archetypes.yaml"
COMPUTABLE = {"source-derived", "rule-derived"}
DISCLAIMER = (
    "These archetype labels are EXPLAINABLE HEURISTICS, NOT objective classifications. "
    "They are computed from PubMed metadata and title/abstract term matches only. Author "
    "position is a positional heuristic (first/middle/last/unknown), not authoritative "
    "leadership or corresponding-author metadata. h-index, citation counts, and "
    "venue-impact tiers are unavailable in this PubMed-only analysis and are never inferred."
)
_CONF_ORDER = {"low": 1, "med": 2, "high": 3}


# ---------------------------------------------------------------------------
# Manifest gate (Fix 1 + 1b): manifest must be approved AND bound to this CSV.
# ---------------------------------------------------------------------------


def _csv_pmids(rows: list[dict]) -> list[str]:
    return [str(r.get("pmid", "")).strip() for r in rows if str(r.get("pmid", "")).strip()]


def _pmid_set_hash(pmids) -> str:
    joined = "\n".join(sorted(set(str(p) for p in pmids)))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def require_approved_manifest(manifest_path: Path, csv_path: Path, rows: list[dict]) -> dict:
    """Halt unless the manifest is approved and its hashes match the CSV."""
    if not manifest_path.exists():
        raise SystemExit(
            f"GATE: no corpus_manifest.json at {manifest_path}. Run fetch_pubmed.py and "
            "approve the corpus first (surname-alone classification is forbidden)."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest.get("review_status") != "approved":
        raise SystemExit(
            f"GATE: manifest review_status is '{manifest.get('review_status')}', not 'approved'. "
            "Review candidates.json and re-run fetch_pubmed.py with --approve."
        )

    actual_csv_sha = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if manifest.get("csv_sha256") != actual_csv_sha:
        raise SystemExit(
            "GATE: csv_sha256 mismatch — this manifest was not generated for this CSV. "
            "Re-run fetch_pubmed.py to regenerate a bound manifest."
        )

    actual_pmid_hash = _pmid_set_hash(_csv_pmids(rows))
    if manifest.get("pmid_set_hash") != actual_pmid_hash:
        raise SystemExit("GATE: pmid_set_hash mismatch — CSV PMID set differs from the manifest.")

    if manifest.get("record_count") != len(rows):
        raise SystemExit(
            f"GATE: record_count mismatch (manifest {manifest.get('record_count')} vs CSV {len(rows)})."
        )
    return manifest


# ---------------------------------------------------------------------------
# Signal metrics
# ---------------------------------------------------------------------------


def _text(r: dict, fields: str = "title") -> str:
    t = (r.get("title", "") or "").lower()
    if fields == "title_abstract":
        t += " " + (r.get("abstract", "") or "").lower()
    return t


def _is_ai(r: dict, terms: list[str]) -> bool:
    text = (r.get("title", "") or "").lower() + " " + (r.get("abstract", "") or "").lower()
    return r.get("study_type") == "AI/ML" or any(t in text for t in terms)


def _year(r: dict):
    y = str(r.get("year", "")).strip()
    return int(y) if y.isdigit() else None


def m_title_term_count(records, p):
    terms = [t.lower() for t in p["any_terms"]]
    fields = p.get("fields", "title")
    matched = [r["pmid"] for r in records if any(t in _text(r, fields) for t in terms)]
    return len(matched) >= p["min_matching_papers"], {"pmids": matched}


def m_study_type_fraction(records, p):
    types = set(p["types"])
    n = len(records)
    hit = [r["pmid"] for r in records if r.get("study_type") in types]
    frac = len(hit) / n if n else 0.0
    return frac >= p["fraction_min"], {
        "summary": {"value": round(frac, 3), "computed_from_n": n, "representative_pmids": hit[:5]}
    }


def m_distinct_topics_within_type(records, p):
    types = set(p["types"])
    subset = [r for r in records if r.get("study_type") in types]
    topics = {r.get("topic") for r in subset if r.get("topic")}
    return len(topics) >= p["min_distinct_topics"], {
        "summary": {"value": len(topics), "computed_from_n": len(subset),
                    "representative_pmids": [r["pmid"] for r in subset[:5]]}
    }


def m_ai_term_fraction(records, p):
    terms = [t.lower() for t in p["terms"]]
    n = len(records)
    hit = [r["pmid"] for r in records if _is_ai(r, terms)]
    frac = len(hit) / n if n else 0.0
    direction = p["direction"]
    if direction == "ge":
        fired = frac >= p["fraction"]
    elif direction == "le":
        fired = frac <= p["fraction"]
    elif direction == "between":
        fired = p["lo"] <= frac <= p["hi"]
    else:
        fired = False
    return fired, {"summary": {"value": round(frac, 3), "computed_from_n": n, "representative_pmids": hit[:5]}}


def m_author_count_papers(records, p):
    amin = p["author_count_min"]
    hit = [r["pmid"] for r in records if str(r.get("n_authors", "")).isdigit() and int(r["n_authors"]) >= amin]
    return len(hit) >= p["min_papers"], {"pmids": hit}


def m_author_count_share(records, p):
    amin = p["author_count_min"]
    n = len(records)
    hit = [r["pmid"] for r in records if str(r.get("n_authors", "")).isdigit() and int(r["n_authors"]) >= amin]
    share = len(hit) / n if n else 0.0
    return share >= p["share_min"], {
        "summary": {"value": round(share, 3), "computed_from_n": n, "representative_pmids": hit[:5]}
    }


def m_venue_drift_ai(records, p):
    terms = [t.lower() for t in p["terms"]]
    yrs = sorted(y for y in (_year(r) for r in records) if y is not None)
    if len(yrs) < 3:
        return False, {"pmids": []}
    ymin, ymax = yrs[0], yrs[-1]
    third = (ymax - ymin) / 3 if ymax > ymin else 0
    early_cut, late_cut = ymin + third, ymax - third
    early_ai, late_ai = 0, []
    for r in records:
        y = _year(r)
        if y is None or not _is_ai(r, terms):
            continue
        if y <= early_cut:
            early_ai += 1
        if y >= late_cut:
            late_ai.append(r["pmid"])
    return (early_ai == 0 and len(late_ai) >= p["min_late"]), {"pmids": late_ai}


def m_dual_genre_copresence(records, p):
    a_terms = [t.lower() for t in p["genre_a_terms"]]
    a_types = set(p.get("genre_a_study_types", []))
    b_terms = [t.lower() for t in p["genre_b_terms"]]
    a_hits, b_hits = [], []
    for r in records:
        text = (r.get("title", "") or "").lower() + " " + (r.get("abstract", "") or "").lower()
        if r.get("study_type") in a_types or any(t in text for t in a_terms):
            a_hits.append(r["pmid"])
        if any(t in text for t in b_terms):
            b_hits.append(r["pmid"])
    fired = len(a_hits) >= p["min_each"] and len(b_hits) >= p["min_each"]
    return fired, {"pmids": list(dict.fromkeys(a_hits[:3] + b_hits[:3]))}


def m_genre_pair_temporal(records, p):
    first_terms = [t.lower() for t in p["first_terms"]]
    second_terms = [t.lower() for t in p["second_terms"]]
    gap = p["max_year_gap"]
    firsts, seconds = [], []
    for r in records:
        y = _year(r)
        if y is None:
            continue
        title = (r.get("title", "") or "").lower()
        if any(t in title for t in first_terms):
            firsts.append((y, r["pmid"]))
        if any(t in title for t in second_terms):
            seconds.append((y, r["pmid"]))
    for yf, pf in firsts:
        for ys, ps in seconds:
            if 0 <= ys - yf <= gap and pf != ps:
                return True, {"pmids": [pf, ps]}
    return False, {"pmids": []}


def m_senior_on_ai_papers(records, p):
    terms = [t.lower() for t in p["terms"]]
    ai = [r for r in records if _is_ai(r, terms)]
    if not ai:
        return False, {"pmids": []}
    senior = [r["pmid"] for r in ai if r.get("author_position") == p["position"]]
    return (len(senior) / len(ai)) >= p["fraction_min"], {"pmids": senior}


def m_pure_ai_no_clinical_floor(records, p):
    terms = [t.lower() for t in p["terms"]]
    n = len(records)
    if n == 0:
        return False, {"pmids": []}
    ai = sum(1 for r in records if _is_ai(r, terms))
    return (ai / n) >= 0.999, {"pmids": []}


METRICS = {
    "title_term_count": (m_title_term_count, "per_paper"),
    "study_type_fraction": (m_study_type_fraction, "corpus_level"),
    "distinct_topics_within_type": (m_distinct_topics_within_type, "corpus_level"),
    "ai_term_fraction": (m_ai_term_fraction, "corpus_level"),
    "author_count_papers": (m_author_count_papers, "per_paper"),
    "author_count_share": (m_author_count_share, "corpus_level"),
    "venue_drift_ai": (m_venue_drift_ai, "per_paper"),
    "dual_genre_copresence": (m_dual_genre_copresence, "per_paper"),
    "genre_pair_temporal": (m_genre_pair_temporal, "per_paper"),
    "senior_on_ai_papers": (m_senior_on_ai_papers, "per_paper"),
    "pure_ai_no_clinical_floor": (m_pure_ai_no_clinical_floor, "per_paper"),
}


# ---------------------------------------------------------------------------
# Scoring (pure function)
# ---------------------------------------------------------------------------


def _present_columns(records: list[dict]) -> set:
    cols = set()
    for r in records:
        cols |= set(r.keys())
    return cols


def _cap_confidence(conf: str, ceiling: str) -> str:
    if conf is None:
        return None
    if _CONF_ORDER.get(conf, 0) > _CONF_ORDER.get(ceiling, 3):
        return ceiling
    return conf


def _score_one(key: str, arc: dict, records: list[dict], present: set) -> dict:
    n = len(records)
    denom = 0.0
    numer = 0.0
    fired_ids: list[str] = []
    evidence_pmids: list[str] = []
    evidence_summary: list[dict] = []
    verify_signals: list[dict] = []

    for sig in arc.get("signals", []):
        prov = sig.get("provenance")
        if prov == "unavailable":
            verify_signals.append({"id": sig["id"], "note": sig.get("verify_note", "")})
            continue
        if prov not in COMPUTABLE:
            continue
        metric_name = sig.get("metric")
        if metric_name not in METRICS:
            continue
        required = set(sig.get("required_columns", []))
        if not required.issubset(present):
            continue  # not computable for this dataset -> excluded from denominator
        fn, kind = METRICS[metric_name]
        weight = float(sig.get("weight", 0.0))
        denom += weight
        fired, ev = fn(records, sig.get("params", {}))
        if fired:
            numer += weight
            fired_ids.append(sig["id"])
            if kind == "per_paper":
                evidence_pmids.extend(ev.get("pmids", []))
            else:
                summary = dict(ev.get("summary", {}))
                summary["signal_id"] = sig["id"]
                evidence_summary.append(summary)

    # Negatives suppress the label regardless of score.
    negatives_fired = []
    for neg in arc.get("negatives", []) or []:
        if set(neg.get("required_columns", [])).issubset(present):
            fn, _ = METRICS.get(neg.get("metric"), (None, None))
            if fn is not None:
                fired, _ev = fn(records, neg.get("params", {}))
                if fired:
                    negatives_fired.append(neg["id"])

    score = round(numer / denom, 3) if denom > 0 else 0.0
    distinct_fired = len(fired_ids)
    min_sample = arc["min_sample"]
    threshold = arc["score_threshold"]

    suppressed = bool(negatives_fired)
    surfaced = (not suppressed) and (n >= min_sample) and (score >= threshold) and (distinct_fired >= 1)

    if distinct_fired >= 3 and n >= min_sample:
        confidence = "high"
    elif distinct_fired >= 2:
        confidence = "med"
    elif distinct_fired >= 1:
        confidence = "low"
    else:
        confidence = None
    confidence = _cap_confidence(confidence, arc.get("max_confidence_mvp", "high"))

    reason = None
    if not surfaced:
        if suppressed:
            reason = f"suppressed by negative rule(s): {', '.join(negatives_fired)}"
        elif n < min_sample:
            reason = f"sample n={n} below min_sample={min_sample}"
        elif distinct_fired == 0:
            reason = "no computable signal fired"
        else:
            reason = f"score {score} below threshold {threshold}"

    result = {
        "label": key,
        "name": arc["name"],
        "score": score,
        "confidence": confidence if surfaced else None,
        "surfaced": surfaced,
        "insufficient_evidence": not surfaced,
        "reason": reason,
        "fired_signals": fired_ids,
        "denominator": round(denom, 3),
        "evidence_pmids": list(dict.fromkeys(evidence_pmids)),
        "evidence_summary": evidence_summary,
        "verify_signals": verify_signals,
        "negatives_fired": negatives_fired,
        "max_confidence_mvp": arc.get("max_confidence_mvp", "high"),
    }
    if surfaced and arc.get("flag"):
        result["flag"] = arc["flag"]
    return result


def score_archetypes(records: list[dict], rubric: dict) -> dict:
    """Pure function: records (list of CSV row dicts) + rubric -> classification dict."""
    present = _present_columns(records)
    archetypes = {key: _score_one(key, arc, records, present)
                  for key, arc in rubric["archetypes"].items()}

    composites = {}
    for key, comp in (rubric.get("composites") or {}).items():
        requires = comp.get("requires_all", [])
        base_ok = all(archetypes.get(r, {}).get("surfaced") for r in requires)
        extra = comp.get("extra_condition", {})
        extra_fired, extra_ev = False, {"pmids": []}
        if base_ok and extra:
            if set(extra.get("required_columns", [])).issubset(present):
                fn, _ = METRICS.get(extra.get("metric"), (None, None))
                if fn is not None:
                    extra_fired, extra_ev = fn(records, extra.get("params", {}))
        surfaced = bool(base_ok and extra_fired)
        composites[key] = {
            "label": key,
            "name": comp["name"],
            "type": "composite",
            "requires_all": requires,
            "surfaced": surfaced,
            "evidence_pmids": extra_ev.get("pmids", []) if surfaced else [],
            "reason": None if surfaced else (
                f"requires all of {requires} to surface" if not base_ok else "extra condition not met"),
        }

    return {
        "disclaimer": DISCLAIMER,
        "sample_n": len(records),
        "archetypes": archetypes,
        "composites": composites,
    }


# ---------------------------------------------------------------------------
# Rubric + IO
# ---------------------------------------------------------------------------


def load_rubric(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    rubric = yaml.safe_load(raw.decode("utf-8"))
    return rubric, hashlib.sha256(raw).hexdigest()


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _md_report(results: dict, meta: dict) -> str:
    out = ["# Trajectory-Archetype Classification", ""]
    out.append(f"> **{DISCLAIMER}**")
    out.append("")
    out.append("## Provenance and disambiguation")
    out.append("")
    out.append(f"- Rubric version: `{meta['rubric_version']}` (sha256 `{meta['rubric_sha256'][:12]}…`)")
    out.append(f"- Corpus: {results['sample_n']} records, manifest review_status `{meta['manifest_review_status']}`")
    basis = meta.get("disambiguation_basis", {})
    basis_str = ", ".join(f"{k}={v}" for k, v in basis.items() if v) or "surname only (review the candidate clusters)"
    out.append(f"- Disambiguation basis: {basis_str}")
    out.append("")
    out.append("## Surfaced archetypes (multi-label)")
    out.append("")
    surfaced = [a for a in results["archetypes"].values() if a["surfaced"]]
    if not surfaced:
        out.append("_No archetype surfaced above threshold — insufficient evidence for all (see below)._")
    for a in sorted(surfaced, key=lambda x: x["score"], reverse=True):
        out.append(f"### {a['label']} — {a['name']}")
        out.append("")
        out.append(f"- Score **{a['score']}** · confidence **{a['confidence']}** "
                   f"(max in MVP: {a['max_confidence_mvp']})")
        out.append(f"- Fired signals: {', '.join(a['fired_signals'])}")
        if a.get("flag"):
            out.append(f"- ⚠️ {a['flag']}")
        if a["evidence_pmids"]:
            out.append(f"- Evidence PMIDs: {', '.join(a['evidence_pmids'][:15])}")
        for s in a["evidence_summary"]:
            out.append(f"- Evidence ({s['signal_id']}): value={s['value']} over n={s['computed_from_n']}")
        if a["verify_signals"]:
            out.append(f"- [VERIFY] not computable in MVP: {', '.join(s['id'] for s in a['verify_signals'])}")
        out.append("")

    comp_surfaced = [c for c in results["composites"].values() if c["surfaced"]]
    if comp_surfaced:
        out.append("## Composite patterns")
        out.append("")
        for c in comp_surfaced:
            out.append(f"- **{c['label']} — {c['name']}** (requires {', '.join(c['requires_all'])}); "
                       f"evidence PMIDs: {', '.join(c['evidence_pmids'][:10])}")
        out.append("")

    out.append("## Insufficient evidence")
    out.append("")
    for a in results["archetypes"].values():
        if not a["surfaced"]:
            out.append(f"- {a['label']} ({a['name']}): {a['reason']}")
    out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Classify an author's trajectory into archetypes (explainable heuristic)")
    ap.add_argument("csv_path", help="Finalized publications CSV from fetch_pubmed.py")
    ap.add_argument("--manifest", help="corpus_manifest.json (default: alongside CSV)", default=None)
    ap.add_argument("--rubric", help="Rubric YAML", default=str(DEFAULT_RUBRIC))
    ap.add_argument("--output-dir", "-o", help="Output directory", default=None)
    args = ap.parse_args()

    csv_path = Path(args.csv_path)
    manifest_path = Path(args.manifest) if args.manifest else csv_path.with_name("corpus_manifest.json")
    out_dir = Path(args.output_dir) if args.output_dir else csv_path.parent / "report"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = read_csv(csv_path)
    manifest = require_approved_manifest(manifest_path, csv_path, rows)

    rubric, rubric_sha = load_rubric(Path(args.rubric))
    results = score_archetypes(rows, rubric)

    meta = {
        "rubric_version": rubric.get("rubric_version", "unknown"),
        "rubric_sha256": rubric_sha,
        "manifest_review_status": manifest.get("review_status"),
        "disambiguation_basis": manifest.get("disambiguators", {}),
    }
    out_json = {**meta, **results}
    (out_dir / "archetype_results.json").write_text(
        json.dumps(out_json, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "archetype_report.md").write_text(_md_report(results, meta), encoding="utf-8")
    print(f"Wrote {out_dir / 'archetype_results.json'} and archetype_report.md")
    surfaced = [a["label"] for a in results["archetypes"].values() if a["surfaced"]]
    print(f"Surfaced archetypes: {', '.join(surfaced) if surfaced else '(none — insufficient evidence)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

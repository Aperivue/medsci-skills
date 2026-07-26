#!/usr/bin/env python3
"""Build a held-out corpus the way a registered protocol requires: auditably, and only once.

`acquire.py` stages a batch from a hand-written queue. That is the right tool for the training
corpus, where the operator picks what to read. It is the WRONG tool for a measurement corpus,
because a hand-picked set has an undeclared selection rule, and an undeclared selection rule is
unauditable — the reviewer's question "how did these forty papers get chosen?" has no answer.

The first held-out corpus was twelve papers chosen to span designs. Defensible for a pilot,
useless as an estimate.

So this runs in phases, each writing an artifact the next phase reads, so the whole cascade is
inspectable afterwards like a STROBE flow:

  frame    query the PMC OA subset; record the query, the date, and EVERY candidate returned
  exclude  apply the registered exclusion rules; count each reason separately
  sample   seeded stratified draw against a target allocation fixed BEFORE the frame was pulled
  fetch    retrieve JATS XML for the drawn records
  render   render_jats.py (never a one-off converter — the renderer IS the denominator)
  seal     verify the coverage targets, then write the manifest with frozen_at + per-record license

WHY SEAL CAN REFUSE
    The protocol's corpus targets (n, distinct design profiles, no coverage value above a share,
    no duplicated full profile) are the difference between "forty papers" and "forty observations".
    They are enforced here rather than checked by intention, because the moment the corpus exists
    there is enormous pressure to seal it anyway.

WHAT THIS DELIBERATELY DOES NOT DO
    It does not read the papers. Nobody may read a held-out record except to label a fire; that is
    the whole firewall. The operator sees counts, DOIs and coverage tuples, never prose.

Usage:
    acquire_heldout.py --phase frame   --work _corpus/_acq --query-file frame_query.txt
    acquire_heldout.py --phase exclude --work _corpus/_acq
    acquire_heldout.py --phase sample  --work _corpus/_acq --alloc alloc.json --seed 42
    acquire_heldout.py --phase fetch   --work _corpus/_acq
    acquire_heldout.py --phase render  --work _corpus/_acq --out _corpus/heldout
    acquire_heldout.py --phase seal    --work _corpus/_acq --out _corpus/heldout \\
                       --manifest _corpus/manifest.json --frozen-at 2026-08-01

Exit: 0 phase completed, 1 the phase refused (targets unmet / nothing drawn), 2 usage or network
error. Stdlib-only (urllib for E-utilities).
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
HERE = Path(__file__).resolve().parent
RE_DIR = HERE.parent
REPO = RE_DIR.parent

# --- registered exclusion rules (06_MEASUREMENT_PROTOCOL.md §4) --------------------------------
# Each is counted separately and reported. A single "excluded: 37" line is not an audit trail.
GUIDELINE_TITLE_RE = re.compile(
    r"\b(?:CONSORT|PRISMA|STROBE|STARD|TRIPOD|SPIRIT|CARE|SQUIRE|COREQ|SRQR|MOOSE|AMSTAR|"
    r"QUADAS|PROBAST|ROBINS|GRADE)\b|"
    r"\b(?:reporting guideline|explanation and elaboration|checklist|statement:? updated"
    r"|extension statement)\b",
    re.IGNORECASE,
)
NON_RESEARCH_TYPE_RE = re.compile(
    r"\b(?:editorial|erratum|correction|corrigendum|retraction|comment|letter|"
    r"correspondence|protocol|preprint|expression of concern|author reply)\b",
    re.IGNORECASE,
)


def eutils(path: str, params: Dict[str, str], retries: int = 3) -> str:
    url = f"{EUTILS}/{path}?" + urllib.parse.urlencode(params)
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as exc:  # pragma: no cover - network
            last = exc
            time.sleep(2 * (i + 1))
    print(f"acquire: E-utilities failed after {retries} tries: {last}", file=sys.stderr)
    raise SystemExit(2)


def load(work: Path, name: str) -> dict:
    p = work / name
    if not p.is_file():
        print(f"acquire: {name} not found in {work} — run the previous phase first", file=sys.stderr)
        raise SystemExit(2)
    return json.loads(p.read_text(encoding="utf-8"))


def save(work: Path, name: str, payload: dict) -> None:
    work.mkdir(parents=True, exist_ok=True)
    (work / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {work / name}")


# --- phases ------------------------------------------------------------------------------------

def phase_frame(a) -> int:
    query = a.query_file.read_text(encoding="utf-8").strip()
    print(f"frame: {query}")
    res = eutils("esearch.fcgi", {"db": "pmc", "term": query, "retmax": str(a.retmax),
                                  "retmode": "json"})
    ids = json.loads(res)["esearchresult"].get("idlist", [])
    print(f"  {len(ids)} candidate record(s)")
    summ = json.loads(eutils("esummary.fcgi", {"db": "pmc", "id": ",".join(ids),
                                               "retmode": "json"})) if ids else {"result": {}}
    cands = []
    for pmcid in ids:
        r = summ["result"].get(pmcid, {})
        doi = next((x.get("value") for x in r.get("articleids", []) if x.get("idtype") == "doi"), "")
        cands.append({
            "pmcid": pmcid, "doi": doi, "title": r.get("title", ""),
            "journal": r.get("fulljournalname", ""), "pubdate": r.get("pubdate", ""),
            "pubtype": r.get("pubtype", []),
        })
    save(a.work, "candidates.json",
         {"query": query, "retrieved_at": a.today, "n": len(cands), "candidates": cands})
    print("  NOTE: every candidate is recorded, including the ones the next phase drops.")
    return 0


def known_dois() -> set:
    """DOIs the project has already touched: queue files, and any train-split manifest record."""
    seen = set()
    for p in (RE_DIR / "doi_lists").glob("*"):
        if p.is_file():
            seen |= {m.group(0).lower()
                     for m in re.finditer(r"10\.\d{4,}/[^\s\"'<>]+", p.read_text(encoding="utf-8", errors="replace"))}
    mf = REPO / "_corpus" / "manifest.json"
    if mf.is_file():
        try:
            for rec in json.loads(mf.read_text(encoding="utf-8")).get("records", []):
                for k in ("doi", "source_url"):
                    v = str(rec.get(k, ""))
                    m = re.search(r"10\.\d{4,}/[^\s\"'<>]+", v)
                    if m:
                        seen.add(m.group(0).lower())
        except Exception:
            pass
    return seen


def phase_exclude(a) -> int:
    cand = load(a.work, "candidates.json")
    already = known_dois()
    blocked_authors = {s.strip().lower() for s in (a.exclude_author or "").split(",") if s.strip()}
    kept, dropped = [], []
    for c in cand["candidates"]:
        reasons = []
        if GUIDELINE_TITLE_RE.search(c.get("title", "")):
            reasons.append("reporting_guideline_document")
        types = " ".join(c.get("pubtype", []))
        if NON_RESEARCH_TYPE_RE.search(types) or NON_RESEARCH_TYPE_RE.search(c.get("title", "")):
            reasons.append("non_research_article_type")
        if c.get("doi", "").lower() in already:
            reasons.append("already_in_development_corpus")
        if not c.get("doi"):
            reasons.append("no_doi")
        for name in blocked_authors:
            if name and name in c.get("title", "").lower():
                reasons.append("toolkit_author_overlap")
        (dropped if reasons else kept).append({**c, "exclusion_reasons": reasons})
    counts = Counter(r for d in dropped for r in d["exclusion_reasons"])
    print(f"exclude: {len(cand['candidates'])} candidates -> {len(kept)} eligible, {len(dropped)} dropped")
    for r, n in counts.most_common():
        print(f"    {n:4d}  {r}")
    print("  Retraction / Expression-of-Concern status and author-institution overlap are NOT"
          "\n  machine-checked here; they are an operator step recorded in exclusions.json.")
    save(a.work, "eligible.json",
         {"from": cand["retrieved_at"], "n_candidates": len(cand["candidates"]),
          "n_eligible": len(kept), "exclusion_counts": dict(counts),
          "eligible": kept, "dropped": dropped})
    return 0 if kept else 1


def phase_sample(a) -> int:
    elig = load(a.work, "eligible.json")
    alloc = json.loads(a.alloc.read_text(encoding="utf-8"))
    assign = alloc.get("assign", {})   # pmcid/doi -> design profile, filled by the operator
    targets = alloc.get("targets", {})  # design profile -> how many to draw
    if not targets:
        print("acquire: alloc.json needs a `targets` map fixed BEFORE the frame was pulled,"
              "\n  otherwise the allocation is chosen after seeing the pool.", file=sys.stderr)
        return 2

    strata: Dict[str, List[dict]] = defaultdict(list)
    unassigned = 0
    for c in elig["eligible"]:
        key = assign.get(c["pmcid"]) or assign.get(c.get("doi", ""))
        if not key:
            unassigned += 1
            continue
        strata[key].append(c)

    rng = random.Random(a.seed)
    drawn, short = [], {}
    for design, want in sorted(targets.items()):
        pool = sorted(strata.get(design, []), key=lambda c: c["pmcid"])  # sort => reproducible
        if len(pool) < want:
            short[design] = {"wanted": want, "available": len(pool)}
        take = rng.sample(pool, min(want, len(pool)))
        for c in take:
            drawn.append({**c, "coverage_design": design})

    print(f"sample: seed={a.seed}  drawn {len(drawn)} of {sum(targets.values())} targeted")
    if unassigned:
        print(f"  {unassigned} eligible record(s) carry no design assignment and were not in any stratum")
    for d, s in short.items():
        print(f"  SHORT {d}: wanted {s['wanted']}, pool had {s['available']}")
    save(a.work, "selection.json",
         {"seed": a.seed, "targets": targets, "n_drawn": len(drawn),
          "short_strata": short, "n_unassigned": unassigned, "drawn": drawn})
    print("  Re-running this phase with the same seed and the same eligible.json redraws exactly"
          "\n  this set. That is what makes the selection rule checkable rather than asserted.")
    return 0 if drawn else 1


def phase_fetch(a) -> int:
    sel = load(a.work, "selection.json")
    raw = a.work / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    n = 0
    for c in sel["drawn"]:
        dest = raw / f"{c['pmcid']}.xml"
        if dest.is_file():
            continue
        xml = eutils("efetch.fcgi", {"db": "pmc", "id": c["pmcid"], "retmode": "xml"})
        dest.write_text(xml, encoding="utf-8")
        n += 1
        time.sleep(0.4)  # be a good citizen at the API
    print(f"fetch: {n} new, {len(sel['drawn'])} total under {raw}")
    return 0


def phase_render(a) -> int:
    sel = load(a.work, "selection.json")
    raw, out = a.work / "raw", a.out
    out.mkdir(parents=True, exist_ok=True)
    renderer = HERE / "render_jats.py"
    ok, failed = 0, []
    for c in sel["drawn"]:
        src = raw / f"{c['pmcid']}.xml"
        if not src.is_file():
            failed.append({"pmcid": c["pmcid"], "why": "not fetched"})
            continue
        rid = c.get("record_id") or f"ho_{c['pmcid']}"
        r = subprocess.run(["python3", str(renderer), "--xml", str(src),
                            "--out", str(out / f"{rid}.md")], capture_output=True, text=True)
        if r.returncode != 0:
            failed.append({"pmcid": c["pmcid"], "why": (r.stderr or "").strip()[:200]})
        else:
            ok += 1
    print(f"render: {ok} rendered, {len(failed)} failed")
    for f in failed:
        print(f"  FAILED {f['pmcid']}: {f['why']}")
    save(a.work, "render_report.json", {"n_ok": ok, "failed": failed})
    print("  Rendered with render_jats.py, whose per-publisher fidelity test is the reason the"
          "\n  denominator can be trusted. A one-off converter here would void the corpus.")
    return 0 if ok else 1


def phase_seal(a) -> int:
    """Refuse unless the corpus is actually the thing the protocol described."""
    sel = load(a.work, "selection.json")
    papers = sorted(p for p in a.out.iterdir() if p.suffix == ".md") if a.out.is_dir() else []
    cov = {c.get("record_id") or f"ho_{c['pmcid']}": {
        "coverage_design": c.get("coverage_design", ""),
        "coverage_modality": c.get("coverage_modality", ""),
        "coverage_task": c.get("coverage_task", ""),
    } for c in sel["drawn"]}

    present = [p for p in papers if p.stem in cov]
    n = len(present)
    profiles = Counter(tuple(sorted(cov[p.stem].items())) for p in present)
    axes: Dict[str, Counter] = defaultdict(Counter)
    for p in present:
        for k, v in cov[p.stem].items():
            if v:
                axes[k][v] += 1

    problems = []
    if n < a.min_n:
        problems.append(f"only {n} rendered paper(s), protocol requires >= {a.min_n}")
    if len(profiles) < a.min_profiles:
        problems.append(f"only {len(profiles)} distinct coverage profile(s), requires >= {a.min_profiles}")
    dupes = [k for k, c in profiles.items() if c > 1]
    if dupes:
        problems.append(f"{len(dupes)} coverage profile(s) appear more than once — "
                        "one pattern measured twice is not two observations")
    for axis, vals in axes.items():
        for val, cnt in vals.items():
            if n and cnt / n > a.max_share:
                problems.append(f"{axis}={val} holds {cnt}/{n} ({cnt/n:.0%}) > {a.max_share:.0%}")
    missing_cov = [p.stem for p in present if not all(cov[p.stem].values())]
    if missing_cov:
        problems.append(f"{len(missing_cov)} record(s) have an incomplete coverage tuple")

    print(f"seal: {n} paper(s), {len(profiles)} distinct profile(s)")
    for axis, vals in sorted(axes.items()):
        print(f"    {axis}: " + ", ".join(f"{v}={c}" for v, c in sorted(vals.items())))
    if problems:
        print("\n  REFUSED — the corpus is not what the protocol described:", file=sys.stderr)
        for p in problems:
            print(f"    - {p}", file=sys.stderr)
        print("\n  Fix the draw, not the target. Sealing anyway is how 'forty papers' quietly"
              "\n  becomes 'one pattern measured forty times'.", file=sys.stderr)
        return 1

    records = []
    for p in present:
        c = next(x for x in sel["drawn"] if (x.get("record_id") or f"ho_{x['pmcid']}") == p.stem)
        records.append({
            "record_id": p.stem, "split": "heldout", "frozen_at": a.frozen_at,
            "source_url": f"https://doi.org/{c['doi']}" if c.get("doi") else "",
            "source_type": "oa_article", "license": c.get("license", "UNKNOWN"),
            "retrieved_at": sel.get("retrieved_at", a.frozen_at),
            "verbatim_allowed": False, "public_reuse_policy": "synthetic_only",
            "coverage": cov[p.stem],
        })
    unknown = [r["record_id"] for r in records if r["license"] == "UNKNOWN"]
    if unknown:
        print(f"\n  {len(unknown)} record(s) carry no license — set them before the manifest is"
              f"\n  committed; an unlicensed record cannot be in a corpus we promise to keep local.",
              file=sys.stderr)
    save(a.work, "seal_records.json", {"frozen_at": a.frozen_at, "n": len(records),
                                       "records": records, "licenses_unknown": unknown})
    print(f"\n  {len(records)} record(s) ready for {a.manifest}. Merge them in, commit, and then"
          "\n  DO NOT READ THE CORPUS until the labeling session.")
    return 1 if unknown else 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--phase", required=True,
                    choices=("frame", "exclude", "sample", "fetch", "render", "seal"))
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--query-file", type=Path)
    ap.add_argument("--retmax", type=int, default=500)
    ap.add_argument("--today", default="")
    ap.add_argument("--exclude-author", default="")
    ap.add_argument("--alloc", type=Path)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--frozen-at", default="")
    ap.add_argument("--min-n", type=int, default=40)
    ap.add_argument("--min-profiles", type=int, default=12)
    ap.add_argument("--max-share", type=float, default=0.20)
    a = ap.parse_args(argv)

    need = {"frame": ["query_file"], "sample": ["alloc"], "render": ["out"],
            "seal": ["out", "frozen_at"]}
    for f in need.get(a.phase, []):
        if not getattr(a, f):
            ap.error(f"--phase {a.phase} requires --{f.replace('_', '-')}")
    if a.phase == "frame" and not a.today:
        ap.error("--phase frame requires --today YYYY-MM-DD (the retrieval date is provenance)")

    return {"frame": phase_frame, "exclude": phase_exclude, "sample": phase_sample,
            "fetch": phase_fetch, "render": phase_render, "seal": phase_seal}[a.phase](a)


if __name__ == "__main__":
    sys.exit(main())

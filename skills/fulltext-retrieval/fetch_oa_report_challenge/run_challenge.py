#!/usr/bin/env python3
"""Offline, network-free challenge for fetch_oa.build_report + title tri-state.

Loads committed fixtures (worklist.tsv, results.json, extracted_text.json),
fabricates stub PDFs in a temp dir for the "retrieved" DOIs, runs
fetch_oa.build_report, and asserts the resulting projection equals
expected/projection.json. Exercises read_doi_file (TSV+title), build_report,
and classify_title_match (match / mismatch / unavailable) without touching the
network or pdftotext. Stdlib-only.
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "fetch_oa.py"


def load_engine():
    spec = importlib.util.spec_from_file_location("fetch_oa", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def projection(report: dict) -> dict:
    items = sorted(
        ({"doi": i["doi"], "status": i["status"], "source": i["source"],
          "title_match": i["title_match"]} for i in report["items"]),
        key=lambda x: x["doi"],
    )
    return {"counts": report["counts"], "items": items}


def main() -> int:
    assert ENGINE.exists(), f"ENV-ERR: {ENGINE} missing"
    m = load_engine()

    records = m.read_doi_file(HERE / "worklist.tsv")
    results = {k: tuple(v) for k, v in
               json.loads((HERE / "results.json").read_text()).items()}
    extracted = json.loads((HERE / "extracted_text.json").read_text())
    expected = json.loads((HERE / "expected" / "projection.json").read_text())

    fails = []

    def check(label, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        if not cond:
            fails.append(label)

    with tempfile.TemporaryDirectory() as tmp:
        outdir = Path(tmp)
        for rec in records:
            status, _ = results.get(rec["doi"], ("fail", ""))
            if status in m.RETRIEVED_STATUSES:
                stub = outdir / f"{m.safe_doi_name(rec['doi'])}.pdf"
                stub.write_bytes(b"%PDF-1.4\n" + b"0" * (11 * 1024))
        report = m.build_report(records, results, outdir, extracted)
        proj = projection(report)

    by_doi = {i["doi"]: i for i in proj["items"]}
    check("valid -> title_match 'match'",
          by_doi["10.1111/valid.match"]["title_match"] == "match")
    check("mislabel -> title_match 'mismatch'",
          by_doi["10.2222/label.mismatch"]["title_match"] == "mismatch")
    check("no-text -> title_match 'unavailable'",
          by_doi["10.3333/no.text"]["title_match"] == "unavailable")
    check("missing -> status 'fail'",
          by_doi["10.9999/not.retrieved"]["status"] == "fail")
    check("counts.retrieved == 3", proj["counts"]["retrieved"] == 3)
    check("counts.not_retrieved == 1", proj["counts"]["not_retrieved"] == 1)
    check("counts.title_mismatch == 1", proj["counts"]["title_mismatch"] == 1)
    check("projection matches expected/projection.json", proj == expected)

    if fails:
        print(f"FAILURES: {len(fails)}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

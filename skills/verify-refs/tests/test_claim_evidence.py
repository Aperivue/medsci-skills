"""Synthetic source-evidence workflow controls; no private papers or network."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import check_claim_fidelity as fidelity
from _claim_evidence import binding_hash, render_table


def write_pdf(path: Path, text: str):
    """A real one-page PDF, using only stdlib and synthetic ASCII text."""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 10 Tf 40 740 Td ({escaped}) Tj ET".encode()
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
    data = b"%PDF-1.4\n"; offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data)); data += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    start = len(data)
    data += f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode()
    data += b"".join(f"{n:010d} 00000 n \n".encode() for n in offsets[1:])
    data += f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode()
    path.write_bytes(data)


class ClaimEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ft = self.root / "fulltext"; self.ft.mkdir()
        self.manuscript = self.root / "manuscript.md"
        self.manuscript.write_text("# Synthetic methods\n\nThe tool reduced latency by 18% in the complete sample [@demo].\n", encoding="utf-8")
        self.bib = self.root / "refs.bib"
        self.bib.write_text("@article{demo,\n title={Synthetic latency comparison},\n doi={10.1000/synthetic.latency}\n}\n", encoding="utf-8")
        self.text = self.ft / "10.1000_synthetic.latency.md"
        self.excerpt = "The tool reduced latency by 18% in the complete sample."
        self.text.write_text(self.excerpt + "\n" + "Synthetic background for a software experiment. " * 85, encoding="utf-8")
        self.pdf = self.ft / "10.1000_synthetic.latency.pdf"
        write_pdf(self.pdf, self.excerpt)
        self.retrieval = self.ft / "retrieval_report.json"
        self.retrieval.write_text(json.dumps({"schema_version":2,"items":[{
            "doi":"10.1000/synthetic.latency", "file":self.pdf.name,
            "file_sha256":hashlib.sha256(self.pdf.read_bytes()).hexdigest(),
            "source_identity":{"status":"consistent","reason":"synthetic first-page evidence"}}]}))
        self.audit = self.root / "reference_audit.json"
        self.audit.write_text(json.dumps({"schema_version":4,"records":[{
            "ref_id":"demo","doi":"10.1000/synthetic.latency","status":"OK"}]}))

    def report(self, reviewed=None, **kwargs):
        args = dict(retrieval_report=self.retrieval, reference_audit=self.audit, reviewed_report=reviewed)
        args.update(kwargs)
        return fidelity.build_report(self.manuscript, self.ft, self.bib, {}, **args)

    def review(self, report=None, verdict="supported"):
        report = copy.deepcopy(report or self.report())
        assessment = report["evidence_rows"][0]["assessment"]
        assessment.update(verdict=verdict, assessor="Synthetic test assessor", assessed_at="2026-01-01",
                          method="synthetic_fixture_annotation", source_scope="full_text", identity_checked=True,
                          source_pages=[1], source_excerpt=self.excerpt,
                          rationale="Synthetic source states the same latency change and population.")
        for side in ("claim", "source"):
            assessment[side] = dict(metric="latency change", unit="percent", denominator="all experimental runs",
                                    population="complete sample", direction="decrease")
        return report

    def save(self, value, name="reviewed.json"):
        path = self.root / name; path.write_text(json.dumps(value), encoding="utf-8"); return path

    def replace_source(self, old, new):
        self.text.write_text(self.text.read_text().replace(old, new))
        self.excerpt = self.excerpt.replace(old, new)
        write_pdf(self.pdf, self.excerpt)
        report = json.loads(self.retrieval.read_text())
        report["items"][0]["file_sha256"] = hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.retrieval.write_text(json.dumps(report))

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "check_claim_fidelity.py"),
                               "--manuscript", str(self.manuscript), "--fulltext-dir", str(self.ft),
                               "--bib", str(self.bib), *map(str, args)], capture_output=True, text=True)

    def test_no_warning_and_real_reference_do_not_establish_support(self):
        report = self.report(); row = report["evidence_rows"][0]
        self.assertEqual(report["findings"], [])
        self.assertEqual(row["reference_audit"]["recorded_status"], "OK")
        self.assertEqual(row["source"]["pdf"]["identity"]["status"], "consistent")
        self.assertEqual(row["verdict"], "not_assessed")

    def test_same_number_in_different_subgroup_stays_unassessed(self):
        self.replace_source("complete sample", "fastest subgroup")
        row = self.report()["evidence_rows"][0]
        self.assertEqual(row["verdict"], "not_assessed")
        reviewed = self.review(verdict="contradicted")
        a = reviewed["evidence_rows"][0]["assessment"]
        a["source"]["population"] = "fastest subgroup"
        a["source_excerpt"] = "The tool reduced latency by 18% in the fastest subgroup."
        a["rationale"] = "Same number describes a different population."
        row = self.report(self.save(reviewed))["evidence_rows"][0]
        self.assertEqual(row["verdict"], "contradicted")
        self.assertNotEqual(row["assessment"]["claim"]["population"], row["assessment"]["source"]["population"])

    def test_opposite_direction_is_not_inferred_from_matching_words(self):
        self.replace_source("reduced", "increased")
        self.assertEqual(self.report()["evidence_rows"][0]["verdict"], "not_assessed")

    def test_wrong_pdf_identity_cannot_carry_support(self):
        payload = json.loads(self.retrieval.read_text())
        payload["items"][0]["source_identity"]["status"] = "conflict"
        self.retrieval.write_text(json.dumps(payload))
        row = self.report(self.save(self.review()))["evidence_rows"][0]
        self.assertEqual(row["reference_audit"]["recorded_status"], "OK")
        self.assertEqual((row["verdict"], row["review_state"]), ("unresolved", "source_identity_conflict"))

    def test_abstract_only_review_remains_unresolved(self):
        self.text.write_text("Synthetic abstract with the same reported latency change.")
        reviewed = self.review(); reviewed["evidence_rows"][0]["assessment"]["source_scope"] = "abstract_only"
        row = self.report(self.save(reviewed))["evidence_rows"][0]
        self.assertEqual(row["verdict"], "unresolved")

    def test_unresolved_citation_is_inventoried_without_attribution_verb(self):
        self.manuscript.write_text("A latency difference of 18% [@missing].")
        row = self.report()["evidence_rows"][0]
        self.assertEqual(row["citation"], "missing"); self.assertIsNone(row["source"]["text_file"])
        self.assertEqual(row["verdict"], "not_assessed")

    def test_recorded_assessment_requires_pages_excerpt_and_comparison(self):
        for key, value in [("assessor", ""), ("source_pages", []), ("source_pages", [True]),
                           ("source_excerpt", ""), ("claim", {}), ("source", {})]:
            with self.subTest(key=key, value=value):
                reviewed = self.review(); reviewed["evidence_rows"][0]["assessment"][key] = value
                self.assertEqual(self.report(self.save(reviewed))["evidence_rows"][0]["verdict"], "unresolved")

    def test_complete_attributed_review_is_retained_without_changing_findings(self):
        initial = self.report(); reviewed = self.review(initial)
        report = self.report(self.save(reviewed)); row = report["evidence_rows"][0]
        self.assertEqual((row["verdict"], row["review_state"]), ("supported", "recorded"))
        self.assertEqual(report["findings"], initial["findings"])
        self.assertIn("not automatically verified facts", report["evidence_scope"])

    def test_changed_pdf_stays_stale_across_repeated_reruns(self):
        reviewed = self.save(self.review())
        write_pdf(self.pdf, "Different synthetic source version.")
        for _ in range(2):
            report = self.report(reviewed); row = report["evidence_rows"][0]
            self.assertEqual(row["verdict"], "unresolved"); self.assertEqual(row["review_state"], "stale_inputs")
            self.assertEqual(row["source"]["pdf"]["hash_status"], "changed_since_retrieval")
            reviewed = self.save(report)

    def test_changed_text_bibliography_and_manuscript_context_invalidate_review(self):
        for path in (self.text, self.bib, self.manuscript):
            with self.subTest(path=path.name):
                old = path.read_bytes(); reviewed = self.save(self.review())
                path.write_bytes(old + b"\nContext updated.\n")
                row = self.report(reviewed)["evidence_rows"][0]
                self.assertEqual(row["review_state"], "stale_inputs")
                path.write_bytes(old)

    def test_changed_sentence_preserves_orphaned_review(self):
        reviewed = self.save(self.review()); self.manuscript.write_text("A changed claim [@demo].")
        report = self.report(reviewed)
        self.assertEqual(report["evidence_rows"][0]["verdict"], "not_assessed")
        self.assertEqual(len(report["orphaned_evidence_reviews"]), 1)

    def test_explicit_reinspection_can_refresh_a_stale_assessment(self):
        reviewed = self.save(self.review())
        self.text.write_text(self.text.read_text() + "\nAdditional synthetic context.\n")
        stale = self.report(reviewed); row = stale["evidence_rows"][0]
        self.assertEqual(row["review_state"], "stale_inputs")
        row["assessment"]["binding_sha256"] = row["binding_sha256"]
        row["assessment"]["rationale"] = "Synthetic assessor rechecked the changed context."
        fresh = self.report(self.save(stale))["evidence_rows"][0]
        self.assertEqual((fresh["verdict"], fresh["review_state"]), ("supported", "recorded"))

    def test_numbered_citation_has_source_and_original_offsets(self):
        raw = "A synthetic latency result [1].\n\n## References\n1. Synthetic source. doi:10.1000/synthetic.latency\n"
        self.manuscript.write_text(raw)
        row = self.report()["evidence_rows"][0]
        self.assertEqual(row["citation"], "1")
        self.assertEqual(row["doi"], "10.1000/synthetic.latency")
        self.assertEqual(row["manuscript"]["char_start"], 0)

    def test_docx_coordinates_are_extracted_text_not_rendered_pages(self):
        from docx import Document
        doc = Document(); doc.add_paragraph("Synthetic latency evidence [@demo].")
        path = self.root / "manuscript.docx"; doc.save(path)
        report = fidelity.build_report(path, self.ft, self.bib, {})
        row = report["evidence_rows"][0]
        self.assertEqual(row["manuscript"]["line_start"], 1)
        self.assertIn("not rendered pages", row["manuscript"]["coordinate_system"])

    def test_duplicate_review_ids_rejected(self):
        reviewed = self.review(); reviewed["evidence_rows"].append(reviewed["evidence_rows"][0])
        with self.assertRaisesRegex(ValueError, "duplicate"): self.report(self.save(reviewed))

    def test_missing_or_duplicate_pdf_report_never_uses_first_match(self):
        payload = json.loads(self.retrieval.read_text()); payload["items"] *= 2
        self.retrieval.write_text(json.dumps(payload))
        self.assertEqual(self.report()["evidence_rows"][0]["source"]["pdf"]["hash_status"], "ambiguous_report")

    def test_report_paths_cannot_escape_the_pdf_directory(self):
        payload = json.loads(self.retrieval.read_text()); payload["items"][0]["file"] = "../outside.pdf"
        self.retrieval.write_text(json.dumps(payload))
        row = self.report()["evidence_rows"][0]
        self.assertIsNone(row["source"]["pdf"]["sha256"])

    def test_prose_positions_survive_exclusions_and_duplicate_sentences(self):
        line = "A synthetic claim [see @demo, p. 1; @missing]."
        raw = "---\ntitle: ignored [@meta]\n---\n# Heading\n\n```\nignored [@code]\n```\n\n| ignored [@table] |\n\n> ignored [@quote]\n\n" + line + "\n\n" + line + "\n\n## References\nignored [@bib]\n"
        self.manuscript.write_text(raw)
        rows = self.report()["evidence_rows"]
        self.assertEqual([r["citation"] for r in rows], ["demo", "missing", "demo", "missing"])
        self.assertEqual(len({r["id"] for r in rows}), 4)
        for row in rows:
            location = row["manuscript"]
            self.assertEqual(raw[location["char_start"]:location["char_end"]], line)
            self.assertEqual(raw.splitlines()[location["line_start"] - 1], line)

    def test_no_report_supplied_preserves_legacy_call_signature(self):
        report = fidelity.build_report(self.manuscript, self.ft, self.bib, {})
        self.assertEqual(report["evidence_rows"][0]["source"]["pdf"]["hash_status"], "not_available")
        self.assertEqual(report["evidence_rows"][0]["verdict"], "not_assessed")

    def test_table_escapes_source_markup(self):
        report = self.report(); report["evidence_rows"][0]["assessment"]["source_excerpt"] = "<img src=x>|[link](https://example.com)\nnext"
        table = render_table(report)
        self.assertNotIn("<img", table); self.assertNotIn("[link](", table); self.assertIn("&#124;", table)

    def test_cli_writes_derived_table_and_preserves_all_sources(self):
        paths = (self.manuscript, self.bib, self.text, self.pdf, self.retrieval, self.audit)
        before = {p:p.read_bytes() for p in paths}
        output = self.root / "claim_fidelity.json"; table = self.root / "claim_fidelity.md"
        result = self.cli("--retrieval-report", self.retrieval, "--reference-audit", self.audit,
                          "--out", output, "--evidence-table", table)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("every checkable claim is supported", result.stdout)
        self.assertIn("not been established", result.stdout)
        self.assertIn(r"not\_assessed", table.read_text())
        self.assertEqual(json.loads(output.read_text())["schema_version"], 2)
        self.assertEqual(before, {p:p.read_bytes() for p in paths})

    def test_cli_rejects_outputs_over_source_files(self):
        for path in (self.manuscript, self.text, self.pdf, self.retrieval):
            with self.subTest(path=path.name):
                before = path.read_bytes()
                result = self.cli("--retrieval-report", self.retrieval, "--out", path)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(path.read_bytes(), before)

    def test_invalid_json_does_not_overwrite_existing_output(self):
        output = self.root / "claim_fidelity.json"; output.write_text("preserve existing output")
        self.retrieval.write_text("broken json")
        result = self.cli("--retrieval-report", self.retrieval, "--out", output)
        self.assertEqual(result.returncode, 2); self.assertEqual(output.read_text(), "preserve existing output")

    def test_table_requires_json_and_cannot_replace_it(self):
        output = self.root / "claim_fidelity.json"
        self.assertEqual(self.cli("--evidence-table", output).returncode, 2)
        self.assertEqual(self.cli("--out", output, "--evidence-table", output).returncode, 2)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

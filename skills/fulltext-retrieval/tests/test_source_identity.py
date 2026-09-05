#!/usr/bin/env python3
"""Synthetic source-identity regressions, including real PDF/CLI round trips.

No source papers, private records, network requests or API credentials are used.
The PDF integration cases use Poppler when available; pure cases are stdlib-only.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ENGINE = Path(__file__).resolve().parents[1] / "fetch_oa.py"
SPEC = importlib.util.spec_from_file_location("fetch_oa_identity_test", ENGINE)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

TITLE = "Deep Learning for Pulmonary Nodule Detection on Chest CT"
DOI = "10.1000/synthetic.nodules"
OTHER = "10.1000/synthetic.crops"
RECORD = {"doi": DOI, "title": TITLE, "pmid": ""}
GOOD = f"{TITLE}\nAlex Example\nhttps://doi.org/{DOI}\nAbstract: Synthetic example."


def write_pdf(path: Path, lines: list[str]) -> None:
    """Write an actual single-page Helvetica PDF with a correct cross-reference table."""
    commands = ["BT /F1 11 Tf 36 750 Td 16 TL"]
    for line in lines:
        line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        commands.append(f"({line}) Tj T*")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
    ]
    data = bytearray(b"%PDF-1.4\n%" + b"synthetic-padding " * 700 + b"\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
                f"startxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(data)


class SourceIdentityTests(unittest.TestCase):
    def test_reference_and_body_mentions_do_not_establish_identity(self):
        for boundary in ("References", "REFERENCES:", "1. Introduction", "Abstract:", "\f"):
            text = f"Genome-wide analysis of crop yield\nDOI: {OTHER}\n{boundary}\n{TITLE}\n{DOI}"
            with self.subTest(boundary=boundary):
                result = m.assess_source_identity(RECORD, text)
                self.assertEqual(result["title_match"], "mismatch")
                self.assertEqual(result["status"], "conflict")
                self.assertEqual(result["observed_identifiers"], [OTHER])

    def test_scattered_title_words_and_reference_entries_are_not_titles(self):
        texts = [
            "Chest CT detection study\nNodule pulmonary learning on deep networks",
            f"Unrelated article\nExample A. {TITLE}. doi:{DOI}",
            f"Unrelated article\nWe discuss {TITLE} in this review.\n{DOI}",
        ]
        for text in texts:
            with self.subTest(text=text):
                # Even the former very permissive threshold cannot produce a match.
                self.assertNotEqual(m.classify_title_match(TITLE, text, 0.1), "match")
                self.assertNotEqual(m.assess_source_identity(RECORD, text)["status"], "consistent")

    def test_wrapped_title_unicode_punctuation_and_doi_url(self):
        text = ("Research Article\nDEEP LEARNING FOR PULMO-\n"
                "NARY NODULE DETECTION ON CHEST CT\nAlex Example\n"
                f"doi: https://doi.org/{DOI.upper()}\nAbstract: example")
        result = m.assess_source_identity({**RECORD, "first_author": "Example"}, text)
        self.assertEqual(result["status"], "consistent")
        self.assertEqual(result["first_author_match"], "match")
        self.assertEqual(m.classify_title_match("Café — α imaging", "CAFE: α imaging"), "match")

    def test_title_alone_and_doi_alone_need_review(self):
        self.assertEqual(m.assess_source_identity(RECORD, TITLE)["reason"], "identifier_not_found")
        result = m.assess_source_identity({"doi": DOI}, GOOD)
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(result["doi_match"], "match")
        self.assertEqual(result["reason"], "expected_title_missing")

    def test_related_versions_and_multiple_identifiers_need_review(self):
        result = m.assess_source_identity(RECORD, GOOD.replace(DOI, "10.48550/arXiv.2401.01234"))
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(result["reason"], "title_matches_other_identifier")
        result = m.assess_source_identity(RECORD, GOOD.replace("Abstract:", f"{OTHER}\nAbstract:"))
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(result["reason"], "multiple_identifiers")

    def test_arxiv_requested_version_must_not_be_silently_replaced(self):
        text = f"{TITLE}\narXiv:2401.01234v2 [cs.CV]\nAbstract: example"
        for doi in ("10.48550/arXiv.2401.01234", "arXiv:2401.01234v2"):
            self.assertEqual(m.assess_source_identity({**RECORD, "doi": doi}, text)["status"],
                             "consistent")
        wrong = m.assess_source_identity({**RECORD, "doi": "arXiv:2401.01234v1"}, text)
        self.assertEqual(wrong["status"], "unresolved")
        old = f"{TITLE}\narXiv:hep-th/9901001v2\nAbstract: example"
        self.assertEqual(m.assess_source_identity({**RECORD, "doi": "arXiv:hep-th/9901001"}, old)
                         ["status"], "consistent")

    def test_author_disagreement_cannot_be_hidden_by_title_and_doi(self):
        result = m.assess_source_identity({**RECORD, "first_author": "Someone Else"}, GOOD)
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(result["reason"], "first_author_not_found")

    def test_missing_extraction_and_unusable_front_matter_are_visible(self):
        for text in (None, "", "   "):
            self.assertEqual(m.assess_source_identity(RECORD, text)["status"], "unavailable")
        self.assertEqual(m.assess_source_identity(RECORD, "Abstract:\n" + GOOD)["reason"],
                         "front_matter_unavailable")
        self.assertEqual(m.classify_title_match("!!!", GOOD), "unavailable")
        with patch.object(m.shutil, "which", return_value=None):
            self.assertIsNone(m.extract_pdf_text(Path("not-read.pdf")))
        with patch.object(m.shutil, "which", return_value="pdftotext"), \
                patch.object(m.subprocess, "run", side_effect=subprocess.TimeoutExpired("pdftotext", 20)):
            self.assertIsNone(m.extract_pdf_text(Path("not-read.pdf")))

    def test_doi_suffix_punctuation(self):
        self.assertEqual(m.front_matter_identifiers("doi:10.1000/example(abc)."),
                         ["10.1000/example(abc)"])
        self.assertEqual(m.front_matter_identifiers("(https://doi.org/10.1000/example)."),
                         ["10.1000/example"])

    def test_optional_author_survives_each_worklist_format(self):
        inputs = {
            "tsv": f"DOI\tTitle\tFirstAuthor\n{DOI}\t{TITLE}\tExample\n",
            "csv": f"DOI,Title,First Author\n{DOI},{TITLE},Example\n",
            "md": f"| DOI | Title | First_Author |\n|---|---|---|\n|{DOI}|{TITLE}|Example|\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            for suffix, text in inputs.items():
                path = Path(tmp) / f"worklist.{suffix}"
                path.write_text(text)
                self.assertEqual(m.read_doi_file(path)[0]["first_author"], "Example")
            path = Path(tmp) / "dois.txt"
            path.write_text(DOI + "\n")
            self.assertEqual(m.read_doi_file(path), [{"doi": DOI, "pmid": "", "title": ""}])

    def test_report_preserves_retrieval_counts_and_binds_identity_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / (m.safe_doi_name(DOI) + ".pdf")
            write_pdf(pdf, GOOD.splitlines())
            report = m.build_report([RECORD], {DOI: ("skip", "existing")}, root, {DOI: GOOD})
            self.assertEqual(report["schema_version"], 2)
            self.assertEqual(report["counts"]["retrieved"], 1)
            self.assertEqual(report["counts"]["source_identity"]["consistent"], 1)
            item = report["items"][0]
            self.assertEqual(item["file_sha256"], hashlib.sha256(pdf.read_bytes()).hexdigest())
            before = item["file_sha256"]
            write_pdf(pdf, ["Unrelated synthetic replacement", OTHER])
            changed = m.build_report([RECORD], {DOI: ("skip", "existing")}, root, {DOI: GOOD},
                                     extracted_sha256_by_doi={DOI: before})
            self.assertEqual(changed["items"][0]["source_identity"]["status"], "unavailable")
            self.assertEqual(changed["items"][0]["source_identity"]["reason"],
                             "pdf_changed_during_assessment")
            self.assertNotEqual(changed["items"][0]["file_sha256"], before)
            pdf.unlink()
            missing = m.build_report([RECORD], {DOI: ("oa", "unpaywall")}, root, {DOI: GOOD})
            self.assertEqual(missing["counts"]["retrieved"], 1)  # resolver-result semantics unchanged
            self.assertEqual(missing["items"][0]["source_identity"]["reason"], "pdf_not_available")
            self.assertEqual(missing["items"][0]["file_sha256"], "")


@unittest.skipUnless(shutil.which("pdftotext"), "Poppler needed for actual PDF/CLI round trips")
class PDFIntegrationTests(unittest.TestCase):
    def test_real_pdfs_through_cli_distinguish_download_from_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdfs = root / "pdfs"
            pdfs.mkdir()
            requested_other = "10.1000/synthetic.other-request"
            for doi, lines in [
                (DOI, GOOD.splitlines()),
                (requested_other, ["Genome-wide analysis of crop yield", f"DOI: {OTHER}",
                                   "Abstract: unrelated synthetic example.", "References", TITLE,
                                   requested_other]),
            ]:
                write_pdf(pdfs / (m.safe_doi_name(doi) + ".pdf"), lines)
            worklist = root / "worklist.tsv"
            worklist.write_text(f"DOI\tTitle\n{DOI}\t{TITLE}\n{requested_other}\t{TITLE}\n")
            output = io.StringIO()
            with patch.object(sys, "argv", [str(ENGINE), str(worklist), "-o", str(pdfs),
                                            "-e", "test@example.com"]), \
                    patch.object(m.time, "sleep"), \
                    patch.object(m.urllib.request, "urlopen", side_effect=AssertionError("network forbidden")), \
                    contextlib.redirect_stdout(output):
                m.main()
            report = json.loads((pdfs / "retrieval_report.json").read_text())
            self.assertEqual(report["counts"]["retrieved"], 2)
            self.assertEqual(report["counts"]["source_identity"],
                             {"consistent": 1, "conflict": 1, "unresolved": 0, "unavailable": 0})
            self.assertIn("Source identity (advisory): consistent=1, conflict=1", output.getvalue())
            self.assertTrue((pdfs / (m.safe_doi_name(requested_other) + ".pdf")).is_file())

    def test_doi_only_cli_still_extracts_identifiers_and_reports_missing_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pdf(root / (m.safe_doi_name(DOI) + ".pdf"), GOOD.splitlines())
            worklist = root / "dois.txt"
            worklist.write_text(DOI + "\n")
            with patch.object(sys, "argv", [str(ENGINE), str(worklist), "-o", str(root),
                                            "-e", "test@example.com"]), \
                    patch.object(m.time, "sleep"), \
                    patch.object(m.urllib.request, "urlopen", side_effect=AssertionError("network forbidden")), \
                    contextlib.redirect_stdout(io.StringIO()):
                m.main()
            item = json.loads((root / "retrieval_report.json").read_text())["items"][0]
            self.assertEqual(item["source_identity"]["observed_identifiers"], [DOI])
            self.assertEqual(item["source_identity"]["status"], "unresolved")
            self.assertEqual(item["source_identity"]["reason"], "expected_title_missing")


if __name__ == "__main__":
    unittest.main(verbosity=2)

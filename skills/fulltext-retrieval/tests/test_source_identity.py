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

    def test_supplement_preface_and_contents_are_not_the_work(self):
        # Each file carries the work's own title and DOI on page 1, which is exactly why
        # title + DOI agreement accepted it: an SI file and a book preface were once
        # counted as successful retrievals of the article and the book.
        for heading in ("Supplementary Information", "SUPPLEMENTARY MATERIAL",
                        "Supplementary Appendix", "Supplementary information for:",
                        "Electronic Supplementary Material", "Preface", "Front Matter",
                        "Table of Contents"):
            with self.subTest(heading=heading):
                result = m.assess_source_identity(RECORD, f"{heading}\n{GOOD}")
                self.assertEqual(result["status"], "unresolved")
                self.assertEqual(result["reason"], "supplement_or_front_matter")

    def test_supplement_words_inside_a_real_article_are_not_markers(self):
        # Precision guard: an article that mentions its supplement, starts its title with
        # "Supplemental", or sits under an Elsevier "Contents lists available" banner is
        # still the work.
        mentions = GOOD.replace("Abstract:", "Supplementary material is available online.\nAbstract:")
        self.assertEqual(m.assess_source_identity(RECORD, mentions)["status"], "consistent")
        banner = "Contents lists available at ScienceDirect\n" + GOOD
        self.assertEqual(m.assess_source_identity(RECORD, banner)["status"], "consistent")
        title = "Supplemental Oxygen after Synthetic Surgery"
        text = f"{title}\nAlex Example\nhttps://doi.org/{DOI}\nAbstract: example"
        self.assertEqual(m.assess_source_identity({**RECORD, "title": title}, text)["status"],
                         "consistent")

    def test_retraction_and_correction_notices_are_not_the_work(self):
        # A notice prints the original work's title and DOI under its own heading, so
        # title + DOI agreement once accepted the notice as the article itself.
        for heading in ("RETRACTION NOTICE", "Retraction", "Retraction Note:",
                        "Notice of Retraction", "Retracted Article", "Erratum", "Errata",
                        "Correction", "Correction to:", "Corrigendum",
                        "Expression of Concern", "EXPRESSION OF CONCERN:"):
            with self.subTest(heading=heading):
                body = GOOD.replace("Abstract:", "This article has been retracted.")
                result = m.assess_source_identity(RECORD, f"{heading}\n{body}")
                self.assertEqual(result["status"], "unresolved")
                self.assertEqual(result["reason"], "correction_or_retraction_notice")

    def test_correction_words_inside_a_real_article_are_not_markers(self):
        # Precision guard: a title that starts with "Correction of", or a sentence that
        # mentions an erratum or a retraction, is still the work.
        title = "Correction of Motion Artifacts in Synthetic Chest CT"
        text = f"{title}\nAlex Example\nhttps://doi.org/{DOI}\nAbstract: example"
        self.assertEqual(m.assess_source_identity({**RECORD, "title": title}, text)["status"],
                         "consistent")
        for line in ("Correction of this article was not needed.",
                     "Retraction Watch database was searched.",
                     "Erratum published separately in a later issue."):
            with self.subTest(line=line):
                mentions = GOOD.replace("Abstract:", f"{line}\nAbstract:")
                self.assertEqual(m.assess_source_identity(RECORD, mentions)["status"],
                                 "consistent")

    def test_a_conflict_stays_a_conflict_with_a_supplement_heading(self):
        text = f"Supplementary Information\nGenome-wide analysis of crop yield\nDOI: {OTHER}"
        self.assertEqual(m.assess_source_identity(RECORD, text)["status"], "conflict")

    def test_page_count_is_recorded_for_the_file_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_pdf(root / (m.safe_doi_name(DOI) + ".pdf"), GOOD.splitlines())
            report = m.build_report([RECORD], {DOI: ("skip", "existing")}, root, {DOI: GOOD},
                                    page_count_by_doi={DOI: 3})
            self.assertEqual(report["items"][0]["page_count"], 3)
            none = m.build_report([RECORD], {DOI: ("fail", "")}, root, {}, page_count_by_doi={DOI: 3})
            self.assertIsNone(none["items"][0]["page_count"])
        with patch.object(m.shutil, "which", return_value=None):
            self.assertIsNone(m.pdf_page_count(Path("not-read.pdf")))

    def test_pmcid_lookup_uses_the_documented_id_converter_root(self):
        # NCBI documents https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/ with
        # required tool/email; the old /pmc/utils/idconv/v1.0/ root was reported returning
        # non-JSON, which the lookup swallowed. No network: urlopen is replaced.
        seen = []

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def fake_urlopen(req, timeout=None):
            seen.append(req.full_url)
            return Resp(json.dumps({"status": "ok", "records": [
                {"doi": "10.0000/example.1", "pmcid": "PMC0000001", "requested-id": "10.0000/example.1"}]}).encode())

        with patch.object(m.urllib.request, "urlopen", side_effect=fake_urlopen):
            self.assertEqual(m.id_to_pmcid("10.0000/example.1", "test@example.com"), "PMC0000001")
        self.assertTrue(seen[0].startswith("https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?"))
        self.assertIn("format=json", seen[0])
        self.assertIn("tool=", seen[0])
        self.assertIn("email=test%40example.com", seen[0])

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

    def test_manual_list_carries_pmcid_and_article_url_when_pdf_fetch_fails(self):
        # A PMCID was resolved but every PDF route failed: manual_needed.txt listed only the DOI,
        # so the user could not tell a PubMed Central article from a subscription one.
        pmc = "PMC1234567"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worklist = root / "dois.txt"
            worklist.write_text(f"{DOI}\n{OTHER}\n")
            argv = [str(ENGINE), str(worklist), "-o", str(root), "-e", "test@example.com"]
            with patch.object(sys, "argv", argv), \
                    patch.object(m.time, "sleep"), \
                    patch.object(m.urllib.request, "urlopen", side_effect=AssertionError("network forbidden")), \
                    patch.object(m, "unpaywall_lookup", return_value=None), \
                    patch.object(m, "id_to_pmcid", side_effect=lambda ident, _e: pmc if ident == DOI else None), \
                    patch.object(m, "download_pmc_pdf", return_value=False), \
                    patch.object(m, "openalex_lookup", return_value=[]), \
                    patch.object(m, "crossref_lookup", return_value=[]), \
                    patch.object(m, "download_from_landing", return_value=False), \
                    contextlib.redirect_stdout(io.StringIO()):
                m.main()
            rows = [ln for ln in (root / "manual_needed.txt").read_text().splitlines()
                    if ln and not ln.startswith("#")]
            self.assertIn(f"{DOI}\t{pmc}\thttps://pmc.ncbi.nlm.nih.gov/articles/{pmc}/", rows)
            self.assertIn(OTHER, rows)  # no PMCID resolved: the DOI alone, as before


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
            if shutil.which("pdfinfo"):
                self.assertEqual({i["page_count"] for i in report["items"]}, {1})

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

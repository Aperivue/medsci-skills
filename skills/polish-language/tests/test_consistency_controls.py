#!/usr/bin/env python3
"""Normal prose controls plus matching failure cases; all inputs are synthetic."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / 'scripts/lint_consistency.py'
spec = importlib.util.spec_from_file_location('linter', SCRIPT)
linter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linter)


class ConsistencyControls(unittest.TestCase):
    def test_normal_us_and_uk_manuscripts_are_clean_and_unchanged(self):
        for name in ('consistent_us.md', 'consistent_uk.md'):
            with self.subTest(name=name):
                path = SKILL / 'scripts/lint_challenge/fixture' / name
                before = path.read_bytes()
                run = subprocess.run([sys.executable, str(SCRIPT), str(path), '--strict'],
                                     capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertIn('Summary: 0 issue(s) across 0 category(ies).', run.stdout)
                self.assertEqual(path.read_bytes(), before)

    def test_one_covid_form_is_not_a_mix(self):
        for text in ('COVID-19', 'COVID19', 'Covid-19', 'COVID-19 and COVID-19'):
            self.assertEqual(linter.check_hyphenation([text]), [], text)

    def test_actual_covid_spelling_and_case_mixes_still_fire(self):
        for text in ('COVID-19 and COVID19', 'COVID-19 and Covid-19'):
            found = linter.check_hyphenation([text])
            self.assertEqual(len(found), 1)
            self.assertIn('COVID-19', found[0][1])

    def test_grammatically_distinct_forms_can_coexist(self):
        self.assertEqual(linter.check_hyphenation([
            'Follow-up continued. We will follow up with the team.',
            'Long-term monitoring helps in the long term.']), [])

    def test_closed_form_mixes_still_fire(self):
        for text in ('Follow-up and followup', 'Long-term and longterm',
                     'Healthcare and health care'):
            self.assertEqual(len(linter.check_hyphenation([text])), 1, text)

    def test_defined_numeric_and_hyphenated_abbreviations_remain_whole(self):
        for abbr in ('CT', 'MRI', 'BRCA1', 'COVID-19', 'COVID19'):
            self.assertEqual(linter.check_abbreviations([
                f'Expanded name ({abbr}) was introduced.', f'{abbr} was used.']), [])

    def test_missing_definitions_are_not_hidden(self):
        found = linter.check_abbreviations(['COVID-19 was discussed.', 'COVID-19 was mentioned again.'])
        self.assertEqual(found, [(1, '"COVID-19" used 2x but never defined')])
        self.assertEqual(linter.check_abbreviations(['Expanded name (CT).']),
                         [(1, '"CT" defined but never used')])

    def test_definition_order_and_duplicate_definition_still_fire(self):
        found = linter.check_abbreviations(['CT was used.', 'Computed tomography (CT).',
                                            'Computed tomography (CT) was mentioned again.'])
        self.assertTrue(any('before its definition' in msg for _, msg in found))
        self.assertTrue(any('more than once' in msg for _, msg in found))

    def test_designators_and_measurements_are_not_counts(self):
        self.assertEqual(linter.check_small_numbers([
            'Figure 2 shows type 2 diabetes. The measurement was 5 mm.']), [])
        self.assertEqual(len(linter.check_small_numbers(['There were 3 samples.'])), 1)

    def test_a_defect_added_to_normal_prose_changes_strict_exit_only(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'text.md'
            path.write_text('The value was 5mg.\n', encoding='utf-8')
            before = path.read_bytes()
            for extra, expected in [((), 0), (('--strict',), 1)]:
                run = subprocess.run([sys.executable, str(SCRIPT), str(path), *extra],
                                     capture_output=True, text=True)
                self.assertEqual(run.returncode, expected)
                self.assertIn('insert a space', run.stdout)
                self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

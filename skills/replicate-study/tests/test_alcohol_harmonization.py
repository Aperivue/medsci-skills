#!/usr/bin/env python3
"""Regression test: the alcohol row means the same thing in both harmonization tables.

origin/main shipped an alcohol mapping where 'Occasional' meant a past-year abstainer in
KNHANES/NHANES but a light current drinker in CHNS (U41-based), and the NHANES side mapped
only ALQ121, so lifetime non-drinkers could not be derived. The checks below read the
structured columns (nhanes_var) and the shared-scheme definition, and are run against
both the shipped references (must be clean) and a frozen copy of the origin/main rows
(must be flagged).
"""
from __future__ import annotations

import csv
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
REFS = HERE.parent / "references"
MAIN_ROWS = HERE / "fixtures" / "main_alcohol_rows"
TABLES = ("harmonization_knhanes_nhanes.csv", "harmonization_3country.csv")
CONCEPT_EN = "Alcohol frequency"
SCHEME_MARK = "Shared alcohol scheme"


def alcohol_row(path: Path) -> dict:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r.get("concept_en") == CONCEPT_EN]
    if len(rows) != 1:
        raise ValueError(f"{path}: expected exactly one '{CONCEPT_EN}' row, found {len(rows)}")
    return rows[0]


def scheme_text(notes: str) -> str | None:
    """The shared-scheme definition: from the marker up to the first per-country clause."""
    start = notes.find(SCHEME_MARK)
    if start < 0:
        return None
    end = notes.find(" KR:", start)
    return notes[start:end if end >= 0 else len(notes)].strip()


def country_clause(notes: str, tag: str) -> str | None:
    start = notes.find(f"{tag}:")
    if start < 0:
        return None
    ends = [notes.find(f" {t}:", start + 1) for t in ("KR", "US", "CN") if t != tag]
    ends = [e for e in ends if e > start]
    return notes[start:min(ends) if ends else len(notes)]


def problems(ref_dir: Path) -> list[str]:
    found: list[str] = []
    rows = {name: alcohol_row(ref_dir / name) for name in TABLES}
    schemes = {}
    for name, row in rows.items():
        if "ALQ111" not in [v.strip() for v in row["nhanes_var"].split("+")]:
            found.append(f"{name}: NHANES alcohol row does not map ALQ111 (lifetime never not derivable)")
        schemes[name] = scheme_text(row["harmonization_notes"])
        if schemes[name] is None:
            found.append(f"{name}: alcohol row has no '{SCHEME_MARK}' definition")
        for tag in ("KR", "US"):
            if country_clause(row["harmonization_notes"], tag) is None:
                found.append(f"{name}: alcohol row has no {tag}: mapping onto the shared scheme")
    if None not in schemes.values() and len(set(schemes.values())) != 1:
        found.append("alcohol shared-scheme definition differs between the two tables")
    cn = country_clause(rows["harmonization_3country.csv"]["harmonization_notes"], "CN")
    if cn is None:
        found.append("harmonization_3country.csv: alcohol row has no CN: mapping onto the shared scheme")
    else:
        current = [seg for seg in cn.split(";") if "Current =" in seg]
        if not current or "U40==1" not in current[0]:
            found.append("harmonization_3country.csv: CHNS 'Current' is not defined by past-year drinking (U40==1)")
    return found


class AlcoholHarmonization(unittest.TestCase):
    def test_shipped_references_are_consistent(self):
        # Negative control: the references the skill ships must be clean.
        self.assertEqual(problems(REFS), [])

    def test_main_rows_are_flagged(self):
        # Positive case: the origin/main alcohol rows that mislabelled categories.
        found = problems(MAIN_ROWS)
        self.assertTrue(any("ALQ111" in p for p in found), found)
        self.assertTrue(any("shared alcohol scheme" in p.lower() for p in found), found)
        self.assertTrue(any("CN:" in p for p in found), found)

    def test_scheme_drift_between_tables_is_flagged(self):
        # Positive case: tables that each carry a scheme but disagree on it.
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmpd = Path(tmp)
            for name in TABLES:
                shutil.copy(REFS / name, tmpd / name)
            path = tmpd / "harmonization_3country.csv"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("Past-year abstainer = no drinking in the past 12 months",
                                         "Past-year abstainer = drinking less than weekly", 1),
                            encoding="utf-8")
            self.assertIn("alcohol shared-scheme definition differs between the two tables",
                          problems(tmpd))

    def test_missing_row_is_an_error(self):
        # Unrecognised input names the file instead of passing silently.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.csv"
            path.write_text("domain,concept,concept_en\nx,y,z\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                alcohol_row(path)
            self.assertIn("t.csv", str(ctx.exception))


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] not in ("-v", "--verbose"):
        target = Path(sys.argv[1])
        try:
            issues = problems(target)
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(2)
        for issue in issues:
            print(f"FLAG: {issue}")
        print("clean" if not issues else f"{len(issues)} problem(s)")
        sys.exit(1 if issues else 0)
    unittest.main()

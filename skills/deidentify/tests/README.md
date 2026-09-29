# Deidentify Test Fixtures

All CSV files in this directory contain **synthetic test data only**.
No real patient or person is represented.

- **Names** (`김철수`, `이영희`, `박민수`, etc.) are common Korean placeholder
  names equivalent to "John Doe" / "Jane Doe" in English. They were chosen
  precisely because they are generic enough to be unattributable to any
  real individual.
- **RRN (주민번호)** values follow the public format specification but the
  digits are arbitrary and do not validate against the official checksum
  algorithm used by the Korean civil registry.
- **Phone numbers**, **addresses**, **emails**, **chart numbers**, and
  **diagnoses** are all constructed for the purpose of exercising the
  PHI detector regexes shipped with `/deidentify`.

These fixtures exist to verify that the de-identifier:
1. Detects the PHI patterns the skill claims to detect.
2. Leaves non-PHI fields (clinical measurements, dates of routine
   nature) untouched.
3. Handles edge cases (mixed date formats, half-width vs full-width
   digits, comma vs newline separators, missing fields).

If you need to add a new fixture, follow the same rule: every value must
be either a published format example or a constructed synthetic string.
Never copy real EMR data into this directory, even for one-off debugging.

## Italian PHI fixture (`test_phi_italian.csv`)

Exercises the `it` locale pack (see `../locales/it.json` and issue #116):

- **Codice fiscale** values follow the public 16-character format specification,
  including one omocodic variant (digit positions written with the
  `L M N P Q R S T U V` substitutions the Agenzia delle Entrate uses when two
  people would otherwise share a code). Check characters are deliberately
  invalid, so none of these can be a real person's code.
- **Phone numbers** (`333 123 4567`, `+39 02 1234567`, `06 1234567`) are
  sequential placeholder digits in valid Italian formats.
- **Names** (`Marco`, `Giulia`, `Anna`) are generic first names equivalent to
  "John Doe" / "Jane Doe" — unattributable to any real individual.
- **Addresses** (`Via Roma 12, Milano`, …) are landmark-style placeholder
  streets, not real residences.
- **Dates of birth** are arbitrary; **diagnoses** (`diabete tipo 2`, …) and
  **measurements** (`5.6`, …) are filler values included so the fixture also
  asserts non-PHI columns stay `SAFE`.

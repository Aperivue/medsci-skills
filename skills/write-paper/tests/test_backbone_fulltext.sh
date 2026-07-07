#!/usr/bin/env bash
# Regression test for skills/write-paper/scripts/gate_backbone_fulltext.py — the
# pre-draft backbone full-text readiness gate (issues #4, #8). Synthetic fixtures.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/write-paper/scripts/gate_backbone_fulltext.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-52s exit=%s\n' "$label" "$actual"; pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"; fail=$((fail + 1))
  fi
}

# project.yaml with a declared backbone
cat > "$TMP/project.yaml" <<'YAML'
paper_type: diagnostic_accuracy
backbone_article: smith2023ctai
YAML

# refs.bib mapping the citekey to a DOI
cat > "$TMP/refs.bib" <<'BIB'
@article{smith2023ctai,
  title = {A CT AI validation study},
  author = {Smith, Jane},
  doi = {10.1000/ctai.2023.42},
  year = {2023}
}
BIB

mkdir -p "$TMP/pdfs"

# a SUBSTANTIAL extracted full text (well above the 3000-byte floor)
{ echo "# A CT AI validation study (10.1000/ctai.2023.42)"; \
  for i in $(seq 1 200); do echo "Full-text paragraph line $i describing methods, cohort, and results in detail."; done; } \
  > "$TMP/pdfs/smith2023ctai.md"

# 1) backbone full text present + substantial -> ready, exit 0
python3 "$V" --project "$TMP/project.yaml" --refs "$TMP/refs.bib" --fulltext-dir "$TMP/pdfs" --strict > /dev/null 2>&1
ck "present + substantial backbone -> ready" 0 "$?"

# 2) no extracted file at all -> MISSING, exit 1
rm -f "$TMP/pdfs/smith2023ctai.md"
python3 "$V" --project "$TMP/project.yaml" --refs "$TMP/refs.bib" --fulltext-dir "$TMP/pdfs" --strict > /dev/null 2>&1
ck "missing backbone full text -> exit 1" 1 "$?"

# 3) an abstract-sized stub (thin) -> THIN, exit 1
printf '# A CT AI validation study\nAbstract only: a short summary.\n' > "$TMP/pdfs/smith2023ctai.md"
python3 "$V" --project "$TMP/project.yaml" --refs "$TMP/refs.bib" --fulltext-dir "$TMP/pdfs" --strict > /dev/null 2>&1
ck "thin (abstract-only) backbone -> exit 1" 1 "$?"

# 4) match by DOI when the file is not named after the citekey
rm -f "$TMP/pdfs/smith2023ctai.md"
{ echo "# Paper (doi 10.1000/ctai.2023.42)"; for i in $(seq 1 200); do echo "Body line $i with detailed methods and results."; done; } \
  > "$TMP/pdfs/downloaded_42.md"
python3 "$V" --project "$TMP/project.yaml" --refs "$TMP/refs.bib" --fulltext-dir "$TMP/pdfs" --strict > /dev/null 2>&1
ck "resolves backbone by DOI in file content" 0 "$?"

# 5) no backbone declared -> UNDECLARED warn, exit 0 (not a hard block)
cat > "$TMP/project_nobb.yaml" <<'YAML'
paper_type: diagnostic_accuracy
YAML
python3 "$V" --project "$TMP/project_nobb.yaml" --fulltext-dir "$TMP/pdfs" --strict > /dev/null 2>&1
ck "undeclared backbone warns but does not fail" 0 "$?"

# 6) explicit --fulltext path (authoritative)
python3 "$V" --backbone smith2023ctai --fulltext "$TMP/pdfs/downloaded_42.md" --strict > /dev/null 2>&1
ck "explicit --fulltext path passes" 0 "$?"

# 7) the MISSING verdict is emitted in the report
rm -f "$TMP"/pdfs/*.md
OUT="$(python3 "$V" --project "$TMP/project.yaml" --refs "$TMP/refs.bib" --fulltext-dir "$TMP/pdfs" 2>&1)"
echo "$OUT" | grep -q BACKBONE_FULLTEXT_MISSING
ck "MISSING verdict reported" 0 "$?"

echo "----"
echo "test_backbone_fulltext: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

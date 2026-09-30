#!/usr/bin/env bash
# Regression test: a Markdown `## References` heading opens the reference list.
#
# The reference-section finder recognised only a bare "References" line. In a .md/.qmd manuscript
# the heading is `## References` (Quarto: `# References {.unnumbered}`), which did not match, so the
# whole file was parsed: the title, body paragraphs and every `- ` bullet became extra references,
# all UNVERIFIED, and `--strict` could never pass. A heading also ends where the next heading of
# the same or a higher level begins, so the Tables and Figure Legends sections that follow the
# list in a manuscript are not read as references either.
#
# Each case is a two-reference manuscript; the audit must hold exactly those two. The first case,
# a bare line with the list last, is the control for the form that already worked. Network-free:
# runs with --offline.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/verify-refs/scripts/verify_refs.py"
[[ -f "$V" ]] || { echo "ENV-ERR: verify_refs.py missing" >&2; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-58s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-58s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# $1 = case name, $2 = the heading line, $3 = "tail" to follow the list with Tables and Figure
# Legends sections. Writes a manuscript around it and prints
# "<total>:<first raw starts with '1.'>" from the audit.
run_case() {
  local dir="$TMP/$1"
  mkdir -p "$dir"
  cat > "$dir/manuscript.md" <<EOF
# A synthetic manuscript title used only by this test

## Introduction

Synthetic body text describing a study that does not exist, long enough to look like a reference line [1].

## Methods

- Participants were drawn from an invented registry of imaginary patients for this test.
- Images were read by two fictional readers who were blinded to every invented outcome.

$2

1. Doe J, Roe R. An invented title about imaginary outcomes in fictional cohorts. J Synth Med. 2020;1:1-2. doi:10.0000/synthetic.0001
2. Poe E, Loe L. Another invented title about made-up findings in a pretend population. J Synth Med. 2021;2:3-4. doi:10.0000/synthetic.0002
EOF
  [ "${3:-}" = "tail" ] && cat >> "$dir/manuscript.md" <<EOF

## Tables

- Data are the number of invented participants with the percentage in parentheses.

## Figure Legends

- Figure 1. A synthetic flow diagram of the invented cohort used only in this test.
EOF
  python3 "$V" "$dir/manuscript.md" --offline --project-root "$dir" >/dev/null 2>&1
  python3 - "$dir/qc/reference_audit.json" <<'PY'
import json, sys
try:
    a = json.load(open(sys.argv[1], encoding="utf-8"))
except OSError:
    print("no-audit"); sys.exit(0)
recs = a["records"]
print(f"{a['total_references']}:{bool(recs) and recs[0]['raw'].startswith('1.')}")
PY
}

ck "bare References line, list last (control)" "2:True" "$(run_case bare 'References')"
ck "## References, list last"               "2:True" "$(run_case atx2 '## References')"
ck "## References, then Tables and Legends" "2:True" "$(run_case atx2_tail '## References' tail)"
ck "# References {.unnumbered} (Quarto)"    "2:True" "$(run_case quarto '# References {.unnumbered}')"
ck "### **References**"                     "2:True" "$(run_case bold_atx '### **References**' tail)"
ck "## Bibliography"                        "2:True" "$(run_case bibliography '## Bibliography' tail)"
ck "bare References line, then Tables"      "2:True" "$(run_case bare_tail 'References' tail)"

echo
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"

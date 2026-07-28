#!/usr/bin/env bash
# Per-publisher fidelity test for the held-out corpus renderer.
#
# WHY PER PUBLISHER AND NOT OVERALL
#   Publishers disagree about WHERE a disclosure lives in JATS. A renderer that knows one
#   publisher's location drops the others' — and a dropped section does not read as a missing
#   signal, it reads as a FIRE. So the corpus acquires a bias correlated with JOURNAL rather than
#   with quality, which for a benchmark is worse than noise: it is systematic, and it aligns with
#   a variable nobody thought to control.
#
#   An "overall" fidelity check passes as soon as one shape works. This one asserts each shape
#   separately, so the failure names the publisher.
#
# Every fixture below is a synthetic JATS document written for this test. Network-free.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
R="$HERE/render_jats.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

# $1 name, $2 rendered file, $3.. required strings
must_contain() {
  local who="$1" f="$2"; shift 2
  for needle in "$@"; do
    grep -qF -- "$needle" "$f" || fail "$who: renderer dropped \"$needle\""
  done
}
# A label that a line-anchored section finder must be able to see: it has to START a line.
must_start_line() {
  local who="$1" f="$2"; shift 2
  for needle in "$@"; do
    grep -qE "^[*]{0,2}${needle}" "$f" \
      || fail "$who: \"$needle\" exists but not at line start — a line-anchored finder cannot see it"
  done
}

# ---------------------------------------------------------------------------------------------
# JAMA shape: everything lives in <author-notes> as sibling <fn> blocks. Flattening them into one
# paragraph is what put every label mid-line in the first corpus.
# ---------------------------------------------------------------------------------------------
cat > "$TMP/jama.xml" <<'EOF'
<article><front><article-meta>
<title-group><article-title>A Randomized Trial of Something</article-title></title-group>
<contrib-group>
  <contrib contrib-type="author"><name><surname>Guo</surname><given-names>Lixin</given-names></name></contrib>
  <contrib contrib-type="author"><name><surname>Xi</surname><given-names>Yue</given-names></name></contrib>
</contrib-group>
<abstract><sec><title>Question</title><p>Does it work?</p></sec></abstract>
<author-notes>
  <fn><p>Funding/Support: Supported by grant 12345.</p></fn>
  <fn><p>Data Sharing Statement: See Supplement 3.</p></fn>
  <fn><p>Conflict of Interest Disclosures: None reported.</p></fn>
</author-notes>
</article-meta></front>
<body><sec><title>Methods</title><p>We randomized 405 adults<xref ref-type="bibr">12</xref>.</p></sec></body>
<back><ref-list><ref><mixed-citation>Smith J. A paper. J Med. 2024;1:1-9.</mixed-citation></ref></ref-list></back>
</article>
EOF
python3 "$R" --xml "$TMP/jama.xml" --out "$TMP/jama.md" >/dev/null
must_contain "jama" "$TMP/jama.md" \
  "A Randomized Trial of Something" "Lixin Guo, Yue Xi" \
  "Funding/Support:" "Data Sharing Statement:" "Conflict of Interest Disclosures:" \
  "We randomized 405 adults" "Smith J. A paper."
must_start_line "jama" "$TMP/jama.md" \
  "Funding/Support:" "Data Sharing Statement:" "Conflict of Interest Disclosures:"
# The xref number must NOT be inlined into the sentence — that is our converter writing citations.
grep -qF "405 adults12" "$TMP/jama.md" \
  && fail "jama: an <xref> was inlined into the prose — a citation-density check would measure us"

# ---------------------------------------------------------------------------------------------
# PLOS shape: funding in <funding-group>, data availability in <custom-meta>. Neither is a section
# and neither is in <body>, so a body-only renderer reports both as absent.
# ---------------------------------------------------------------------------------------------
cat > "$TMP/plos.xml" <<'EOF'
<article><front><article-meta>
<title-group><article-title>An Open Access Study</article-title></title-group>
<contrib-group><contrib contrib-type="author"><name><surname>Doe</surname><given-names>Jane</given-names></name></contrib></contrib-group>
<abstract><p>Unsectioned abstract text.</p></abstract>
<funding-group><funding-statement>This work was funded by NIH R01.</funding-statement></funding-group>
<custom-meta-group>
  <custom-meta><meta-name>data-availability</meta-name><meta-value>All data are within the manuscript.</meta-value></custom-meta>
  <custom-meta><meta-name>pmc-simple-viewer</meta-name><meta-value>true</meta-value></custom-meta>
</custom-meta-group>
</article-meta></front>
<body><sec><title>Results</title><p>Everything worked.</p></sec></body>
</article>
EOF
python3 "$R" --xml "$TMP/plos.xml" --out "$TMP/plos.md" >/dev/null
must_contain "plos" "$TMP/plos.md" \
  "An Open Access Study" "Jane Doe" "Unsectioned abstract text." \
  "This work was funded by NIH R01." "All data are within the manuscript."
must_start_line "plos" "$TMP/plos.md" "Data Availability:"
grep -qF "pmc-simple-viewer" "$TMP/plos.md" \
  && fail "plos: PMC housekeeping metadata leaked into the corpus — detectors would read our pipeline"

# ---------------------------------------------------------------------------------------------
# Elsevier shape: "Declaration of competing interest" is a BACK SECTION, not author-notes.
# ---------------------------------------------------------------------------------------------
cat > "$TMP/elsevier.xml" <<'EOF'
<article><front><article-meta>
<title-group><article-title>A Systematic Review</article-title></title-group>
<contrib-group><contrib contrib-type="author"><name><surname>Roe</surname><given-names>Richard</given-names></name></contrib></contrib-group>
</article-meta></front>
<body><sec><title>Introduction</title><p>Background prose.</p></sec></body>
<back>
  <sec><title>Declaration of competing interest</title><p>The authors declare none.</p></sec>
  <ack><p>We thank the librarians.</p></ack>
  <ref-list><ref><mixed-citation>Roe R. Prior work. 2023.</mixed-citation></ref></ref-list>
</back>
</article>
EOF
python3 "$R" --xml "$TMP/elsevier.xml" --out "$TMP/elsevier.md" >/dev/null
must_contain "elsevier" "$TMP/elsevier.md" \
  "Declaration of competing interest" "The authors declare none." "We thank the librarians." \
  "Roe R. Prior work."
must_start_line "elsevier" "$TMP/elsevier.md" "## Declaration of competing interest"

# ---------------------------------------------------------------------------------------------
# MDPI shape: contributions in a back <fn-group>, with an EM DASH inside the CRediT term.
# The dash is ledger C5 — the term scan shredded "Writing—original draft" at the dash.
# ---------------------------------------------------------------------------------------------
cat > "$TMP/mdpi.xml" <<'EOF'
<article><front><article-meta>
<title-group><article-title>A Radiomics Study</article-title></title-group>
<contrib-group>
  <contrib contrib-type="author"><name><surname>Rossi</surname><given-names>Paolo</given-names></name></contrib>
</contrib-group>
</article-meta></front>
<body><sec><title>Methods</title><p>Features were extracted.</p></sec></body>
<back>
  <fn-group>
    <fn><p>Author Contributions: Conceptualization, P.R.; Writing—original draft preparation, P.R.</p></fn>
    <fn><p>Data Availability Statement: Data are available on request.</p></fn>
  </fn-group>
</back>
</article>
EOF
python3 "$R" --xml "$TMP/mdpi.xml" --out "$TMP/mdpi.md" >/dev/null
must_contain "mdpi" "$TMP/mdpi.md" \
  "Author Contributions:" "Writing—original draft preparation" "Data Availability Statement:"
must_start_line "mdpi" "$TMP/mdpi.md" "Author Contributions:" "Data Availability Statement:"
grep -qF "Writing—original draft" "$TMP/mdpi.md" \
  || fail "mdpi: the em dash inside a CRediT term did not survive rendering"

# ---------------------------------------------------------------------------------------------
# BMC / Springer shape: declarations as nested back sections under one parent.
# ---------------------------------------------------------------------------------------------
cat > "$TMP/bmc.xml" <<'EOF'
<article><front><article-meta>
<title-group><article-title>A Cohort Study</article-title></title-group>
<contrib-group>
  <contrib contrib-type="author"><name><surname>Kim</surname><given-names>Minji</given-names></name></contrib>
  <contrib contrib-type="author"><collab>The Consortium Group</collab></contrib>
</contrib-group>
</article-meta></front>
<body><sec><title>Discussion</title><p>Interpretation.</p></sec></body>
<back><sec><title>Declarations</title>
  <sec><title>Availability of data and materials</title><p>Datasets are in the repository.</p></sec>
  <sec><title>Competing interests</title><p>The authors declare no competing interests.</p></sec>
</sec></back>
</article>
EOF
python3 "$R" --xml "$TMP/bmc.xml" --out "$TMP/bmc.md" >/dev/null
must_contain "bmc" "$TMP/bmc.md" \
  "Availability of data and materials" "Datasets are in the repository." \
  "Competing interests" "The Consortium Group"
# A heading must never be fused to the paragraph that follows it. This is not hypothetical: the
# throwaway renderer that built the first corpus emitted
#     Competing interestsThe authors declare that they have no competing interests.
# and check_disclosure_availability anchors its section match with \b, which cannot fire between
# "s" and "T". Four of twelve papers were therefore reported as having NO conflict-of-interest
# statement while plainly carrying one — a false positive manufactured by our own converter and
# indistinguishable, at the point of reading, from a detector defect (the Class B trap).
# Found by the metamorphic probe, which is the only thing that ever looked.
for H in "Competing interests" "Availability of data and materials"; do
  grep -qE "^#{2,4} ${H}\s*$" "$TMP/bmc.md" \
    || fail "bmc: \"${H}\" is not a heading on its own line — a fused heading is invisible to a \\b-anchored section finder"
done
# And prove the assertion has teeth. Mutating THIS renderer cannot easily produce a fused heading
# (it joins its parts on newlines), so the check is verified against the defect directly: the exact
# byte sequence the old converter produced must fail the same grep. An assertion never shown to
# fail is an assertion nobody has tested.
printf 'Competing interestsThe authors declare that they have no competing interests.\n' \
  > "$TMP/fused.md"
grep -qE "^#{2,4} Competing interests\s*$" "$TMP/fused.md" \
  && fail "the heading-boundary check passes on a FUSED heading — it detects nothing"

# ---------------------------------------------------------------------------------------------
# The regression that started it: a <body>-only renderer must FAIL this suite, not squeak through.
# Proven by rendering a JAMA fixture and asserting the disclosure block is what carries the labels
# — if a future refactor drops <author-notes>, every assertion above fires, naming the publisher.
# ---------------------------------------------------------------------------------------------
python3 - "$TMP/jama.md" <<'PY' || exit 1
import sys
md = open(sys.argv[1]).read()
labels = ["Funding/Support:", "Data Sharing Statement:", "Conflict of Interest Disclosures:"]
lines = [ln for ln in md.splitlines() if any(ln.startswith(x) for x in labels)]
assert len(lines) == 3, \
    "author-notes were flattened: %d of 3 labels start their own line" % len(lines)
PY

echo "PASS: renderer preserves byline, abstract, body, author-notes (unflattened), funding-group,"
echo "      custom-meta, back sections, fn-groups and references across 5 publisher shapes."

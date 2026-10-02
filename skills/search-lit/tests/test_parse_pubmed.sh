#!/usr/bin/env bash
# Regression test: parse_pubmed.py keeps the whole title and abstract when PubMed marks them up.
#
# PubMed efetch XML carries inline markup inside <ArticleTitle> and <AbstractText>: italic species
# names, sub/superscripts. `findtext()` and `.text` return only the text before the first child
# element, so "Eradication of <i>Helicobacter pylori</i> infection." became
# `title = {Eradication of },` in an entry stamped `verified = {true}`, and an abstract reading
# "CO<sub>2</sub> levels rose." became "CO". The pre-fix parser fails checks 1-4; checks 5-6 are
# the negative control (a title with no markup is unchanged).
#
# No network: the XML is synthetic and inline.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PARSER="$HERE/../references/parse_pubmed.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cat >"$TMP/markup.xml" <<'XML'
<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>99999991</PMID>
      <Article>
        <Journal>
          <Title>Journal of Synthetic Medicine</Title>
          <ISOAbbreviation>J Synth Med</ISOAbbreviation>
          <JournalIssue><Volume>1</Volume><Issue>2</Issue><PubDate><Year>2024</Year></PubDate></JournalIssue>
        </Journal>
        <ArticleTitle>Eradication of <i>Helicobacter pylori</i> infection.</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">CO<sub>2</sub> levels rose.</AbstractText>
        </Abstract>
        <AuthorList><Author><LastName>Researcher</LastName><ForeName>Ada</ForeName></Author></AuthorList>
        <ELocationID EIdType="doi">10.0/synthetic.markup</ELocationID>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
XML

cat >"$TMP/plain.xml" <<'XML'
<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>99999992</PMID>
      <Article>
        <Journal>
          <Title>Journal of Synthetic Medicine</Title>
          <JournalIssue><PubDate><Year>2023</Year></PubDate></JournalIssue>
        </Journal>
        <ArticleTitle>Plain title without markup.</ArticleTitle>
        <Abstract><AbstractText>Plain abstract.</AbstractText></Abstract>
        <AuthorList><Author><LastName>Writer</LastName><ForeName>Dan</ForeName></Author></AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
XML

fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %s\n' "$1"; else printf '  FAIL  %s (want %s got %s)\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }
has() { grep -qF -- "$2" "$1" && echo yes || echo no; }

python3 "$PARSER" bibtex <"$TMP/markup.xml" >"$TMP/markup.bib"
python3 "$PARSER" efetch <"$TMP/markup.xml" >"$TMP/markup.md"
python3 "$PARSER" bibtex <"$TMP/plain.xml" >"$TMP/plain.bib"
python3 "$PARSER" efetch <"$TMP/plain.xml" >"$TMP/plain.md"

# 1-2. a title with inline <i> keeps the text inside and after it
ck "bibtex title keeps the italic species name" yes \
  "$(has "$TMP/markup.bib" 'title     = {Eradication of Helicobacter pylori infection.},')"
ck "efetch title keeps the italic species name" yes \
  "$(has "$TMP/markup.md" '**Title**: Eradication of Helicobacter pylori infection.')"
# 3-4. an abstract with inline <sub> keeps the text inside and after it
ck "efetch abstract keeps the subscript and the rest of the sentence" yes \
  "$(has "$TMP/markup.md" '**Abstract**: BACKGROUND: CO2 levels rose.')"
ck "  ...and never stops at the first child element" no \
  "$(has "$TMP/markup.bib" 'title     = {Eradication of },')"

# 5-6. negative control: a title with no markup is unchanged
ck "plain bibtex title is unchanged" yes "$(has "$TMP/plain.bib" 'title     = {Plain title without markup.},')"
ck "plain efetch abstract is unchanged" yes "$(has "$TMP/plain.md" '**Abstract**: Plain abstract.')"

if [ "$fail" -eq 0 ]; then
  echo "PASS: parse_pubmed.py keeps titles and abstracts whole through inline markup."
else
  echo "FAIL: $fail check(s) failed." >&2
  exit 1
fi

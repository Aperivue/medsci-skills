# Note Templates

Two templates: literature notes (one per paper) and atomic concept notes (synthesized across
papers). Match the frontmatter field names exactly — Dataview fails silently on a renamed
field, returning an empty table rather than an error.

Korean-structured vaults: see `locale/ko/note_templates.md`.

## 1. Literature note

Save to `<vault>/Literature/{short descriptive title}.md`.

```markdown
---
title: "Exact paper title, including any subtitle"
authors: [Family1, Family2, Family3]   # max 5, then "et al."
journal: "Journal name, or arXiv:XXXX.XXXXX"
date_published: YYYY-MM-DD
tags:
  - 📝Paper
  - 🤖AI/LLM
  - 🏥ClinicalReasoning
status: 🟢Completed
aliases:
  - ShortAlias
---

# Paper title

📎 **Open the PDF inside Obsidian**: ![[exact_source_filename.pdf]]

## 📌 One-line summary
Who did what, how, and how much — one sentence, from the text.

## 🎯 Background and aim
* What earlier work left unresolved
* The problem this paper attacks
* The hypothesis, if stated

## 🔑 Methods and results
1. **Design**: n, dataset, evaluation protocol — as written in the text
2. **Main results**: exact figures only (e.g. "accuracy 91.1%", "p < 0.001",
   "median 10, IQR 9–10")
3. **Comparison**: against baselines or competing models
4. **Limitations**: the ones the authors state

## 💡 My reading
* What this implies for my own work — the reader's judgement, not the authors' claims
* Second implication

---
## Related notes
* [[domain hub note]]
* [[existing concept note]]
* [[proposed new concept]]
```

### Rules

1. **Field names are fixed**: `title`, `authors`, `journal`, `date_published`, `tags`,
   `status`, `aliases`.
2. **`authors` is a YAML list** of at most five entries; append `et al.` beyond that.
3. **`date_published` is `YYYY-MM-DD`.** Year-only sources use `YYYY-01-01` with a note in
   the body.
4. **Tags carry emoji prefixes** — see `tag-vocabulary.md`.
5. **`status: 🟢Completed`** only once the note is written from verified extracted text.
6. **The PDF embed is mandatory** and goes directly under the H1, reproducing the source
   filename exactly.
7. **Every number comes from the extracted text.** Never from model knowledge.
8. **The related-notes section carries at least four wikilinks** — a domain hub, at least one
   cross-folder link, and the concept notes this paper touches. A note with no outbound links
   is an island, and islands are never revisited.

## 2. Atomic concept note

Save to `<vault>/Concepts/{concept name}.md`.

```markdown
---
title: "Concept name"
type: concept
tags:
  - 🧠Concept
  - (domain tag)
aliases:
  - AlternativeName
related_papers:
  - "[[literature note 1]]"
  - "[[literature note 2]]"
  - "[[literature note 3]]"
status: 🌱Seedling      # 🌱Seedling | 🌿Growing | 🌳Mature
---

# Concept name

## 📖 Definition, in my own words
The reader's understanding, not the textbook phrasing and not a sentence copied from any
paper. This section is the whole point of the layer.

## 🌐 Why it matters
Why this concept earns attention in this domain — the reader's judgement.

## 📚 How different papers treat it
- **[[Paper A]]**: its treatment, with a specific quoted claim
- **[[Paper B]]**: a different angle or method
- **[[Paper C]]**: a contrary or complementary position

## 🔗 Related concepts
- [[another atomic concept]] — how they connect
- [[a concept not yet written]] — related, still a stub

## ❓ Open questions
- What remains unanswered about this concept
- What a future paper would have to show

## 📝 Update log
- YYYY-MM-DD: drafted from {N} papers
```

### Rules

1. **`type: concept`** separates these from literature notes in every query.
2. **Status lifecycle** — 🌱Seedling: drafted, ~3 papers. 🌿Growing: 5–10 papers, the reader
   has edited it. 🌳Mature: 10+ papers, the reader's own position is established.
3. **The definition must be rewritten by the reader.** A concept note that is still entirely
   AI-drafted is a summary, not a second layer. Create it as 🌱Seedling and say so.
4. **`related_papers` entries are quoted wikilinks**: `"[[note title]]"`.
5. **Open questions are never left empty** — one or two minimum. They are the seed of the
   next layer.

## 3. Filename conventions

**Literature notes** — 3–5 keyword concepts, space-separated:

- ✅ `Clinical reasoning GenAI vs physicians.md`
- ✅ `MAIRA-2 grounded radiology report.md`
- ❌ `towards accurate differential diagnosis with LLM clinicopathological NEJM.md` (the PDF's full title)
- ❌ `paper_001.md` (carries no meaning)

**Concept notes** — the concept, with an English alias in parentheses when the field uses one:

- ✅ `Sequential decision-making.md`
- ✅ `Management reasoning.md`
- ❌ `Decision making.md` (too general to synthesize)
- ❌ `SDM.md` (an abbreviation alone)

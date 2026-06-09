# Korean (ko) locale — Obsidian vault layout + note templates

> Opt-in Korean variant for `/lit-sync`. The skill defaults to English folder names
> (`Literature/`, `Concepts/`) and English note headings. Use this layout when the user's
> Obsidian vault already follows a Korean structure (the skill honors an existing layout) or
> when the user explicitly prefers Korean notes.

## Vault folder layout (Korean)

- Literature notes: `02 연구/문헌/{citekey}.md`
- Concept notes: `02 연구/개념노트/{concept name}.md`

```bash
# Step 3.1 — count existing literature notes
ls "$VAULT/02 연구/문헌/" | grep -v "📊" | wc -l
```

## Literature note template (Korean headings)

```markdown
---
notetype: literature
citekey: "{citekey}"
title: "{title}"
authors: "{authors}"
journal: "{journal}"
year: {year}
doi: "{doi}"
pmid: "{pmid}"
created: "{today}"
tags:
  - type/literature
  - _unread
---

# {title}

## 서지 정보
- **저자**: {authors}
- **저널**: {journal}{volume_issue_pages}
- **연도**: {year}
- **DOI**: [{doi}](https://doi.org/{doi})
{pmid_line}

## 핵심 내용 (내 언어로)



## 내 생각



## 관련 노트
- [[🗺️ 연구 종합]]
- [[🗺️ 논문과 리뷰]]
-
-
```

- Leave `## 핵심 내용` and `## 내 생각` blank — the user fills these in personally.
- `## 관련 노트` contains 2 hub links + 2 empty slots (reserved for later concept-note linking).

## Concept note template (Korean headings)

```markdown
---
title: "{concept name}"
type: concept
tags:
  - 🧠개념
  - {domain tag}
aliases:
  - {English/Korean alternative name}
related_papers:
  - "[[{lit-note-1}]]"
  - "[[{lit-note-2}]]"
  - "[[{lit-note-3}]]"
status: 🌱Seedling
---

# {concept name}

## 정의 (My Understanding)
> TODO: write in your own words

## 왜 중요한가
{why the concept matters in this domain — AI supplies a draft}

## 논문별 관점
- **[[{lit-note-1}]]**: {this paper's angle}
- **[[{lit-note-2}]]**: {a different angle}
- **[[{lit-note-3}]]**: {comparison / complement}

## 관련 개념
- [[{another concept}]]

## 열린 질문
- {open question 1}
- {open question 2}

## 관련 노트
- [[🗺️ 연구 종합]]
- [[{related project hub}]]
- [[{lit-note-1}]]
- [[{lit-note-2}]]
```

- Keep the `## 정의` section as a `> TODO` marker — the 2nd-layer note only becomes meaningful once the user writes the definition in their own words.
- Never auto-fill `## 정의` of a concept note — keep the TODO marker.
- At least 4 wikilinks under `## 관련 노트` (vault convention).

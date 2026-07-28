# Challenge: a Perspective drafted like an original article

A **Perspective** earns its place through prose, not data. Two habits carried over from IMRAD
writing make a draft read as a study rather than an argument, and reviewers notice both:

1. **IMRAD section headings.** Published Perspectives name their sections as *argument-moves*
   — "The model reads your account, not your patient" — never "Introduction / Methods / Results
   / Discussion". A generic IMRAD heading in a Perspective is a tell.
2. **A thesis abstract with no authorial move.** Eight of nine sampled npj Digital Medicine
   Perspectives open the abstract with an explicit "we argue" / "we propose" / "here we ...". A
   purely declarative abstract reads as a report.

`check_perspective_structure.py` catches exactly these two surface forms — and only when the
manuscript is a Perspective (front-matter `article_type:` or `--type`). Both verdicts are Minor
(advisory); the gate never judges the argument.

## Why the parser has to be careful

The trap is false positives on a *good* Perspective, so the parser (hardened against a Codex
design review) must:

- read the genre only from the leading `---` front matter, not a body `**Article type**` line;
- blank HTML comment blocks first, so a commented-out `## Methods` is not flagged and a
  "we argue" inside a comment does not suppress the abstract verdict;
- treat only level-2 `##` lines as sections (`### Box 1` is not one) and strip leading section
  numbers ("1. Introduction") before the IMRAD-token test;
- skip structural / front / back-matter headings (Title page, Abstract, Display items,
  Submission notes, References, ...);
- evaluate the first body Abstract and warn on a duplicate;
- allow Conclusion / Summary headings and an absent abstract.

## What the fixtures assert

| Fixture | Expectation |
|---|---|
| `perspective_bad.md` | fires HEADING (`## 1. Introduction`, `## Methods`) **and** ABSTRACT (flat) |
| `perspective_ok.md` | silent — argument-move headings + "Here we argue ..." abstract |
| `not_perspective.md` | silent — an Original Article with full IMRAD (genre gate) |
| `edge_hardened.md` | silent findings + a duplicate-abstract warning — commented `## Methods` and "we argue" ignored, `### Box` is not a section, the first (authorial) abstract wins |

The gate is Minor-only, so it always exits 0; the verdicts are in stdout, which is why
`verify.sh` diffs the golden stdout rather than trusting an exit code.

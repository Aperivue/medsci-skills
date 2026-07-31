# Presentations

One 10-minute `conference_oral` talk per demo. Each is built by `build_deck.py` and checked by
`make_deck.sh`, which runs the two gates this repository requires of a deck:

- `check_slide_tells.py` — the marks that make a deck read as machine-made: chrome on every slide,
  scaffolding sentences, section-label titles instead of findings, repeated identical shapes,
  unlabelled arrows.
- `check_deck_budget.py` — words per slide, slides per minute and a font floor, against the
  archetype declared in `deck.qc`.

**Every number on every slide is read from the shipped artifacts at build time.** There are no
typed-in figures in the deck scripts; change a result and the deck changes with it. Titles state
the finding rather than naming the section, and figures are the ones the analysis already produced.

Speaker notes are Korean narrative prose, per the presenter's convention; slide bodies are English.

```bash
bash make_deck.sh          # build + both gates
```

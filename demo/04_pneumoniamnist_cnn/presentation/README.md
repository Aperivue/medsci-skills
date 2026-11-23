# Presentation

A 10-minute `conference_oral` talk built on the medsci slide template
(`skills/present-paper/templates/slide_template/`), pine palette, plain by default: white layouts
throughout, no section band, because the figures (the Grad-CAM panel included) are drawn on a white
ground. The nine slides are the cover, disclosure, the two pre-training gates, discrimination over
seeds (a ROC figure and a per-seed table), calibration, Grad-CAM, limitations and the take-home.

![The slides](contact_sheet.png)

The image is a PowerPoint render of the built deck.

`build_deck.py` starts the deck with `new_deck.make_deck(palette="pine", band=False)` and fills it by
layout name and placeholder idx: `put_rich` for the spans in the two accent colours, `fit_picture` for the
figures the analysis already produced, `plain_table` and `set_cell` for the two small tables. The first
accent marks the point of a slide and the second marks what it is set against.
`make_deck.sh` builds it and runs the two gates this repository requires of a deck:

- `check_slide_tells.py`: the marks that make a deck read as machine-made.
- `check_deck_budget.py`: words per slide, slides per minute and a type-size floor, against the
  archetype declared in `deck.qc`.

**Every number on every slide is read from the shipped artifacts at build time.** There are no
typed-in figures in the deck script; change a result and the deck changes with it. Titles state
the finding, and the figures are the ones the analysis produced. The Grad-CAM slide credits the
public dataset's images (PneumoniaMNIST, MedMNIST v2, CC BY 4.0, Yang et al. 2023) in its source line.

Slide text is English; speaker notes are Korean prose, per the presenter's convention.

```bash
bash make_deck.sh                              # build + both gates
python3 build_deck.py --band banded.pptx       # the same slides with the section band
```

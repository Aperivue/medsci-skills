# medsci slide template

A PowerPoint template for clinical research talks and teaching: one master, 31 layouts, three
quiet palettes or your own colours, no pictures and no logo. White ground for text, figures and
tables; black "Imaging" layouts for image-heavy slides. A plain Word handout template comes with it.

This is the default look for a new deck made with this skill. When a meeting or an employer
supplies its own template, use that one instead.

| File | Use |
|---|---|
| `medsci_slides.pptx` | The template: the 31 layouts and no slides. Open it and add slides, or start from it with `new_deck.py`. |
| `build_slide_template.py` | Rebuilds the template and a sample deck (`medsci_slides_sample.pptx`, one slide per layout, synthetic text; not shipped). |
| `new_deck.py` | Starts a deck from the template: empty, or one of five starter skeletons. |
| `medsci_handout.docx` | A one-page handout skeleton: title block, learning objectives, key points, one figure, note lines, references. |
| `build_handout_template.py` | Rebuilds the handout. |

Needs `python-pptx`, `python-docx` and `lxml`. Nothing else is read at build time: no image, no
font file.

```bash
python3 build_slide_template.py --force               # rebuilds medsci_slides.pptx (and the sample deck) here
python3 build_slide_template.py out/ --palette stone
python3 build_slide_template.py out/ --accent 1D6A4F  # your own accent on the mono palette
python3 new_deck.py talk.pptx --type conference-oral
python3 new_deck.py my_template.potx                  # the template as a PowerPoint template file (File > New from Template)
python3 build_handout_template.py out/
```

None of the three scripts replaces an existing output unless given `--force` (checked when the run
starts). Each writes under a temporary name in the output folder and moves the finished file into
place, so a failed run leaves the previous file, or none; the slide builder moves its two files one
after the other, not as a pair. `new_deck.py` writes only `.pptx` and refuses to write over its
template.

Which layout to use for which slide, and what the research-talk set is for:
`../../references/slide_template_layouts.md`.

## What it looks like, and why

The research-talk layouts have no band, no rule, no panel and no outlined box. Space and type size
separate the parts of a slide. Tables carry three rules only: above the header, under it, and
under the last row. Emphasis is weight or the palette's one accent, never a second colour. The
template spends the accent in one place among the research-talk layouts, the number on Key
Finding; elsewhere it is yours to spend, once per slide. On black, the Quiz answer uses the
dark-ground accent.

The teaching layouts (Content, Title Only, Table, Lessons and the Imaging layouts except Blank,
Full, Full Center and the two Overlays) carry an optional section name above the title in small
grey type. Left empty, it does not show in the
slide show or in an exported PDF. The research-talk layouts have no section name: a ten-minute
talk has no sections to name.

The Section divider is the palette's section colour with a number, a title and one line. Closing
carries the conclusion in one line and a contact line; the last slide stays up during questions,
so it says the finding, not "thank you".

## Layouts

| Layout | What it carries |
|---|---|
| Cover | Event line, title, presenter, affiliation, left-aligned. Optional picture (right part of the slide) and optional logo; both invisible when empty. |
| Section | Part number, title, one-line subtitle on the section colour. |
| Content / Title Only | Title and bulleted body / title alone. Optional section name. |
| Blank | Page number only. |
| Closing | The conclusion in one line and a contact line. Optional picture and logo, as on the Cover. |
| Disclosure | Conflicts of interest and funding, two short text slots under small labels. |
| Agenda | A numbered list in a narrow column. |
| Key Finding | The finding as a sentence (title), one large number in the accent colour, the unit, the interval line, a source line. |
| Study Design | Flow-diagram picture slot, and a narrow column for population, period and reference standard. |
| Result · Figure | One large figure slot under the title, a source line. No line under the title: say where to look. |
| Result · Table | Table slot, one line under the table naming the row or column to read, a source line. |
| Comparison | Two columns, each with a header. |
| Limitations | Three limitations, each beside what it does to the result. |
| Take-home | Three lines in large type. |
| References · QR | A short numbered reference list and a QR picture slot with a caption. |
| Table | One table slot: a lecture roadmap or a section summary. |
| Lessons | Square picture and two or three lines beside it: a missed or difficult case. |
| Imaging · Content / Title Only / Blank | Black ground; text typed here is white. |
| Imaging · Case | Title is the one-line presentation; square picture and a findings slot. |
| Imaging · 2×2 | Four square pictures with a sequence label in each corner, findings at the right. |
| Imaging · 1×3 | Three square pictures with labels, one line under them. |
| Imaging · DSA Pair | Two square pictures, labels under the panels (readable over a white subtracted image). |
| Imaging · 4 Steps | Four square pictures with a step name under each, one line under them. |
| Imaging · Quiz | Square picture, question, and an answer slot in the dark-ground accent. |
| Imaging · Full | The picture fills the slide. Title in the top-left corner, two yellow label slots. |
| Imaging · Full Center | A square picture at full height in the middle, yellow labels at either side. |
| Imaging · Overlay | Full-slide picture (dim it: Picture Format > Transparency, about 55%) under a title and two to four lines. |
| Imaging · Overlay Table | The same, under a table. |

Picture placeholders crop the picture to fill the slot. That is right for a CT, MR or DSA frame,
which is why those slots are square, and wrong for a plot, a flow diagram, a QR code or a logo.
For those, use Picture Format > Crop > Fit after inserting, or `new_deck.fit_picture()` from a
script.

Patient images: remove names, numbers and dates from the image pixels and its metadata before
inserting the image. A crop in PowerPoint, or a shape laid over a field, hides it on screen only;
the whole image stays inside the `.pptx` and can be recovered by anyone given the file.

The research-talk layouts expect a title that states the point ("Accuracy held in the external
set"), not a label ("Results"). Their prompts say so.

## Placeholder idx table

For filling a deck from a script. Find the layout by name and the slot by idx. Each cell lists
idx, placeholder type and shape name. `tests/test_slide_template.py` checks this table against
the built file; regenerate it with `python3 build_slide_template.py --print-table`.

<!-- placeholder-table:start -->
| Layout | Placeholders |
|---|---|
| Cover | 0 ctrTitle `Title` · 1 subTitle `Presenter` · 13 body `Event` · 14 body `Affiliation` · 15 pic `Logo (optional)` · 16 pic `Cover picture (optional)` |
| Section | 0 title `Section title` · 13 body `Section number` · 14 body `Section subtitle` |
| Content | 0 title `Title` · 1 obj `Content` · 20 body `Section name` |
| Title Only | 0 title `Title` · 20 body `Section name` |
| Blank | none |
| Closing | 0 title `Conclusion` · 13 body `Contact` · 15 pic `Logo (optional)` · 16 pic `Closing picture (optional)` |
| Disclosure | 0 title `Title` · 1 body `Conflicts of interest` · 13 body `Funding` |
| Agenda | 0 title `Title` · 1 body `Agenda items` |
| Key Finding | 0 title `Title` · 13 body `Number` · 14 body `Unit` · 15 body `Interval` · 16 body `Source` |
| Study Design | 0 title `Title` · 13 body `Population` · 14 body `Period` · 15 body `Reference standard` · 30 pic `Flow diagram` |
| Result · Figure | 0 title `Title` · 14 body `Source` · 30 pic `Figure` |
| Result · Table | 0 title `Title` · 13 body `Takeaway` · 14 body `Source` · 21 tbl `Table` |
| Comparison | 0 title `Title` · 1 body `Left text` · 2 body `Right text` · 13 body `Left header` · 14 body `Right header` |
| Limitations | 0 title `Title` · 13 body `Limitation 1` · 14 body `Limitation 2` · 15 body `Limitation 3` · 16 body `Consequence 1` · 17 body `Consequence 2` · 18 body `Consequence 3` |
| Take-home | 0 title `Title` · 1 body `Take-home lines` |
| References · QR | 0 title `Title` · 1 body `References` · 13 body `QR caption` · 30 pic `QR code` |
| Table | 0 title `Title` · 20 body `Section name` · 21 tbl `Table` |
| Lessons | 0 title `Title` · 1 body `Lessons text` · 20 body `Section name` · 30 pic `Image` |
| Imaging · Content | 0 title `Title` · 1 obj `Content` · 20 body `Section name` |
| Imaging · Title Only | 0 title `Title` · 20 body `Section name` |
| Imaging · Blank | none |
| Imaging · Case | 0 title `Title` · 1 body `Findings` · 20 body `Section name` · 30 pic `Image` |
| Imaging · 2×2 | 0 title `Title` · 1 body `Findings` · 20 body `Section name` · 30 pic `Image 1` · 31 pic `Image 2` · 32 pic `Image 3` · 33 pic `Image 4` · 40 body `Sequence 1` · 41 body `Sequence 2` · 42 body `Sequence 3` · 43 body `Sequence 4` |
| Imaging · 1×3 | 0 title `Title` · 1 body `Findings` · 20 body `Section name` · 30 pic `Image 1` · 31 pic `Image 2` · 32 pic `Image 3` · 40 body `Sequence 1` · 41 body `Sequence 2` · 42 body `Sequence 3` |
| Imaging · DSA Pair | 0 title `Title` · 20 body `Section name` · 30 pic `DSA 1` · 31 pic `DSA 2` · 40 body `Label 1` · 41 body `Label 2` |
| Imaging · 4 Steps | 0 title `Title` · 1 body `Note` · 20 body `Section name` · 30 pic `Step 1` · 31 pic `Step 2` · 32 pic `Step 3` · 33 pic `Step 4` · 40 body `Step label 1` · 41 body `Step label 2` · 42 body `Step label 3` · 43 body `Step label 4` |
| Imaging · Quiz | 0 title `Title` · 1 body `Question` · 20 body `Section name` · 30 pic `Image` · 50 body `Answer` |
| Imaging · Full | 0 title `Title` · 30 pic `Image` · 40 body `Label 1` · 41 body `Label 2` |
| Imaging · Full Center | 0 title `Title` · 30 pic `Image` · 40 body `Label 1` · 41 body `Label 2` |
| Imaging · Overlay | 0 title `Title` · 1 body `Text` · 30 pic `Image (dimmed)` |
| Imaging · Overlay Table | 0 title `Title` · 21 tbl `Table` · 30 pic `Image (dimmed)` |
<!-- placeholder-table:end -->

A slot is identified by the pair (layout name, idx), not by idx alone. The ranges are mostly shared
(0 title, 1 and 2 body text, 13 to 18 short text slots, 20 section name, 21 table, 30 to 33
pictures, 40 to 43 labels, 50 quiz answer), with one exception: on Cover and Closing, 15 and 16 are
the logo and picture slots, while on Key Finding they are text.

## Filling a deck from a script

```python
from pathlib import Path
from pptx import Presentation
import new_deck, build_slide_template as t

prs = Presentation("talk.pptx")                      # made by new_deck.py
lay = {l.name: l for l in prs.slide_layouts}
s = prs.slides.add_slide(lay["Result · Figure"])
slot = {p.placeholder_format.idx: p for p in s.placeholders}
slot[0].text_frame.text = "Accuracy held in the external set"
new_deck.fit_picture(slot[30], "roc.png")            # whole figure, not cropped
prs.save("talk.pptx")
t.post_process(Path("talk.pptx"))                    # after the last save
```

- `build_slide_template.plain_table(slot[21], rows, cols, header)` inserts a table with no fill
  and three rules. python-pptx's own default is a filled header and banded rows.
- `new_deck.appear_on_click(slide, [shape, ...])` makes shapes appear one per click, in order. Call
  it once per slide with every shape; a slide that already has animation is refused. The layouts
  themselves carry no animation: on a slide added by hand (the Quiz answer, the findings on the
  Imaging layouts) add the click yourself, in PowerPoint (Animations > Appear) or with this
  function. The starter decks already do. The sample deck is a preview of the layouts and has none.
- A run that contains Hangul needs `lang="ko-KR"` (`new_deck.set_lang`), or PowerPoint breaks
  lines inside a word.
- Leave a placeholder's position and size alone, or set all four of left, top, width and height.
  Setting one makes python-pptx write the others as zero.
- Run `post_process` after the last save. It updates the slide, notes and hidden-slide counts and
  the slide titles in `docProps/app.xml` and leaves its other properties alone; without that
  PowerPoint for Mac offers to repair the file.
- Slots you do not fill can stay. An empty placeholder does not show in the slide show or the PDF.

## Starter decks

`new_deck.py OUT.pptx --type NAME`. Each slide has `<angle-bracket>` text to overwrite and a
speaker note saying what the slide is for. Picture slots are empty.

| Type | For | Slides |
|---|---|---|
| `conference-oral` | Research talk, 8 to 12 minutes | Cover, Disclosure, the question, Study Design, Result · Figure, Key Finding, Result · Table, Comparison, Limitations, Take-home, References · QR |
| `journal-club` | Appraisal of one paper, 20 to 40 minutes | Cover, the claim, Comparison (design needed against design used), Study Design, Result · Figure, Key Finding, Result · Table, Limitations, what would change my mind, Take-home, References · QR |
| `lecture` | Didactic lecture, about 30 minutes | Cover, opening case, roadmap Table, then per part: Section, Content, Imaging · 2×2, Imaging · Case, summary Table; Lessons, two Quiz slides, Take-home, Closing |
| `case-conference` | Case or imaging conference | Cover, Imaging · Case, 2×2, Quiz, 1×3, Content, Lessons, Closing |
| `procedure` | Procedure or technique talk | Cover, principle, roadmap Table, then per technique: Section, Imaging · Case, DSA Pair, 4 Steps, complications, technique Table; Lessons, Take-home, Closing |

The two research starters leave the section-name slot empty; the three teaching starters fill it.

## Colours

`--palette NAME` picks one of three. None uses navy or red.

| Role | `mono` (default) | `stone` | `pine` |
|---|---|---|---|
| Text (ink) | `111111` | `1C1B19` | `15191A` |
| Section divider ground (section) | `111111` | `2B2925` | `1E2B27` |
| Emphasis on white (accent) | `0050C8` | `7A4E00` | `1D6A4F` |
| Emphasis on black (accent_dk) | `4DA3FF` | `E0B25A` | `7FD1AE` |
| Captions, labels, bullets, page number (muted) | `6E6E6E` | `66615A` | `5B6763` |
| Light ground in the colour picker (paper) | `FAFAF7` | `F7F5F0` | `F4F7F5` |

`mono` takes its values from `references/slide_visual_styles/editorial_mono.md`: near-black, grey
and one blue. `stone` is warm greys with a dark ochre accent; `pine` is cool greys with a deep
green accent. All three print legibly in greyscale. Fixed in every palette: white, black, a grey
`A3A3A3` for the page number and section name on black, and annotation yellow `FFD400` for labels
laid over an image.

Your own colours: any role, as a CLI option or a JSON file, applied over the chosen palette.

```bash
python3 build_slide_template.py out/ --accent "#1D6A4F" --section 1E2B27
python3 build_slide_template.py out/ --palette-file colours.json   # {"accent": "7A4E00", "ink": "1C1B19"}
```

Each value must be six hex digits, with or without `#`. Before anything is written, every text
role is checked against the ground it is set on (ink, muted and accent on white; white on the
section colour; the dark accent on black; ink and muted on paper) and the build stops if any pair
is below 4.5:1, the WCAG AA level for body text, naming the pairs that failed. Keep to one accent.

In the colour picker the first two theme accents are the two emphasis colours: accent 1 on white
slides, accent 2 on black slides.

## Adding your own logo and cover picture

The template ships without either.

- **Cover and Closing**: click the logo slot (top left) and insert your logo, then
  Picture Format > Crop > Fit so it is not cropped. The picture slot takes the right part of the
  slide; a photograph or illustration is cropped to fill it. From a script: `fit_picture(slot[15],
  "logo.png")` and `slot[16].insert_picture("cover.jpg")`.
- **Every content slide**: View > Slide Master, select the top master, and paste the logo there,
  bottom right, left of the page number, about 0.27 in (0.7 cm) high. Consider leaving it off: the
  audience knows whose talk it is, and a logo on every slide takes room from the figure.
- **Permanently**: do either in the template and save it as your own (`new_deck.py my_template.potx`
  gives a `.potx` to start from). Check that you may
  use the logo and the picture; this repository does not ship any for that reason.

## Fonts

Arial for Latin text and Malgun Gothic for Korean, declared once in the theme of both the slides
and the handout; no font has to be installed beyond what the operating system has. Arial is on
Windows and macOS. Malgun Gothic ships with Windows and is not part of macOS: on a Mac that does
not have it, Korean text falls back to a system face and may wrap differently.
`scripts/check_font_portability.py` reports this. Take a PDF to the venue either way.

## The handout

`medsci_handout.docx` is laid out to fit one A4 page (a target, not checked by a test): title block, three learning objectives, key points (the
term in bold, then two or three sentences), one figure with its caption, ruled lines for notes,
and a numbered reference list. No table and no box. The handout is read after the talk, so it
carries the sentences the slides left out. Paste the summary tables from the slides into it
yourself; nothing copies them. Generate the reference list with a reference manager.

## Checking a build

```bash
python3 ../../tests/test_slide_template.py          # layouts, README table, palettes, contrast, no media, no names
soffice --headless --convert-to pdf medsci_slides_sample.pptx
python3 ../../scripts/check_text_overflow.py medsci_slides_sample.pptx --pdf medsci_slides_sample.pdf
```

Two builds from the same source give the same parts: the document dates and zip entry times are
fixed. A LibreOffice render hides defects PowerPoint shows. Open the built file in PowerPoint once
before relying on a changed build.

The skill's deck checkers (`check_slide_tells.py`, `check_deck_budget.py`) read positions and
type sizes written on the slide. Text in a placeholder inherits both from the layout, so on a
deck filled through this template those checkers see the tables and little else; a clean result
from them on such a deck is not evidence about its text.

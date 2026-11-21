# Choosing a layout in the medsci slide template

The template is `templates/slide_template/` (README there: placeholders, colours, starters). This
page answers one question per slide: which layout? The rules for what goes on a slide (assertion
titles, type floor, empty space) are in `presentation_design_guidelines.md` §1–3 and are not
repeated here.

## Pick by what the slide has to do

| The slide has to... | Layout |
|---|---|
| say who is speaking, where | Cover |
| declare conflicts and funding | Disclosure |
| show the route through a talk of more than three parts | Agenda (research) or Table (lecture roadmap) |
| make one number the thing people leave with | Key Finding — once per talk |
| make the design believable | Study Design: the flow diagram, drawn as code, plus three facts |
| show the evidence for the title | Result · Figure (one figure) or Result · Table (a few rows) |
| set two things against each other | Comparison — only when the contrast is the argument |
| name why the finding might be wrong | Limitations: three, each with its effect on the result |
| leave three lines the room can repeat | Take-home |
| open a part of a lecture | Section |
| teach from an image | an Imaging layout: Case, 2×2, 1×3, DSA Pair, 4 Steps, Full, Full Center |
| check that a taught point landed | Imaging · Quiz; make the answer appear on click (the starters do; on a slide you add, Animations > Appear) |
| tell a case that went wrong and what changed | Lessons |
| summarise a part as a table the handout will repeat | Table, or Imaging · Overlay Table over a dimmed image |
| end | Closing: the conclusion in one line and a contact line, never a bare "thank you" |
| anything else | Content or Title Only, before inventing a new arrangement |

If two layouts fit, the slide is probably carrying two messages. Split it.

## The research-talk set

Disclosure, Agenda, Key Finding, Study Design, Result · Figure, Result · Table, Comparison,
Limitations, Take-home and References · QR are the slides a conference oral or a journal club is
built from. `new_deck.py --type conference-oral` and `journal-club` each use a subset, in the order
listed in the template README's starter table. They share three choices:

- **No section name and no band.** A short talk has no sections, and a label above every title is
  chrome (`ai_slide_tells.md` §2).
- **No line under the title.** The title already states the point; where to look is said aloud.
  Result · Table keeps one line under the table, naming the row to read.
- **The accent is spent once.** The template uses it on the Key Finding number only. A deck with
  Key Finding on four slides has no key finding.

Not every talk needs every one. Agenda belongs in a talk of more than three parts; Comparison only
when a contrast carries the claim; References · QR goes after the last slide, off the clock.

## Teaching decks

For a lecture, the order that works is: one case that shows why the topic matters, the roadmap
table, then for each part the same fixed sequence (definition, who, imaging, differential), images
large with labels on the anatomy, a summary table at the end of the part, and a quiz per taught
item. The image comes first and the words appear on click, because the audience reads whatever is
on the screen before it looks at the image. Keep the sequence labels and their order fixed through
the deck. Paste the summary tables into the handout (`medsci_handout.docx`), which also carries the
sentences the slides left out, so the slides can stay sparse.

Use the speaker's own de-identified cases where possible; a lecture built only from journal
figures is one the audience could have read. De-identify the image file before inserting it (pixels
and metadata): a crop or a shape in PowerPoint hides a field on screen and leaves it in the file.

# Generated illustrations — when they earn a slide, and the four rules

A text-only slide that stays text-only because nobody wanted to open an image tool is a slide the
audience reads instead of listens to. An image-generation API removes that excuse. It also removes
the friction that used to stop a deck from filling with decoration, so the rules below exist to put
the friction back where it belongs.

Read this before generating anything for a slide. For a figure destined for a **journal** —
graphical abstract, Central Illustration — stop here and read
`~/.claude/rules/journal-ai-image-policies.md` instead: several journals prohibit AI imagery
outright, and that is a different decision from the one this file governs.

---

## 1. Never generate a medical image

Not a CT, not an MRI, not a histology field, not a radiograph — not even "as an illustration".

The obvious reason is that a generated scan shown next to real numbers reads as data, and an
audience has no way to tell which slide was which by the time they are in the hallway.

The reason that actually bites is narrower and worth stating, because it has happened: **a deck can
contradict its own evidence.** A talk that presents a reader study showing experts cannot reliably
distinguish AI-generated medical images from real ones, and then displays a generated CT as if it
were a segmentation result, has undermined its own finding in front of the people best equipped to
notice. One audience question ends the talk.

What to do instead:

| You need | Use |
|---|---|
| A segmentation / detection result | The method's own published example asset — check its licence. nnU-Net, TotalSegmentator, MONAI ship figures under permissive licences |
| A modality example | A public dataset with a redistribution licence, cited on the slide |
| "What this kind of model does", conceptually | A drawn schematic (matplotlib / shapes), labelled as a schematic |
| Anatomy | SMART Servier (CC BY), NIAID BioArt — see `slide_design_principles.md` |

Generation is for **concepts, scenes, and metaphor-free explanation**. Nothing that could be mistaken
for a measurement.

---

## 2. Keep text out of the image

Image models still mangle non-Latin scripts, and a slide with a misspelt Korean label is worse than
a slide with no label. Two workable modes:

- **No text at all** (default). The slide supplies every label in real type, where it stays
  editable, searchable, and correctly hyphenated.
- **One short English word**, when the word *is* the subject — `PROMPT`, `HARNESS`. Even then,
  expect roughly one in three to come back without it or with it garbled. Regenerate or drop the
  word; never ship the garbled one.

Put `Absolutely no text, no letters, no numbers, no labels, no watermarks anywhere.` in the style
block of every prompt. It does not always hold, which is why you look at the output.

---

## 3. Put the deck's palette in the prompt, not in post

An illustration that arrives in the deck's own two colours reads as part of the design. One that
arrives in generic tech-blue reads as stock art, and no amount of cropping fixes it.

A style block that has produced usable output:

```
Flat editorial vector illustration for an academic medical conference slide.
Restrained palette: deep navy #1B2A4E, muted coral #B83E3A, warm grey, white background.
Clean geometric shapes, thin confident linework, generous white space, no gradients,
no drop shadows, no 3-D render look, no photorealism.
Absolutely no text, no letters, no numbers, no labels, no watermarks anywhere.
Wide 3:2 composition, subject centred with breathing room.
```

Swap the two hex values for the deck's own. Keep everything else — each clause is there because its
absence produced something unusable: gradients and drop shadows are the strongest "stock
illustration" tell, and a 3-D render next to flat charts looks like it came from a different deck.

Describe the **scene and its geometry**, not the mood. `LEFT: … RIGHT: …`, `foreground / background`,
`connected by a thin arrow to`. Prompts that ask for a feeling return decoration; prompts that
describe a layout return something that carries an argument.

---

## 4. Record where every image came from

One `assets/SOURCES.md` beside the deck, one row per image: file, origin, licence or status. Fill it
as you add images, not at submission.

| File | Origin | Licence / status |
|---|---|---|
| `img_*.png` | Generated (`gen_images.py`, model + date) | — |
| `nnunet_*.png` | Upstream repo `documentation/assets` | Apache-2.0, cited on slide |
| product screenshots | Public product site | Domain shown on slide; developer notified |
| paper figures | Author's own | Own work |

This is what makes the deck safe to hand to a society office, and it is the file you will want when
someone asks about one image four months later.

---

## Disclosure

A **lecture** does not require a per-slide "AI-generated" mark, and seven of them scattered through a
deck read as anxiety rather than rigour. If a disclosure is wanted, one line on the closing slide —
*"Some illustrations were generated with AI"* — carries it without taxing every slide.

A **journal-destined** figure is the opposite case and is governed elsewhere; see the rule named
above. Do not reason from this file to that one.

---

## Where an illustration actually helps

Generated art is cheap now, which is exactly why the count needs a reason. The slides that improved
had one thing in common: **an abstract claim that the audience had to hold in their head while the
speaker talked.** A picture gave them somewhere to put it.

Worth an illustration:

- A **contrast the whole talk turns on** — two paths, two roles, before/after. The image does what a
  two-column list only asserts.
- A **scene the audience is not in** — a reading room, a cluster, a workflow they do not perform.
- An **abstract principle** stated as keywords with nothing to look at.

Not worth one:

- Slides that already carry a table, a chart, a screenshot, or a real figure. Adding art crowds the
  thing that carries the evidence.
- Section dividers and full-bleed statement slides. Those work because they are empty; an image
  removes the pause they exist to create.
- The title slide.

If a deck ends up with an illustration on most slides, the illustrations have stopped being signal.

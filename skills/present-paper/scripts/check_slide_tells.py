#!/usr/bin/env python3
"""Find the marks an AI leaves on a slide deck — in the built .pptx, not in the build script.

People can tell. Reviewers report that a third of the decks they now see were made by an AI, that
they can spot it immediately, and that the tell is not ugliness — it is that the deck stops
communicating. "무슨 말을 하고 싶은 것인지 전달이 잘 안 된다." The maker was made comfortable; the
audience was not served.

The marks are mechanical, which means they can be caught mechanically:

  CHROME_ON_EVERY_SLIDE  the little words along the top and bottom edges of every slide — the
                         all-caps eyebrow label, the "2026 · NEUROGENETICS" brand footer. They
                         carry no information, they appear because a template said to, and they are
                         the first thing a reader's eye registers as machine-made. This project's
                         own house style *mandated* them, which is how we shipped the tell.

  SCAFFOLD_PHRASE        "핵심은 ~라는 점이다." "요약하자면." "단순히 A가 아니라 B이다." "이는 세
                         가지 층위에서 살펴볼 수 있다." "As we saw above." These are not thoughts.
                         They are the *record of a thought being assembled* — a model narrating its
                         own steps. A person thinks A→B→C→D in silence and writes down only D; a
                         model says "having done B, I will now do C" and leaves the sentence in.
                         Scaffolding is what a writer removes in revision. AI delivers the
                         scaffolding still bolted to the building.

  TOPIC_TITLE            A content slide titled "Results" instead of saying what the result WAS.
                         The headline is the one line everyone reads; spending it on a filing label
                         means the point must be excavated from the body. (Assertion-evidence:
                         Alley & Neeley 2005.)

  SHAPE_MONOTONY         The same rounded rectangle, eight times, at the same size. A person draws
                         the shape the idea needs; a generator reaches for the shape it has.

  DEAD_SPACE_BAND        A wide empty stripe between objects — not negative space, which is chosen,
                         but the gap left when boxes are placed by a layout rule rather than an eye.

  ARROW_NO_SEMANTICS     Two or more arrows in a diagram and not one of them labelled. An arrow is
                         a claim: causes, becomes, flows into, is compared with. An unlabelled arrow
                         is read differently by every person in the room, and one wrong arrow can
                         derail a whole discussion.

What this does NOT do: judge whether the deck is beautiful, or whether AI was used. AI used as a
*booster* leaves none of these marks. AI used as a *button* leaves all of them.

Stdlib only — it reads the .pptx as the ZIP of XML that it is, so it runs on any deck from anyone
(PowerPoint, Keynote export, a colleague's file) with nothing installed.

Usage:
    check_slide_tells.py deck.pptx [--json out.json] [--strict]

Exit: 0 clean (or findings without --strict), 1 findings with --strict, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

DETECTOR = "check_slide_tells"

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

EMU_PER_INCH = 914400


# ---------------------------------------------------------------------------------------------
# The scaffolding bank
#
# Sentences that describe the making of the thought instead of the thought. Korean and English,
# because a Korean deck with English body text mixes both. Kept narrow on purpose: every entry here
# must be a phrase whose *removal never loses information*, or the check becomes a style opinion.
# ---------------------------------------------------------------------------------------------

SCAFFOLD_PATTERNS: Sequence[Tuple[str, str]] = (
    # Korean — the process narration the critique names
    (r"핵심은\s*.{0,30}?(라는\s*점|점이|것이)", "핵심은 ~라는 점이다"),
    (r"요약하(자면|면)", "요약하자면"),
    (r"정리하(자면|면)\s*다음과\s*같", "정리하면 다음과 같다"),
    (r"단순히\s*.{1,25}?\s*(이|가)\s*아니라", "단순히 A가 아니라 B이다"),
    (r"(두|세|네|다섯|몇)\s*가지\s*(층위|측면|차원)에서\s*살펴", "N가지 층위에서 살펴볼 수 있다"),
    (r"살펴본\s*바와\s*같이", "위에서 살펴본 바와 같이"),
    (r"앞서\s*(언급|설명)한\s*(바와\s*같이|대로)", "앞서 언급한 바와 같이"),
    (r"본\s*(발표|장표|슬라이드|글)에서는\s*.{0,20}?(다룬다|살펴본다|알아본다)", "이 글에서는 ~를 다룬다"),
    (r"요청하신\s*(내용|사항)", "요청하신 내용을 정리하면 (echo prompting)"),
    (r"이러한\s*감각", "이러한 감각이다"),
    # English — the same machine narrating itself
    (r"\bit is important to note\b", "It is important to note"),
    (r"\bin summary\b", "In summary"),
    (r"\bto summari[sz]e\b", "To summarize"),
    (r"\bas we (saw|discussed) (above|earlier)\b", "As we saw above"),
    (r"\bthis (slide|section) (shows|presents|covers|will cover)\b", "This slide shows…"),
    (r"\bin this (talk|presentation|deck),? (we|I) will\b", "In this talk we will…"),
    (r"\bnot (simply|just|merely) .{1,30}? but rather\b", "Not simply X but rather Y"),
    (r"\blet('| u)s (explore|dive|delve|unpack)\b", "Let's dive into…"),
    (r"\bthe key (point|takeaway) (here )?is\b", "The key takeaway is…"),
    (r"\bcan be (viewed|understood|examined) (on|at|through) (two|three|four|several) (levels|layers|dimensions)\b",
     "can be understood on three levels"),
)

# Filing labels. A *divider* slide may legitimately carry one; a content slide must not, because the
# headline is the only line everyone reads.
TOPIC_TITLES = {
    "overview", "introduction", "background", "methods", "method", "materials and methods",
    "results", "discussion", "conclusion", "conclusions", "summary", "key takeaways",
    "key points", "takeaways", "limitations", "future directions", "agenda", "outline",
    "objectives", "aims", "study design", "next steps", "questions",
    "개요", "배경", "서론", "방법", "연구방법", "결과", "고찰", "결론", "요약", "목차",
    "시사점", "제한점", "향후 계획", "질의응답",
}


@dataclass
class Shape:
    kind: str  # sp | pic | graphicFrame | cxnSp | grpSp
    text: str
    x: int
    y: int
    cx: int
    cy: int
    prst: str = ""
    max_pt: float = 0.0
    has_arrow: bool = False
    is_textbox: bool = False  # <p:cNvSpPr txBox="1"/> — text, not a drawn shape
    is_chrome: bool = False   # small type hugging the top or bottom edge

    @property
    def cxm(self) -> float:
        return self.x + self.cx / 2

    @property
    def cym(self) -> float:
        return self.y + self.cy / 2


@dataclass
class Finding:
    detector: str
    verdict: str
    slide: Optional[int]
    summary: str
    evidence: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------------------------
# Reading the deck
# ---------------------------------------------------------------------------------------------


def _first(el: ET.Element, path: str) -> Optional[ET.Element]:
    found = el.find(path)
    return found


def parse_shape(el: ET.Element, kind: str) -> Optional[Shape]:
    xfrm = el.find(f".//{A}xfrm")
    if xfrm is None:
        return None
    off, ext = xfrm.find(f"{A}off"), xfrm.find(f"{A}ext")
    if off is None or ext is None:
        return None
    try:
        x, y = int(off.get("x", 0)), int(off.get("y", 0))
        cx, cy = int(ext.get("cx", 0)), int(ext.get("cy", 0))
    except (TypeError, ValueError):
        return None

    texts = [t.text or "" for t in el.iter(f"{A}t")]
    text = "".join(texts).strip()

    sizes = [int(rpr.get("sz")) / 100 for rpr in el.iter(f"{A}rPr") if rpr.get("sz")]
    max_pt = max(sizes) if sizes else 0.0

    geom = el.find(f".//{A}prstGeom")
    prst = geom.get("prst", "") if geom is not None else ""

    # An arrow is a line whose head or tail is not "none" — that is what makes it a claim rather
    # than a rule.
    has_arrow = False
    for end in (f".//{A}headEnd", f".//{A}tailEnd"):
        e = el.find(end)
        if e is not None and e.get("type", "none") != "none":
            has_arrow = True
    if kind == "cxnSp" and not has_arrow:
        has_arrow = True  # a connector drawn between two things is read as directional anyway

    cnv = el.find(f".//{P}cNvSpPr")
    is_textbox = cnv is not None and cnv.get("txBox") == "1"

    return Shape(kind=kind, text=text, x=x, y=y, cx=cx, cy=cy, prst=prst, max_pt=max_pt,
                 has_arrow=has_arrow, is_textbox=is_textbox)


def read_deck(path: Path) -> Tuple[List[List[Shape]], List[str], int, int]:
    """-> (shapes per slide, notes per slide, slide width, slide height) in EMU."""
    with zipfile.ZipFile(path) as z:
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        sz = pres.find(f"{P}sldSz")
        w = int(sz.get("cx")) if sz is not None else 12192000
        h = int(sz.get("cy")) if sz is not None else 6858000

        names = sorted(
            (n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
            key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)),
        )
        slides: List[List[Shape]] = []
        notes: List[str] = []
        for n in names:
            root = ET.fromstring(z.read(n))
            tree = root.find(f".//{P}cSld/{P}spTree")
            shapes: List[Shape] = []
            if tree is not None:
                for child in tree:
                    tag = child.tag.split("}")[-1]
                    if tag in {"sp", "pic", "graphicFrame", "cxnSp", "grpSp"}:
                        s = parse_shape(child, tag)
                        if s:
                            shapes.append(s)
            slides.append(shapes)

            idx = int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1))
            note_name = f"ppt/notesSlides/notesSlide{idx}.xml"
            if note_name in z.namelist():
                nroot = ET.fromstring(z.read(note_name))
                notes.append("".join(t.text or "" for t in nroot.iter(f"{A}t")))
            else:
                notes.append("")
    return slides, notes, w, h


# ---------------------------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------------------------


def is_page_number(text: str) -> bool:
    """A bare page number earns its place — someone in Q&A says "go back to 12"."""
    return bool(re.fullmatch(r"\d{1,3}", text.strip()))


def mark_chrome(slides, h) -> None:
    """Decide once what counts as chrome, so every check below agrees.

    Chrome = small type hugging the top or bottom edge. A bare page number is exempt: it is the one
    piece of edge furniture the audience actually uses.
    """
    top_band, bottom_band = 0.12 * h, 0.88 * h
    for shapes in slides:
        for s in shapes:
            if s.kind != "sp" or not s.text or is_page_number(s.text):
                continue
            if s.max_pt and s.max_pt > 14:
                continue  # a real headline, not chrome
            if (s.y + s.cy <= top_band) or (s.y >= bottom_band):
                s.is_chrome = True


def check_chrome(slides, w, h) -> List[Finding]:
    """The little words along the top and bottom edge of every slide."""
    with_chrome: List[int] = []
    samples: List[str] = []
    for i, shapes in enumerate(slides, start=1):
        chrome = [s for s in shapes if s.is_chrome]
        if chrome:
            with_chrome.append(i)
            for s in chrome:
                if len(samples) < 5 and s.text not in samples:
                    samples.append(s.text)

    n = len(slides)
    if n >= 4 and len(with_chrome) / n >= 0.6:
        return [Finding(
            DETECTOR, "CHROME_ON_EVERY_SLIDE", None,
            f"{len(with_chrome)} of {n} slides carry small text along the top or bottom edge "
            "(eyebrow labels / brand footers). This is the first thing a reader registers as "
            "machine-made, and it carries no information they need.",
            [f"e.g. {t!r}" for t in samples] + ["Keep the page number. Drop the rest, or keep it "
                                                "only on the title and divider slides."],
        )]
    return []


def check_scaffold(slides, notes) -> List[Finding]:
    """Sentences that record the assembling of a thought rather than the thought."""
    out: List[Finding] = []
    for i, shapes in enumerate(slides, start=1):
        blob = " ".join(s.text for s in shapes if s.text)
        for pat, label in SCAFFOLD_PATTERNS:
            m = re.search(pat, blob, re.IGNORECASE)
            if m:
                out.append(Finding(
                    DETECTOR, "SCAFFOLD_PHRASE", i,
                    f"Slide {i} narrates its own construction: {label!r}.",
                    [f"…{blob[max(0, m.start() - 40):m.end() + 40].strip()}…",
                     "Delete the sentence and keep what it was pointing at. This is the scaffolding "
                     "a writer takes down before handing over the building."],
                ))
                break  # one finding per slide is enough to make the point
    for i, note in enumerate(notes, start=1):
        for pat, label in SCAFFOLD_PATTERNS:
            m = re.search(pat, note, re.IGNORECASE)
            if m:
                out.append(Finding(
                    DETECTOR, "SCAFFOLD_PHRASE", i,
                    f"Speaker notes for slide {i} narrate their own construction: {label!r}.",
                    [f"…{note[max(0, m.start() - 40):m.end() + 40].strip()}…",
                     "You will say this out loud. Say the finding instead."],
                ))
                break
    return out


def check_topic_titles(slides, h) -> List[Finding]:
    """A content slide whose headline is a filing label instead of the finding."""
    out: List[Finding] = []
    for i, shapes in enumerate(slides, start=1):
        texts = [s for s in shapes if s.kind == "sp" and s.text]
        if not texts:
            continue
        # The headline: the largest type in the upper half.
        upper = [s for s in texts if s.cym < h * 0.5]
        if not upper:
            continue
        head = max(upper, key=lambda s: (s.max_pt, -s.y))
        label = head.text.strip().rstrip(":：.").lower()
        if label not in TOPIC_TITLES:
            continue
        # A divider slide may carry a filing label — that is its whole job. A slide with a body
        # may not.
        body = [s for s in shapes if s is not head and (s.text or s.kind in {"pic", "graphicFrame"})]
        if len(body) < 2:
            continue
        out.append(Finding(
            DETECTOR, "TOPIC_TITLE", i,
            f"Slide {i} is titled {head.text.strip()!r} — a filing label, on a slide that has a "
            "body. The headline is the one line everyone reads; this one spends it saying nothing.",
            ["Say the finding: not 'Results' but 'Adjunctive ablation halved local recurrence "
             "(12% vs 26%).' The body then becomes the evidence for it (assertion-evidence, "
             "Alley & Neeley 2005)."],
        ))
    return out


def check_shape_monotony(slides) -> List[Finding]:
    """The same shape, at the same size, over and over — the shape the generator has, not the shape
    the idea needs."""
    buckets: Dict[Tuple[str, int, int], int] = {}
    total = 0
    for shapes in slides:
        for s in shapes:
            # A text box is text, not a drawn shape. Counting them was diluting the denominator so
            # badly that nine identical boxes on one slide came out under the threshold — the check
            # existed and did nothing, which is the worst state for a check to be in.
            if s.kind != "sp" or s.is_textbox or not s.prst or s.prst == "line":
                continue
            total += 1
            key = (s.prst, round(s.cx / EMU_PER_INCH * 2), round(s.cy / EMU_PER_INCH * 2))
            buckets[key] = buckets.get(key, 0) + 1
    if total < 8:
        return []
    (prst, bw, bh), n = max(buckets.items(), key=lambda kv: kv[1])
    if n >= 8 and n / total >= 0.5:
        return [Finding(
            DETECTOR, "SHAPE_MONOTONY", None,
            f"{n} of {total} drawn shapes are the same {prst} at the same size "
            f"(~{bw / 2:.1f}\" × {bh / 2:.1f}\"). A deck built out of one repeated box reads as "
            "generated, and the repetition is doing no work.",
            ["Either the ideas are genuinely parallel — in which case say so once, in a table — or "
             "they are not, and the shapes should differ because the ideas do."],
        )]
    return []


def check_dead_space(slides, w, h) -> List[Finding]:
    """A wide empty stripe on a slide that is nearly empty anyway.

    This one nearly shipped as a false-positive machine. A first pass measured the biggest vertical
    gap between objects and fired at 1.5" — which flagged the *clean* fixture, because the footer
    sits at the bottom edge and every ordinary title-then-body slide has a gap under its headline.
    A check that fires on good work is a check that gets switched off, and it takes the other five
    with it.

    So it now demands BOTH conditions, and ignores chrome (which is what created the phantom gaps):

      * a band of ≥2.5" with nothing in it, between the *content* rows, and
      * a slide that is genuinely sparse — the content covers under a fifth of the surface.

    A title above a large body has the first and not the second. A well-composed diagram with air
    around it has the second and not the first. Only a slide that is both mostly empty AND has a
    hole in the middle of it is the thing being described: boxes placed by a layout rule that ran
    out of content.
    """
    out: List[Finding] = []
    band_limit = 2.5 * EMU_PER_INCH
    slide_area = w * h

    for i, shapes in enumerate(slides, start=1):
        objs = [
            s for s in shapes
            if not s.is_chrome
            and not is_page_number(s.text)
            and (s.text or s.kind in {"pic", "graphicFrame"})
            and s.cy > 0
        ]
        if len(objs) < 3:
            continue  # one big figure is not dead space, it is a figure

        coverage = sum(s.cx * s.cy for s in objs) / slide_area
        if coverage >= 0.20:
            continue  # the slide is doing work; whatever gaps it has are composition

        rows = sorted((s.y, s.y + s.cy) for s in objs)
        merged: List[List[int]] = []
        for top, bot in rows:
            if merged and top <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], bot)
            else:
                merged.append([top, bot])
        gaps = [(merged[k + 1][0] - merged[k][1]) for k in range(len(merged) - 1)]
        if not gaps or max(gaps) < band_limit:
            continue

        out.append(Finding(
            DETECTOR, "DEAD_SPACE_BAND", i,
            f"Slide {i} is {coverage * 100:.0f}% covered and has a "
            f"{max(gaps) / EMU_PER_INCH:.1f}\" empty band through the middle of it. That is not "
            "negative space, which is chosen — it is what is left over when boxes are placed by a "
            "layout rule that ran out of content.",
            ["Either this slide has more to say and should say it, or it has one thing to say and "
             "should say that one thing large."],
        ))
    return out


def check_arrows(slides) -> List[Finding]:
    """Arrows are claims. An unlabelled arrow is read differently by every person in the room."""
    out: List[Finding] = []
    near = 0.7 * EMU_PER_INCH
    for i, shapes in enumerate(slides, start=1):
        arrows = [s for s in shapes if s.has_arrow]
        if len(arrows) < 2:
            continue
        # A label is a label because it is not the headline — not because it is under some point
        # size. Tying this to "≤18 pt" made the two checks fight: a legible 20-pt arrow label would
        # satisfy a reader and the back row, and then be invisible *here*, so the slide would be
        # reported as having unlabelled arrows. Sizing advice must not silently redefine what a
        # label is.
        texts = [s for s in shapes if s.text.strip()]
        head_pt = max((s.max_pt for s in texts), default=0.0)
        labels = [s for s in texts if head_pt == 0.0 or s.max_pt < head_pt]
        unlabelled = 0
        for a in arrows:
            if a.text.strip():
                continue
            if any(abs(t.cxm - a.cxm) < near and abs(t.cym - a.cym) < near for t in labels):
                continue
            unlabelled += 1
        if unlabelled >= 2:
            out.append(Finding(
                DETECTOR, "ARROW_NO_SEMANTICS", i,
                f"Slide {i} has {len(arrows)} arrows and {unlabelled} of them carry no label. "
                "An arrow is a claim — causes, becomes, flows into, is compared with — and an "
                "unlabelled one is read differently by every person in the room.",
                ["Label each arrow, or add a legend that says what an arrow means on this diagram. "
                 "One wrong arrow can derail the whole discussion."],
            ))
    return out


# ---------------------------------------------------------------------------------------------


def audit(path: Path) -> List[Finding]:
    slides, notes, w, h = read_deck(path)
    mark_chrome(slides, h)  # one definition of chrome, agreed before any check runs
    findings: List[Finding] = []
    findings += check_chrome(slides, w, h)
    findings += check_topic_titles(slides, h)
    findings += check_scaffold(slides, notes)
    findings += check_shape_monotony(slides)
    findings += check_dead_space(slides, w, h)
    findings += check_arrows(slides)
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("deck", type=Path, help="the built .pptx")
    ap.add_argument("--json", type=Path, help="write the findings here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if anything is found")
    a = ap.parse_args()

    if not a.deck.is_file():
        print(f"cannot read {a.deck}", file=sys.stderr)
        return 2
    try:
        findings = audit(a.deck)
    except (zipfile.BadZipFile, ET.ParseError, KeyError) as exc:
        print(f"{a.deck} is not a readable .pptx ({exc})", file=sys.stderr)
        return 2

    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(
            {"detector": DETECTOR, "deck": str(a.deck),
             "findings": [f.__dict__ for f in findings]},
            indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not findings:
        print(f"OK: {a.deck.name} carries none of the marks this checks for.")
        return 0

    print(f"{len(findings)} finding(s) in {a.deck.name}\n")
    for f in findings:
        where = f"slide {f.slide}" if f.slide else "deck"
        print(f"  [{f.verdict}] ({where})")
        print(f"      {f.summary}")
        for e in f.evidence:
            print(f"      - {e}")
        print()
    print("None of this is about beauty. It is about whether the deck says anything.")
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""JATS XML -> Markdown, for the held-out corpus. The renderer IS the denominator.

WHY THIS EXISTS AS A COMMITTED SCRIPT
    The first held-out corpus was rendered by a throwaway script in a session scratchpad. That
    script took four corrections, each of which moved the measured fire rate, and then it was gone
    — so the corpus could not be rebuilt, the corrections could not be re-run, and the number had
    no reproducible provenance. For a measurement instrument that is a hole, not an inconvenience.

WHAT A DROPPED SECTION DOES TO A MEASUREMENT
    A converter that loses a section the detectors read does not produce a missing signal. It
    produces a FIRE, and that fire is indistinguishable from a detector defect at the point of
    reading. The four corrections, in order, and the fire rate after each:

      <body> only                                    disclosure detector fired on 12 of 12   0.031
      + <author-notes>, <back>                       JAMA / Elsevier keep disclosures there   0.018
      + <funding-group>, <custom-meta>               PLOS keeps them there and nowhere else   0.015
      + <contrib-group> (the byline)                 CRediT cannot resolve initials without it 0.015

    And a fifth, subtler one: <author-notes> flattened into a single paragraph puts every JAMA
    label ("Funding/Support:", "Data Sharing Statement:") mid-line, where a line-anchored section
    finder cannot see it. Structure is part of the content.

THE BIAS THIS GUARDS AGAINST
    Publishers disagree about WHERE a disclosure lives in the XML. A renderer that knows one
    publisher's location manufactures fires for the other publishers' papers only — a bias
    correlated with journal rather than with quality, which for a benchmark corpus is worse than
    noise: it is systematic, and it aligns with a variable nobody thought to control. So the
    fidelity test is PER PUBLISHER SHAPE, not overall (test_render_jats.sh).

Usage:
    render_jats.py --xml a.nxml --out _corpus/heldout/record_id.md
    render_jats.py --xml-dir raw/ --out-dir _corpus/heldout/   # stem is preserved as record_id

Exit: 0 rendered, 1 a required element was absent (named), 2 usage/parse error. Stdlib-only.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

# PMC writes housekeeping into custom-meta too. These are not article content and a detector that
# reads them is reading our pipeline, not the paper.
PMC_INTERNAL_META = {"pmc-simple-viewer", "pmc-article-type", "processing-meta", "dtd-version"}

# Elements whose text is never article prose.
DROP_TAGS = {"xref", "graphic", "inline-graphic", "media", "table-wrap-foot", "label"}


def text_of(el: Optional[ET.Element]) -> str:
    """All descendant text, minus cross-reference furniture, whitespace-normalised.

    itertext() would happily inline every <xref> number into the sentence, turning
    "as shown previously" into "as shown previously 12 13 14" — which is how a citation-density
    detector comes to measure our converter.
    """
    if el is None:
        return ""
    parts: List[str] = []

    def walk(node: ET.Element) -> None:
        tag = node.tag.split("}")[-1]
        if tag in DROP_TAGS:
            if node.tail:
                parts.append(node.tail)
            return
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
        if node.tail:
            parts.append(node.tail)

    walk(el)
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def find(el: ET.Element, path: str) -> Optional[ET.Element]:
    return el.find(path)


def byline(article_meta: ET.Element) -> str:
    """Author names in order. Without this the CRediT check cannot resolve a single initial."""
    names: List[str] = []
    for group in article_meta.findall("contrib-group"):
        for contrib in group.findall("contrib"):
            if contrib.get("contrib-type") not in (None, "author"):
                continue
            name = contrib.find("name")
            if name is not None:
                given = text_of(name.find("given-names"))
                sur = text_of(name.find("surname"))
                full = " ".join(x for x in (given, sur) if x)
                if full:
                    names.append(full)
                continue
            coll = contrib.find("collab")
            if coll is not None and text_of(coll):
                names.append(text_of(coll))
    return ", ".join(names)


def render_sections(parent: ET.Element, level: int, out: List[str]) -> None:
    """Sections recursively, heading level tracking depth. Paragraphs stay paragraphs."""
    for child in parent:
        tag = child.tag.split("}")[-1]
        if tag == "sec":
            title = text_of(child.find("title"))
            if title:
                out.append(f"\n{'#' * min(level, 6)} {title}\n")
            render_sections(child, level + 1, out)
        elif tag in ("p", "disp-quote", "statement"):
            t = text_of(child)
            if t:
                out.append(t + "\n")
        elif tag == "list":
            for item in child.findall("list-item"):
                t = text_of(item)
                if t:
                    out.append(f"- {t}")
            out.append("")
        elif tag in ("table-wrap", "fig"):
            cap = text_of(child.find("caption"))
            lab = text_of(child.find("label"))
            if cap or lab:
                out.append(f"**{lab}** {cap}".strip() + "\n")
        elif tag == "title":
            continue


def render_author_notes(article_meta: ET.Element, out: List[str]) -> None:
    """Author notes, ONE PARAGRAPH PER CHILD.

    Flattening these was the fourth correction. JAMA puts "Funding/Support:", "Data Sharing
    Statement:" and "Conflict of Interest Disclosures:" in sibling <fn> blocks; joined into one
    paragraph, every label lands mid-line and a line-anchored section finder sees none of them.
    """
    notes = article_meta.find("author-notes")
    if notes is None:
        return
    blocks: List[str] = []
    for child in notes:
        tag = child.tag.split("}")[-1]
        if tag == "corresp":
            t = text_of(child)
            if t:
                blocks.append(t)
        elif tag == "fn":
            for p in child.findall("p") or [child]:
                t = text_of(p)
                if t:
                    blocks.append(t)
        else:
            t = text_of(child)
            if t:
                blocks.append(t)
    if blocks:
        out.append("\n## Article Information\n")
        out.extend(b + "\n" for b in blocks)


def render_funding(article_meta: ET.Element, out: List[str]) -> None:
    """PLOS keeps funding in <funding-group> and nowhere a body-only renderer would look."""
    fg = article_meta.find("funding-group")
    if fg is None:
        return
    lines: List[str] = []
    stmt = fg.find("funding-statement")
    if stmt is not None and text_of(stmt):
        lines.append(text_of(stmt))
    for award in fg.findall("award-group"):
        t = text_of(award)
        if t:
            lines.append(t)
    if lines:
        out.append("\n## Funding\n")
        out.extend(x + "\n" for x in lines)


def render_custom_meta(article_meta: ET.Element, out: List[str]) -> None:
    """Non-PMC custom-meta. PLOS puts data availability here — as a <custom-meta>, not a section.

    Rendered as `**name:** value` on its own line so a label-anchored finder can see it, which is
    the same lesson as author-notes: the label has to start a line.
    """
    for group in article_meta.findall("custom-meta-group"):
        for meta in group.findall("custom-meta"):
            name = text_of(meta.find("meta-name"))
            value = text_of(meta.find("meta-value"))
            if not name or not value:
                continue
            if name.strip().lower() in PMC_INTERNAL_META:
                continue
            label = name.replace("-", " ").strip().title()
            out.append(f"\n**{label}:** {value}\n")


def render_back(back: Optional[ET.Element], out: List[str]) -> None:
    """Acknowledgements, notes, footnote groups, back sections, then references.

    Elsevier's "Declaration of competing interest" is a back <sec>; MDPI's contributions live in a
    back <fn-group>. Both are invisible to a <body>-only renderer.
    """
    if back is None:
        return
    for child in back:
        tag = child.tag.split("}")[-1]
        if tag == "ack":
            out.append("\n## Acknowledgements\n")
            render_sections(child, 3, out)
        elif tag == "fn-group":
            out.append("\n## Notes\n")
            for fn in child.findall("fn"):
                for p in fn.findall("p") or [fn]:
                    t = text_of(p)
                    if t:
                        out.append(t + "\n")
        elif tag == "notes":
            title = text_of(child.find("title")) or "Notes"
            out.append(f"\n## {title}\n")
            render_sections(child, 3, out)
        elif tag == "sec":
            title = text_of(child.find("title")) or "Section"
            out.append(f"\n## {title}\n")
            render_sections(child, 3, out)
        elif tag == "ref-list":
            out.append("\n## References\n")
            for i, ref in enumerate(child.findall("ref"), 1):
                t = text_of(ref)
                if t:
                    out.append(f"{i}. {t}")
            out.append("")


def render(xml_path: Path) -> str:
    try:
        root = ET.parse(str(xml_path)).getroot()
    except ET.ParseError as exc:
        raise SystemExit(f"render_jats: cannot parse {xml_path}: {exc}")

    article = root if root.tag.split("}")[-1] == "article" else root.find(".//article")
    if article is None:
        raise SystemExit(f"render_jats: no <article> element in {xml_path}")

    front = article.find("front")
    article_meta = front.find("article-meta") if front is not None else None
    if article_meta is None:
        raise SystemExit(f"render_jats: no front/article-meta in {xml_path}")

    out: List[str] = []
    title = text_of(article_meta.find("title-group/article-title"))
    out.append(f"# {title}\n" if title else "# (untitled)\n")

    names = byline(article_meta)
    if names:
        out.append(names + "\n")

    for abstract in article_meta.findall("abstract"):
        kind = abstract.get("abstract-type")
        out.append(f"\n## {'Abstract' if not kind else kind.title() + ' Abstract'}\n")
        render_sections(abstract, 3, out)
        # An unsectioned abstract is a bare <p> run, which render_sections already emits.

    body = article.find("body")
    if body is not None:
        render_sections(body, 2, out)

    render_author_notes(article_meta, out)
    render_funding(article_meta, out)
    render_custom_meta(article_meta, out)
    render_back(article.find("back"), out)

    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--xml", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--xml-dir", type=Path)
    ap.add_argument("--out-dir", type=Path)
    a = ap.parse_args(argv)

    if a.xml_dir:
        if not a.out_dir:
            ap.error("--xml-dir requires --out-dir")
        a.out_dir.mkdir(parents=True, exist_ok=True)
        n = 0
        for x in sorted(a.xml_dir.iterdir()):
            if x.suffix.lower() not in (".xml", ".nxml"):
                continue
            (a.out_dir / f"{x.stem}.md").write_text(render(x), encoding="utf-8")
            n += 1
        print(f"render_jats: {n} file(s) -> {a.out_dir}")
        return 0

    if not a.xml or not a.out:
        ap.error("pass --xml and --out, or --xml-dir and --out-dir")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(render(a.xml), encoding="utf-8")
    print(f"render_jats: {a.xml} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

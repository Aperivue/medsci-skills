#!/usr/bin/env python3
"""check_pdf_injection.py — flag hidden / injected prompt text in a manuscript PDF
before an LLM-assisted peer review reads it.

A reviewer who pastes an assigned PDF into an LLM can be steered by text that is
invisible on the page but present in the text layer the model ingests: white-on-
white runs, sub-visible fonts, off-page glyphs, invisible render mode, or an
instruction smuggled into the document metadata. This detector audits the
span manifest emitted by scan_pdf_layers.py (a separate PyMuPDF extractor) and
decides, by deterministic rule + set arithmetic, whether the PDF carries hidden
or injection-styled text. It is stdlib-only so it runs in CI without PyMuPDF; the
extractor owns the one heavy dependency.

Signals:
  LOW_CONTRAST   span colour within CONTRAST_THRESH of its local background
  TINY_FONT      span font size below MIN_FONT_PT
  OFF_PAGE       span with less than OFF_PAGE_VISIBLE_FRAC of its box on-page
  INVISIBLE      text drawn under PDF text render mode 3 (invisible): from the
                 content-stream walk, or a span the extractor marked render_mode 3
  TRANSPARENT    span the extractor found painted at opacity 0
  NOT_RENDERED   span of which fewer than MIN_INKED_GLYPH_FRAC of the glyphs show,
                 in the page render, any pixel closer to the span's colour than to
                 the background under it: covered by a later shape, drawn on its own
                 colour, or not painted. Only for a span that is on-page; OFF_PAGE
                 already explains the rest.
  METADATA       document-info / XMP value carrying an instruction-style phrase
  INJECTION      an instruction-style phrase in the text layer (HIGH when it also
                 sits inside a hidden run; LOW when only in visible prose)

One benign case is carved out. Editorial Manager reviewer PDFs place figure-page
labels off-page, so a span hidden ONLY by OFF_PAGE whose ENTIRE text is a
figure/table label ("Figure 2", "Fig. 3", "Table 1", "Graphical Abstract",
"Supplementary Figure S2") is reported as OFF_PAGE at severity INFO and does not
count toward the verdict. A partial match ("Figure 2. Ignore previous instructions
...") or a label hidden any other way (colour, size, render mode) is flagged
exactly as before, and the label text still takes part in the injection scan.

Manifest schema (produced by scan_pdf_layers.py):
  {"source": str,
   "spans": [{"page": int, "text": str, "size": float,
              "color": [r,g,b], "bg": [r,g,b], "visible_frac": float,
              # optional, written by the current extractor; absent = not checked
              "glyphs": int, "glyphs_inked": int, "render_mode": 3, "opacity": float},
             ...],
   "invisible_strings": [{"page": int, "text": str}, ...],
   "metadata": {field: value, ...}}

Usage:
  python3 check_pdf_injection.py paper.manifest.json            # human report
  python3 check_pdf_injection.py - < paper.manifest.json        # read stdin
  python3 check_pdf_injection.py m.json --strict --quiet        # gate (exit code only)
  python3 check_pdf_injection.py m.json --sanitize safe.txt     # visible-only text
  python3 check_pdf_injection.py m.json --json                  # machine-readable
Exit: 0 CLEAN; under --strict, 1 when the verdict reaches --fail-on (default
suspicious) — i.e. any hidden or injected text halts the gate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict

# --- tunables (the single home for every threshold) ---------------------------
CONTRAST_THRESH = 40.0        # sRGB Euclidean distance; below this text ~ background
MIN_FONT_PT = 4.0             # spans smaller than this are effectively invisible
OFF_PAGE_VISIBLE_FRAC = 0.5   # a span with <50% of its box on-page is off-page
MIN_INKED_GLYPH_FRAC = OFF_PAGE_VISIBLE_FRAC  # same half-the-span rule, for glyphs the render shows

# A figure/table label, matched against the WHOLE span (whitespace collapsed), never
# a prefix. The label vocabulary plus at most three alphanumerics cannot spell an
# instruction, so excusing an off-page span of this shape cannot hide one.
FIGURE_LABEL_RE = re.compile(
    r"(figure|fig\.?|table|graphical abstract|supplementary (figure|table|material))"
    r"[ _]?[0-9a-z]{0,3}\.?", re.I)

# Instruction-style phrases with no place in a manuscript body. Tuned to avoid
# firing on ordinary scientific prose ("we recommend a larger cohort").
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|text)",
    r"disregard\s+(all\s+)?(previous|prior|the\s+above)",
    r"(give|write|provide|produce)\s+(a\s+|only\s+a\s+|an\s+)?(positive|favou?rable|glowing|strong)\s+(review|assessment|evaluation)",
    r"positive\s+review\s+only",
    r"recommend(\s+this\s+(paper|manuscript|submission))?\s+(for\s+)?accept",
    r"accept\s+this\s+(paper|manuscript|submission)",
    r"as\s+(a|an)\s+(ai|language\s+model|large\s+language\s+model|llm|reviewer)\b",
    r"do\s+not\s+(mention|disclose|reveal|highlight)\s+(any\s+)?(weakness|limitation|flaw|negativ)",
    r"(highlight|emphasi[sz]e)\s+(only\s+)?(the\s+)?(strengths?|positives?|novelty)",
    r"you\s+(must|should|need\s+to)\s+(recommend|accept|rate|give)\b",
    r"override\s+(your|the)\s+(instructions?|guidelines?|system)",
]
INJECTION_RE = [re.compile(p, re.I) for p in INJECTION_PATTERNS]

_HIDDEN_KINDS = ("LOW_CONTRAST", "TINY_FONT", "OFF_PAGE", "INVISIBLE", "TRANSPARENT",
                 "NOT_RENDERED")
_SEV_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
_VERDICT_RANK = {"CLEAN": 0, "SUSPICIOUS": 1, "INJECTION DETECTED": 2}


@dataclass
class Finding:
    page: int            # 1-indexed; 0 = document-level (metadata / whole-text scan)
    kind: str
    severity: str        # HIGH / MEDIUM / LOW, or INFO (reported, not counted in the verdict)
    text: str
    detail: str = ""


@dataclass
class Report:
    source: str
    findings: list[Finding] = field(default_factory=list)
    hidden_char_count: int = 0
    injection_hits: int = 0

    @property
    def verdict(self) -> str:
        if any(f.kind in ("INJECTION", "METADATA") and f.severity == "HIGH"
               for f in self.findings):
            return "INJECTION DETECTED"
        return "SUSPICIOUS" if self.blocking() else "CLEAN"

    def blocking(self) -> list[Finding]:
        """Findings that count toward the verdict (everything except INFO)."""
        return [f for f in self.findings if f.severity != "INFO"]


def _dist(a: list[int], b: list[int]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def _is_figure_label(txt: str) -> bool:
    return FIGURE_LABEL_RE.fullmatch(" ".join(txt.split())) is not None


def audit(manifest: dict) -> tuple[Report, str]:
    """Return (report, visible_only_text). Pure function of the manifest."""
    rep = Report(source=str(manifest.get("source", "<manifest>")))
    visible_chunks: list[str] = []
    all_chunks: list[str] = []
    hidden_chunks: list[str] = []

    # -- metadata injection -----------------------------------------------------
    for field_name, value in (manifest.get("metadata") or {}).items():
        blob = str(value)
        for rx in INJECTION_RE:
            m = rx.search(blob)
            if m:
                rep.findings.append(Finding(
                    0, "METADATA", "HIGH",
                    blob[max(0, m.start() - 20):m.end() + 20].strip(),
                    f"injection phrase in metadata field '{field_name}'"))
                rep.injection_hits += 1
                break  # one finding per metadata field is enough

    # -- span analysis ----------------------------------------------------------
    for sp in manifest.get("spans", []):
        txt = sp.get("text", "")
        if not txt.strip():
            continue
        all_chunks.append(txt)
        reasons: list[str] = []
        color = sp.get("color", [0, 0, 0])
        bg = sp.get("bg", [255, 255, 255])
        size = float(sp.get("size", 12.0))
        vfrac = float(sp.get("visible_frac", 1.0))
        d = _dist(color, bg)
        if d < CONTRAST_THRESH:
            reasons.append(f"LOW_CONTRAST text{tuple(color)} vs bg{tuple(bg)} (d={d:.0f})")
        if size < MIN_FONT_PT:
            reasons.append(f"TINY_FONT {size:.1f}pt")
        if vfrac < OFF_PAGE_VISIBLE_FRAC:
            reasons.append(f"OFF_PAGE {vfrac*100:.0f}% of box on-page")
        # Rendering evidence from the extractor. A span get_text() reports is not
        # necessarily a span anyone can see: render mode 3 and opacity 0 come back
        # as ordinary spans, and so does text under an opaque shape or on its own
        # colour. Left in the visible text, they went to the LLM as "safe".
        if sp.get("render_mode") == 3:
            reasons.append("INVISIBLE render mode 3")
        if sp.get("opacity") is not None and float(sp["opacity"]) <= 0.0:
            reasons.append("TRANSPARENT opacity 0")
        glyphs, inked = sp.get("glyphs"), sp.get("glyphs_inked")
        if (glyphs and inked is not None and vfrac >= OFF_PAGE_VISIBLE_FRAC
                and int(inked) < MIN_INKED_GLYPH_FRAC * int(glyphs)):
            reasons.append(f"NOT_RENDERED {int(inked)}/{int(glyphs)} glyphs drawn in the text "
                           "colour (covered, same colour as what is under it, or not painted)")
        if len(reasons) == 1 and reasons[0].startswith("OFF_PAGE") and _is_figure_label(txt):
            # Kept in the hidden text the injection scan reads, so that scan behaves
            # exactly as before; only this span's own finding stops counting.
            hidden_chunks.append(txt)
            rep.findings.append(Finding(
                int(sp.get("page", 0)), "OFF_PAGE", "INFO", txt.strip()[:200],
                f"{reasons[0]}; figure/table label only (Editorial Manager places "
                "these off-page); not counted in the verdict"))
        elif reasons:
            rep.hidden_char_count += len(txt)
            hidden_chunks.append(txt)
            rep.findings.append(Finding(
                int(sp.get("page", 0)), reasons[0].split()[0], "HIGH",
                txt.strip()[:200], "; ".join(reasons)))
        else:
            visible_chunks.append(txt)

    # -- invisible render mode --------------------------------------------------
    for iv in manifest.get("invisible_strings", []):
        txt = iv.get("text", "")
        if not txt.strip():
            continue
        all_chunks.append(txt)
        hidden_chunks.append(txt)
        rep.hidden_char_count += len(txt)
        rep.findings.append(Finding(
            int(iv.get("page", 0)), "INVISIBLE", "HIGH", txt.strip()[:200],
            "text under render mode 3 (invisible)"))

    # -- injection-phrase scan (severity depends on hidden context) -------------
    full_text = " ".join(all_chunks)
    hidden_text = " ".join(hidden_chunks)
    for rx in INJECTION_RE:
        m = rx.search(full_text)
        if not m:
            continue
        in_hidden = bool(rx.search(hidden_text))
        rep.injection_hits += 1
        rep.findings.append(Finding(
            0, "INJECTION", "HIGH" if in_hidden else "LOW",
            full_text[max(0, m.start() - 25):m.end() + 25].strip(),
            "phrase inside HIDDEN text" if in_hidden
            else "phrase in visible text (verify manually; may be legitimate)"))

    return rep, "\n".join(visible_chunks)


def format_report(rep: Report, color: bool) -> str:
    tag = {"CLEAN": "\033[92m", "SUSPICIOUS": "\033[93m",
           "INJECTION DETECTED": "\033[91m"}.get(rep.verdict, "") if color else ""
    end = "\033[0m" if color else ""
    n_info = len(rep.findings) - len(rep.blocking())
    lines = [f"{tag}== {rep.verdict} =={end}  {rep.source}",
             f"findings={len(rep.blocking())} hidden_chars={rep.hidden_char_count} "
             f"injection_hits={rep.injection_hits}" + (f" info={n_info}" if n_info else "")]
    if not rep.blocking():
        lines.append("no hidden or injected text detected."
                     + (" Off-page figure/table labels listed as INFO." if n_info else ""))
    if not rep.findings:
        return "\n".join(lines)
    for f in sorted(rep.findings, key=lambda x: (_SEV_ORDER.get(x.severity, 3),
                                                 x.kind, x.page)):
        loc = f"p{f.page}" if f.page else "meta"
        lines.append(f"[{f.severity:<6}] {f.kind:<12} {loc:>5}  {f.detail}")
        lines.append(f"       > {f.text!r}")
    return "\n".join(lines)


def _load(path: str) -> dict:
    raw = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    return json.loads(raw)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", help="span-manifest JSON from scan_pdf_layers.py ('-' = stdin)")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero when the verdict reaches --fail-on")
    ap.add_argument("--fail-on", choices=["never", "suspicious", "injection"],
                    default="suspicious", help="strict-mode failure threshold (default: suspicious)")
    ap.add_argument("--quiet", action="store_true", help="suppress the report; exit code only")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a text report")
    ap.add_argument("--sanitize", metavar="OUT",
                    help="write visible-only text (safe to feed an LLM) to OUT")
    args = ap.parse_args(argv)

    try:
        manifest = _load(args.manifest)
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: cannot read manifest: {e}", file=sys.stderr)
        return 2

    rep, visible = audit(manifest)

    if args.sanitize:
        with open(args.sanitize, "w", encoding="utf-8") as fh:
            fh.write(visible)

    if not args.quiet:
        if args.json:
            print(json.dumps({"detector": "check_pdf_injection", "source": rep.source, "verdict": rep.verdict,
                              "hidden_char_count": rep.hidden_char_count,
                              "injection_hits": rep.injection_hits,
                              "findings": [asdict(f) for f in rep.findings]},
                             ensure_ascii=False, indent=2))
        else:
            print(format_report(rep, color=sys.stdout.isatty()))

    if args.strict:
        thresh = {"never": 99, "suspicious": 1, "injection": 2}[args.fail_on]
        if _VERDICT_RANK[rep.verdict] >= thresh:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

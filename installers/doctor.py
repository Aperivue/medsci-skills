#!/usr/bin/env python3
"""What MedSci Skills can actually do on THIS computer — and how to fix what it cannot.

Python is the only hard requirement: every integrity detector is stdlib-only, and so are the
skills that draft, review, and audit a manuscript. Everything else is needed by *some* skills and
not others — pandoc to render a manuscript into a journal-formatted Word file, poppler to read a
submission PDF, python-docx to open a .docx at all.

Each of those skills already fails politely when its tool is absent. The problem is *when*: you
find out at the moment you needed it, halfway through the work, and a clinician who hits that
message does not install a package manager — they close the window and go back to doing it by
hand. This tells them before they start, in terms of what they were trying to do, and offers to
install the missing piece for them.

Two rules it does not break:

  * It never installs anything without being asked. Not on import, not in --brief, not silently.
  * It never installs anything *large* — a TeX distribution is several gigabytes, R is a separate
    ecosystem, and PyTorch is not something to drop on a laptop because a setup script felt like
    it. Those are printed with their size and their command, and left to the person.

Usage:
    doctor.py               # what works, what does not, and the exact fix for each
    doctor.py --fix         # ask before installing each missing piece
    doctor.py --brief       # only what is missing (what the installer prints at the end)
    doctor.py --json        # machine-readable (used by the tests)

Stdlib only. Exit code is 0 unless --strict is given: a missing *optional* tool is not an error.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

REPO = "https://github.com/Aperivue/medsci-skills"


# --------------------------------------------------------------------------------------------
# What a capability can need
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Pip:
    """A Python package."""

    module: str  # what `import` calls it
    package: str  # what pip calls it
    heavy: str = ""  # a size, e.g. "~2.5 GB". Set => never installed for you, only explained.


@dataclass(frozen=True)
class Tool:
    """A program that must exist on PATH."""

    binary: str
    label: str
    brew: str = ""
    winget: str = ""
    apt: str = ""
    page: str = ""  # a download page that works on ANY platform (a .pkg, a .exe, a landing page)
    win_page: str = ""  # a Windows-only download, when `page` would send a Mac user somewhere wrong
    heavy: str = ""  # a size, e.g. "~4 GB". Set => never installed for you, only explained.


@dataclass(frozen=True)
class Capability:
    """Something the person wanted to do — not a package they have never heard of."""

    key: str
    title: str
    skills: str
    pips: Sequence[Pip] = field(default_factory=tuple)
    tools: Sequence[Tool] = field(default_factory=tuple)
    aside: str = ""  # shown even when ready — e.g. "you probably do not need this"


# --------------------------------------------------------------------------------------------
# The tools, named once
# --------------------------------------------------------------------------------------------

PANDOC = Tool(
    binary="pandoc",
    label="pandoc",
    brew="pandoc",
    winget="JohnMacFarlane.Pandoc",
    apt="pandoc",
    page="https://pandoc.org/installing.html",
)

# poppler gives pdftotext/pdfinfo. Homebrew and apt package it; on Windows there is no reliable
# winget package, so we send people to the build everyone actually uses rather than invent an id
# that would fail on their machine. That build is WINDOWS-ONLY — offering it to a Mac user as "the
# download page" would send them somewhere useless, so it is not `page`. On macOS there is no
# double-click poppler, and saying so is better than pretending.
POPPLER = Tool(
    binary="pdftotext",
    label="poppler (pdftotext)",
    brew="poppler",
    apt="poppler-utils",
    win_page="https://github.com/oschwartz10612/poppler-windows/releases",
)

GH = Tool(
    binary="gh",
    label="GitHub CLI",
    brew="gh",
    winget="GitHub.cli",
    apt="gh",
    page="https://cli.github.com/",
)

XELATEX = Tool(
    binary="xelatex",
    label="XeLaTeX (a TeX distribution)",
    brew="--cask mactex-no-gui",
    winget="MiKTeX.MiKTeX",
    apt="texlive-xetex texlive-fonts-recommended",
    page="https://www.tug.org/mactex/",
    heavy="~1–4 GB",
)

RLANG = Tool(
    binary="Rscript",
    label="R",
    brew="--cask r",
    winget="RProject.R",
    apt="r-base",
    page="https://cran.r-project.org/",
    heavy="~200 MB + packages",
)

TESSERACT = Tool(
    binary="tesseract",
    label="Tesseract OCR",
    brew="tesseract",
    winget="UB-Mannheim.TesseractOCR",
    apt="tesseract-ocr",
    page="https://github.com/tesseract-ocr/tesseract",
)


# --------------------------------------------------------------------------------------------
# The capabilities, in the order a clinician meets them
# --------------------------------------------------------------------------------------------

CAPABILITIES: Tuple[Capability, ...] = (
    Capability(
        key="core",
        title="Draft, review, and audit a manuscript",
        skills="/write-paper, /self-review, /check-reporting, and every integrity detector",
        # Nothing. This is the point of the toolkit being stdlib-only.
    ),
    Capability(
        key="everyday",
        title="Open and check Word documents, and read project files",
        skills="/manage-refs, /revise, /peer-review, /sync-submission, /fill-protocol",
        pips=(Pip("docx", "python-docx"), Pip("yaml", "PyYAML")),
    ),
    Capability(
        key="render",
        title="Turn your manuscript into a journal-formatted Word file",
        skills="/manage-refs (render_pandoc.sh — the CSL renderer)",
        tools=(PANDOC,),
    ),
    Capability(
        key="pdf",
        title="Read and QC PDFs — submission proofs, checklists, codebooks",
        skills="/sync-submission, /find-cohort-gap",
        tools=(POPPLER,),
    ),
    Capability(
        key="pdf_deep",
        title="Scan a PDF's hidden layers; lift a figure out of a paper",
        skills="/peer-review (prompt-injection scan), /make-figures",
        pips=(Pip("fitz", "PyMuPDF"),),
    ),
    Capability(
        key="figures",
        title="Make publication figures — STROBE/PRISMA flow, forest, ROC",
        skills="/make-figures",
        pips=(
            Pip("matplotlib", "matplotlib"),
            Pip("numpy", "numpy"),
            Pip("PIL", "Pillow"),
            Pip("lxml", "lxml"),
            Pip("pptx", "python-pptx"),
        ),
    ),
    Capability(
        key="slides",
        title="Build slide decks — journal club, grand rounds, conference",
        skills="/present-paper",
        pips=(Pip("pptx", "python-pptx"), Pip("PIL", "Pillow")),
    ),
    Capability(
        key="data",
        title="Codebooks, dataset versioning, cohort profiles",
        skills="/generate-codebook, /version-dataset, /find-cohort-gap",
        pips=(Pip("pandas", "pandas"), Pip("openpyxl", "openpyxl")),
    ),
    Capability(
        key="contribute",
        title="Send an improvement back as a pull request",
        skills="/contribute",
        tools=(GH,),
    ),
    Capability(
        key="pdfdoc",
        title="Render a proposal or handout to PDF",
        skills="/render-pdf-doc",
        pips=(Pip("fontTools", "fonttools"),),
        tools=(PANDOC, XELATEX),
        aside="Only if you need PDF output. Word output does not need TeX.",
    ),
    Capability(
        key="stats_r",
        title="Run the statistics in R instead of Python",
        skills="/analyze-stats",
        tools=(RLANG,),
        aside="Not needed by default: /analyze-stats writes Python unless you ask it for R. The "
        "toolkit itself never runs R — this is only to run the code it writes for you.",
    ),
    Capability(
        key="ml",
        title="Train or fine-tune an imaging model",
        skills="/model-scaffold",
        pips=(
            Pip("torch", "torch", heavy="~2.5 GB"),
            Pip("torchvision", "torchvision"),
            Pip("timm", "timm"),
        ),
        aside="Only for the deep-learning lane, and only to RUN the code /model-scaffold writes — "
        "writing it needs nothing.",
    ),
    Capability(
        key="ocr",
        title="Read text out of a figure image (OCR)",
        skills="/make-figures (figure critic)",
        pips=(Pip("pytesseract", "pytesseract"),),
        tools=(TESSERACT,),
        aside="Rarely needed.",
    ),
)

# Capabilities that are genuinely optional: their absence is never an error, and --fix will not
# install their heavy parts for you.
OPTIONAL = {"pdfdoc", "stats_r", "ocr", "pdf_deep", "ml"}


def os_name() -> str:
    """`platform.system()` says "Darwin". Nobody who owns a Mac calls it that."""
    return {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}.get(platform.system(), platform.system() or "unknown")


def py() -> str:
    """The interpreter, written the short way when the short way means the same thing.

    Printing `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pip install ...` is correct and
    unreadable. Printing `python3` is readable and, on a computer with two Pythons, WRONG — it can
    install the package into an interpreter the skills do not run under. So: shorten it only after
    checking that `python3` really is this interpreter.
    """
    short = shutil.which("python3")
    if short:
        try:
            if Path(short).resolve() == Path(sys.executable).resolve():
                return "python3"
        except OSError:
            pass
    return sys.executable


# --------------------------------------------------------------------------------------------
# Probing
# --------------------------------------------------------------------------------------------


def have_module(name: str) -> bool:
    """True if `import name` would work — without actually importing it (no side effects)."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def have_tool(binary: str) -> bool:
    return shutil.which(binary) is not None


def missing_of(cap: Capability) -> Tuple[List[Pip], List[Tool]]:
    return (
        [p for p in cap.pips if not have_module(p.module)],
        [t for t in cap.tools if not have_tool(t.binary)],
    )


def install_hint(tool: Tool) -> str:
    """The one command for this computer — or the page, when there is no clean command.

    On a Mac WITHOUT Homebrew, "brew install pandoc" is not one step, it is two, and the hidden one
    is enormous: installing Homebrew pulls the Xcode command-line tools. Telling a physician to do
    that so they can convert a document is how you lose them. Most of these tools ship a plain
    double-click installer, so when there is no brew, the download page goes first and brew is
    mentioned only as the alternative for people who already live in a terminal.
    """
    system = platform.system()
    if system == "Darwin":
        if tool.brew and have_tool("brew"):
            return "brew install " + tool.brew
        if tool.page:
            alt = ("   (or, with Homebrew:  brew install " + tool.brew + ")") if tool.brew else ""
            return "download it from  " + tool.page + alt
        if tool.brew:
            # No double-click download exists for this one (poppler). Homebrew really is the way,
            # so say the whole truth — including the part they will not enjoy.
            return "brew install " + tool.brew + "   (needs Homebrew first: https://brew.sh)"
    elif system == "Windows":
        if tool.winget:
            return "winget install --exact --id " + tool.winget
        if tool.win_page or tool.page:
            return "download it from  " + (tool.win_page or tool.page)
    elif tool.apt:
        return "sudo apt install " + tool.apt
    return "see " + tool.page if tool.page else "see " + REPO


def pip_hint(pkgs: Sequence[Pip]) -> str:
    names = " ".join(sorted({p.package for p in pkgs}))
    return py() + " -m pip install --user " + names


# --------------------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------------------


def report(emit: Callable[[str], None], brief: bool = False) -> int:
    """Print the state of this computer. Returns the number of NON-optional things missing."""
    ready: List[Capability] = []
    broken: List[Tuple[Capability, List[Pip], List[Tool]]] = []

    for cap in CAPABILITIES:
        pips, tools = missing_of(cap)
        if pips or tools:
            broken.append((cap, pips, tools))
        else:
            ready.append(cap)

    essential_missing = sum(1 for cap, _, _ in broken if cap.key not in OPTIONAL)

    if not brief:
        emit("")
        emit("MedSci Skills — setup check")
        emit(
            "  Python %s  ·  %s"
            % (".".join(str(n) for n in sys.version_info[:3]), os_name())
        )
        emit("")
        emit("WORKS NOW")
        for cap in ready:
            emit("  [ok] " + cap.title)
        emit("")

    if brief:
        # The tail of an install that already succeeded. Say something only if there is something
        # to do — an optional tool nobody asked for is not news, and a wall of green is noise.
        if not essential_missing:
            return 0
        emit("")
        emit("Some skills need a program this computer does not have yet:")
        for cap, _pips, _tools in broken:
            if cap.key not in OPTIONAL:
                emit("  - " + cap.title)
        emit("")
        emit("  See what they are, and install them (it asks before each one):")
        emit("    " + py() + " installers/doctor.py --fix")
        return essential_missing

    if not broken:
        emit("Nothing is missing. Every skill in the toolkit can run here.")
        return 0

    emit("NOT YET — each of these needs one more program")
    for cap, pips, tools in broken:
        tag = "  [--]" if cap.key in OPTIONAL else "  [  ]"
        emit(tag + " " + cap.title)
        emit("        used by: " + cap.skills)
        if cap.aside:
            emit("        note:    " + cap.aside)
        if pips:
            size = next((("  [" + p.heavy + " — big]") for p in pips if p.heavy), "")
            emit("        missing: " + ", ".join(p.package for p in pips) + size)
            emit("        install: " + pip_hint(pips))
        for t in tools:
            size = ("  [" + t.heavy + " — big]") if t.heavy else ""
            emit("        missing: " + t.label + size)
            emit("        install: " + install_hint(t))
        emit("")

    emit("  [  ] = a skill you are likely to want      [--] = optional, most people never need it")
    emit("")
    emit("To install these, with a question before each one:")
    emit("    " + py() + " " + str(__file__) + " --fix")
    emit("")
    emit("Big things (a TeX distribution, R, PyTorch) are never installed for you — the command is")
    emit("printed above and the choice stays yours.")
    return essential_missing


def brief_summary(emit: Callable[[str], None]) -> None:
    """The tail of a successful install: say what is missing, never fail, never install."""
    try:
        report(emit, brief=True)
    except Exception:  # noqa: BLE001 - a setup *check* must never break an install that worked
        pass


# --------------------------------------------------------------------------------------------
# Fixing (only ever after a yes)
# --------------------------------------------------------------------------------------------


def ask(question: str, assume_yes: bool) -> bool:
    if assume_yes:
        print(question + " yes (--yes)")
        return True
    try:
        answer = input(question + " [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def run(cmd: List[str]) -> Tuple[int, str]:
    print("    $ " + " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        return 1, str(exc)
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        tail = "\n".join(out.strip().splitlines()[-6:])
        print(tail)
    return proc.returncode, out


def pip_install(pkgs: Sequence[str], assume_yes: bool) -> bool:
    cmd = [sys.executable, "-m", "pip", "install", "--user"] + sorted(set(pkgs))
    code, out = run(cmd)
    if code == 0:
        print("    installed.")
        return True

    # PEP 668: a Python installed by Homebrew or by a Linux distribution refuses to let pip put
    # anything into it, to stop pip from fighting the package manager over the same files. For
    # pure-Python libraries into the *user* site that is not the danger the message implies — but
    # it is still an override of a deliberate safety, so it is never done silently.
    if "externally-managed-environment" in out:
        print()
        print("    This Python is managed by your operating system, so it blocks pip by default.")
        print("    These are ordinary Python libraries and installing them into your own user")
        print("    folder does not touch the system's own packages.")
        if ask("    Install them anyway?", assume_yes):
            code, _ = run(cmd + ["--break-system-packages"])
            if code == 0:
                print("    installed.")
                return True
    print("    could not install — the command above shows what failed.")
    return False


def tool_install(tool: Tool, assume_yes: bool) -> bool:
    system = platform.system()
    if system == "Darwin" and tool.brew and have_tool("brew"):
        code, _ = run(["brew", "install"] + tool.brew.split())
        return code == 0
    if system == "Windows" and tool.winget and have_tool("winget"):
        code, _ = run(
            [
                "winget",
                "install",
                "--exact",
                "--id",
                tool.winget,
                "--accept-source-agreements",
                "--accept-package-agreements",
            ]
        )
        return code == 0
    # Linux needs sudo, and a setup script does not get to ask for a password. Everything else
    # (no Homebrew, no winget) gets the page.
    print("    Install it yourself with:  " + install_hint(tool))
    return False


def fix(assume_yes: bool) -> int:
    report(print)

    wanted_pips: List[str] = []
    wanted_tools: List[Tool] = []
    heavy: List[Tuple[str, str, str]] = []  # (label, size, command)

    for cap in CAPABILITIES:
        pips, tools = missing_of(cap)
        if cap.key in OPTIONAL:
            # Optional capabilities are offered one at a time and are never swept into a bulk
            # install — not even with --yes. --yes means "stop asking me about the small, safe
            # things I clearly want", not "decide for me what I want".
            if not (pips or tools):
                continue
            print()
            print("Optional: " + cap.title)
            if cap.aside:
                print("  " + cap.aside)
            if not ask("  Set this up?", assume_yes=False):
                continue
        for t in tools:
            if t.heavy:
                heavy.append((t.label, t.heavy, install_hint(t)))
            else:
                wanted_tools.append(t)

        # A heavy Python package (PyTorch is 2.5 GB) is no more welcome on a laptop than a heavy
        # program is. If any package in a group is heavy, the whole group is the person's call —
        # torchvision without torch would be a pointless half-install.
        if any(p.heavy for p in pips):
            size = next(p.heavy for p in pips if p.heavy)
            heavy.append((", ".join(p.package for p in pips), size, pip_hint(pips)))
        else:
            wanted_pips.extend(p.package for p in pips)

    if not (wanted_pips or wanted_tools or heavy):
        print()
        print("Nothing to install.")
        return 0

    if wanted_pips:
        print()
        print("Python packages to install: " + " ".join(sorted(set(wanted_pips))))
        print("  (small, official, from the Python Package Index)")
        if ask("Install them?", assume_yes):
            pip_install(wanted_pips, assume_yes)

    for tool in wanted_tools:
        print()
        print("Program to install: " + tool.label)
        print("  " + install_hint(tool))
        if ask("Install it?", assume_yes):
            if tool_install(tool, assume_yes):
                print("    installed.")

    if heavy:
        print()
        print("NOT installed for you — these are large, and the choice should be yours:")
        for label, size, command in heavy:
            print("  " + label + "  (" + size + ")")
            print("      " + command)

    print()
    print("Checking again:")
    report(print)
    return 0


def as_json() -> int:
    out = []
    for cap in CAPABILITIES:
        pips, tools = missing_of(cap)
        out.append(
            {
                "key": cap.key,
                "title": cap.title,
                "optional": cap.key in OPTIONAL,
                "ready": not (pips or tools),
                "missing_packages": [p.package for p in pips],
                "missing_tools": [t.label for t in tools],
                "fix": ([pip_hint(pips)] if pips else []) + [install_hint(t) for t in tools],
            }
        )
    print(json.dumps({"python": sys.version.split()[0], "capabilities": out}, indent=2))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="What MedSci Skills can do on this computer, and how to fix what it cannot."
    )
    ap.add_argument("--fix", action="store_true", help="offer to install what is missing (asks first)")
    ap.add_argument("--brief", action="store_true", help="only what is missing")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    ap.add_argument("--yes", action="store_true", help="with --fix: do not ask about the small, safe installs")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if anything non-optional is missing (for CI, not for people)",
    )
    a = ap.parse_args(argv)

    if a.json:
        return as_json()
    if a.fix:
        return fix(a.yes)

    missing = report(print, brief=a.brief)
    return 1 if (a.strict and missing) else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env bash
# Build this demo's talk and run both gates the repository requires of a deck.
# Every number on a slide is read from the shipped artifacts at build time — none is typed in.
set -euo pipefail
cd "$(dirname "$0")"
SK="../../../skills/present-paper/scripts"
python3 build_deck.py
python3 "$SK/check_slide_tells.py"   demo2_bcg_meta_analysis.pptx
python3 "$SK/check_deck_budget.py"   demo2_bcg_meta_analysis.pptx --archetype conference_oral --minutes 10
echo "OK — demo2_bcg_meta_analysis.pptx passes the AI-tell scan and the archetype budget."

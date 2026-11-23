#!/usr/bin/env bash
# Build this demo's talk and run both gates the repository requires of a deck.
# Slide text is English, speaker notes Korean; every figure is cropped from a CC BY article (assets/SOURCES.md).
set -euo pipefail
cd "$(dirname "$0")"
SK="../../../skills/present-paper/scripts"
python3 build_deck.py
python3 "$SK/check_slide_tells.py"   demo6_circle_of_willis.pptx
python3 "$SK/check_deck_budget.py"   demo6_circle_of_willis.pptx --archetype didactic --minutes 30
echo "OK — demo6_circle_of_willis.pptx passes the AI-tell scan and the archetype budget."

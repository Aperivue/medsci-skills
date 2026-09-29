#!/usr/bin/env bash
# Moved to skills/meta-analysis/scripts/tag_cleanup_gate.sh so an installed copy of the skill can
# run it. This shim keeps the old repo-root path working for existing projects and notes.
exec bash "$(cd "$(dirname "$0")" && pwd)/../skills/meta-analysis/scripts/tag_cleanup_gate.sh" "$@"

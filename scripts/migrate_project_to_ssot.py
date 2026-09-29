#!/usr/bin/env python3
"""Moved to skills/manage-project/scripts/migrate_project_to_ssot.py so an installed copy of the skill can run it.

This shim keeps the old repo-root path working for existing projects and notes.
"""
import runpy
import sys
from pathlib import Path

target = Path(__file__).resolve().parent.parent / "skills" / "manage-project" / "scripts" / "migrate_project_to_ssot.py"
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")

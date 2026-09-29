#!/usr/bin/env python3
"""Moved to skills/sync-submission/scripts/verify_package_integrity.py so an installed copy of the skill can run it.

This shim keeps the old repo-root path working for existing projects and notes.
"""
import runpy
import sys
from pathlib import Path

target = Path(__file__).resolve().parent.parent / "skills" / "sync-submission" / "scripts" / "verify_package_integrity.py"
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")

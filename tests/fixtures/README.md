# Validator Regression Fixtures (Phase 0.5.9)

Two minimal projects for `validate_project_contract.py` dual-path testing.

## Usage

```bash
# Legacy path: project.yaml only -> warn, valid
python3 scripts/validate_project_contract.py --project-root tests/fixtures/legacy_project

# SSOT path: SSOT.yaml only -> clean, valid
python3 scripts/validate_project_contract.py --project-root tests/fixtures/ssot_project
```

Expected exit codes: both 0 (valid). Legacy emits a sunset warning until 2026-10-24.

## Purpose

Lock the two contract formats in-repo so Phase 0.5+ changes to the validator or schemas can be regression-tested without a real project checkout.

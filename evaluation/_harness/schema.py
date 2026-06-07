"""Dataclasses for evaluation log-package records.

Kept deliberately small and stdlib-only. ``component_type`` and
``expected_reproducibility`` use the controlled vocabularies fixed in the plan.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

COMPONENT_TYPES = (
    "deterministic_script",
    "rules_based_checker",
    "llm_baseline",
    "human_adjudication",
)

REPRODUCIBILITY = ("exact", "near-exact", "non-deterministic")


@dataclass
class ComponentRecord:
    """One entry in run_manifest.json::components."""

    component_type: str
    git_sha: str
    command_args: list
    expected_reproducibility: str
    rerun_policy: str
    script_path: Optional[str] = None
    model_name: Optional[str] = None
    seed: Optional[int] = None
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None

    def __post_init__(self) -> None:
        if self.component_type not in COMPONENT_TYPES:
            raise ValueError(f"bad component_type: {self.component_type}")
        if self.expected_reproducibility not in REPRODUCIBILITY:
            raise ValueError(
                f"bad expected_reproducibility: {self.expected_reproducibility}"
            )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class InjectionRecord:
    """One injected defect variant (one line of injected_defects.jsonl)."""

    defect_id: str
    defect_class: str
    demo: str
    target_file: str
    injector: str
    detector_id: str
    expected_codes: list
    status: str  # INJECTED | SKIPPED | NOT_RUN
    reason: str = ""
    before_excerpt: str = ""
    after_excerpt: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

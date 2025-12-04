from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Set


class SourceType(str, Enum):
    KOTLIN = "KOTLIN"
    OPENAPI = "OPENAPI"


@dataclass
class Rule:
    internal_id: int
    description: str
    source_file: str
    start_line: int
    end_line: int
    source_type: SourceType
    endpoint: Optional[str] = None
    endpoint_entity: Optional[str] = None
    rule_id: Optional[str] = None
    depends_on_internal: Set[int] = field(default_factory=set)
    depends_on_ids: Set[str] = field(default_factory=set)
    meta: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.start_line > self.end_line:
            raise ValueError("start_line cannot be greater than end_line")


def sort_rules(rules: Set[Rule] | list[Rule]) -> list[Rule]:
    """Return rules ordered deterministically for ID assignment and output.

    Sorting follows the design requirement of ordering by source type, then
    source file path, then the rule's starting line. ``end_line`` and
    ``internal_id`` break ties to ensure stability across runs.
    """

    return sorted(
        rules,
        key=lambda rule: (
            rule.source_type.value,
            rule.source_file,
            rule.start_line,
            rule.end_line,
            rule.internal_id,
        ),
    )

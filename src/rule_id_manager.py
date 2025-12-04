from __future__ import annotations

import re
from typing import Dict, Iterable, Tuple

from .models import Rule, sort_rules


_RULE_ID_PATTERN = re.compile(r"^(?P<prefix>.+)-(?P<number>\d+)$")


def assign_rule_ids(rules: Iterable[Rule], starting_rule_id: str) -> Dict[int, str]:
    """Assign rule IDs to the provided rules in a deterministic order.

    Rules are sorted by source type, source file, and starting line before IDs
    are assigned to ensure consistent ordering. The numeric portion of the
    starting ID is incremented sequentially while preserving its zero padding.

    Returns a mapping of ``internal_id`` to ``rule_id``.
    """

    prefix, current_number, width = _parse_starting_rule_id(starting_rule_id)
    sorted_rules = sort_rules(list(rules))
    assigned: Dict[int, str] = {}

    for offset, rule in enumerate(sorted_rules):
        rule_id = f"{prefix}-{current_number + offset:0{width}d}"
        rule.rule_id = rule_id
        assigned[rule.internal_id] = rule_id

    return assigned


def _parse_starting_rule_id(starting_rule_id: str) -> Tuple[str, int, int]:
    match = _RULE_ID_PATTERN.match(starting_rule_id)
    if not match:
        raise ValueError("starting_rule_id must follow the pattern <PREFIX>-<NUMBER>")

    prefix = match.group("prefix")
    number_str = match.group("number")
    return prefix, int(number_str), len(number_str)

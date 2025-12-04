from __future__ import annotations

import logging
from typing import Dict, Iterable, Set

from .models import Rule


def resolve_dependencies(rules: Iterable[Rule], logger: logging.Logger | None = None) -> None:
    """Populate ``depends_on_ids`` and emit warnings for dependency cycles.

    This function expects rule IDs to be assigned already. Unknown dependency
    references raise ``ValueError`` to avoid silently losing dependency edges.
    """

    logger = logger or logging.getLogger("valid_builder")
    rules_list = list(rules)
    internal_id_map: Dict[int, Rule] = {rule.internal_id: rule for rule in rules_list}

    if len(internal_id_map) != len(rules_list):
        raise ValueError("Duplicate internal IDs are not allowed")

    for rule in rules_list:
        if not rule.rule_id:
            raise ValueError("Dependencies can only be resolved after rule IDs are assigned")

    _populate_depends_on_ids(rules_list, internal_id_map)
    _warn_on_cycles(rules_list, internal_id_map, logger)


def _populate_depends_on_ids(rules_list: list[Rule], internal_id_map: Dict[int, Rule]) -> None:
    for rule in rules_list:
        resolved_ids: Set[str] = set()
        for dependency_internal_id in rule.depends_on_internal:
            if dependency_internal_id not in internal_id_map:
                raise ValueError(f"Unknown dependency internal id: {dependency_internal_id}")
            dependency_rule = internal_id_map[dependency_internal_id]
            if not dependency_rule.rule_id:
                raise ValueError("Dependency rules must have assigned rule IDs")
            resolved_ids.add(dependency_rule.rule_id)
        rule.depends_on_ids = resolved_ids


def _warn_on_cycles(
    rules_list: list[Rule], internal_id_map: Dict[int, Rule], logger: logging.Logger
) -> None:
    graph: Dict[int, Set[int]] = {
        rule.internal_id: set(rule.depends_on_internal) for rule in rules_list
    }
    visited: Dict[int, str] = {}
    cycles_logged: Set[frozenset[int]] = set()

    def dfs(node: int, path: list[int]) -> None:
        if visited.get(node) == "visiting":
            cycle_start_index = path.index(node)
            cycle_nodes = path[cycle_start_index:]
            cycle_key = frozenset(cycle_nodes)
            if cycle_key not in cycles_logged:
                cycles_logged.add(cycle_key)
                rule_ids = [internal_id_map[n].rule_id for n in cycle_nodes if internal_id_map[n].rule_id]
                previous_propagate = logger.propagate
                try:
                    logger.propagate = True
                    logger.warning("Detected dependency cycle: %s", " -> ".join(rule_ids))
                finally:
                    logger.propagate = previous_propagate
            return
        if visited.get(node) == "visited":
            return

        visited[node] = "visiting"
        path.append(node)
        for neighbor in graph.get(node, set()):
            dfs(neighbor, path)
        path.pop()
        visited[node] = "visited"

    for node in graph:
        if visited.get(node):
            continue
        dfs(node, [])

import logging

import pytest

from src.dependency_resolver import resolve_dependencies
from src.models import Rule, SourceType
from src.rule_id_manager import assign_rule_ids


def test_resolve_dependencies_translates_internal_to_rule_ids():
    rule_a = Rule(
        internal_id=1,
        description="first",
        source_file="a.kt",
        start_line=1,
        end_line=2,
        source_type=SourceType.KOTLIN,
    )
    rule_b = Rule(
        internal_id=2,
        description="second",
        source_file="a.kt",
        start_line=3,
        end_line=4,
        source_type=SourceType.KOTLIN,
        depends_on_internal={1},
    )

    assign_rule_ids([rule_a, rule_b], "RULE-001")
    resolve_dependencies([rule_a, rule_b])

    assert rule_b.depends_on_ids == {"RULE-001"}
    assert rule_a.depends_on_ids == set()


def test_resolve_dependencies_raises_on_missing_internal_id():
    rule = Rule(
        internal_id=1,
        description="lonely",
        source_file="file.kt",
        start_line=1,
        end_line=1,
        source_type=SourceType.KOTLIN,
        depends_on_internal={99},
    )
    rule.rule_id = "RULE-001"

    with pytest.raises(ValueError):
        resolve_dependencies([rule])


def test_resolve_dependencies_warns_on_cycles(caplog):
    caplog.set_level(logging.WARNING)
    parent = Rule(
        internal_id=1,
        description="parent",
        source_file="a.kt",
        start_line=1,
        end_line=1,
        source_type=SourceType.KOTLIN,
        depends_on_internal={2},
    )
    child = Rule(
        internal_id=2,
        description="child",
        source_file="a.kt",
        start_line=2,
        end_line=2,
        source_type=SourceType.KOTLIN,
        depends_on_internal={1},
    )

    assign_rule_ids([parent, child], "RULE-050")
    resolve_dependencies([parent, child], logger=logging.getLogger("valid_builder"))

    assert parent.depends_on_ids == {"RULE-051"}
    assert child.depends_on_ids == {"RULE-050"}
    assert any("Detected dependency cycle" in message for message in caplog.text.splitlines())

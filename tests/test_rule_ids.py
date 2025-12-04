import pytest

from src.models import Rule, SourceType
from src.rule_id_manager import assign_rule_ids


def test_assign_rule_ids_orders_by_source_and_line():
    rules = [
        Rule(
            internal_id=2,
            description="late kotlin",
            source_file="z.kt",
            start_line=20,
            end_line=21,
            source_type=SourceType.KOTLIN,
        ),
        Rule(
            internal_id=1,
            description="early openapi",
            source_file="a.yml",
            start_line=1,
            end_line=2,
            source_type=SourceType.OPENAPI,
        ),
        Rule(
            internal_id=3,
            description="earlier kotlin",
            source_file="a.kt",
            start_line=5,
            end_line=6,
            source_type=SourceType.KOTLIN,
        ),
    ]

    assigned = assign_rule_ids(rules, "RULE-010")

    expected_assignment = {
        3: "RULE-010",  # Kotlin file comes before OpenAPI when sorted
        2: "RULE-011",
        1: "RULE-012",
    }
    assert assigned == expected_assignment
    assert {rule.internal_id: rule.rule_id for rule in rules} == expected_assignment


def test_assign_rule_ids_requires_numeric_suffix():
    with pytest.raises(ValueError):
        assign_rule_ids([], "RULE")


def test_assign_rule_ids_preserves_padding():
    rules = [
        Rule(
            internal_id=5,
            description="only rule",
            source_file="file.kt",
            start_line=1,
            end_line=1,
            source_type=SourceType.KOTLIN,
        )
    ]

    assign_rule_ids(rules, "RULE-009")

    assert rules[0].rule_id == "RULE-009"

import pytest

from src.models import Rule, SourceType, sort_rules


def test_rule_defaults_and_independent_sets():
    rule_a = Rule(
        internal_id=1,
        description="desc",
        source_file="a.kt",
        start_line=1,
        end_line=2,
        source_type=SourceType.KOTLIN,
    )
    rule_b = Rule(
        internal_id=2,
        description="other",
        source_file="b.yaml",
        start_line=3,
        end_line=4,
        source_type=SourceType.OPENAPI,
    )

    assert rule_a.depends_on_internal == set()
    assert rule_a.depends_on_ids == set()
    assert rule_a.meta == {}

    rule_a.depends_on_internal.add(99)
    assert rule_b.depends_on_internal == set(), "depends_on_internal sets must not be shared"


def test_rule_rejects_invalid_line_ranges():
    with pytest.raises(ValueError):
        Rule(
            internal_id=3,
            description="bad range",
            source_file="file.kt",
            start_line=10,
            end_line=5,
            source_type=SourceType.KOTLIN,
        )


def test_sort_rules_orders_by_type_file_and_line():
    kotlin_first = Rule(
        internal_id=10,
        description="k1",
        source_file="b.kt",
        start_line=5,
        end_line=6,
        source_type=SourceType.KOTLIN,
    )
    kotlin_second = Rule(
        internal_id=11,
        description="k2",
        source_file="b.kt",
        start_line=8,
        end_line=9,
        source_type=SourceType.KOTLIN,
    )
    openapi_rule = Rule(
        internal_id=12,
        description="o1",
        source_file="a.yml",
        start_line=1,
        end_line=2,
        source_type=SourceType.OPENAPI,
    )

    sorted_rules = sort_rules([openapi_rule, kotlin_second, kotlin_first])

    assert [r.internal_id for r in sorted_rules] == [kotlin_first.internal_id, kotlin_second.internal_id, openapi_rule.internal_id]

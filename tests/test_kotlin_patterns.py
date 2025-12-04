from pathlib import Path

import pytest

from src.analyzers.kotlin_analyzer import analyze_kotlin_file
from src.description import describe_kotlin_if_throw, describe_kotlin_require
from src.models import SourceType


@pytest.mark.parametrize(
    "source_lines,expect_description",
    [
        (
            ["fun validate(input: String) {", "    require(input.isNotEmpty()) { \"input required\" }", "}"],
            describe_kotlin_require("input.isNotEmpty()", message="input required"),
        ),
        (
            [
                "fun check(value: Int) {",
                "    if (value <= 0) {",
                "        throw IllegalArgumentException(\"must be positive\")",
                "    }",
                "}",
            ],
            describe_kotlin_if_throw(
                "value <= 0", exception="IllegalArgumentException", message="must be positive"
            ),
        ),
    ],
)
def test_basic_construct_detection(tmp_path, source_lines, expect_description):
    kotlin_file = tmp_path / "Sample.kt"
    kotlin_file.write_text("\n".join(source_lines))

    rules = analyze_kotlin_file(kotlin_file)

    assert len(rules) == 1
    rule = rules[0]
    assert rule.description == expect_description
    assert rule.source_file == kotlin_file.name
    assert rule.source_type is SourceType.KOTLIN
    construct_index = next(
        idx for idx, text in enumerate(source_lines) if "require" in text or "throw" in text
    )
    assert rule.start_line <= construct_index + 1
    assert rule.end_line >= rule.start_line


def test_guard_and_dependency_detection(tmp_path):
    content = """
fun validate(data: String) {
    if (shouldCheck(data)) {
        checkDetails(data)
    }
}

fun shouldCheck(data: String): Boolean = data.startsWith("X")

fun checkDetails(data: String) {
    if (data.endsWith("!")) {
        throw IllegalStateException("no shouting")
    }
}
""".strip()
    kotlin_file = tmp_path / "Guarded.kt"
    kotlin_file.write_text(content)

    rules = analyze_kotlin_file(kotlin_file)

    assert len(rules) == 2, "Guard and validation rules should both be emitted"
    guard_rule, validation_rule = rules

    assert "shouldCheck(data" in guard_rule.description
    assert "checkDetails" in guard_rule.description
    assert validation_rule.depends_on_internal == {guard_rule.internal_id}
    assert guard_rule.start_line == 1
    assert validation_rule.start_line > guard_rule.start_line
    assert validation_rule.end_line >= validation_rule.start_line
    assert validation_rule.description.endswith("."), "Descriptions should be human readable"

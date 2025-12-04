import csv
from types import SimpleNamespace

import pytest

from src import csv_writer


def make_rule(
    rule_id="RULE-001",
    description="Sample",
    source_file="file.kt",
    start_line=1,
    end_line=1,
    endpoint=None,
    endpoint_entity=None,
    depends_on_ids=None,
):
    return SimpleNamespace(
        rule_id=rule_id,
        description=description,
        source_file=source_file,
        start_line=start_line,
        end_line=end_line,
        endpoint=endpoint,
        endpoint_entity=endpoint_entity,
        depends_on_ids=depends_on_ids or set(),
    )


def test_writes_header_and_basic_row_without_unneeded_quotes(tmp_path):
    """Ensures header is always written and simple fields stay unquoted."""
    output_path = tmp_path / "rules.csv"
    rule = make_rule(description="Plain text", start_line=10, end_line=12)

    csv_writer.write_rules_csv(output_path, [rule])

    expected = (
        "Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on\n"
        "RULE-001,Plain text,file.kt,10-12,,,\n"
    )
    assert output_path.read_text() == expected


def test_quotes_and_escapes_special_characters(tmp_path):
    """Quotes fields with commas/newlines and escapes embedded double quotes."""
    output_path = tmp_path / "quoted.csv"
    rules = [
        make_rule(
            rule_id="RULE-100",
            description="Contains,comma",
            source_file="a.kt",
            start_line=3,
            end_line=3,
        ),
        make_rule(
            rule_id="RULE-101",
            description='Says "hello"',
            source_file="b.kt",
            start_line=4,
            end_line=5,
        ),
        make_rule(
            rule_id="RULE-102",
            description="Line one\nLine two",
            source_file="c.kt",
            start_line=6,
            end_line=7,
        ),
    ]

    csv_writer.write_rules_csv(output_path, rules)

    with output_path.open(newline="") as f:
        rows = list(csv.reader(f))

    assert rows[0] == [
        "Rule ID",
        "Description",
        "Source file",
        "Lines",
        "Endpoint",
        "Endpoint entity",
        "Depends on",
    ]
    assert rows[1] == ["RULE-100", "Contains,comma", "a.kt", "3-3", "", "", ""]
    assert rows[2] == ["RULE-101", 'Says "hello"', "b.kt", "4-5", "", "", ""]
    assert rows[3] == ["RULE-102", "Line one\nLine two", "c.kt", "6-7", "", "", ""]

    content = output_path.read_text()
    assert 'RULE-100,"Contains,comma"' in content
    assert 'RULE-101,"Says ""hello"""' in content
    assert 'RULE-102,"Line one\nLine two"' in content


def test_joins_multiple_dependencies_in_sorted_order(tmp_path):
    """Combines multiple dependencies into a deterministic, comma-separated list."""
    output_path = tmp_path / "deps.csv"
    rule = make_rule(
        rule_id="RULE-200",
        description="Has parents",
        depends_on_ids={"RULE-300", "RULE-201"},
    )

    csv_writer.write_rules_csv(output_path, [rule])

    line = output_path.read_text().splitlines()[1]
    assert line == 'RULE-200,Has parents,file.kt,1-1,,,"RULE-201,RULE-300"'


def test_atomic_write_removes_temp_on_failure(tmp_path, monkeypatch):
    """If writing fails, no CSV or temp file is left behind (atomic write)."""
    output_path = tmp_path / "result.csv"
    rule = make_rule()
    before = set(tmp_path.iterdir())

    def explode(src, dst, *args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(csv_writer.os, "replace", explode)

    with pytest.raises(RuntimeError):
        csv_writer.write_rules_csv(output_path, [rule])

    after = set(tmp_path.iterdir())
    assert output_path not in after
    assert after == before

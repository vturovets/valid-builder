import logging
from pathlib import Path

from src.config import Config
from src.models import Rule, SourceType
from src.orchestrator import orchestrate


def test_orchestrator_runs_pipeline_and_writes_csv(tmp_path, monkeypatch, caplog):
    """Exercises the success path: detection, analysis, ID assignment, dependencies, and CSV output."""

    input_file = tmp_path / "input.kt"
    input_file.write_text("fun main() = Unit\n")
    output_file = tmp_path / "output.csv"

    created_rules = [
        Rule(
            internal_id=1,
            description="guard rule",
            source_file=input_file.name,
            start_line=1,
            end_line=1,
            source_type=SourceType.KOTLIN,
        ),
        Rule(
            internal_id=2,
            description="validation rule",
            source_file=input_file.name,
            start_line=5,
            end_line=6,
            source_type=SourceType.KOTLIN,
            depends_on_internal={1},
        ),
    ]

    def fake_analyzer(path: Path) -> list[Rule]:
        assert path == input_file
        return created_rules

    monkeypatch.setattr("src.orchestrator.analyze_kotlin_file", fake_analyzer)
    monkeypatch.setattr("src.orchestrator.analyze_openapi_file", lambda p: [])

    config = Config(
        default_rule_id="RULE-010",
        openapi_endpoint_entities=[],
        llm_method="rule-based",
        llm_model="",
        llm_url="",
        llm_api_key="",
        log_file="",
        log_level="INFO",
    )

    logger = logging.getLogger("valid_builder")
    logger.handlers.clear()
    logger.propagate = True

    caplog.set_level(logging.INFO, logger="valid_builder")
    rules = orchestrate(input_file, output_file, config, logger=logger)

    assert all(rule.rule_id for rule in rules)
    assert rules[1].depends_on_ids == {"RULE-010"}

    lines = output_file.read_text().splitlines()
    assert lines[0] == "Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on"
    assert lines[1].startswith("RULE-010,guard rule,input.kt,1-1,,,")
    assert lines[2].endswith(",RULE-010")

    assert any("Detected 2 validation rules" in record.message for record in caplog.records)
    assert any("Completed extraction" in record.message for record in caplog.records)

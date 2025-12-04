import logging
from pathlib import Path

import pytest

from src.config import Config
from src.models import Rule, SourceType
from src.orchestrator import orchestrate


def test_orchestrator_preserves_output_on_failure(tmp_path, monkeypatch):
    """Validates that fatal errors stop the run without altering the output file."""

    input_file = tmp_path / "input.kt"
    input_file.write_text("fun main() = Unit\n")
    output_file = tmp_path / "output.csv"
    output_file.write_text("original contents\n")

    failing_rule = Rule(
        internal_id=1,
        description="broken rule",
        source_file=input_file.name,
        start_line=1,
        end_line=1,
        source_type=SourceType.KOTLIN,
        depends_on_internal={99},
    )

    def failing_analyzer(path: Path):
        assert path == input_file
        return [failing_rule]

    monkeypatch.setattr("src.orchestrator.analyze_kotlin_file", failing_analyzer)

    config = Config(
        default_rule_id="RULE-001",
        openapi_endpoint_entities=[],
        llm_method="rule-based",
        llm_model="",
        llm_url="",
        llm_api_key="",
        log_file="",
        log_level="INFO",
    )

    with pytest.raises(Exception):
        orchestrate(input_file, output_file, config, logger=logging.getLogger("valid_builder"))

    assert output_file.read_text() == "original contents\n"


def test_detect_source_type_invalid_override(tmp_path):
    """Confirms invalid language overrides are treated as user errors."""

    sample = tmp_path / "file.dat"
    sample.write_text("content")

    with pytest.raises(ValueError):
        orchestrate(
            sample,
            tmp_path / "out.csv",
            Config(
                default_rule_id="RULE-001",
                openapi_endpoint_entities=[],
                llm_method="rule-based",
                llm_model="",
                llm_url="",
                llm_api_key="",
                log_file="",
                log_level="INFO",
            ),
            lang_override="unknown",
            logger=logging.getLogger("valid_builder"),
        )

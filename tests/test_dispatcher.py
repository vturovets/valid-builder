import logging
from pathlib import Path

import pytest

from src.models import SourceType
from src.orchestrator import detect_source_type


def test_detect_source_type_prefers_override(tmp_path):
    """Checks that an explicit --lang override forces the selected analyzer."""

    yaml_file = tmp_path / "spec.yaml"
    yaml_file.write_text("openapi: 3.0.0")

    result = detect_source_type(yaml_file, lang_override="kotlin")

    assert result == SourceType.KOTLIN


def test_detect_source_type_extension_and_heuristic(tmp_path):
    """Verifies extension detection and heuristic fallback for OpenAPI content."""

    kotlin_file = tmp_path / "example.kt"
    kotlin_file.write_text("fun main() {}\n")
    assert detect_source_type(kotlin_file) == SourceType.KOTLIN

    unknown_yaml = tmp_path / "api.txt"
    unknown_yaml.write_text("openapi: 3.0.0\npaths:\n")
    assert detect_source_type(unknown_yaml) == SourceType.OPENAPI


def test_detect_source_type_rejects_unknown(tmp_path):
    """Ensures unsupported files raise a clear error instead of guessing."""

    unknown = tmp_path / "data.txt"
    unknown.write_text("just some text")

    with pytest.raises(ValueError):
        detect_source_type(unknown)

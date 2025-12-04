from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterable

from .analyzers.kotlin_analyzer import analyze_kotlin_file
from .analyzers.openapi_analyzer import analyze_openapi_file
from .config import Config
from .csv_writer import write_rules_csv
from .dependency_resolver import resolve_dependencies
from .models import Rule, SourceType
from .rule_id_manager import assign_rule_ids


LANG_MAP = {
    "kotlin": SourceType.KOTLIN,
    "openapi": SourceType.OPENAPI,
}


class OrchestratorError(RuntimeError):
    """Raised when the orchestration pipeline cannot complete."""


def detect_source_type(input_file: str | Path, lang_override: str | None = None) -> SourceType:
    """Determine the source type using override, extension, or heuristics."""

    if lang_override:
        try:
            return LANG_MAP[lang_override]
        except KeyError as exc:
            raise ValueError(f"Unsupported language override: {lang_override}") from exc

    path = Path(input_file)
    extension = path.suffix.lower()
    if extension == ".kt":
        return SourceType.KOTLIN
    if extension in {".yml", ".yaml"}:
        return SourceType.OPENAPI

    content = path.read_text(errors="ignore")
    lowered = content.lower()
    if "openapi:" in lowered or "paths:" in lowered:
        return SourceType.OPENAPI
    if "fun " in lowered or lowered.startswith("package "):
        return SourceType.KOTLIN

    raise ValueError(f"Cannot detect source type for file: {path}")


def orchestrate(
    input_file: str | Path,
    output_file: str | Path,
    config: Config,
    *,
    lang_override: str | None = None,
    logger: logging.Logger | None = None,
) -> list[Rule]:
    """Run the end-to-end extraction pipeline for a single file."""

    logger = logger or logging.getLogger("valid_builder")
    input_path = Path(input_file)
    output_path = Path(output_file)

    source_type = detect_source_type(input_path, lang_override)
    analyzer: Callable[[Path | str], Iterable[Rule]]
    if source_type is SourceType.KOTLIN:
        analyzer = analyze_kotlin_file
    elif source_type is SourceType.OPENAPI:
        analyzer = analyze_openapi_file
    else:
        raise OrchestratorError(f"Unsupported source type: {source_type}")

    logger.info("Reading source file %s as %s", input_path, source_type.value)

    try:
        rules = list(analyzer(input_path))
    except Exception as exc:  # pragma: no cover - defensive wrapper
        logger.error("Failed to analyze %s", input_path, exc_info=True)
        raise OrchestratorError("Analysis failed") from exc

    logger.info("Detected %d validation rules", len(rules))

    try:
        assign_rule_ids(rules, config.default_rule_id)
        resolve_dependencies(rules, logger)
    except Exception as exc:
        logger.error("Failed while post-processing rules", exc_info=True)
        raise OrchestratorError("Post-processing failed") from exc

    try:
        write_rules_csv(output_path, rules)
    except Exception as exc:  # pragma: no cover - defensive wrapper
        logger.error("Failed to write CSV output", exc_info=True)
        if output_path.exists():
            output_path.unlink()
        raise OrchestratorError("Output write failed") from exc

    logger.info("Completed extraction; wrote %d rules to %s", len(rules), output_path)
    return rules

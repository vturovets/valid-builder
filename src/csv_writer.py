from __future__ import annotations

import csv
import logging
import os
import tempfile
from pathlib import Path
from typing import Iterable


CSV_HEADERS = [
    "Rule ID",
    "Description",
    "Source file",
    "Lines",
    "Endpoint",
    "Endpoint entity",
    "Depends on",
]


def write_rules_csv(output_path: Path | str, rules: Iterable[object]) -> None:
    """Write validation rules to an RFC4180-style CSV file atomically.

    The writer keeps RFC4180 quoting rules in mind: fields containing commas, newlines,
    or double quotes are wrapped in quotes, and embedded quotes are doubled. A temporary
    file is created alongside the target output and then atomically replaced to avoid
    partial or corrupted results if an error occurs.
    """

    logger = logging.getLogger("valid_builder")
    output_path = Path(output_path)
    temp_path: Path | None = None

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with _temp_csv_file(output_path.parent) as tmp_file:
            temp_path = Path(tmp_file.name)
            writer = csv.writer(
                tmp_file,
                quoting=csv.QUOTE_MINIMAL,
                # Use a deterministic newline for tests while remaining RFC4180-friendly.
                lineterminator="\n",
            )
            writer.writerow(CSV_HEADERS)

            row_count = 0
            for rule in rules:
                writer.writerow(_serialize_rule(rule))
                row_count += 1

        os.replace(temp_path, output_path)
        logger.info("Wrote %s rule rows to %s", row_count, output_path)
    except Exception:
        _cleanup_temp_file(temp_path, logger)
        raise


def _temp_csv_file(directory: Path):
    """Return a NamedTemporaryFile opened for CSV writing in the given directory."""

    return tempfile.NamedTemporaryFile(
        "w", delete=False, dir=directory, newline="", suffix=".tmp", encoding="utf-8"
    )


def _serialize_rule(rule: object) -> list[str]:
    """Convert a rule namespace into a row matching ``CSV_HEADERS`` order."""

    depends_on = ",".join(sorted(rule.depends_on_ids)) if getattr(rule, "depends_on_ids", None) else ""
    return [
        rule.rule_id,
        rule.description,
        rule.source_file,
        f"{rule.start_line}-{rule.end_line}",
        getattr(rule, "endpoint", None) or "",
        getattr(rule, "endpoint_entity", None) or "",
        depends_on,
    ]


def _cleanup_temp_file(temp_path: Path | None, logger: logging.Logger) -> None:
    """Attempt to remove a leftover temp file, logging any cleanup issues."""

    if not temp_path:
        return

    try:
        if temp_path.exists():
            temp_path.unlink()
    except OSError:
        logger.warning("Failed to clean up temporary CSV file at %s", temp_path, exc_info=True)

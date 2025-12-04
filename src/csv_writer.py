import csv
import os
import tempfile
from pathlib import Path


def write_rules_csv(output_path, rules):
    output_path = Path(output_path)
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=output_path.parent, newline="", suffix=".tmp"
        ) as tmp_file:
            temp_path = Path(tmp_file.name)
            writer = csv.writer(tmp_file, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [
                    "Rule ID",
                    "Description",
                    "Source file",
                    "Lines",
                    "Endpoint",
                    "Endpoint entity",
                    "Depends on",
                ]
            )

            for rule in rules:
                depends_on = ",".join(sorted(rule.depends_on_ids)) if rule.depends_on_ids else ""
                writer.writerow(
                    [
                        rule.rule_id,
                        rule.description,
                        rule.source_file,
                        f"{rule.start_line}-{rule.end_line}",
                        rule.endpoint or "",
                        rule.endpoint_entity or "",
                        depends_on,
                    ]
                )

        os.replace(temp_path, output_path)
    except Exception:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink()
        raise

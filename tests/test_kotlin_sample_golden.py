import logging
from pathlib import Path

from src.analyzers.kotlin_analyzer import analyze_kotlin_file
from src.csv_writer import write_rules_csv
from src.dependency_resolver import resolve_dependencies
from src.rule_id_manager import assign_rule_ids


def test_sample_kotlin_matches_expected_csv(tmp_path):
    kotlin_path = Path("docs/RequestValidator_sample.kt")
    rules = analyze_kotlin_file(kotlin_path)

    assign_rule_ids(rules, "RULE-001")
    resolve_dependencies(rules, logger=logging.getLogger("kotlin_test"))

    output_path = tmp_path / "validation_rules.csv"
    write_rules_csv(output_path, rules)

    expected = (
        "Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on\n"
        "RULE-001,\"If the site region resolved from 'channel.siteID' equals 'wr' AND 'beneAdminFeesFeatureFlag' is true, "
        "then the request's (target, medium) must be validated against the configured channel mapping.\",RequestValidator_sample.kt,94-105,,,\n"
        "RULE-002,\"For region 'wr' with 'beneAdminFeesFeatureFlag' = true, the pair (target.lowercase(), medium.uppercase()) "
        "must exist in 'channelConfig.targetToMediumMap'; otherwise the request is rejected with 'Invalid channel mapping for target: <target> and medium: <medium>'.\",RequestValidator_sample.kt,103-120,,,RULE-001\n"
    )

    assert output_path.read_text() == expected

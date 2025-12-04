from src import cli


def test_cli_kotlin_end_to_end(tmp_path):
    """Running the CLI on the sample Kotlin file produces the expected CSV output."""

    output = tmp_path / "validation_rules.csv"

    exit_code = cli.main(
        ["docs/RequestValidator_sample.kt", "--output", str(output)]
    )

    expected = (
        "Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on\n"
        "RULE-001,\"If the site region resolved from 'channel.siteID' equals 'wr' AND 'beneAdminFeesFeatureFlag' is true, "
        "then the request's (target, medium) must be validated against the configured channel mapping.\",RequestValidator_sample.kt,94-105,,,\n"
        "RULE-002,\"For region 'wr' with 'beneAdminFeesFeatureFlag' = true, the pair (target.lowercase(), medium.uppercase()) "
        "must exist in 'channelConfig.targetToMediumMap'; otherwise the request is rejected with 'Invalid channel mapping for target: <target> and medium: <medium>'.\",RequestValidator_sample.kt,103-120,,,RULE-001\n"
    )

    assert exit_code == 0
    assert output.read_text() == expected

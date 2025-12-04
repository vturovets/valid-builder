"""Tests for RULE-002 derived from RequestValidator Kotlin sample."""

from pathlib import Path

import pytest

from src.analyzers.kotlin_analyzer import analyze_kotlin_file


RULE002_DESCRIPTION = (
    "For region 'wr' with 'beneAdminFeesFeatureFlag' = true, the pair (target.lowercase(), "
    "medium.uppercase()) must exist in 'channelConfig.targetToMediumMap'; otherwise the "
    "validator throws a ValidationException with ValidationProblem(title='Validation failed for "
    "Holiday Offers request', system='Holiday Offers', validationIssues=['Invalid channel mapping "
    "for target: <target> and medium: <medium>'])."
)


class TestRequestValidatorRule002:
    @pytest.fixture(scope="class")
    def rule002(self):
        rules = analyze_kotlin_file(Path("docs/RequestValidator_sample.kt"))
        return next(rule for rule in rules if rule.description.startswith("For region 'wr'") or "Invalid channel mapping" in rule.description)

    def test_rule002_description_matches_expected(self, rule002):
        assert rule002.description == RULE002_DESCRIPTION

    def test_rule002_captures_validation_problem_details(self, rule002):
        assert "validationIssues=['Invalid channel mapping for target: <target> and medium: <medium>']" in rule002.description
        assert "Validation failed for Holiday Offers request" in rule002.description
        assert "Holiday Offers" in rule002.description

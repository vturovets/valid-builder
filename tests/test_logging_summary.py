from src import logging_utils


def test_success_summary_reports_warning_count(capsys):
    """Checks that success summary reports rule and warning counts to stdout."""

    logger = logging_utils.setup_logging(log_level="INFO")
    summary = logging_utils.attach_summary_handler(logger)

    logger.warning("first warning")
    logging_utils.log_final_summary(logger, summary, rule_count=5, success=True)

    captured = capsys.readouterr()

    assert "Completed successfully. Extracted 5 rules. 1 warning(s)." in captured.out
    assert "Completed successfully" not in captured.err


def test_failure_summary_counts_errors_and_targets_stderr(capsys):
    """Checks that failure summary reports errors to stderr even when warnings exist."""

    logger = logging_utils.setup_logging(log_level="INFO")
    summary = logging_utils.attach_summary_handler(logger)

    logger.error("boom")
    logger.warning("later warning")
    logging_utils.log_final_summary(logger, summary, rule_count=None, success=False)

    captured = capsys.readouterr()

    assert "Failed with 1 error(s). See messages above." in captured.err
    assert "Failed with" not in captured.out

from src import logging_utils


def test_info_to_stdout_and_warning_to_stderr(capsys):
    """INFO logs go to stdout; WARNING/ERROR go to stderr."""
    logger = logging_utils.setup_logging(log_level="INFO")

    logger.info("info message")
    logger.warning("warn message")

    captured = capsys.readouterr()

    assert "info message" in captured.out
    assert "warn message" not in captured.out
    assert "warn message" in captured.err


def test_logs_are_duplicated_to_file(tmp_path):
    """When log_file is set, messages are also written to that file."""
    log_file = tmp_path / "app.log"
    logger = logging_utils.setup_logging(log_level="INFO", log_file=str(log_file))

    logger.info("file info")
    logger.error("file error")

    contents = log_file.read_text()

    assert "file info" in contents
    assert "file error" in contents

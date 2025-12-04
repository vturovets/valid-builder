import pytest

from src import cli


def test_requires_input_file():
    """CLI must fail if no input path is provided."""
    with pytest.raises(SystemExit):
        cli.parse_cli_args([])


def test_defaults_for_output_lang_and_config():
    """Defaults apply when only input path is provided."""
    args = cli.parse_cli_args(["input.kt"])

    assert args.input_file == "input.kt"
    assert args.output == "output.csv"
    assert args.lang is None
    assert args.config == ".env"


def test_accepts_output_and_lang_overrides():
    """Explicit output and language flags are parsed correctly."""
    args = cli.parse_cli_args(
        ["spec.yml", "--output", "custom.csv", "--lang", "openapi"]
    )

    assert args.input_file == "spec.yml"
    assert args.output == "custom.csv"
    assert args.lang == "openapi"


def test_custom_config_path():
    """CLI accepts a custom .env path."""
    args = cli.parse_cli_args(["file.kt", "--config", "settings/.env.dev"])

    assert args.config == "settings/.env.dev"


def test_rejects_invalid_lang_choice():
    """Invalid language choices trigger argument parsing errors."""
    with pytest.raises(SystemExit):
        cli.parse_cli_args(["file.kt", "--lang", "javascript"])

import pytest

from src import config


def test_load_config_defaults_when_env_missing(tmp_path):
    """Defaults are applied when no .env exists."""
    env_path = tmp_path / ".env"

    cfg = config.load_config(env_path=env_path)

    assert cfg.default_rule_id == "RULE-001"
    assert cfg.openapi_endpoint_entities == ["parameters", "requestBody", "responses"]
    assert cfg.llm_method == "rule-based"
    assert cfg.llm_model == ""
    assert cfg.llm_url == ""
    assert cfg.llm_api_key == ""
    assert cfg.log_file == ""
    assert cfg.log_level == "INFO"


def test_load_config_reads_env_values(tmp_path, monkeypatch):
    """Values from .env are parsed and override built-in defaults."""
    env_content = """
DEFAULT_RULE_ID=ID-100
OPENAPI_ENDPOINT_ENTITIES=foo, bar ,baz
LLM_METHOD=rule-based
LLM_MODEL=gpt
LLM_URL=https://example.test/api
LLM_API_KEY=secret
LOG_FILE=/tmp/valid-builder.log
LOG_LEVEL=DEBUG
"""
    env_path = tmp_path / ".env"
    env_path.write_text(env_content)

    # Ensure we don't accidentally read a real .env in cwd
    monkeypatch.chdir(tmp_path)

    cfg = config.load_config(env_path=env_path)

    assert cfg.default_rule_id == "ID-100"
    assert cfg.openapi_endpoint_entities == ["foo", "bar", "baz"]
    assert cfg.llm_method == "rule-based"
    assert cfg.llm_model == "gpt"
    assert cfg.llm_url == "https://example.test/api"
    assert cfg.llm_api_key == "secret"
    assert cfg.log_file == "/tmp/valid-builder.log"
    assert cfg.log_level == "DEBUG"


def test_cli_overrides_take_precedence(tmp_path):
    """CLI override values supersede entries in the .env file."""
    env_path = tmp_path / ".env"
    env_path.write_text(
        """
DEFAULT_RULE_ID=ID-200
LOG_FILE=env.log
LOG_LEVEL=INFO
"""
    )

    overrides = {"LOG_FILE": "cli.log", "LOG_LEVEL": "WARNING"}

    cfg = config.load_config(env_path=env_path, overrides=overrides)

    assert cfg.default_rule_id == "ID-200"
    assert cfg.log_file == "cli.log"
    assert cfg.log_level == "WARNING"

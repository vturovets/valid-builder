from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class Config:
    default_rule_id: str
    openapi_endpoint_entities: List[str]
    llm_method: str
    llm_model: str
    llm_url: str
    llm_api_key: str
    log_file: str
    log_level: str


def _parse_env_file(env_path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _parse_endpoint_entities(raw: str) -> List[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def load_config(env_path: Optional[Path] = None, overrides: Optional[Dict[str, str]] = None) -> Config:
    env_file = Path(env_path) if env_path is not None else Path(".env")

    defaults: Dict[str, str] = {
        "DEFAULT_RULE_ID": "RULE-001",
        "OPENAPI_ENDPOINT_ENTITIES": "parameters,requestBody,responses",
        "LLM_METHOD": "rule-based",
        "LLM_MODEL": "",
        "LLM_URL": "",
        "LLM_API_KEY": "",
        "LOG_FILE": "",
        "LOG_LEVEL": "INFO",
    }

    env_values = _parse_env_file(env_file)

    combined: Dict[str, str] = {**defaults, **env_values}
    if overrides:
        combined.update(overrides)

    openapi_entities_raw = combined.get("OPENAPI_ENDPOINT_ENTITIES", "")

    return Config(
        default_rule_id=combined.get("DEFAULT_RULE_ID", defaults["DEFAULT_RULE_ID"]),
        openapi_endpoint_entities=_parse_endpoint_entities(openapi_entities_raw),
        llm_method=combined.get("LLM_METHOD", defaults["LLM_METHOD"]),
        llm_model=combined.get("LLM_MODEL", defaults["LLM_MODEL"]),
        llm_url=combined.get("LLM_URL", defaults["LLM_URL"]),
        llm_api_key=combined.get("LLM_API_KEY", defaults["LLM_API_KEY"]),
        log_file=combined.get("LOG_FILE", defaults["LOG_FILE"]),
        log_level=combined.get("LOG_LEVEL", defaults["LOG_LEVEL"]),
    )

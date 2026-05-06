"""YAML config loader with environment variable substitution."""

import os
import re
from pathlib import Path
from typing import Any

import yaml

ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")


def substitute_env_vars(value: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)
        env_value = os.environ.get(var_name)
        if env_value is not None:
            return env_value
        if default is not None:
            return default
        return match.group(0)

    return ENV_VAR_PATTERN.sub(replacer, value)


def process_config_value(value: Any) -> Any:
    if isinstance(value, str):
        substituted = substitute_env_vars(value)
        if substituted != value and substituted.isdigit():
            return int(substituted)
        return substituted
    if isinstance(value, dict):
        return {k: process_config_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [process_config_value(item) for item in value]
    return value


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    if raw_config is None:
        return {}

    return process_config_value(raw_config)

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from tuxemon.database.config import DatabaseConfig
from tuxemon.database.yaml_utils import load_yaml


def load_config(config_path: str) -> DatabaseConfig:
    """Loads configuration from a YAML file and validates it against the DatabaseConfig schema."""
    try:
        data = load_yaml(Path(config_path))
        return DatabaseConfig(**data)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Configuration file '{config_path}' not found."
        )
    except ValidationError as e:
        raise ValueError(
            f"Invalid configuration structure in '{config_path}': {e}"
        )
    except Exception as e:
        raise ValueError(
            f"Unexpected error loading configuration from '{config_path}': {e}"
        )

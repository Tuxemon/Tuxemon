# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import yaml
from pydantic import ValidationError

from tuxemon.database.config import DatabaseConfig


def load_config(config_path: str) -> DatabaseConfig:
    """Loads configuration from a YAML file and validates it against the DatabaseConfig schema."""
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return DatabaseConfig(**data)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Configuration file '{config_path}' not found."
        )
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in '{config_path}': {e}")
    except ValidationError as e:
        raise ValueError(
            f"Invalid configuration structure in '{config_path}': {e}"
        )

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from pathlib import Path
from typing import IO, Any

import yaml

logger = logging.getLogger(__name__)


def load_yaml(filepath: Path) -> Any:
    try:
        with filepath.open(encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.warning(f"Error parsing YAML file: {exc}")
        raise


def dump_yaml_path(path: Path, data: Any, **kwargs: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, **kwargs)


def dump_yaml_io(file: IO[str], data: Any, **kwargs: Any) -> None:
    yaml.safe_dump(data, file, **kwargs)

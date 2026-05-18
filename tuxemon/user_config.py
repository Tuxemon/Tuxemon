# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""Loads and manages the user's game configuration."""

from __future__ import annotations

import logging

from tuxemon.config import TuxemonConfig
from tuxemon.constants import paths
from tuxemon.database.yaml_utils import dump_yaml_path

logger = logging.getLogger(__name__)


def setup_user_environment() -> TuxemonConfig:
    """Sets up user storage directories and loads/saves the game configuration."""
    logger.debug("Setting up user environment and config.")
    try:
        paths.USER_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        paths.USER_GAME_DATA_DIR.mkdir(parents=True, exist_ok=True)
        paths.USER_GAME_SAVE_DIR.mkdir(parents=True, exist_ok=True)
        paths.USER_RECORDING_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("User directories ensured.")
    except OSError as e:
        logger.critical(f"Failed to create user directories: {e}")
        raise

    loaded_config = TuxemonConfig(paths.USER_CONFIG_PATH)

    try:
        dump_yaml_path(
            paths.USER_CONFIG_PATH,
            loaded_config.config_model.model_dump(),
            default_flow_style=False,
            indent=4,
        )
        loaded_config.reload_config()
        logger.info(
            f"Configuration loaded and saved to {paths.USER_CONFIG_PATH}"
        )
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

    return loaded_config


CONFIG = setup_user_environment()

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.constants.asset_loader import fetch_asset, fetch_mod_asset_roots
from tuxemon.constants.paths import mods_folder
from tuxemon.database.data import ModData
from tuxemon.database.loader import ModelLoader
from tuxemon.database.registry import validator
from tuxemon.database.utils import load_config
from tuxemon.database.validator import Validator
from tuxemon.db import load_model_map
from tuxemon.locale.locale import T
from tuxemon.user_config import CONFIG


def bootstrap_database() -> ModData:
    """
    Fully initialize the Tuxemon database layer.
    """
    T.initialize_translations()
    fetch_mod_asset_roots(CONFIG)
    config_path = fetch_asset(mods_folder.as_posix(), "db_config.yaml")
    config = load_config(config_path)
    model_map = load_model_map(config.model_map)
    loader = ModelLoader(model_map)
    db = ModData(config, loader)
    validator.set(Validator(db))
    return db

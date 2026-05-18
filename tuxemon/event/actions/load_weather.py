# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.constants import paths
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.world.weather import (
    WorldWeatherManager,
    load_weather_transition_rules,
)

logger = logging.getLogger(__name__)


@final
@dataclass
class LoadWeatherAction(EventAction):
    """
    Loads a YAML file containing weather previsions using the Pydantic schema
    and registers it with the WorldWeatherManager.

    Script usage:
        .. code-block::

            load_weather <path_to_yaml_file>

    Script parameters:
        model_file: Path to the YAML file (e.g., "weather_previsions.yml").
    """

    name = "load_weather"
    model_file: str | None = None

    def start(self, session: Session) -> None:

        if self.model_file is None:
            yaml_path = paths.mods_folder / "weather_previsions.yml"
        else:
            yaml_path = paths.mods_folder / self.model_file

        rules_model = load_weather_transition_rules(yaml_path)
        manager = WorldWeatherManager(rules_model=rules_model)
        session.client.weather_manager = manager
        logger.info("Weather manager initialized and registered in session.")

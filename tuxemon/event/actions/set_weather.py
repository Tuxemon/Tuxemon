# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetWeatherAction(EventAction):
    """
    Sets the weather to a specific slug using the WorldWeatherManager.
    If no slug is provided, it triggers a weather advancement check.

    Script usage:
        .. code-block::

            set_weather <weather_slug>      # Sets weather directly
            set_weather                     # Advances weather based on previsions

    Script parameters:
        slug: Optional weather slug (e.g., "rain", "sunny", "foggy").
    """

    name = "set_weather"
    slug: Optional[str] = None

    def start(self, session: Session) -> None:
        manager = session.client.weather_manager

        if self.slug:
            transition = None
            current_slug = manager.current_slug
            model = manager._previsions_model

            if model and current_slug in model.previsions:
                for p in model.previsions[current_slug]:
                    if p.next_slug == self.slug:
                        transition = p
                        break

            success = manager.set_weather(self.slug, transition=transition)
            if success:
                logger.info(f"Weather manually set to '{self.slug}'.")
                if transition:
                    logger.info(
                        f"Metadata: temperature={transition.temperature}, wind={transition.wind}"
                    )
            else:
                logger.warning(
                    f"Failed to set weather to '{self.slug}'. Slug may be invalid."
                )
        else:
            manager.advance_turn()
            logger.info("Weather advancement triggered due to missing slug.")

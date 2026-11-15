# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

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
    slug: str | None = None

    def start(self, session: Session) -> None:
        manager = session.client.weather_manager

        if self.slug:
            rule = None
            current_slug = manager.current_slug
            model = manager._transition_rules_model

            if model and current_slug in model.transitions:
                for p in model.transitions[current_slug]:
                    if p.next_slug == self.slug:
                        rule = p
                        break

            success = manager.set_weather(self.slug, rule=rule)
            if success:
                logger.info(f"Weather manually set to '{self.slug}'.")
                if rule:
                    logger.info(
                        f"Metadata: temperature={rule.temperature}, wind={rule.wind}"
                    )
            else:
                logger.warning(
                    f"Failed to set weather to '{self.slug}'. Slug may be invalid."
                )
        else:
            manager.advance_turn()
            logger.info("Weather advancement triggered due to missing slug.")

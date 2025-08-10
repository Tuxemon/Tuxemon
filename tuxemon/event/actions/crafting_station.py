# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger()


@final
@dataclass
class CraftingStationAction(EventAction):
    """
    Change to the specified state.

    Script usage:
        .. code-block::

            crafting_station <character_slug>,<method>[,file_yaml]

    Script parameters:
        character_slug: The slug of the character (NPC).
        method: Suggests how the recipe is executed, e.g., cooking, forging.
        file_yaml: The YAML file (like `recipe.yaml`) that contains the recipe
            definitions to load into the system (mods folder).
    """

    name = "crafting_station"
    character_slug: str
    method: str
    file_yaml: Optional[str] = None

    def start(self, session: Session) -> None:
        self.client = session.client

        if self.client.current_state is None:
            raise RuntimeError("No current state active. This is unexpected.")

        if self.client.current_state.name == "CraftMenuState":
            logger.error(
                f"The state 'CraftMenuState' is already active. No action taken."
            )
            return

        character = get_npc(session, self.character_slug)
        if character is None:
            logger.error(
                f"Character '{self.character_slug}' not found for CraftMenuState."
            )
            return

        file_yaml = self.file_yaml or "recipes.yaml"
        self.client.push_state(
            "CraftMenuState",
            character=character,
            file_yaml=file_yaml,
            method=self.method,
        )

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("CraftMenuState")
        except ValueError:
            self.stop()

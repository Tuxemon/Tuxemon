# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class CameraAction(EventAction):
    """
    Centers the camera on a specified NPC or the original entity.

    Script usage:
        .. code-block::

            camera [slug]

    Script parameters:
        npc_slug: The slug of the character to center the camera on.
        Defaults to None, which centers the camera on the original entity.

    """

    name = "camera"
    npc_slug: Optional[str] = None

    def start(self) -> None:
        self.npc_slug = self.npc_slug or "player"
        character = get_npc(self.session, self.npc_slug)

        world = self.session.client.get_state_by_name(WorldState)
        if character is None:
            world.camera.switch_to_original_entity()
            logger.info("Camera has been reset to the original entity.")
        else:
            world.camera.switch_to_entity(character)
            logger.info(f"Camera has been set on ({character.slug})")

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class CameraFollowAction(EventAction):
    """
    Centers the camera on a specified NPC or the original entity.

    Script usage:
        .. code-block::

            camera_follow [slug]

    Script parameters:
        npc_slug: The slug of the character to center the camera on.
        Defaults to None, which centers the camera on the original entity.
    """

    name = "camera_follow"
    npc_slug: Optional[str] = None

    def start(self, session: Session) -> None:
        self.npc_slug = self.npc_slug or "player"
        character = get_npc(session, self.npc_slug)
        active_camera = session.client.camera_manager.get_active_camera()

        if active_camera is None:
            logger.error("No active camera found.")
            return

        if character is None:
            active_camera.switch_to_original_entity()
            logger.info("Camera has been reset to the original entity.")
        else:
            active_camera.switch_to_entity(character)
            logger.info(f"Camera has been set on ({character.slug})")

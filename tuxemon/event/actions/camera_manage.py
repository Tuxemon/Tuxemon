# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from tuxemon.camera.camera import Camera
from tuxemon.event.eventaction import EventAction

if TYPE_CHECKING:
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class CameraManageAction(EventAction):
    """
    Adds, removes, or switches/follows a camera in the camera manager.

    Script usage:
        .. code-block::

            camera_manage add [name] [npc_slug]
            camera_manage remove [name]
            camera_manage follow [name] [npc_slug]

    Script parameters:
        action: "add", "remove", or "follow"
        camera_name: The identifier for the camera.
        npc_slug: Optional slug of the NPC/entity to follow (used for add/follow).
    """

    name = "camera_manage"
    action: str
    camera_name: str = "default"
    npc_slug: str | None = None

    def start(self, session: Session) -> None:
        manager = session.client.camera_manager

        if self.action == "add":
            entity = session.client.get_npc(self.npc_slug or "player")
            if entity is None:
                logger.error(
                    f"Cannot add camera '{self.camera_name}': NPC '{self.npc_slug}' not found."
                )
                self.stop()
                return
            camera = Camera(
                entity, session.client.boundary, session.client.context
            )
            manager.add_camera(self.camera_name, camera)
            logger.info(
                f"Camera '{self.camera_name}' added following entity '{entity.slug}'."
            )

        elif self.action == "remove":
            try:
                manager.remove_camera(self.camera_name)
                logger.info(f"Camera '{self.camera_name}' removed.")
            except ValueError:
                logger.error(
                    f"Camera '{self.camera_name}' not managed by CameraManager."
                )

        elif self.action == "follow":
            follow = manager.cameras.get(self.camera_name)
            if not follow:
                logger.error(f"Camera '{self.camera_name}' not found.")
                self.stop()
                return
            entity = session.client.get_npc(self.npc_slug or "player")
            if entity is None:
                follow.switch_entity()
                logger.info(
                    f"Camera '{self.camera_name}' reset to original entity."
                )
            else:
                follow.switch_entity(entity)
                logger.info(
                    f"Camera '{self.camera_name}' now following '{entity.slug}'."
                )

        else:
            logger.error(f"Unknown camera_manage action: {self.action}")

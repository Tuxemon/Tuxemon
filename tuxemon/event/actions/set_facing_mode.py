# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.db import FacingMode
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetFacingModeAction(EventAction):
    """
    Change the facing mode of an NPC.

    Script usage:
        .. code-block::

            set_facing_mode <npc_slug>,<mode>

    Script parameters:
        npc_slug: Slug of the NPC whose facing mode will be changed.
        mode: One of the valid facing mode names:
            - follow_movement
            - locked
            - scripted

    This action immediately updates the NPC's facing behavior. When set to
    'locked' or 'scripted', the NPC will no longer automatically rotate to
    match movement direction. When set to 'follow_movement', the NPC resumes
    normal facing updates driven by the PathController.
    """

    name = "set_facing_mode"
    npc_slug: str
    mode: str

    def start(self, session: Session) -> None:
        npc = session.client.get_npc(self.npc_slug)
        if not npc:
            self.stop()
            return

        mode_str = self.mode.strip().lower()

        if mode_str == "follow_movement":
            npc.set_facing_mode(FacingMode.FOLLOW_MOVEMENT)
        elif mode_str == "locked":
            npc.set_facing_mode(FacingMode.LOCKED)
        elif mode_str == "scripted":
            npc.set_facing_mode(FacingMode.SCRIPTED)
        else:
            raise ValueError(
                f"Invalid facing mode '{self.mode}' for NPC '{self.npc_slug}'."
            )

        self.stop()

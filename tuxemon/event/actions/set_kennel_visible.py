# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import KENNEL
from tuxemon.session import Session
from tuxemon.states.pc_kennel import HIDDEN_LIST

logger = logging.getLogger(__name__)


@final
@dataclass
class SetKennelVisibleAction(EventAction):
    """
    Set the kennel visible or hidden.

    From hidden to visible:
    set_kennel_visible player,name_kennel,true

    From visible to hidden:
    set_kennel_visible player,name_kennel,false

    Script usage:
        .. code-block::

            set_kennel_visible <character>,<kennel>,<visible>

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
        kennel: Name of the kennel.
        visible: true/false.

    """

    name = "set_kennel_visible"
    npc_slug: str
    kennel: str
    visible: str

    def start(self, session: Session) -> None:
        character = get_npc(session, self.npc_slug)
        if character is None:
            logger.error(f"{self.npc_slug} not found")
            return

        kennel = self.kennel
        visible = self.visible

        if kennel == KENNEL:
            raise ValueError(
                f"{kennel} cannot be made invisible.",
            )
        else:
            if character.monster_boxes.has_box(kennel, "monster"):
                if visible == "true":
                    if kennel in HIDDEN_LIST:
                        HIDDEN_LIST.remove(kennel)
                    else:
                        return
                elif visible == "false":
                    if kennel in HIDDEN_LIST:
                        return
                    else:
                        HIDDEN_LIST.append(kennel)
                else:
                    raise ValueError(
                        f"{visible} is invalid, must be true or false",
                    )
            else:
                return

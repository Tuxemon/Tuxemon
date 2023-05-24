# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.pc_kennel import HIDDEN_LIST

logger = logging.getLogger(__name__)


@final
@dataclass
class SetKennelAction(EventAction):
    """
    Create a new kennel.
    E.g. set_kennel new_kennel,true

    If the kennel is visible, then it's advisable
    to create a msgid in the en_US PO file.

    msgid "kennel_name"
    msgstr "Kennel Name"

    Script usage:
        .. code-block::

            set_kennel <kennel>,<visible>

    Script parameters:
        kennel: Name of the kennel.
        visible: true/false.

    """

    name = "set_kennel"
    kennel: str
    visible: str

    def start(self) -> None:
        player = self.session.player
        kennel = self.kennel
        visible = self.visible
        if kennel not in player.monster_boxes.keys():
            if visible == "true":
                logger.info(f"Visible storage box {kennel} has been created.")
                player.monster_boxes[kennel] = list()
            elif visible == "false":
                logger.info(f"Hidden storage box {kennel} has been created.")
                HIDDEN_LIST.append(kennel)
                player.monster_boxes[kennel] = list()
            else:
                logger.error(f"{visible} is invalid, must be true or false")
                raise ValueError()
        else:
            return

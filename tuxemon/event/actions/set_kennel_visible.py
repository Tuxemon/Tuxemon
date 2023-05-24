# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.pc import KENNEL
from tuxemon.states.pc_kennel import HIDDEN_LIST

logger = logging.getLogger(__name__)


@final
@dataclass
class SetKennelVisibleAction(EventAction):
    """
    Set the kennel visible or hidden.

    From hidden to visible:
    set_kennel_visible name_kennel,true

    From visible to hidden:
    set_kennel_visible name_kennel,false

    Script usage:
        .. code-block::

            set_kennel_visible <kennel>,<visible>

    Script parameters:
        kennel: Name of the kennel.
        visible: true/false.

    """

    name = "set_kennel_visible"
    kennel: str
    visible: str

    def start(self) -> None:
        player = self.session.player
        kennel = self.kennel
        visible = self.visible

        if kennel == KENNEL:
            logger.error(f"{kennel} cannot be made invisible.")
            raise ValueError()
        else:
            if kennel in player.monster_boxes:
                if visible == "true":
                    if kennel in HIDDEN_LIST:
                        logger.info(f"Storage box {kennel} is now visible.")
                        HIDDEN_LIST.remove(kennel)
                    else:
                        return
                elif visible == "false":
                    if kennel in HIDDEN_LIST:
                        return
                    else:
                        logger.info(f"Storage box {kennel} is now hidden.")
                        HIDDEN_LIST.append(kennel)
                else:
                    logger.error(
                        f"{visible} is invalid, must be true or false"
                    )
                    raise ValueError()
            else:
                return

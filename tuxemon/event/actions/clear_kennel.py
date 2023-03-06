# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.pc import KENNEL


@final
@dataclass
class ClearKennelAction(EventAction):
    """
    Clear a kennel.

    It advisable to save the game and check twice.

    Remember the main kennel is "Kennel"

    Without destination (transfer) the monster will
    be deleted as well as the kennel.

    Script usage:
        .. code-block::

            clear_kennel <kennel>[,transfer]

    Script parameters:
        kennel: The kennel to clear.
        transfer: The kennel to transfer the monsters.

    """

    name = "clear_kennel"
    kennel: str
    transfer: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        kennel = self.kennel
        transfer = self.transfer

        if kennel == KENNEL:
            raise ValueError(
                f"{kennel} cannot be cleared.",
            )
        else:
            if kennel in player.monster_boxes:
                monsters_kennel = player.monster_boxes[kennel]
                if transfer is None:
                    player.monster_boxes.pop(kennel)
                else:
                    if transfer in player.monster_boxes:
                        for mon in monsters_kennel:
                            player.monster_boxes[transfer].append(mon)
                            player.monster_boxes.pop(kennel)
                    else:
                        player.monster_boxes[transfer] = monsters_kennel
                        player.monster_boxes.pop(kennel)
            else:
                return

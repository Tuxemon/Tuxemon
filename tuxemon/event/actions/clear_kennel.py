# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import KENNEL


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
            if player.monster_boxes.has_box(kennel, "monster"):
                if transfer is None:
                    player.monster_boxes.remove_box(kennel)
                else:
                    player.monster_boxes.merge_boxes(kennel, transfer)
                    player.monster_boxes.remove_box(kennel)
            else:
                return

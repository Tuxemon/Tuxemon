# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.pc_kennel import HIDDEN_LIST


@final
@dataclass
class KennelAction(EventAction):
    """
    Print all the kennels or one.
    It returns <name, qty, visible/hidden>
    *qty = number of monsters inside

    Script usage:
        .. code-block::

            kennel_print [kennel]

        Script parameters:
            kennel: Name of the kennel.

    """

    name = "kennel_print"
    kennel: Optional[str] = None

    def start(self) -> None:
        player = self.session.player
        kennel = self.kennel

        if kennel in player.monster_boxes:
            monsters = player.monster_boxes[kennel]
            if kennel in HIDDEN_LIST:
                print(f"{kennel}, {len(monsters)}, hidden")
            else:
                print(f"{kennel}, {len(monsters)}, visible")
        else:
            keys = list(player.monster_boxes.keys())
            for i in keys:
                if i in HIDDEN_LIST:
                    print(i, len(player.monster_boxes[i]), "hidden")
                else:
                    print(i, len(player.monster_boxes[i]), "visible")

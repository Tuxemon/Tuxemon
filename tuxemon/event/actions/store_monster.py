# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Union, final

from tuxemon.event.eventaction import EventAction
from tuxemon.prepare import KENNEL


@final
@dataclass
class StoreMonsterAction(EventAction):
    """
    Store a monster in a box.

    Save the player's monster with the given instance_id to
    the named storage box, removing it from the player party.

    Script usage:
        .. code-block::

            store_monster <monster_id>[,box]

    Script parameters:
        monster_id: Id of the monster to store.
        box: An existing box where the monster will be stored.

    """

    name = "store_monster"
    monster_id: str
    box: Union[str, None] = None

    def start(self) -> None:
        player = self.session.player
        instance_id = uuid.UUID(
            player.game_variables[self.monster_id],
        )
        box = self.box
        monster = player.find_monster_by_id(instance_id)
        if monster is None:
            raise ValueError(
                f"No monster found with instance_id {instance_id}",
            )

        if box is None:
            store = KENNEL
        else:
            if box not in player.monster_boxes.keys():
                raise ValueError(
                    f"No box found with name {box}",
                )
            else:
                store = box

        player.monster_boxes[store].append(monster)
        player.remove_monster(monster)

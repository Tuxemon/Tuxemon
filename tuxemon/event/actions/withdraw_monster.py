# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState

logger = logging.getLogger(__name__)


@final
@dataclass
class WithdrawMonsterAction(EventAction):
    """
    Pull a monster from the given trainer's storage and puts it in their party.

    Note:
        If the trainer's party is already full then the monster will be
        deposited into the default storage box automatically.

    Script usage:
        .. code-block::

            withdraw_monster <trainer>,<monster_id>

    Script parameters:
        trainer: The trainer slug.
        monster_id: The id of the monster to pull.

    """

    name = "withdraw_monster"
    trainer: str
    monster_id: str

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)

        trainer = self.trainer.replace("player", "npc_red")
        npc = world.get_entity(trainer)
        assert npc
        instance_id = uuid.UUID(npc.game_variables[self.monster_id])
        mon = npc.find_monster_in_storage(instance_id)
        assert mon

        npc.remove_monster_from_storage(mon)
        npc.add_monster(mon)

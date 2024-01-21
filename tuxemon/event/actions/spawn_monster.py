# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon import formula, monster
from tuxemon.event import get_monster_by_iid, get_npc
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.states.dialog import DialogState
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
@final
@dataclass
class SpawnMonsterAction(EventAction):
    """
    Breed a new monster.

    Add a new monster, created by breeding the two
    given mons (identified by instance_id, stored in a
    variable) and adds it to the given character's party
    (identified by slug). The parents must be in either
    the trainer's party, or a storage box owned by the
    trainer.

    Script usage:
        .. code-block::

            spawn_monster [npc_slug]

    Script parameters:
        character: Either "player" or npc slug name (e.g. "npc_maple").
            the one who is going to receive the new born

    """

    name = "spawn_monster"
    character: str

    def start(self) -> None:
        player = self.session.player
        mother_id = uuid.UUID(player.game_variables["breeding_mother"])
        father_id = uuid.UUID(player.game_variables["breeding_father"])

        mother = get_monster_by_iid(self.session, mother_id)
        if mother is None:
            logger.debug("Mother not found in party, searching boxes.")
            mother = player.find_monster_in_storage(mother_id)
            if mother is None:
                logger.debug(f"Mother {mother_id} not found in boxes.")
                return

        father = get_monster_by_iid(self.session, father_id)
        if father is None:
            logger.debug("Father not found in party, searching boxes.")
            father = player.find_monster_in_storage(father_id)
            if father is None:
                logger.debug(f"Father {father_id} not found in boxes.")
                return

        # matrix, it respects the types[0], strong against weak.
        # Mother (Water), Father (Earth)
        # Earth > Water => Child (Earth)
        if mother.types[0].slug.water and father.types[0].slug.earth:
            seed = father
        elif mother.types[0].slug.fire and father.types[0].slug.water:
            seed = father
        elif mother.types[0].slug.wood and father.types[0].slug.metal:
            seed = father
        elif mother.types[0].slug.metal and father.types[0].slug.fire:
            seed = father
        elif mother.types[0].slug.earth and father.types[0].slug.wood:
            seed = father
        else:
            seed = mother

        # retrieve the basic form
        for element in seed.history:
            if element.evo_stage.basic:
                seed_slug = element.mon_slug

        # continues the creation of the child.
        child = monster.Monster()
        child.load_from_db(seed_slug)
        child.set_level(5)
        child.set_moves(5)
        child.set_capture(formula.today_ordinal())
        child.current_hp = child.hp
        # child gets random father's moves
        father_moves = len(father.moves)
        replace_tech = random.randrange(0, 2)
        child.moves[replace_tech] = father.moves[
            random.randrange(0, father_moves - 1)
        ]

        character = get_npc(self.session, self.character)
        if character is None:
            logger.error(f"{self.character} not found")
            return
        character.add_monster(child, len(character.monsters))

        msg = T.format("got_new_tuxemon", {"monster_name": child.name})
        open_dialog(self.session, [msg])

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(DialogState)
        except ValueError:
            self.stop()

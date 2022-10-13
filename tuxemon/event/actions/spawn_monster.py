#
# Tuxemon
# Copyright (c) 2020      William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Adam Chevalier <chevalierAdam2@gmail.com>
from __future__ import annotations

import logging
import uuid
from typing import NamedTuple, Optional, Sequence, final

from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import get_avatar
from tuxemon.locale import process_translate_text
from tuxemon.sprite import Sprite
from tuxemon.states.dialog import DialogState
from tuxemon.states.world.worldstate import WorldState
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


class SpawnMonsterActionParameters(NamedTuple):
    npc_slug: str
    breeding_mother: str
    breeding_father: str


# noinspection PyAttributeOutsideInit
@final
class SpawnMonsterAction(EventAction[SpawnMonsterActionParameters]):
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

            spawn_monster <npc_slug>,<breeding_mother>,<breeding_father>

    Script parameters:
        npc_slug: Either "player" or npc slug name (e.g. "npc_maple").
        breeding_mother: Id of the mother monster.
        breeding_father: Id of the father monster.

    """

    name = "spawn_monster"
    param_class = SpawnMonsterActionParameters

    def start(self) -> None:
        npc_slug, breeding_mother, breeding_father = self.parameters
        world = self.session.client.get_state_by_name(WorldState)

        npc_slug = npc_slug.replace("player", "npc_red")
        trainer = world.get_entity(npc_slug)
        if trainer is None:
            logger.error(
                f"Could not find NPC corresponding to slug {npc_slug}"
            )
            return

        mother_id = uuid.UUID(trainer.game_variables[breeding_mother])
        father_id = uuid.UUID(trainer.game_variables[breeding_father])

        mother = trainer.find_monster_by_id(mother_id)
        if mother is None:
            logger.debug("Mother not found in party, searching storage boxes.")
            mother = trainer.find_monster_in_storage(mother_id)

        father = trainer.find_monster_by_id(father_id)
        if father is None:
            logger.debug("Father not found in party, searching storage boxes.")
            father = trainer.find_monster_in_storage(father_id)

        if mother is None:
            logger.error(
                f"Could not find (mother) monster with instance id {mother_id}"
            )
            return
        if father is None:
            logger.error(
                f"Could not find (father) monster with instance id {father_id}"
            )
            return

        new_mon = mother.spawn(father)
        trainer.add_monster(new_mon)

        replace = [f"monster_name={new_mon.name}"]
        avatar = get_avatar(self.session, new_mon.slug)

        self.open_dialog(
            process_translate_text(
                self.session,
                "got_new_tuxemon",
                replace,
            ),
            avatar,
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(DialogState)
        except ValueError:
            self.stop()

    def open_dialog(
        self,
        pages: Sequence[str],
        avatar: Optional[Sprite],
    ) -> None:
        logger.info("Opening dialog window")
        open_dialog(self.session, pages, avatar)

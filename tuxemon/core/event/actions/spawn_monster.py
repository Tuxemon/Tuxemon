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
import uuid

from tuxemon.core.locale import process_translate_text
from tuxemon.core.event.eventaction import EventAction
from tuxemon.core.tools import open_dialog
from tuxemon.core.graphics import get_avatar
import logging

logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class SpawnMonsterAction(EventAction):
    """ Adds a new monster, created by breeding the two
    given mons (identified by instance_id, stored in a
    variable) and adds it to the given character's party
    (identified by slug). The parents must be in either
    the trainer's party, or a storage box owned by the
    trainer.

    Valid Parameters: trainer, breeding_mother, breeding_father

    **Examples:**

    >>> EventAction.__dict__
    {
        "type": "spawn_monster",
        "parameters": [
            "npc_red",
            "123e4567-e89b-12d3-a456-426614174000",
            "123e4567-e89b-12d3-a456-426614174001"
        ]
    }

    """
    name = "spawn_monster"
    valid_parameters = [
        (str, "npc_slug"),
        (str, "breeding_mother"),
        (str, "breeding_father")
    ]

    def start(self):
        npc_slug, breeding_mother, breeding_father = self.parameters
        world = self.session.client.get_state_by_name("WorldState")
        if not world:
            return False

        npc_slug = npc_slug.replace("player", "npc_red")
        trainer = world.get_entity(npc_slug)
        if trainer is None:
            logger.error("Could not find NPC corresponding to slug {}".format(npc_slug))
            return False

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
            logger.error("Could not find (mother) monster with instance id {}".format(mother_id))
            return False
        if father is None:
            logger.error("Could not find (father) monster with instance id {}".format(father_id))
            return False

        new_mon = mother.spawn(father)
        trainer.add_monster(new_mon)

        replace = ["monster_name={}".format(new_mon.name)]
        avatar = get_avatar(self.session, new_mon.slug)

        self.open_dialog(
            process_translate_text(
                self.session,
                "got_new_tuxemon",
                replace,
            ), avatar
        )

    def update(self):
        if self.session.client.get_state_by_name("DialogState") is None:
            self.stop()

    def open_dialog(self, pages, avatar):
        logger.info("Opening dialog window")
        open_dialog(self.session, pages, avatar)
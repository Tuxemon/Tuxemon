# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.actions.common import CommonAction
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterAttributeAction(EventAction):
    """
    Set the given attribute of the monster to the given value.

    Script usage:
        .. code-block::

            set_monster_attribute <variable>,<attribute>,<value>

    Script parameters:
        variable: Name of the variable where to store the monster id.
        attribute: Name of the attribute.
        value: Value of the attribute.

    """

    name = "set_monster_attribute"
    variable: str
    attribute: str
    value: str

    def start(self) -> None:
        player = self.session.player
        if self.variable not in player.game_variables:
            logger.error(f"Game variable {self.variable} not found")
            return

        monster_id = uuid.UUID(player.game_variables[self.variable])
        monster = get_monster_by_iid(self.session, monster_id)
        if monster is None:
            monster = player.monster_boxes.get_monsters_by_iid(monster_id)
            if monster is None:
                logger.error("Monster not found")
                return

        CommonAction.set_entity_attribute(monster, self.attribute, self.value)

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.actions.common import CommonAction
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

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

    def start(self, session: Session) -> None:
        player = session.player
        monster_id = get_valid_uuid(player.game_variables, self.variable)
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.variable}'"
            )
            self.stop()
            return  # Exit early if no valid UUID
        monster = session.client.get_monster_by_iid(monster_id)
        if monster is None:
            monster = player.monster_boxes.get_monsters_by_iid(monster_id)
            if monster is None:
                logger.error("Monster not found")
                self.stop()
                return

        CommonAction.set_entity_attribute(monster, self.attribute, self.value)

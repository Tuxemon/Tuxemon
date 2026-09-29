# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.db import LearningMethod
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

logger = logging.getLogger(__name__)


@final
@dataclass
class LearnTechByMethodAction(EventAction):
    """
    Teaches a technique to a specific monster using a specific learning method.

    Script usage:
        .. code-block::

            learn_tech_by_method <monster_var>,<technique>,<method>

    Parameters:
        monster_var: Game variable name containing the monster UUID.
        technique: Slug of the technique to learn.
        method: Learning method enum name (e.g. "EVENT", "TM")

    Examples:
        "learn_tech_by_method monster_id,flamethrower,EVENT"
        "learn_tech_by_method monster_id,fireblast,TM"
    """

    name = "learn_tech_by_method"
    monster_var: str
    technique: str
    method: str

    def start(self, session: Session) -> None:
        player = session.player

        monster_id = get_valid_uuid(player.game_variables, self.monster_var)
        if monster_id is None:
            logger.info(
                f"No valid monster selected for variable '{self.monster_var}'"
            )
            self.stop()
            return  # Exit early if no valid UUID

        monster = session.client.get_monster_by_iid(monster_id)

        if monster is None:
            logger.error(f"Monster with ID '{monster_id}' not found")
            self.stop()
            return

        try:
            method_enum = LearningMethod[self.method.upper()]
        except KeyError:
            logger.error(f"Invalid learning method: {self.method}")
            self.stop()
            return

        technique_obj = monster.moves.learn_by_method(
            monster, self.technique, method_enum
        )

        if technique_obj:
            logger.info(
                f"{monster.name} learned {technique_obj.slug} via {method_enum.name}"
            )
        else:
            logger.warning(
                f"{monster.name} failed to learn {self.technique} via {method_enum.name}"
            )

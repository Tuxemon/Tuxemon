# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final
from uuid import UUID

from tuxemon.db import LearningMethod
from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

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

        if self.monster_var not in player.game_variables:
            logger.error(f"Monster variable '{self.monster_var}' not found")
            return

        monster_id = UUID(player.game_variables[self.monster_var])
        monster = get_monster_by_iid(session, monster_id)

        if monster is None:
            logger.error(f"Monster with ID '{monster_id}' not found")
            return

        try:
            method_enum = LearningMethod[self.method.upper()]
        except KeyError:
            logger.error(f"Invalid learning method: {self.method}")
            return

        technique_obj = monster.moves.learn_by_method(
            monster.instance_id, self.technique, method_enum
        )

        if technique_obj:
            logger.info(
                f"{monster.name} learned {technique_obj.slug} via {method_enum.name}"
            )
        else:
            logger.warning(
                f"{monster.name} failed to learn {self.technique} via {method_enum.name}"
            )

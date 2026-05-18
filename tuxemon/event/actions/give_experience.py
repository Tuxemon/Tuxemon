# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid, parse_flag

logger = logging.getLogger(__name__)


@final
@dataclass
class GiveExperienceAction(EventAction):
    """
    Gives experience points to the monster.

    Script usage:
        .. code-block::

            give_experience <variable>,<exp>

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters get experience.
        exp: Name of the variable where to store the experience points or
            directly the number of points. Negative value will result in 0.
        trigger_ui: Trigger UI flag ("true", "1", "yes" for True).
            Default False.

    eg. "give_experience name_variable,steps_variable"
    eg. "give_experience name_variable,420"
    """

    name = "give_experience"
    variable: str | None = None
    exp: str | None = None
    trigger_ui: str | None = None

    def start(self, session: Session) -> None:
        player = session.player
        trigger_ui = parse_flag(self.trigger_ui)

        self.exp = "0" if self.exp is None else self.exp
        if self.exp.isdigit():
            exp = int(self.exp)
        else:
            exp = int(player.game_variables.get(self.exp, 0))

        exp = 0 if exp < 0 else exp

        if self.variable is None:
            monsters = player.monsters
        else:
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
            monsters = [monster]

        if not monsters:
            self.stop()
            return

        for mon in monsters:
            mon.give_experience(exp)
            logger.info(f"{mon.name} +{exp} exp")
            result = mon.consume_levelup_summary()
            if result and trigger_ui:
                start, end, diff = result
                session.client.push_state(
                    "LevelUpSummaryState",
                    monster=mon,
                    start_level=start,
                    end_level=end,
                    diff=diff,
                )

    def update(self, session: Session, dt: float) -> None:
        trigger_ui = parse_flag(self.trigger_ui)
        if trigger_ui:
            if "LevelUpSummaryState" not in session.client.active_state_names:
                self.stop()

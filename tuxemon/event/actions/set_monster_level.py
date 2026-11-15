# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster.monster import Monster
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid, parse_flag

logger = logging.getLogger(__name__)


@final
@dataclass
class SetMonsterLevelAction(EventAction):
    """
    Change the level of a monster in the current player's party.

    Script usage:
        .. code-block::

            set_monster_level [variable][,levels_added]

    Script parameters:
        variable: Name of the variable where to store the monster id. If no
            variable is specified, all monsters level up.
        levels_added: Number of levels to add. Negative numbers are allowed.
            Default 1.
        trigger_ui: Trigger UI flag ("true", "1", "yes" for True).
            Default False.
    """

    name = "set_monster_level"
    variable: str | None = None
    levels_added: int | None = None
    trigger_ui: str | None = None

    def start(self, session: Session) -> None:
        player = session.player
        trigger_ui = parse_flag(self.trigger_ui)
        if not player.monsters:
            self.stop()
            return

        if self.levels_added is None:
            self.levels_added = 1

        monsters_to_update: list[Monster] = []

        if self.variable is not None:
            monster_id = get_valid_uuid(player.game_variables, self.variable)
            if monster_id is None:
                logger.info(
                    f"No valid monster selected for variable '{self.variable}'"
                )
                self.stop()
                return
            monster = session.client.get_monster_by_iid(monster_id)
            if monster is None:
                logger.error("Monster not found")
                self.stop()
                return
            monsters_to_update.append(monster)
        else:
            monsters_to_update.extend(player.monsters)

        for monster in monsters_to_update:
            new_level = max(1, monster.level + self.levels_added)
            monster.set_level(new_level, monster.level)

        for monster in monsters_to_update:
            result = monster.consume_levelup_summary()
            if result and trigger_ui:
                start, end, diff = result
                session.client.push_state(
                    "LevelUpSummaryState",
                    monster=monster,
                    start_level=start,
                    end_level=end,
                    diff=diff,
                )

    def update(self, session: Session, dt: float) -> None:
        trigger_ui = parse_flag(self.trigger_ui)
        if trigger_ui:
            if "LevelUpSummaryState" not in session.client.active_state_names:
                self.stop()

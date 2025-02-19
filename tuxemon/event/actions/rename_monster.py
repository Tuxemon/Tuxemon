# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import final

from tuxemon.event import get_monster_by_iid
from tuxemon.event.eventaction import EventAction
from tuxemon.locale import T
from tuxemon.menu.input import InputMenu

logger = logging.getLogger(__name__)


@final
@dataclass
class RenameMonsterAction(EventAction):
    """
    Open the text input screen to rename the monster.

    Script usage:
        .. code-block::

            rename_monster <variable>

    Script parameters:
        variable: Name of the variable where to store the monster id.

    """

    name = "rename_monster"
    variable: str

    def set_monster_name(self, name: str) -> None:
        self.monster.name = name
        logger.info(f"Now {T.translate(self.monster.slug)} is {name}!")

    def start(self) -> None:
        player = self.session.player
        if self.variable not in player.game_variables:
            logger.error(f"Game variable {self.variable} not found")
            return

        monster_id = uuid.UUID(player.game_variables[self.variable])
        monster = get_monster_by_iid(self.session, monster_id)
        if monster is None:
            logger.error("Monster not found")
            return

        self.monster = monster

        self.session.client.push_state(
            InputMenu(
                prompt=T.translate("input_monster_name"),
                callback=self.set_monster_name,
                escape_key_exits=False,
                initial=T.translate(self.monster.slug),
            )
        )

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(InputMenu)
        except ValueError:
            self.stop()

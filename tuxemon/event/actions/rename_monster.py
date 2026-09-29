# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.platform.const.sizes import PLAYER_NAME_LIMIT
from tuxemon.session import Session
from tuxemon.tools import get_valid_uuid

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
            logger.error("Monster not found")
            self.stop()
            return

        self.monster = monster

        session.client.push_state(
            "InputMenu",
            prompt=T.translate("input_monster_name"),
            callback=self.set_monster_name,
            escape_key_exits=False,
            initial=T.translate(self.monster.slug),
            char_limit=PLAYER_NAME_LIMIT,
        )

    def update(self, session: Session, dt: float) -> None:
        if "InputMenu" not in session.client.active_state_names:
            self.stop()

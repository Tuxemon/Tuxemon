# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import ClassVar, final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session
from tuxemon.states.monster_menu import MonsterMenuHandler

logger = logging.getLogger(__name__)


@final
@dataclass
class OpenMenuAction(EventAction):
    """
    Open the team view or the world menu from a script, and wait until the
    player closes it.

    Menu-driven maps (where a choice dialog is always showing) use this so
    the player can still rearrange the team, use items or save.

    Script usage:
        .. code-block::

            open_menu <menu>

    Script parameters:
        menu: "team" for the team view (reorder, info, items), or "world"
            for the full menu (team, bag, save, options...).
    """

    name = "open_menu"
    menu: str

    STATES: ClassVar[dict[str, str]] = {
        "team": "MonsterMenuState",
        "world": "WorldMenuState",
    }

    def start(self, session: Session) -> None:
        client = session.client
        if self.menu not in self.STATES:
            logger.error(
                f"open_menu: unknown menu '{self.menu}', "
                f"use one of {sorted(self.STATES)}"
            )
            self.stop()
            return

        if self.menu == "team":
            MonsterMenuHandler(client, session.player.party).open_monster_menu()
        else:
            client.push_state(
                "WorldMenuState",
                menu_manager=session.world.menu_manager,
                character=session.player,
            )

    def update(self, session: Session, dt: float) -> None:
        if self.STATES[self.menu] not in session.client.active_state_names:
            self.stop()

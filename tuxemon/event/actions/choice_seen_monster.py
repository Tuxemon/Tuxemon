# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import final

from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.session import Session
from tuxemon.ui.menu_options import MenuOptions, create_choice_options

logger = logging.getLogger(__name__)

NO_CHOICE = "no_choice"


@final
@dataclass
class ChoiceSeenMonsterAction(EventAction):
    """
    Ask the player to show one species from their Tuxepedia (seen or caught).

    Each entry has its name (opens its Tuxepedia page) and a pick button.
    Back closes the menu without a pick, unless a pick is required.

    Script usage:
        .. code-block::

            choice_seen_monster <variable>[,must]

    Script parameters:
        variable: Variable that receives the species slug, or "no_choice"
            when the menu was closed or the Tuxepedia is empty.
        must: Write "must" to make the player pick (Back does nothing).
    """

    name = "choice_seen_monster"
    variable: str
    must: str | None = None

    def start(self, session: Session) -> None:
        player = session.player
        player.game_variables.set(self.variable, NO_CHOICE)

        def _pick(slug: str) -> None:
            player.game_variables.set(self.variable, slug)
            session.client.remove_state_by_name("ChoiceSeenMonster")

        slugs = sorted(
            player.tuxepedia.get_monsters(),
            key=lambda slug: MonsterModel.lookup(slug, db).txmn_id,
        )
        if not slugs:
            logger.error("choice_seen_monster: the Tuxepedia is empty")
            self.stop()
            return

        options = create_choice_options(
            {slug: partial(_pick, slug) for slug in slugs}
        )
        for opt in options:
            opt.display_text = T.translate(opt.key)

        session.client.push_state(
            "ChoiceSeenMonster",
            menu=MenuOptions(options),
            escape_key_exits=self.must != "must",
        )

    def update(self, session: Session, dt: float) -> None:
        if "ChoiceSeenMonster" not in session.client.active_state_names:
            self.stop()

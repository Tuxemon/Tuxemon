# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session


@final
@dataclass
class RankShowAction(EventAction):
    """
    Copy the player's rank title on a path where a dialog can show it.

    Script usage:
        .. code-block::

            rank_show <path>,<none_text>

    Script parameters:
        path: Name of the path, e.g. scholar.
        none_text: Text to show when the player has no rank on that path.

    Variable set: ``ladder_rank_show_<path>`` (the title, or <none_text>).
    """

    name = "rank_show"
    path: str
    none_text: str

    def start(self, session: Session) -> None:
        variables = session.player.game_variables
        title = variables.get(f"ladder_rank_{self.path}_title")
        variables.set(f"ladder_rank_show_{self.path}", title or self.none_text)

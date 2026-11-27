# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.combat import ranks
from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class RankUpAction(EventAction):
    """
    Raise the player's rank on a path and store its title.

    Script usage:
        .. code-block::

            rank_up <path>,<titles>[,<rank>]

    Script parameters:
        path: Name of the path, e.g. scholar.
        titles: The path's titles from lowest to highest, joined by colons
            (Novice:Scribe:Sage).
        rank: Optional. Raise the rank to this number (a rank already
            higher is kept) instead of by one.

    Variables set: ``ladder_rank_<path>`` (1 = first title, capped at the
    number of titles) and ``ladder_rank_<path>_title`` (the current title).
    """

    name = "rank_up"
    path: str
    titles: str
    rank: int | None = None

    def start(self, session: Session) -> None:
        variables = session.player.game_variables
        titles = ranks.parse_titles(self.titles)
        if not titles:
            logger.error(f"rank_up: no titles for '{self.path}'")
            return
        key = f"ladder_rank_{self.path}"
        current = ranks.parse_rank(variables.get(key))
        if self.rank is None:
            rank = ranks.raise_rank(current, len(titles))
        else:
            rank = ranks.reach_rank(current, int(self.rank), len(titles))
        variables.set(key, str(rank))
        variables.set(f"{key}_title", ranks.title_for(titles, rank) or "")

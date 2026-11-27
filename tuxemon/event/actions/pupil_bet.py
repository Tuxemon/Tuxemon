# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.combat import bets
from tuxemon.database.runtime import db
from tuxemon.db import MonsterModel
from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.session import Session

logger = logging.getLogger(__name__)

PREFIX = "ladder_bet_"


@final
@dataclass
class PupilBetAction(EventAction):
    """
    Judge what the player showed a temple pupil and store the outcome.

    Script usage:
        .. code-block::

            pupil_bet seen,<variable>,<bar_cm>
            pupil_bet team,<variable>,<stat>,<bar>

    Script parameters:
        seen: <variable> holds a species slug picked from the Tuxepedia
            (choice_seen_monster); wins if the species is taller than
            <bar_cm>.
        team: <variable> holds the instance id of a team monster
            (get_player_monster); wins if its <stat> (melee, ranged, armour,
            dodge, speed, level, weight in kg or height in cm) is at least
            <bar>.

    Variables set (prefix ladder_bet_): result (win / lose / none, none =
    nothing was shown), name (the monster shown), value (its height as
    text, or its stat).
    """

    name = "pupil_bet"
    kind: str
    variable: str
    first: str
    second: str | None = None

    def set(self, session: Session, key: str, value: object) -> None:
        session.player.game_variables.set(PREFIX + key, str(value))

    def start(self, session: Session) -> None:
        player = session.player
        shown = str(player.game_variables.get(self.variable) or "")
        self.set(session, "result", bets.NONE)

        if self.kind == "seen":
            if shown not in player.tuxepedia.get_monsters():
                return
            model = MonsterModel.lookup(shown, db)
            unit = session.client.config.unit_measure
            self.set(session, "name", T.translate(model.slug))
            self.set(session, "value", bets.height_text(model.height, unit))
            self.set(
                session,
                "result",
                bets.taller_than(model.height, float(self.first)),
            )

        elif self.kind == "team":
            stat = self.first
            if stat not in bets.BET_STATS or self.second is None:
                logger.error(f"pupil_bet team: bad stat or bar ({stat})")
                return
            for monster in player.monsters:
                if monster.instance_id.hex == shown:
                    value = getattr(monster, stat)
                    unit = session.client.config.unit_measure
                    self.set(session, "name", monster.name)
                    self.set(
                        session, "value", bets.value_text(stat, value, unit)
                    )
                    self.set(
                        session,
                        "result",
                        bets.strong_enough(value, float(self.second)),
                    )
                    return

        else:
            logger.error(f"pupil_bet: unknown kind '{self.kind}'")

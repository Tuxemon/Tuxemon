# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import final

from tuxemon.combat import rival
from tuxemon.database.runtime import db
from tuxemon.db import ElementModel, MonsterModel
from tuxemon.event.eventaction import EventAction
from tuxemon.locale.locale import T
from tuxemon.monster.monster import Monster
from tuxemon.session import Session

logger = logging.getLogger(__name__)

PREFIX = "ladder_contest_"


def species_pool() -> list[rival.Species]:
    """Every first-stage monster the rival could buy."""
    pool = []
    for slug in db.database["monster"]:
        model = MonsterModel.lookup(slug, db)
        if model.txmn_id > 0 and model.stage.value in ("basic", "standalone"):
            pool.append(
                rival.Species(model.slug, tuple(model.types), model.catch_rate)
            )
    return pool


def type_chart() -> dict[str, dict[str, float]]:
    chart = {}
    for slug in db.database["element"]:
        model = ElementModel.lookup(slug, db)
        chart[slug] = {t.against: t.multiplier for t in model.types}
    return chart


@final
@dataclass
class RivalContestAction(EventAction):
    """
    Run one step of a rival contest and store the outcome in game variables.

    Script usage:
        .. code-block::

            rival_contest <kind>[,<arg>[,<level>]]

    Script parameters:
        kind:
            pick_stat - choose the breeder's stat at random.
            stat - compare the player's chosen monster (instance id in
                variable <arg>) with a rival monster on that stat (the
                rival's is freshly bought: level rival.SHOW_LEVEL).
            rarity - compare the chosen monster's rarity with the rival's.
            collect_start / collect_step / collect_end - the collector's
                route race (snapshot, count down encounters, score).
            team - give the rival NPC <arg> a battle team countering the
                player's team.
        arg: monster variable (stat, rarity) or NPC slug (team).
        level: (team only) fixed level for every monster on the rival's
            team, e.g. ``rival_contest team,rex,1``.  Omit to derive
            levels from the player's team as usual.

    Variables set (prefix ladder_contest_): stat, stat_name, result
    (win/lose/draw), you, rival, your_monster, rival_monster, left.
    """

    name = "rival_contest"
    kind: str
    arg: str | None = None
    level: str | None = None

    def set(self, session: Session, key: str, value: object) -> None:
        session.player.game_variables.set(PREFIX + key, str(value))

    def get(self, session: Session, key: str) -> str | None:
        value = session.player.game_variables.get(PREFIX + key)
        return None if value is None else str(value)

    def chosen(self, session: Session) -> Monster | None:
        iid = session.player.game_variables.get(self.arg or "")
        for monster in session.player.monsters:
            if monster.instance_id.hex == iid:
                return monster
        return None

    def start(self, session: Session) -> None:
        rng = random.Random()
        player = session.player

        if self.kind == "pick_stat":
            stat = rng.choice(rival.CONTEST_STATS)
            self.set(session, "stat", stat)
            self.set(
                session,
                "stat_name",
                T.translate(f"field_notes_stat_{stat}_name"),
            )

        elif self.kind in ("stat", "rarity"):
            mon = self.chosen(session)
            if mon is None:
                logger.error(
                    f"rival_contest: no monster chosen in '{self.arg}'"
                )
                self.set(session, "result", "lose")
                return
            pick = rival.counter_species(
                [t.slug for t in mon.types.current],
                species_pool(),
                type_chart(),
                rng,
            )
            level = (
                rival.SHOW_LEVEL
                if self.kind == "stat"
                else rival.rival_level(mon.level, rng)
            )
            other = Monster.spawn_base(pick.slug, level)
            if self.kind == "stat":
                stat = self.get(session, "stat") or "melee"
                you = getattr(mon, stat)
                them = rival.show_stat(getattr(other, stat))
            else:
                you = rival.rarity(mon.catch_rate)
                them = rival.rarity(other.catch_rate)
            self.set(session, "you", you)
            self.set(session, "rival", them)
            self.set(session, "your_monster", mon.name)
            self.set(session, "rival_monster", other.name)
            self.set(session, "result", rival.outcome(you, them))

        elif self.kind == "collect_start":
            self.set(session, "caught0", player.tuxepedia.get_caught_count())
            self.set(session, "left", rival.COLLECT_ENCOUNTERS)

        elif self.kind == "collect_step":
            left = int(self.get(session, "left") or 0)
            self.set(session, "left", max(0, left - 1))

        elif self.kind == "collect_end":
            start = int(self.get(session, "caught0") or 0)
            you = player.tuxepedia.get_caught_count() - start
            them = rng.randint(*rival.RIVAL_HAUL)
            self.set(session, "you", you)
            self.set(session, "rival", them)
            self.set(session, "result", rival.outcome(you, them))

        elif self.kind == "team":
            npc = session.client.get_npc(self.arg or "")
            if npc is None:
                logger.error(f"rival_contest team: NPC '{self.arg}' not found")
                return
            party = [
                ([t.slug for t in m.types.current], m.level)
                for m in player.monsters
            ]
            team_level: int | None = None
            if self.level is not None:
                try:
                    team_level = int(self.level)
                except ValueError:
                    logger.error(
                        f"rival_contest team: level '{self.level}' "
                        "is not a whole number"
                    )
            for slug, lvl in rival.rival_team(
                party, species_pool(), type_chart(), rng, level=team_level
            ):
                monster = Monster.spawn_base(slug, lvl)
                npc.party.add_monster(monster, len(npc.monsters))

        else:
            logger.error(f"rival_contest: unknown kind '{self.kind}'")

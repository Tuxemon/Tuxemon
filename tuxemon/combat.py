# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

Combat related code that can be independent of the combat state.

Code here might be shared by states, actions, conditions, etc.

"""

from __future__ import annotations

import logging
import random
from collections.abc import Generator, Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon.db import PlagueType
from tuxemon.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.player import Player


logger = logging.getLogger()


def check_battle_legal(player: Player) -> bool:
    """
    Checks to see if the player has any monsters fit for battle.

    Parameters:
        player: Player object.

    Returns:
        Whether the player has monsters that can fight.

    """
    # Don't start a battle if we don't even have monsters in our party yet.
    if len(player.monsters) < 1:
        logger.warning("Cannot start battle, player has no monsters!")
        return False
    else:
        if fainted_party(player.monsters):
            logger.warning(
                "Cannot start battle, player's monsters are all DEAD."
            )
            return False
        else:
            return True


def pre_checking(
    monster: Monster,
    technique: Technique,
    target: Monster,
) -> Technique:
    """
    Pre checking allows to check if there are statuses
    or other conditions that change the chosen technique.
    """
    if monster.status:
        monster.status[0].phase = "pre_checking"
        result_status = monster.status[0].use(target)
        if result_status["technique"]:
            technique = result_status["technique"]

    status = Technique()
    if monster.plague == PlagueType.infected:
        value = random.randint(1, 8)
        if value == 1:
            status.load("spyderbite")
            technique = status
    return technique


def has_status(monster: Monster, status_name: str) -> bool:
    """
    Checks to see if the monster has a specific status/condition.
    """
    return any(t for t in monster.status if t.slug == status_name)


def has_effect(technique: Technique, effect_name: str) -> bool:
    """
    Checks to see if the technique has a specific effect (eg ram -> damage).
    """
    return any(t for t in technique.effects if t.name == effect_name)


def has_effect_param(
    tech: Technique, effect: str, status: str, param: str
) -> bool:
    """
    Checks to see if the effect has the corresponding parameter.
    """
    find: bool = False
    for ele in tech.effects:
        if ele.name == effect:
            output = getattr(ele, param)
            if output == status:
                find = True
    return find


def fainted(monster: Monster) -> bool:
    return has_status(monster, "faint") or monster.current_hp <= 0


def get_awake_monsters(
    player: NPC, monsters: list[Monster], turn: int
) -> Generator[Monster, None, None]:
    """
    Iterate all non-fainted monsters in party.

    Parameters:
        player: Player object.

    Yields:
        Non-fainted monsters.

    """
    mons = [
        ele
        for ele in player.monsters
        if not fainted(ele) and ele not in monsters
    ]
    if mons:
        if len(mons) > 1:
            mon = random.choice(mons)
            # avoid random choice (1st turn)
            if turn == 1:
                yield from mons
            else:
                yield mon
        else:
            yield mons[0]


def alive_party(player: NPC) -> list[Monster]:
    not_fainted = [ele for ele in player.monsters if not fainted(ele)]
    return not_fainted


def fainted_party(party: Sequence[Monster]) -> bool:
    return all(map(fainted, party))


def defeated(player: NPC) -> bool:
    return fainted_party(player.monsters)


def check_moves(monster: Monster, levels: int) -> Optional[str]:
    tech = monster.update_moves(levels)
    if tech:
        message = T.format(
            "tuxemon_new_tech",
            {
                "name": monster.name.upper(),
                "tech": tech.name.upper(),
            },
        )
        return message
    return None

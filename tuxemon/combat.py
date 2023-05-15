# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

Combat related code that can be independent of the combat state.

Code here might be shared by states, actions, conditions, etc.

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Generator, List, Sequence

from tuxemon.db import PlagueType
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.player import Player
    from tuxemon.technique.technique import Technique


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


def has_effect_give(technique: Technique, status: str) -> bool:
    """
    Checks to see if the give effect has the corresponding status.
    """
    effect_name: str = "give"
    find: bool = False
    for ele in technique.effects:
        if ele.name == effect_name:
            output = getattr(ele, "condition")
            if output == status:
                find = True
    return find


def has_status_bond(monster: Monster) -> bool:
    """
    Statuses connected are the ones where an effect is present only
    if both monsters are alive (lifeleech, grabbed).
    """
    if has_status(monster, "status_grabbed"):
        return True
    elif has_status(monster, "status_lifeleech"):
        return True
    else:
        return False


def fainted(monster: Monster) -> bool:
    return has_status(monster, "status_faint") or monster.current_hp <= 0


def get_awake_monsters(
    player: NPC, monsters: List[Monster]
) -> Generator[Monster, None, None]:
    """
    Iterate all non-fainted monsters in party.

    Parameters:
        player: Player object.

    Yields:
        Non-fainted monsters.

    """
    for monster in player.monsters:
        if not fainted(monster):
            if monster not in monsters:
                yield monster


def alive_party(player: NPC) -> List[Monster]:
    not_fainted = [ele for ele in player.monsters if not fainted(ele)]
    return not_fainted


def fainted_party(party: Sequence[Monster]) -> bool:
    return all(map(fainted, party))


def defeated(player: NPC) -> bool:
    return fainted_party(player.monsters)


def scope(monster: Monster) -> str:
    message = T.format(
        "combat_scope",
        {
            "AR": monster.armour,
            "DE": monster.dodge,
            "ME": monster.melee,
            "RD": monster.ranged,
            "SD": monster.speed,
        },
    )
    return message


def spyderbite(monster: Monster) -> str:
    message: str
    if monster.plague == PlagueType.infected:
        message = T.format(
            "combat_state_plague3",
            {
                "target": monster.name.upper(),
            },
        )
    else:
        message = T.format(
            "combat_state_plague0",
            {
                "target": monster.name.upper(),
            },
        )
    return message

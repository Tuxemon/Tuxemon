# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

Combat related code that can be independent of the combat state.

Code here might be shared by states, actions, conditions, etc.

"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Generator, List, Sequence, Union

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
    player: NPC,
    enemy: NPC,
) -> Technique:
    """
    Pre checking allows to check if there are statuses
    or other conditions that change the choosen technique.
    """
    status = Technique()
    if has_status(monster, "status_dozing"):
        status.load("status_dozing")
        technique = status
    if has_status(monster, "status_flinching"):
        fli = random.randint(1, 2)
        if fli == 1:
            status.load("skip")
            technique = status
            monster.status.clear()
    if has_status(monster, "status_wild"):
        wild = random.randint(1, 4)
        if wild == 1:
            status.load("skip")
            technique = status
            monster.current_hp -= monster.hp // 8
    if has_status(monster, "status_confused"):
        confusion = random.randint(1, 2)
        if confusion == 1:
            player.game_variables["status_confused"] = "on"
            confused = [
                ele
                for ele in monster.moves
                if ele.next_use <= 0
                and not has_effect_give(ele, "status_confused")
            ]
            if confused:
                technique = random.choice(confused)
            else:
                status.load("skip")
                technique = status
        else:
            player.game_variables["status_confused"] = "off"
    if monster.plague == PlagueType.infected:
        value = random.randint(1, 8)
        if value == 1:
            status.load("status_spyderbite")
            technique = status
            # infect mechanism
            if (
                enemy.plague == PlagueType.infected
                or enemy.plague == PlagueType.healthy
            ):
                target.plague = PlagueType.infected
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
    mons = [
        ele
        for ele in player.monsters
        if not fainted(ele) and ele not in monsters
    ]
    if mons:
        if len(mons) > 1:
            mon = random.choice(mons)
            # avoid random choice filling battlefield (1st turn)
            if player.isplayer:
                yield from mons
            else:
                yield mon
        else:
            yield mons[0]


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


def confused(monster: Monster, technique: Technique) -> str:
    message = T.format(
        "combat_state_confused_tech",
        {
            "target": monster.name.upper(),
            "name": technique.name.upper(),
        },
    )
    return message


def check_moves(monster: Monster, levels: int) -> Union[str, None]:
    tech: Union[Technique, None] = None
    for move in monster.moveset:
        # monster levels up 1 level
        if levels == 1:
            if move.level_learned == monster.level:
                tech = learn(monster, move.technique)
        # monster levels up multiple levels
        else:
            level_before = monster.level - levels
            # if there are techniques in this range
            if level_before < move.level_learned <= monster.level:
                tech = learn(monster, move.technique)
    if tech:
        monster.learn(tech)
        message = T.format(
            "tuxemon_new_tech",
            {
                "name": monster.name.upper(),
                "tech": tech.name.upper(),
            },
        )
        return message
    else:
        return None


def learn(monster: Monster, tech: str) -> Union[Technique, None]:
    technique = Technique()
    technique.load(tech)
    duplicate = [mov for mov in monster.moves if mov.slug == technique.slug]
    if duplicate:
        return None
    return technique

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

Combat related code that can be independent of the combat state.

Code here might be shared by states, actions, conditions, etc.

"""

from __future__ import annotations

import datetime as dt
import logging
import random
from collections.abc import Generator, Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon.battle import Battle
from tuxemon.db import OutputBattle, PlagueType, SeenStatus
from tuxemon.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.states.combat.combat import CombatState, DamageMap


logger = logging.getLogger()


def check_battle_legal(character: NPC) -> bool:
    """
    Checks to see if the character has any monsters fit for battle.

    Parameters:
        character: Character object.

    Returns:
        Whether the character has monsters that can fight.

    """
    if not character.monsters:
        logger.error(f"Cannot start battle, {character.name} has no monsters!")
        return False
    else:
        if fainted_party(character.monsters):
            logger.error(
                f"Cannot start battle, {character.name}'s monsters are all DEAD."
            )
            return False
        else:
            return True


def pre_checking(
    monster: Monster,
    technique: Technique,
    target: Monster,
    combat: CombatState,
) -> Technique:
    """
    Pre checking allows to check if there are statuses
    or other conditions that change the chosen technique.
    """
    if monster.status:
        monster.status[0].combat_state = combat
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
    """
    Checks to see if the monster is fainted.
    """
    return has_status(monster, "faint") or monster.current_hp <= 0


def recharging(technique: Technique) -> bool:
    """
    Checks to see if a technique is recharging.
    """
    return technique.next_use > 0


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
        params = {"name": monster.name.upper(), "tech": tech.name.upper()}
        message = T.format("tuxemon_new_tech", params)
        return message
    return None


def award_money(loser: Monster, winner: Monster) -> int:
    """
    It calculates money to be awarded. It allows multiple methods.
    The default one is "default".

    The method could be changed by setting a new value for the game
    variable called "method_money".

    Parameters:
        loser: Fainted monster.
        winner: Winner monster.

    Returns:
        Amount of money.
    """
    method: str = "default"
    # update method
    if winner.owner and winner.owner.isplayer:
        trainer = winner.owner
        if "method_money" not in trainer.game_variables:
            trainer.game_variables["method_money"] = "default"
        method = trainer.game_variables["method_money"]

    # methods
    if method == "default":
        result = loser.level * loser.money_modifier
        money = int(result)
    else:
        raise ValueError(f"A formula for '{method}' doesn't exist.")
    return money


def award_experience(
    loser: Monster, winner: Monster, damages: list[DamageMap]
) -> int:
    """
    It calculates experience to be awarded. It allows multiple methods.
    The default one is "default".

    The method could be changed by setting a new value for the game
    variable called "method_experience".

    Parameters:
        loser: Fainted monster.
        winner: Winner monster.
        damages: The list with all the damages.

    Returns:
        Amount of experience.
    """
    # how many loser has been hit
    hits = len([ele for ele in damages if ele.defense == loser])
    # how many loser has been hit by the winner
    hits_mon = len(
        [
            ele
            for ele in damages
            if ele.defense == loser and ele.attack == winner
        ]
    )
    # all the monsters who hit the loser
    winners = [ele.attack for ele in damages if ele.defense == loser]

    method: str = "default"
    exp_tot = float(loser.total_experience)
    exp_mod = float(loser.experience_modifier)

    # update method
    if winner.owner and winner.owner.isplayer:
        trainer = winner.owner
        if "method_experience" not in trainer.game_variables:
            trainer.game_variables["method_experience"] = "default"
        method = trainer.game_variables["method_experience"]

    # methods
    if method == "default":
        result = (exp_tot // (loser.level * hits)) * exp_mod
        exp = int(result)
    elif method == "proportional":
        prop = hits_mon / hits
        result = (exp_tot // (loser.level * hits)) * exp_mod * prop
        exp = int(result)
    elif method == "test":
        traded = 1.5 if winner.traded else 1.0
        wild = 1 if loser.money_modifier == 0 else 1.5
        result = (
            ((exp_tot * loser.level) / 7)
            * 1
            / len(winners)
            * exp_mod
            * traded
            * wild
        )
        exp = int(result)
    elif method == "xp_transmitter":
        alive = alive_party(trainer)
        idle_monsters = list(set(alive).symmetric_difference(winners))
        result = (exp_tot // (loser.level * hits)) * exp_mod * 1 / len(alive)
        exp = int(result)
        for monster in idle_monsters:
            monster.give_experience(exp)
    else:
        raise ValueError(f"A formula for '{method}' doesn't exist.")
    return exp


def get_winners(loser: Monster, damages: list[DamageMap]) -> set[Monster]:
    """
    It extracts from the damages the monster/s who hit the loser.

    Parameters:
        loser: Fainted monster.
        damages: The list with all the damages.

    Returns:
        Set of winners.
    """
    method: str = "default"
    winners = [ele.attack for ele in damages if ele.defense == loser]

    # update method
    if winners and winners[0].owner and winners[0].owner.isplayer:
        trainer = winners[0].owner
        if "method_experience" not in trainer.game_variables:
            trainer.game_variables["method_experience"] = "default"
        method = trainer.game_variables["method_experience"]

    # methods
    if method == "xp_transmitter":
        alive = alive_party(trainer)
        return set(alive)
    else:
        return set(winners)


def battlefield(monster: Monster, players: Sequence[NPC]) -> None:
    """
    Record the useful properties of the last monster fought.

    Parameters:
        monster: The monster on the ground.
        players: All the remaining players.

    """
    human = [player for player in players if player.isplayer]
    for _human in human:
        var = _human.game_variables
        if monster not in _human.monsters:
            var["battle_last_monster_name"] = monster.name
            var["battle_last_monster_level"] = monster.level
            var["battle_last_monster_type"] = monster.types[0].slug
            var["battle_last_monster_category"] = monster.category
            var["battle_last_monster_shape"] = monster.shape
            # Avoid reset string to seen if monster has already been caught
            if monster.slug not in _human.tuxepedia:
                _human.tuxepedia[monster.slug] = SeenStatus.seen


def plague(player: NPC) -> None:
    """
    Infects all the team if the trainer is infected.

    Parameters:
        player: All the remaining players.

    """
    if player.plague == PlagueType.infected:
        for monster in player.monsters:
            monster.plague = PlagueType.infected


def track_battles(
    output: str,
    player: NPC,
    players: Sequence[NPC],
    prize: int = 0,
    trainer_battle: bool = False,
) -> str:
    """
    Tracks battles, fills variables and returns the message.

    Parameters:
        output: Output of the battle: won, lost, draw
        player: The human player.
        players: All the players (eg if player is winner, players are losers)
        prize: Amount of money (prize) after fighting.
        trainer_battle: Whether a trainer or wild encounter.

    Returns:
        Message to display.
    """

    if output == "won":
        winner = player
        losers = players
        winner.game_variables["battle_last_result"] = OutputBattle.won
        if trainer_battle:
            winner.give_money(prize)
            for _loser in losers:
                params = {
                    "npc": _loser.name.upper(),
                    "prize": prize,
                    "currency": "$",
                }
                winner.game_variables["battle_last_trainer"] = _loser.slug
                message = T.format("combat_victory_trainer", params)
                register_battles(OutputBattle.won, winner, _loser)
            return message
        else:
            return T.translate("combat_victory")
    elif output == "lost":
        loser = player
        winners = players
        loser.game_variables["battle_last_result"] = OutputBattle.lost
        loser.game_variables["teleport_clinic"] = OutputBattle.lost
        message = T.translate("combat_defeat")
        if trainer_battle:
            for _winner in winners:
                loser.game_variables["battle_last_trainer"] = _winner.slug
                register_battles(OutputBattle.lost, loser, _winner)
            return message
        return message
    else:
        # draw
        defeat = list(players)
        defeat.remove(player)
        player.game_variables["battle_last_result"] = OutputBattle.draw
        player.game_variables["teleport_clinic"] = OutputBattle.lost
        if trainer_battle:
            for _player in defeat:
                player.game_variables["battle_last_trainer"] = _player.slug
                register_battles(OutputBattle.draw, player, _player)
        return T.translate("combat_draw")


def register_battles(output: OutputBattle, player: NPC, enemy: NPC) -> None:
    """
    Registers battles in Battle()

    Parameters:
        output: Output of the battle: won, lost, draw
        player: The human player.
        enemy: The enemy player.

    """
    battle = Battle()
    battle.opponent = enemy.slug
    battle.outcome = output
    battle.date = dt.date.today().toordinal()
    player.battles.append(battle)

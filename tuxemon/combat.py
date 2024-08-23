# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""

Combat related code that can be independent of the combat state.

Code here might be shared by states, actions, conditions, etc.

"""

from __future__ import annotations

import logging
import random
from collections.abc import Generator, Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon.db import (
    GenderType,
    OutputBattle,
    PlagueType,
    SeenStatus,
    StatType,
)
from tuxemon.locale import T
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState
    from tuxemon.states.combat.combat_classes import DamageReport


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
            if party_no_tech(character.monsters):
                no_tech = party_no_tech(character.monsters)
                logger.error(
                    f"Cannot start battle, {no_tech} has/have no techniques."
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


def party_no_tech(party: list[Monster]) -> list[str]:
    """
    Return list of monsters without techniques.
    """
    return [p.name for p in party if not p.moves]


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
    character: NPC,
    monsters: list[Monster],
    turn: int,
    method: Optional[str] = None,
) -> Generator[Monster, None, None]:
    """
    Iterate all non-fainted monsters in party.

    Parameters:
        character: The character.
        monsters: List of monsters in the battlefield.
        turn: Turn of the battle.
        method: Parameter change the monster.

    Yields:
        Non-fainted monsters.

    """
    mons = [
        _mon
        for _mon in character.monsters
        if not fainted(_mon) and _mon not in monsters
    ]
    if mons:
        if len(mons) > 1:
            if turn == 1:
                yield from mons
            else:
                if method is None:
                    yield from mons
                else:
                    mon = retrieve_from_party(mons, method)
                    yield mon
        else:
            yield mons[0]


def alive_party(character: NPC) -> list[Monster]:
    """
    Returns a list with all the monsters alive in the character's party.
    """
    alive = [ele for ele in character.monsters if not fainted(ele)]
    return alive


def fainted_party(party: Sequence[Monster]) -> bool:
    """
    Whether the party is fainted or not.
    """
    return all(map(fainted, party))


def defeated(character: NPC) -> bool:
    """
    Whether all the character's party is fainted.
    """
    return fainted_party(character.monsters)


def check_moves(monster: Monster, levels: int) -> Optional[str]:
    """
    Checks if during the levelling up there is/are new tech/s to learn.
    If there is/are new tech/s it returns the message, otherwise None.
    """
    techs = monster.update_moves(levels)
    if techs:
        tech_list = ", ".join(tech.name.upper() for tech in techs)
        params = {"name": monster.name.upper(), "tech": tech_list}
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
    method = (
        winner.owner.game_variables.get("method_money", "default")
        if winner.owner and winner.owner.isplayer
        else "default"
    )

    def default_method() -> int:
        return int(loser.level * loser.money_modifier)

    methods = {"default": default_method}

    if method not in methods:
        raise ValueError(f"A formula for {method} doesn't exist.")

    return methods[method]()


def award_experience(
    loser: Monster, winner: Monster, damages: list[DamageReport]
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
    hits = sum(1 for damage in damages if damage.defense == loser)
    hits_mon = sum(
        1
        for damage in damages
        if damage.defense == loser and damage.attack == winner
    )
    winners = [damage.attack for damage in damages if damage.defense == loser]

    method = (
        winner.owner.game_variables.get("method_experience", "default")
        if winner.owner and winner.owner.isplayer
        else "default"
    )

    exp_tot = float(loser.total_experience)
    exp_mod = float(loser.experience_modifier)

    def default_method() -> int:
        return int((exp_tot // (loser.level * hits)) * exp_mod)

    def proportional_method() -> int:
        return int(
            (exp_tot // (loser.level * hits)) * exp_mod * (hits_mon / hits)
        )

    def test_method() -> int:
        return int(
            ((exp_tot * loser.level) / 7)
            * 1
            / len(winners)
            * exp_mod
            * (1.5 if winner.traded else 1.0)
            * (1 if loser.money_modifier == 0 else 1.5)
        )

    def xp_transmitter_method() -> int:
        return distribute_experience(
            exp_tot, loser.level, hits, exp_mod, winners, winner.owner
        )

    methods = {
        "default": default_method,
        "proportional": proportional_method,
        "test": test_method,
        "xp_transmitter": xp_transmitter_method,
    }

    if method not in methods:
        raise ValueError(f"A formula for {method} doesn't exist.")

    return methods[method]()


def distribute_experience(
    exp_tot: float,
    level: int,
    hits: int,
    exp_mod: float,
    winners: list[Monster],
    owner: Optional[NPC],
) -> int:
    if owner:
        alive = alive_party(owner)
        idle_monsters = list(set(alive).symmetric_difference(winners))
        exp = int((exp_tot // (level * hits)) * exp_mod * 1 / len(alive))
        for monster in idle_monsters:
            monster.give_experience(exp)
        return exp
    return 0


def get_winners(loser: Monster, damages: list[DamageReport]) -> set[Monster]:
    """
    It extracts from the damages the monster/s who hit the loser.

    Parameters:
        loser: Fainted monster.
        damages: The list with all the damages.

    Returns:
        Set of winners.
    """
    winners = {damage.attack for damage in damages if damage.defense == loser}
    if winners and next(iter(winners)).owner:
        trainer = next(iter(winners)).owner
        if trainer and trainer.isplayer:
            method = trainer.game_variables.get("method_experience", "default")
            if method == "xp_transmitter":
                return set(alive_party(trainer))
    return winners


def battlefield(
    session: Session, monster: Monster, players: Sequence[NPC]
) -> None:
    """
    Record the useful properties of the last monster fought.

    Parameters:
        session: Session
        monster: The monster on the ground.
        players: All the remaining players.

    """
    human = [player for player in players if player.isplayer]
    for _human in human:
        if monster not in _human.monsters:
            set_var(session, "battle_last_monster_name", monster.name)
            set_var(session, "battle_last_monster_level", str(monster.level))
            set_var(session, "battle_last_monster_type", monster.types[0].slug)
            set_var(session, "battle_last_monster_category", monster.category)
            set_var(session, "battle_last_monster_shape", monster.shape)
            # updates tuxepedia
            set_tuxepedia(session, _human.slug, monster.slug, "seen")


def set_tuxepedia(
    session: Session, character: str, monster: str, label: str
) -> None:
    """
    Registers monster in Tuxepedia.

    Parameters:
        character: Character slug.
        monster: The key game variable.
        value: The value game variable.

    """
    client = session.client.event_engine
    client.execute_action("set_tuxepedia", [character, monster, label], True)


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
    session: Session,
    output: str,
    player: NPC,
    players: Sequence[NPC],
    prize: int = 0,
    trainer_battle: bool = False,
) -> str:
    """
    Tracks battles, fills variables and returns the message.

    Parameters:
        session: Session
        output: Output of the battle: won, lost, draw
        player: The human player.
        players: All the players (eg if player is winner, players are losers)
        prize: Amount of money (prize) after fighting.
        trainer_battle: Whether a trainer or wild encounter.

    Returns:
        Message to display.
    """
    _won = OutputBattle.won.value
    _lost = OutputBattle.lost.value
    _draw = OutputBattle.draw.value
    if output == "won":
        winner = player
        losers = players
        info = {"name": winner.name.upper()}
        if trainer_battle:
            # register battle
            for _loser in losers:
                set_battle(session, OutputBattle.won, winner, _loser)
            # set variables
            if winner.isplayer:
                set_var(session, "battle_last_result", _won)
                set_var(session, "battle_last_winner", "player")
                client = session.client.event_engine
                var = ["player", prize]
                client.execute_action("modify_money", var, True)
                if prize > 0:
                    set_var(session, "battle_last_prize", str(prize))
                    info = {
                        "name": winner.name.upper(),
                        "prize": str(prize),
                        "currency": "$",
                    }
                    return T.format("combat_victory_trainer", info)
                else:
                    return T.format("combat_victory", info)
            else:
                set_var(session, "battle_last_winner", winner.slug)
                set_var(session, "battle_last_trainer", winner.slug)
                return T.format("combat_victory", info)
        else:
            # wild monster
            info = {"name": winner.name.upper()}
            if winner.slug == "random_encounter_dummy":
                info = {"name": winner.monsters[0].name.upper()}
            return T.format("combat_victory", info)
    elif output == "lost":
        loser = player
        winners = players
        info = {"name": loser.name.upper()}
        set_var(session, "teleport_clinic", _lost)
        if trainer_battle:
            # set variables
            if loser.isplayer:
                set_var(session, "battle_last_result", _lost)
                set_var(session, "battle_last_loser", "player")
            else:
                set_var(session, "battle_last_loser", loser.slug)
                set_var(session, "battle_last_trainer", loser.slug)
            # register battle
            for _winner in winners:
                set_battle(session, OutputBattle.lost, loser, _winner)
            return T.format("combat_defeat", info)
        return ""
    else:
        # draw
        defeat = list(players)
        defeat.remove(player)
        set_var(session, "teleport_clinic", _lost)
        if trainer_battle:
            set_var(session, "battle_last_result", _draw)
            for _player in defeat:
                set_var(session, "battle_last_trainer", _player.slug)
                set_battle(session, OutputBattle.draw, player, _player)
        return T.translate("combat_draw")


def set_var(session: Session, key: str, value: str) -> None:
    """
    Registers variable in game_variables.

    Parameters:
        session: Session
        key: The key game variable.
        value: The value game variable.

    """
    client = session.client.event_engine
    var = f"{key}:{value}"
    client.execute_action("set_variable", [var], True)


def set_battle(
    session: Session, output: OutputBattle, player: NPC, enemy: NPC
) -> None:
    """
    Registers battles in Battle()

    Parameters:
        session: Session
        output: Output of the battle: won, lost, draw
        player: The human player.
        enemy: The enemy player.

    """
    fighter = "player" if player.isplayer else player.slug
    opponent = "player" if enemy.isplayer else enemy.slug
    client = session.client.event_engine
    client.execute_action("set_battle", [fighter, output, opponent], True)


def build_hud_text(
    menu: str,
    monster: Monster,
    is_right: bool,
    is_trainer: bool,
    is_status: Optional[SeenStatus] = None,
) -> str:
    """
    Returns the text image for use on the callout of the monster.
    eg. Rockitten Lv3

    Parameters:
        menu: Combat menu (eg. MainCombatMenuState).
        monster: The monster fighting.
        is_right: Boolean side (true: right side, false: left side).
            right side (player), left side (opponent)
        is_trainer: Boolean battle (trainer: true, wild: false).

    """
    trainer = monster.owner
    icon: str = ""
    if menu == "MainParkMenuState" and trainer and is_right:
        ball = T.translate("tuxeball_park")
        item = trainer.find_item("tuxeball_park")
        if item is None:
            return f"{ball.upper()}: 0"
        return f"{ball.upper()}: {item.quantity}"
    else:
        if monster.gender == GenderType.male:
            icon += "♂"
        if monster.gender == GenderType.female:
            icon += "♀"
        if not is_trainer:
            # shows captured symbol (wild encounter)
            symbol: str = ""
            if is_status and is_status == SeenStatus.caught and not is_right:
                symbol += "◉"
            return f"{monster.name}{icon} Lv.{monster.level}{symbol}"
        else:
            return f"{monster.name}{icon} Lv.{monster.level}"


def retrieve_from_party(party: list[Monster], method: str) -> Monster:
    """
    Who is the "method" monster in the party?
    Picks the respective monster from the party.

    Parameters:
        party: List of monster.
        method: Parameter to pick the monster (random, strongest, etc.)

    Returns:
        Monster.
    """
    if method == "lv_highest":
        highest = max([m.level for m in party])
        return next(mon for mon in party if mon.level == highest)
    elif method == "lv_lowest":
        lowest = min([m.level for m in party])
        return next(mon for mon in party if mon.level == lowest)
    elif method == "healthiest":
        current_hp = max([m.current_hp for m in party])
        return next(mon for mon in party if mon.current_hp == current_hp)
    elif method in list(StatType):
        stat = max([getattr(m, method) for m in party])
        return next(mon for mon in party if getattr(mon, method) == stat)
    else:
        return random_from_party(party)


def random_from_party(party: list[Monster]) -> Monster:
    """
    Picks a monster randomly from the party.

    Parameters:
        party: List of monster.

    Returns:
        Monster.
    """
    return random.choice(party)

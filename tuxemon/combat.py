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
        if any(
            technique.target.get(target, False)
            for target in ["enemy_monster", "enemy_team", "enemy_trainer"]
        ):
            if random.randint(1, 8) == 1:
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
        monsters: List of monsters on the battlefield.
        turn: Current turn of the battle.
        method: Method to use when selecting a monster (default: None).

    Yields:
        Non-fainted monsters.

    """
    awake_monsters = [
        monster
        for monster in character.monsters
        if not fainted(monster) and monster not in monsters
    ]

    if awake_monsters:
        if len(awake_monsters) == 1:
            yield awake_monsters[0]
        else:
            if turn == 1 or method is None:
                yield from awake_monsters
            else:
                yield retrieve_from_party(awake_monsters, method)


def alive_party(character: NPC) -> list[Monster]:
    """
    Returns a list with all the monsters alive in the character's party.
    """
    return [monster for monster in character.monsters if not fainted(monster)]


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
    eligible_players = [
        p for p in players if p.isplayer and monster not in p.monsters
    ]
    if not eligible_players:
        return

    for player in eligible_players:
        set_var(session, "battle_last_monster_name", monster.name)
        set_var(session, "battle_last_monster_level", str(monster.level))
        set_var(session, "battle_last_monster_type", monster.types[0].slug)
        set_var(session, "battle_last_monster_category", monster.category)
        set_var(session, "battle_last_monster_shape", monster.shape)

        if monster.txmn_id > 0:
            set_tuxepedia(session, player.slug, monster.slug, "seen")


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
    battle_outcomes = {
        "won": OutputBattle.won.value,
        "lost": OutputBattle.lost.value,
        "draw": OutputBattle.draw.value,
    }

    if output not in battle_outcomes:
        raise ValueError("Invalid battle output")

    if output == "won":
        return _handle_win(session, player, players, prize, trainer_battle)
    elif output == "lost":
        return _handle_loss(session, player, players, trainer_battle)
    else:
        return _handle_draw(session, player, players, trainer_battle)


def _handle_win(
    session: Session,
    winner: NPC,
    losers: Sequence[NPC],
    prize: int,
    trainer_battle: bool,
) -> str:
    """
    Handles the case where the human player won the battle.

    Parameters:
        session: Session
        winner: The human player.
        losers: All the players that lost.
        prize: Amount of money (prize) after fighting.
        trainer_battle: Whether a trainer or wild encounter.

    Returns:
        Message to display.
    """
    info = {"name": winner.name.upper()}

    if trainer_battle:
        for loser in losers:
            set_battle(session, OutputBattle.won, winner, loser)

        if winner.isplayer:
            set_var(session, "battle_last_result", OutputBattle.won.value)
            set_var(session, "battle_last_winner", "player")
            client = session.client.event_engine
            var = ["player", prize]
            client.execute_action("modify_money", var, True)

            if prize > 0:
                set_var(session, "battle_last_prize", str(prize))
                info["prize"] = str(prize)
                info["currency"] = "$"
                return T.format("combat_victory_trainer", info)
            else:
                return T.format("combat_victory", info)
        else:
            set_var(session, "battle_last_winner", winner.slug)
            set_var(session, "battle_last_trainer", winner.slug)
            return T.format("combat_victory", info)
    else:
        if winner.slug == "random_encounter_dummy":
            info["name"] = winner.monsters[0].name.upper()
        return T.format("combat_victory", info)


def _handle_loss(
    session: Session,
    loser: NPC,
    winners: Sequence[NPC],
    trainer_battle: bool,
) -> str:
    """
    Handles the case where the human player lost the battle.

    Parameters:
        session: Session
        loser: The human player.
        winners: All the players that won.
        trainer_battle: Whether a trainer or wild encounter.

    Returns:
        Message to display.
    """
    info = {"name": loser.name.upper()}
    set_var(session, "teleport_clinic", OutputBattle.lost.value)

    if trainer_battle:
        if loser.isplayer:
            set_var(session, "battle_last_result", OutputBattle.lost.value)
            set_var(session, "battle_last_loser", "player")
        else:
            set_var(session, "battle_last_loser", loser.slug)
            set_var(session, "battle_last_trainer", loser.slug)

        for winner in winners:
            set_battle(session, OutputBattle.lost, loser, winner)
        return T.format("combat_defeat", info)
    return ""


def _handle_draw(
    session: Session,
    player: NPC,
    players: Sequence[NPC],
    trainer_battle: bool,
) -> str:
    """
    Handles the case where the battle was a draw.

    Parameters:
        session: Session
        player: The human player.
        players: All the players.
        trainer_battle: Whether a trainer or wild encounter.

    Returns:
        Message to display.
    """
    defeat = list(players)
    defeat.remove(player)
    set_var(session, "teleport_clinic", OutputBattle.draw.value)

    if trainer_battle:
        set_var(session, "battle_last_result", OutputBattle.draw.value)
        for player_defeated in defeat:
            set_var(session, "battle_last_trainer", player_defeated.slug)
            set_battle(session, OutputBattle.draw, player, player_defeated)
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

    Parameters:
        menu: Combat menu (eg. MainCombatMenuState).
        monster: The monster fighting.
        is_right: Boolean side (true: right side, false: left side).
            right side (player), left side (opponent)
        is_trainer: Boolean battle (trainer: true, wild: false).

    Returns:
        A string representing the HUD text for the monster.

    """
    if menu == "MainParkMenuState" and monster.owner and is_right:
        # Special case for MainParkMenuState
        ball = T.translate("tuxeball_park")
        item = monster.owner.find_item("tuxeball_park")
        if item is None:
            return f"{ball.upper()}: 0"
        return f"{ball.upper()}: {item.quantity}"

    icon = ""
    if monster.gender == GenderType.male:
        icon = "♂"
    elif monster.gender == GenderType.female:
        icon = "♀"

    symbol = ""
    if not is_trainer and is_status == SeenStatus.caught and not is_right:
        symbol = "◉"

    return f"{monster.name}{icon} Lv.{monster.level}{symbol}"


def retrieve_from_party(party: list[Monster], method: str) -> Monster:
    """
    Retrieves a monster from the party based on the specified method.

    Parameters:
        party: List of monsters in the party.
        method: Method to use when selecting a monster
            (e.g., 'lv_highest', 'healthiest', etc.).

    Returns:
        Monster: The selected monster.

    Notes:
        If the method is not recognized, a random monster from
        the party will be returned.

    """
    methods = {
        "lv_highest": ("level", max),
        "lv_lowest": ("level", min),
        "healthiest": ("current_hp", max),
        "weakest": ("current_hp", min),
        "oldest": ("steps", max),
        "newest": ("steps", min),
    }

    # eg. speed_max, armour_max, etc.
    methods.update(
        {f"{stat.value}_max": (stat.value, max) for stat in StatType}
    )
    # eg. speed_min, armour_min, etc.
    methods.update(
        {f"{stat.value}_min": (stat.value, min) for stat in StatType}
    )

    if method not in methods:
        return random.choice(party)

    attr, func = methods[method]
    return func(party, key=lambda m: getattr(m, attr))

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Combat related code that can be independent of the combat state.
Code here might be shared by states, actions, conditions, etc.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from tuxemon.db import (
    GenderType,
    OutputBattle,
)
from tuxemon.locale import T
from tuxemon.menu.formatter import CurrencyFormatter
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.npc import NPC
    from tuxemon.session import Session


logger = logging.getLogger()


def check_battle_legal(character: NPC) -> bool:
    """
    Checks if the character has monsters fit for battle.

    Parameters:
        character: Character object.

    Returns:
        True if the character's monsters can fight, False otherwise.
    """
    if not character.monsters:
        logger.error(f"Cannot start battle, {character.name} has no monsters!")
        return False

    if fainted_party(character.monsters):
        logger.error(
            f"Cannot start battle, {character.name}'s monsters are all DEAD."
        )
        return False

    if party_no_tech(character.monsters):
        logger.error(
            f"Cannot start battle, {party_no_tech(character.monsters)} has/have no techniques."
        )
        return False

    return True


def check_repellent(character: NPC) -> bool:
    """
    Checks if the repellent is still active.
    """
    repellent_tracker = character.step_tracker.get_tracker("repellent")
    if repellent_tracker is None:
        return False
    return repellent_tracker.countdown > 0


def has_effect(technique: Technique, effect_name: str) -> bool:
    """
    Checks to see if the technique has a specific effect (eg ram -> damage).
    """
    return any(t for t in technique.effects if t.name == effect_name)


def party_no_tech(party: list[Monster]) -> list[str]:
    """
    Return list of monsters without techniques.
    """
    return [p.name for p in party if not p.moves.has_moves()]


def has_effect_param(
    tech: Technique, effect_name: str, attribute: str, name: str
) -> bool:
    """
    Checks whether a specific effect contains the specified attribute with a
    matching value.

    Parameters:
        tech: The technique object containing a list of effects.
        effect_name: The name of the effect to look for (e.g., 'give').
        attribute: The attribute within the effect to check (e.g., 'condition'
            in the 'give' effect).
        name: The expected value of the attribute (e.g., 'diehard', which is
            assigned by the 'give' effect).

    Returns:
        bool: True if an effect with the given name and attribute value is
            found, otherwise False.
    """
    return any(
        ele.name == effect_name and getattr(ele, attribute, None) == name
        for ele in tech.effects
    )


def alive_party(character: NPC) -> list[Monster]:
    """
    Returns a list with all the monsters alive in the character's party.
    """
    return [m for m in character.monsters if not m.is_fainted]


def fainted_party(party: Sequence[Monster]) -> bool:
    """Whether the party is fainted or not."""
    return all(monster.is_fainted for monster in party)


def defeated(character: NPC) -> bool:
    """
    Whether all the character's party is fainted.
    """
    return fainted_party(character.monsters)


def battlefield(session: Session, monster: Monster) -> None:
    """
    Record the useful properties of the last monster fought.

    Parameters:
        session: Session
        monster: The monster on the ground.
        players: All the remaining players.
    """
    set_var(session, "battle_last_monster_name", monster.name)
    set_var(session, "battle_last_monster_level", str(monster.level))
    set_var(session, "battle_last_monster_type", monster.types.primary.slug)


def track_battles(
    session: Session,
    output: str,
    player: NPC,
    players: Sequence[NPC],
    turns: int,
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
        turns: Number of turns the battle lasted.

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

    location = session.client.get_map_name()

    if output == "won":
        return _handle_win(
            session, player, players, turns, location, prize, trainer_battle
        )
    elif output == "lost":
        return _handle_loss(
            session, player, players, turns, location, trainer_battle
        )
    else:
        return _handle_draw(
            session, player, players, turns, location, trainer_battle
        )


def _handle_win(
    session: Session,
    winner: NPC,
    losers: Sequence[NPC],
    turns: int,
    location: str,
    prize: int,
    trainer_battle: bool,
) -> str:
    """Handles the case where the human player won the battle."""
    info = {"name": winner.name.upper()}

    if trainer_battle:
        for loser in losers:
            winner.battle_handler.record_battle(
                opponent=loser.slug,
                outcome=OutputBattle.won,
                steps=int(winner.steps),
                location=location,
                turns=turns,
            )

        if winner.is_player:
            set_var(session, "battle_last_result", OutputBattle.won.value)
            set_var(session, "battle_last_winner", "player")
            money_manager = winner.money_controller.money_manager
            remaining = money_manager.apply_all_battle_shares(prize)
            money_manager.add_money(remaining)

            if remaining > 0:
                formatter = CurrencyFormatter()
                formatted_prize = formatter.format(remaining)
                info["prize"] = formatted_prize
                return T.format("combat_victory_trainer", info)
            else:
                return T.format("combat_victory", info)
        else:
            set_var(session, "battle_last_winner", winner.slug)
            set_var(session, "battle_last_trainer", winner.slug)
            return T.format("combat_victory", info)
    else:
        if winner.monsters[0].wild:
            info["name"] = winner.monsters[0].name.upper()
        return T.format("combat_victory", info)


def _handle_loss(
    session: Session,
    loser: NPC,
    winners: Sequence[NPC],
    turns: int,
    location: str,
    trainer_battle: bool,
) -> str:
    """Handles the case where the human player lost the battle."""
    info = {"name": loser.name.upper()}

    if trainer_battle:
        if loser.is_player:
            set_var(session, "battle_last_result", OutputBattle.lost.value)
            set_var(session, "battle_last_loser", "player")
        else:
            set_var(session, "battle_last_loser", loser.slug)
            set_var(session, "battle_last_trainer", loser.slug)

        for winner in winners:
            loser.battle_handler.record_battle(
                opponent=loser.slug,
                outcome=OutputBattle.lost,
                steps=int(winner.steps),
                location=location,
                turns=turns,
            )
        return T.format("combat_defeat", info)
    return ""


def _handle_draw(
    session: Session,
    player: NPC,
    players: Sequence[NPC],
    turns: int,
    location: str,
    trainer_battle: bool,
) -> str:
    """Handles the case where the battle was a draw."""
    defeat = list(players)
    defeat.remove(player)

    if trainer_battle:
        set_var(session, "battle_last_result", OutputBattle.draw.value)
        for player_defeated in defeat:
            set_var(session, "battle_last_trainer", player_defeated.slug)
            player.battle_handler.record_battle(
                opponent=player_defeated.slug,
                outcome=OutputBattle.draw,
                steps=int(player.steps),
                location=location,
                turns=turns,
            )
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


def build_hud_text(
    menu: str,
    monster: Monster,
    is_right: bool,
    is_trainer: bool,
    is_status: bool,
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
    if menu == "MainParkMenuState" and is_right:
        # Special case for MainParkMenuState
        ball = T.translate("tuxeball_park")
        owner = monster.get_owner()
        item = owner.items.find_item("tuxeball_park")
        if item is None:
            return f"{ball.upper()}: 0"
        return f"{ball.upper()}: {item.quantity}"

    icon = ""
    if monster.gender == GenderType.male:
        icon = "♂"
    elif monster.gender == GenderType.female:
        icon = "♀"

    symbol = ""
    if not is_trainer and is_status and not is_right:
        symbol = "◉"

    return f"{monster.name}{icon} Lv.{monster.level}{symbol}"

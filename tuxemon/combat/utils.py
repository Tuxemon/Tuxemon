# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Combat related code that can be independent of the combat state.
Code here might be shared by states, actions, conditions, etc.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from tuxemon.combat.combat_context import CombatType
from tuxemon.db import BattleMusicModel, GenderType, OutputBattle
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

    if character.party.is_fainted:
        logger.error(
            f"Cannot start battle, {character.name}'s monsters are all DEAD."
        )
        return False

    if character.party.no_tech:
        logger.error(
            f"Cannot start battle, {character.party.no_tech} has/have no techniques."
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


def get_battle_outcome_music(
    session: Session, default_music: BattleMusicModel, monster: Monster
) -> Optional[tuple[str, float]]:
    """
    Return the appropriate music track based on outcome and participants.
    Player-centric: only trigger music if a player is involved.
    """
    if not monster.owner:
        return None

    # Require at least one human player still active
    if not any(True for _ in session.client.combat_session.human_players):
        return None

    # Use override if present, else fall back to default
    active_music = monster.owner.get_active_battle_music(default_music)

    # If the defeated was a player → defeat music
    if (
        monster.owner.is_player
        and active_music.defeat_music
        and active_music.defeat_music.music
    ):
        return (
            active_music.defeat_music.music,
            active_music.defeat_music.volume,
        )

    # If the defeated was not a player → victory music
    if (
        not monster.owner.is_player
        and active_music.victory_music
        and active_music.victory_music.music
    ):
        return (
            active_music.victory_music.music,
            active_music.victory_music.volume,
        )

    return None


def play_outcome_music(
    session: Session,
    music: BattleMusicModel,
    monster: Monster,
) -> None:
    track = get_battle_outcome_music(session, music, monster)
    if track:
        music_name, volume = track
        session.client.current_music.play(music_name)
        session.client.current_music.set_volume(volume)


def track_battles(
    session: Session,
    output: OutputBattle,
    character: NPC,
    opponents: Sequence[NPC],
    turns: int,
    combat_type: CombatType,
    prize: int = 0,
) -> str:
    """
    Records the outcome of a battle for a given character and returns a formatted message.

    Parameters:
        session: The current game session.
        output: The result of the battle (won, lost, or draw).
        character: The character whose battle result is being tracked.
        opponents: The opposing characters in the battle.
        turns: Number of turns the battle lasted.
        combat_type: Type of combat (e.g., trainer, wild, horde).
        prize: Amount of money awarded for winning (if applicable).

    Returns:
        A formatted message describing the battle outcome.
    """
    location = session.client.get_map_name()
    opponents = [op for op in opponents if op.slug != character.slug]

    if output == OutputBattle.won:
        return _handle_win(
            session, character, opponents, turns, location, prize, combat_type
        )
    elif output == OutputBattle.lost:
        return _handle_loss(
            session, character, opponents, turns, location, combat_type
        )
    else:
        return _handle_draw(
            session, character, opponents, turns, location, combat_type
        )


def _handle_win(
    session: Session,
    winner: NPC,
    losers: Sequence[NPC],
    turns: int,
    location: str,
    prize: int,
    combat_type: CombatType,
) -> str:
    """Handles the case where the human player won the battle."""
    info = {"name": winner.name.upper()}

    if combat_type == CombatType.TRAINER:
        for loser in losers:
            winner.battle_handler.record_battle(
                opponent=loser.slug,
                outcome=OutputBattle.won,
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
    combat_type: CombatType,
) -> str:
    """Handles the case where the human player lost the battle."""
    info = {"name": loser.name.upper()}

    if combat_type == CombatType.TRAINER:
        if loser.is_player:
            set_var(session, "battle_last_result", OutputBattle.lost.value)
            set_var(session, "battle_last_loser", "player")
        else:
            set_var(session, "battle_last_loser", loser.slug)
            set_var(session, "battle_last_trainer", loser.slug)

        for winner in winners:
            loser.battle_handler.record_battle(
                opponent=winner.slug,
                outcome=OutputBattle.lost,
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
    combat_type: CombatType,
) -> str:
    """Handles the case where the battle was a draw."""
    defeat = list(players)
    defeat.remove(player)

    if combat_type == CombatType.TRAINER:
        set_var(session, "battle_last_result", OutputBattle.draw.value)
        for player_defeated in defeat:
            set_var(session, "battle_last_trainer", player_defeated.slug)
            player.battle_handler.record_battle(
                opponent=player_defeated.slug,
                outcome=OutputBattle.draw,
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
) -> dict[str, str]:
    """
    Returns the text elements for use on the HUD.

    Parameters:
        menu: Combat menu (eg. MainCombatMenuState).
        monster: The monster fighting.
        is_right: Boolean side (true: right side, false: left side).
            right side (player), left side (opponent)
        is_trainer: Boolean battle (trainer: true, wild: false).
    """
    if menu == "MainParkMenuState" and is_right:
        # Special case for MainParkMenuState
        ball = T.translate("tuxeball_park").upper()
        owner = monster.get_owner()
        item = owner.bag.find_item("tuxeball_park")
        quantity = item.quantity if item else 0
        return {"line1": f"{ball}: {quantity}", "line2": ""}

    icon = ""
    if monster.gender == GenderType.male:
        icon = "♂"
    elif monster.gender == GenderType.female:
        icon = "♀"

    symbol = ""
    if not is_trainer and is_status and not is_right:
        symbol = "◉"

    return {
        "line1": f"{monster.name}{icon} Lv.{monster.level}{symbol}",
        "line2": "",
    }

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from tuxemon.combat import alive_party
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.states.combat.combat_classes import DamageTracker
    from tuxemon.technique.technique import Technique
    from tuxemon.monster import Monster

from dataclasses import dataclass


class ExperienceMethod(Enum):
    DEFAULT = "default"
    PROPORTIONAL = "proportional"
    TEST = "test"
    XP_TRANSMITTER = "xp_transmitter"


@dataclass
class RewardDataEntry:
    winner: Monster
    money: int
    experience: int


@dataclass
class RewardData:
    winners: list[RewardDataEntry]
    messages: list[str]
    moves: list[Technique]
    update: bool
    prize: int


class RewardSystem:
    def __init__(
        self, damage_map: DamageTracker, is_trainer_battle: bool
    ) -> None:
        self.damage_map = damage_map
        self.is_trainer_battle = is_trainer_battle

    def award_rewards(self, monster: Monster) -> RewardData:
        """
        Calculate and distribute rewards (experience, money, and moves)
        to the winning monsters in a battle.

        This method determines which monsters contributed to fainting the
        defeated `monster` and calculates their individual rewards based
        on various conditions, such as whether the battle involves a
        trainer. Rewards include money, experience points, and potential
        move updates. Additionally, messages are generated to summarize
        the results, and the method updates the game's state if necessary.

        Parameters:
            monster: The monster that was defeated in battle.

        Returns:
            RewardData: An object containing:
                - `winners`: A list of winners with
                details about their money and experience rewards.
                - `messages`: A list of messages summarizing
                reward details, including experience gains.
                - `moves`: A list of any new moves learned
                by the winning monsters.
                - `update`: A flag indicating whether the game state
                (e.g., HUD or leveling up) needs to be updated.
                - `prize`: The total monetary prize awarded if the
                battle was against a trainer.
        """
        winners = get_winners(monster, self.damage_map)
        rewards_data = RewardData([], [], [], False, 0)

        if winners:
            for winner in winners:
                # Award money and experience
                awarded_money = calculate_money(monster, winner)
                awarded_exp = calculate_experience(
                    monster, winner, self.damage_map
                )
                rewards_data.winners.append(
                    RewardDataEntry(
                        winner=winner,
                        money=awarded_money,
                        experience=awarded_exp,
                    )
                )

                # Grant experience and update moves
                if winner.owner and winner.owner.isplayer:
                    levels = winner.give_experience(awarded_exp)
                    rewards_data.moves = winner.update_moves(levels)
                    rewards_data.messages.append(
                        T.format(
                            "combat_gain_exp",
                            {"name": winner.name.upper(), "xp": awarded_exp},
                        )
                    )

                    # Add money for trainer battles
                    if self.is_trainer_battle:
                        rewards_data.prize += awarded_money

                    # Update HUD or handle level-up externally
                    rewards_data.update = True

        return rewards_data


def calculate_money(loser: Monster, winner: Monster) -> int:
    """
    Calculate money to be awarded using a default method or custom methods.
    """
    method = (
        winner.owner.game_variables.get(
            "method_money", ExperienceMethod.DEFAULT.value
        )
        if winner.owner and winner.owner.isplayer
        else ExperienceMethod.DEFAULT.value
    )

    def default_method() -> int:
        return int(loser.level * loser.money_modifier)

    methods = {ExperienceMethod.DEFAULT.value: default_method}

    if method not in methods:
        raise ValueError(f"A formula for {method} doesn't exist.")

    return methods[method]()


def calculate_experience(
    loser: Monster, winner: Monster, damages: DamageTracker
) -> int:
    """
    Calculate experience to be awarded using defined methods.
    """
    hits, hits_mon = damages.count_hits(loser, winner)

    method = (
        winner.owner.game_variables.get(
            "method_experience", ExperienceMethod.DEFAULT.value
        )
        if winner.owner and winner.owner.isplayer
        else ExperienceMethod.DEFAULT.value
    )

    def default_method() -> int:
        return calculate_experience_base(
            loser.total_experience,
            loser.level,
            hits,
            loser.experience_modifier,
        )

    def proportional_method() -> int:
        return calculate_experience_base(
            loser.total_experience,
            loser.level,
            hits,
            loser.experience_modifier,
        ) * round(hits_mon / hits)

    methods = {
        ExperienceMethod.DEFAULT.value: default_method,
        ExperienceMethod.PROPORTIONAL.value: proportional_method,
    }

    if method not in methods:
        raise ValueError(f"A formula for {method} doesn't exist.")

    return methods[method]()


def calculate_experience_base(
    total_experience: float, level: int, hits: int, experience_modifier: float
) -> int:
    """
    Base formula for experience calculation.
    """
    return int((total_experience // (level * hits)) * experience_modifier)


def get_winners(loser: Monster, damages: DamageTracker) -> set[Monster]:
    """
    Extract the monsters who hit the loser.
    """
    winners = damages.get_attackers(loser)
    if winners:
        monster = next(iter(winners))
        trainer = monster.owner
        if (
            trainer
            and trainer.isplayer
            and trainer.game_variables.get("method_experience")
            == ExperienceMethod.XP_TRANSMITTER.value
        ):
            return set(alive_party(trainer))
    return winners

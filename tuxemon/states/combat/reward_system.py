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
    XP_EQUAL = "xp_equal"
    XP_TRANSMITTER = "xp_transmitter"
    XP_FEEDER = "xp_feeder"


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
        winners = self.damage_map.get_attackers(monster)
        rewards_data = RewardData([], [], [], False, 0)

        if winners:
            winner = next(iter(winners))

            if winner.owner is not None:
                all_monsters = set(alive_party(winner.owner))
            else:
                all_monsters = set()

            non_participants = all_monsters - winners

            if non_participants:
                _, awarded_exp = calculate_experience(
                    monster, next(iter(winners)), self.damage_map
                )
                for non_participant in non_participants:
                    levels = non_participant.give_experience(awarded_exp)
                    non_participant.update_moves(levels)

            for winner in winners:
                # Award money and experience
                awarded_exp, _ = calculate_experience(
                    monster, winner, self.damage_map
                )
                awarded_money = calculate_money(monster, winner)

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
    held_item = winner.held_item.get_item()

    def default_method() -> int:
        return int(loser.level * loser.money_modifier)

    methods = {ExperienceMethod.DEFAULT.value: default_method}

    return methods[ExperienceMethod.DEFAULT.value]()


def calculate_experience(
    loser: Monster, winner: Monster, damages: DamageTracker
) -> tuple[int, int]:
    """
    Calculate experience for participants and non-participants using defined methods.

    Returns:
        tuple[int, int]: (participant_exp, non_participant_exp)
    """
    total_hits, monster_hits = damages.count_hits(loser, winner)

    def default_method() -> tuple[int, int]:
        exp = calculate_experience_base(
            loser.total_experience,
            loser.level,
            total_hits,
            loser.experience_modifier,
        )
        return exp, 0

    def equal_method() -> tuple[int, int]:
        exp = calculate_experience_base(
            loser.total_experience,
            loser.level,
            total_hits,
            loser.experience_modifier,
        ) * round(monster_hits / total_hits)
        return exp, 0

    def feeder_method() -> tuple[int, int]:
        total_exp = calculate_experience_base(
            loser.total_experience,
            loser.level,
            total_hits,
            loser.experience_modifier,
        )

        participants = damages.get_attackers(loser)
        item_holder_exp = total_exp // 2
        participant_exp = (
            (total_exp - item_holder_exp) // len(participants)
            if participants
            else 0
        )

        held_item = winner.held_item.get_item()
        if held_item and held_item.slug == ExperienceMethod.XP_FEEDER.value:
            participant_exp = item_holder_exp

        return participant_exp, 0

    def transmitter_method() -> tuple[int, int]:
        total_exp = calculate_experience_base(
            loser.total_experience,
            loser.level,
            total_hits,
            loser.experience_modifier,
        )

        participants = damages.get_attackers(loser)

        if winner.owner is None:
            return 0, 0

        all_monsters = set(alive_party(winner.owner))
        non_participants = all_monsters - participants

        participant_exp = (
            total_exp // 2 // len(participants) if participants else 0
        )
        non_participant_exp = (
            total_exp // 2 // len(non_participants) if non_participants else 0
        )

        return participant_exp, non_participant_exp

    methods = {
        ExperienceMethod.DEFAULT.value: default_method,
        ExperienceMethod.XP_EQUAL.value: equal_method,
        ExperienceMethod.XP_TRANSMITTER.value: transmitter_method,
        ExperienceMethod.XP_FEEDER.value: feeder_method,
    }

    held_item = winner.held_item.get_item()
    if held_item:
        if held_item.slug == ExperienceMethod.XP_TRANSMITTER.value:
            return methods[ExperienceMethod.XP_TRANSMITTER.value]()
        elif held_item.slug == ExperienceMethod.XP_FEEDER.value:
            return methods[ExperienceMethod.XP_FEEDER.value]()
        elif held_item.slug == ExperienceMethod.XP_EQUAL.value:
            return methods[ExperienceMethod.XP_EQUAL.value]()

    return methods[ExperienceMethod.DEFAULT.value]()


def calculate_experience_base(
    total_experience: float, level: int, hits: int, experience_modifier: float
) -> int:
    """
    Base formula for experience calculation.
    """
    return int((total_experience // (level * hits)) * experience_modifier)

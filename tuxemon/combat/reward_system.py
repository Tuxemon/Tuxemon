# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tuxemon.combat.combat_context import CombatType
from tuxemon.combat.experience_strategies import (
    ExperienceAward,
    calculate_experience,
)
from tuxemon.combat.money_strategies import calculate_money, get_money_method
from tuxemon.database.rules import config_monster
from tuxemon.locale.locale import T
from tuxemon.monster.stats import BasicStats

if TYPE_CHECKING:
    from collections.abc import Iterable

    from tuxemon.combat.damage_tracker import DamageTracker
    from tuxemon.combat.money_strategies import MoneyMethod
    from tuxemon.entity.npc import NPC
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


@dataclass
class RewardDataEntry:
    winner: Monster
    experience: int
    levels_gained: int = 0
    bond_milestones_crossed: set[int] = field(default_factory=set)
    total_experience: int = 0


@dataclass
class RewardData:
    winners: list[RewardDataEntry]
    messages: list[str]
    moves: list[str]
    update: bool
    prize: int


class RewardSystem:
    def __init__(
        self,
        session: Session,
        combat_type: CombatType,
        calculator: RewardCalculator,
    ) -> None:
        self.session = session
        self.combat_type = combat_type
        self.calculator = calculator

    def apply_penalties(self, monster: Monster) -> None:
        """Applies defeat-related penalties to the specified monster."""
        monster.current_hp = 0
        owner = monster.get_owner()
        if owner.bag.find_item("friendship_scroll"):
            monster.bond_handler.apply_bond_modifier("fainted")

    def award_rewards(
        self, loser: Monster, winners: set[Monster] | None = None
    ) -> RewardData:
        """Calculate and distribute rewards to winners."""
        if winners is None:
            winners = self.calculator.get_attackers(loser)

        rewards_data = RewardData([], [], [], False, 0)

        if not winners:
            return rewards_data

        # Handle non-participants
        self.calculator.calculate_non_participant_rewards(loser, winners)

        # The purse is calculated exactly once per defeat. How the
        # participants affect it is up to the campaign's money method.
        if self.combat_type == CombatType.TRAINER:
            rewards_data.prize = self.calculator.calculate_prize(
                loser, winners, get_money_method(self.session)
            )

        # Handle winners
        for winner in winners:
            if winner.owner and winner.owner.is_player:
                if winner.is_fainted:
                    continue
                entry = self.calculator.calculate_winner_entry(loser, winner)
                rewards_data.winners.append(entry)

                self.calculator.update_moves_and_messages(
                    winner, entry, rewards_data
                )

                rewards_data.update = True

        return rewards_data


class RewardCalculator:
    def __init__(self, damage_map: DamageTracker):
        self.damage_map = damage_map

    def get_attackers(self, loser: Monster) -> set[Monster]:
        return self.damage_map.get_attackers(loser)

    def calculate_non_participant_rewards(
        self, loser: Monster, winners: set[Monster]
    ) -> None:
        """Distribute experience to non-participating monsters in the party.

        The reward method is resolved per winner, so the payout must not
        depend on which winner happens to come first out of the set. Every
        owning party is credited, with the best payout any of its winners
        earned.
        """
        awards: dict[NPC, ExperienceAward] = {}
        for winner in winners:
            owner = winner.owner
            if owner is None:
                continue
            award = calculate_experience(loser, winner, self.damage_map)
            previous = awards.get(owner)
            if previous is None or (award.non_participant, award.holder) > (
                previous.non_participant,
                previous.holder,
            ):
                awards[owner] = award

        for owner, award in awards.items():
            non_participants = set(owner.party.alive) - winners
            for non_participant in non_participants:
                non_participant.give_experience(
                    award.holder
                    if non_participant in award.holders
                    else award.non_participant
                )

    def calculate_prize(
        self,
        loser: Monster,
        participants: Iterable[Monster],
        method: MoneyMethod,
    ) -> int:
        """
        Calculate the purse paid out for defeating the loser.
        """
        return calculate_money(loser, participants, method)

    def calculate_winner_entry(
        self, loser: Monster, winner: Monster
    ) -> RewardDataEntry:
        """
        Calculate rewards for a single winning monster against a defeated loser.
        """
        award = calculate_experience(loser, winner, self.damage_map)
        awarded_exp = (
            award.holder if winner in award.holders else award.participant
        )
        calculate_tps(winner, loser)
        levels = winner.give_experience(awarded_exp)
        crossed = winner.bond_handler.apply_bond_modifier("win_battle")
        return RewardDataEntry(
            winner=winner,
            experience=awarded_exp,
            levels_gained=levels,
            bond_milestones_crossed=crossed,
            total_experience=winner.total_experience,
        )

    def update_moves_and_messages(
        self, winner: Monster, entry: RewardDataEntry, rewards_data: RewardData
    ) -> None:
        """Update moves and add messages for a winner."""
        new_moves = winner.moves.preview_moves_learned(
            winner, entry.levels_gained
        )
        if new_moves:
            rewards_data.moves.extend(new_moves)

        rewards_data.messages.append(
            T.format(
                "combat_gain_exp",
                {"name": winner.name, "xp": entry.experience},
            )
        )


class TrainerRewardCalculator(RewardCalculator):
    def calculate_winner_entry(
        self, loser: Monster, winner: Monster
    ) -> RewardDataEntry:
        entry = super().calculate_winner_entry(loser, winner)
        return entry


class WildRewardCalculator(RewardCalculator):
    def calculate_winner_entry(
        self, loser: Monster, winner: Monster
    ) -> RewardDataEntry:
        entry = super().calculate_winner_entry(loser, winner)
        return entry


class HordeRewardCalculator(RewardCalculator):
    def calculate_winner_entry(
        self, loser: Monster, winner: Monster
    ) -> RewardDataEntry:
        entry = super().calculate_winner_entry(loser, winner)
        return entry


def calculate_tps(
    winner: Monster,
    loser: Monster,
    tp_gain: int = config_monster.default_tp_gain,
) -> list[tuple[str, int]]:
    """
    Compares winner's stats to loser's.
    Awards training points to the winner for each stat where the opponent's value is higher.
    Returns a list of (stat_name, tp_gain) tuples.
    """
    awarded_stats = []

    logger.debug(
        f"Calculating TP for winner '{winner.name}' vs loser '{loser.name}'"
    )

    for stat_name in BasicStats.names():
        w_val = getattr(winner.base_stats, stat_name)
        l_val = getattr(loser.base_stats, stat_name)

        if l_val > w_val:
            logger.debug(
                f"Awarding {tp_gain} TP for '{stat_name}' (loser: {l_val} > winner: {w_val})"
            )
            winner.give_tps(stat_name, tp_gain)
            awarded_stats.append((stat_name, tp_gain))

    return awarded_stats

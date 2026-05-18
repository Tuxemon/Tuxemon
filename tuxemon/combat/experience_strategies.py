# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from tuxemon.database.rules import config_monster
from tuxemon.db import EvolutionStage, ExperienceMethod

if TYPE_CHECKING:
    from tuxemon.combat.damage_tracker import DamageTracker
    from tuxemon.monster.monster import Monster


class ExperienceStrategy(ABC):
    name: ClassVar[ExperienceMethod]

    @abstractmethod
    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        """Return (participant_exp, non_participant_exp)."""


class DefaultExperienceStrategy(ExperienceStrategy):
    """
    Split evenly among all attackers.
    Participant XP: total_exp // num_participants
    Non-Participant XP: 0
    Notes: Simple, fair split
    """

    name: ClassVar[ExperienceMethod] = ExperienceMethod.DEFAULT

    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        total_exp = round(
            calculate_experience_base(
                loser.total_experience, loser.level, loser.experience_modifier
            )
            * exp_multiplier
        )
        participants = damages.get_attackers(loser)
        num_participants = len(participants) or 1
        return total_exp // num_participants, 0


class EqualExperienceStrategy(ExperienceStrategy):
    """
    Proportional to number of hits.
    Participant XP: total_exp * (monster_hits / total_hits)
    Non-Participant XP: 0
    Notes: Rewards frequent attackers
    """

    name: ClassVar[ExperienceMethod] = ExperienceMethod.XP_EQUAL

    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        total_exp = round(
            calculate_experience_base(
                loser.total_experience, loser.level, loser.experience_modifier
            )
            * exp_multiplier
        )
        total_hits, monster_hits = damages.count_hits(loser, winner)
        proportional_exp = int(total_exp * (monster_hits / total_hits))
        return proportional_exp, 0


class FeederExperienceStrategy(ExperienceStrategy):
    """
    Half XP reserved for item holder.
    Participant XP: item holder gets total_exp // 2,
        others share (total_exp - item_holder_exp).
    Non-Participant XP: 0
    Notes: Applies only if held item has XP_FEEDER
    """

    name: ClassVar[ExperienceMethod] = ExperienceMethod.XP_FEEDER

    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        total_exp = round(
            calculate_experience_base(
                loser.total_experience, loser.level, loser.experience_modifier
            )
            * exp_multiplier
        )
        participants = damages.get_attackers(loser)
        item_holder_exp = total_exp // 2
        participant_exp = (
            (total_exp - item_holder_exp) // len(participants)
            if participants
            else 0
        )
        if (
            winner.held_item
            and winner.held_item.reward_method == ExperienceMethod.XP_FEEDER
        ):
            participant_exp = item_holder_exp
        return participant_exp, 0


class TransmitterExperienceStrategy(ExperienceStrategy):
    """
    Half XP to participants, half to Non-Participants.
    Participant XP: total_exp // 2 // num_participants
    Non-Participant XP: total_exp // 2 // num_non_participants
    Notes: Encourages whole-party growth
    """

    name: ClassVar[ExperienceMethod] = ExperienceMethod.XP_TRANSMITTER

    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        total_exp = round(
            calculate_experience_base(
                loser.total_experience, loser.level, loser.experience_modifier
            )
            * exp_multiplier
        )
        participants = damages.get_attackers(loser)
        if not winner.owner:
            return 0, 0
        all_monsters = set(winner.owner.party.alive)
        non_participants = all_monsters - participants
        participant_exp = total_exp // 2 // (len(participants) or 1)
        non_participant_exp = total_exp // 2 // (len(non_participants) or 1)
        return participant_exp, non_participant_exp


class OverkillExperienceStrategy(ExperienceStrategy):
    """
    Bonus for final blow.
    Participant XP: base_share + 25% bonus if finisher
    Non-Participant XP: 0
    Notes: Rewards decisive finishing hit
    """

    name: ClassVar[ExperienceMethod] = ExperienceMethod.XP_OVERKILL

    BONUS_RATIO: float = 0.25  # class variable, 25% bonus

    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        total_exp = round(
            calculate_experience_base(
                loser.total_experience, loser.level, loser.experience_modifier
            )
            * exp_multiplier
        )

        all_reports = [
            r
            for reports in damages._damage_map.values()
            for r in reports
            if r.defense == loser
        ]
        if not all_reports:
            return 0, 0

        last_hit = max(all_reports, key=lambda r: r.turn)
        finishing_bonus = int(total_exp * self.BONUS_RATIO)

        participants = damages.get_attackers(loser)
        num_participants = len(participants) or 1
        base_share = total_exp // num_participants

        if last_hit.attack == winner:
            return base_share + finishing_bonus, 0
        return base_share, 0


class DamageProportionalExperienceStrategy(ExperienceStrategy):
    """
    XP proportional to damage dealt.
    Participant XP: total_exp * (damage_by_winner / total_damage)
    Non-Participant XP: 0
    Notes: Rewards high damage contribution
    """

    name: ClassVar[ExperienceMethod] = ExperienceMethod.XP_DAMAGE_PROP

    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        total_exp = round(
            calculate_experience_base(
                loser.total_experience, loser.level, loser.experience_modifier
            )
            * exp_multiplier
        )

        participants = damages.get_attackers(loser)
        total_damage = (
            sum(damages.total_damage_by_attacker(att) for att in participants)
            or 1
        )
        damage_by_winner = damages.total_damage_by_attacker(winner)

        proportional_exp = int(total_exp * (damage_by_winner / total_damage))
        return proportional_exp, 0


class BondExperienceStrategy(ExperienceStrategy):
    """
    Scale XP rewards based on the monster's bond level (1-100).
    Participant XP: base_exp * (1 + bond_level / 100)
    Non-Participant XP: 0
    Notes: Rewards monsters with stronger bonds to their trainer.
    """

    name: ClassVar[ExperienceMethod] = ExperienceMethod.XP_BOND

    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        base_exp = calculate_experience_base(
            loser.total_experience, loser.level, loser.experience_modifier
        )

        bond_level = winner.bond_handler.bond
        bond_bonus = 1 + (bond_level / 100.0)
        total_exp = round(base_exp * exp_multiplier * bond_bonus)

        participants = damages.get_attackers(loser)
        num_participants = len(participants) or 1
        return total_exp // num_participants, 0


class StageScalingExperienceStrategy(ExperienceStrategy):
    """
    Scale XP rewards based on the monster's evolution stage.
    Participant XP: base_exp * stage_multiplier
    Non-Participant XP: 0
    Notes: Rewards defeating higher‑stage monsters more heavily.
    """

    name: ClassVar[ExperienceMethod] = ExperienceMethod.XP_STAGE

    STAGE_MULTIPLIERS = {
        EvolutionStage.BASIC: 1.0,  # unevolved
        EvolutionStage.STAGE1: 1.5,  # mid evolution
        EvolutionStage.STAGE2: 2.0,  # final evolution
        EvolutionStage.STANDALONE: 2.0,  # no evolution path, treat as final
    }

    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        base_exp = calculate_experience_base(
            loser.total_experience, loser.level, loser.experience_modifier
        )

        stage_multiplier = self.STAGE_MULTIPLIERS.get(loser.stage, 1.0)
        total_exp = round(base_exp * exp_multiplier * stage_multiplier)

        participants = damages.get_attackers(loser)
        num_participants = len(participants) or 1
        return total_exp // num_participants, 0


class SurvivorExperienceStrategy(ExperienceStrategy):
    """
    Reward monsters that survive the battle (not fainted).
    Participant XP: base_exp // num_survivors
    Non-Participant XP: 0
    Notes: Encourages keeping monsters alive, even if they didn't attack.
    """

    name: ClassVar[ExperienceMethod] = ExperienceMethod.XP_SURVIVOR

    def calculate(
        self,
        loser: Monster,
        winner: Monster,
        damages: DamageTracker,
        exp_multiplier: float,
    ) -> tuple[int, int]:
        base_exp = calculate_experience_base(
            loser.total_experience, loser.level, loser.experience_modifier
        )

        total_exp = round(base_exp * exp_multiplier)

        if not winner.owner:
            return 0, 0

        survivors = [m for m in winner.owner.party.alive if not m.is_fainted]
        num_survivors = len(survivors) or 1

        return total_exp // num_survivors, 0


STRATEGY_MAP = {
    ExperienceMethod.DEFAULT: DefaultExperienceStrategy(),
    ExperienceMethod.XP_EQUAL: EqualExperienceStrategy(),
    ExperienceMethod.XP_FEEDER: FeederExperienceStrategy(),
    ExperienceMethod.XP_TRANSMITTER: TransmitterExperienceStrategy(),
    ExperienceMethod.XP_OVERKILL: OverkillExperienceStrategy(),
    ExperienceMethod.XP_DAMAGE_PROP: DamageProportionalExperienceStrategy(),
    ExperienceMethod.XP_BOND: BondExperienceStrategy(),
    ExperienceMethod.XP_STAGE: StageScalingExperienceStrategy(),
    ExperienceMethod.XP_SURVIVOR: SurvivorExperienceStrategy(),
}


def calculate_experience(
    loser: Monster, winner: Monster, damages: DamageTracker
) -> tuple[int, int]:
    """Main entry point for XP calculation."""
    if winner.level >= config_monster.level_range[1]:
        return 0, 0
    exp_multiplier = winner.get_experience_multiplier()
    method = (
        winner.held_item.reward_method
        if winner.held_item
        else ExperienceMethod.DEFAULT
    )
    strategy = STRATEGY_MAP.get(method, STRATEGY_MAP[ExperienceMethod.DEFAULT])
    return strategy.calculate(loser, winner, damages, exp_multiplier)


def calculate_experience_base(
    total_experience: float, level: int, experience_modifier: float
) -> int:
    """Base XP formula used by all strategies."""
    return int((total_experience // level) * experience_modifier)

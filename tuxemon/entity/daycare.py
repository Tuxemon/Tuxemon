# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from tuxemon.db import Acquisition, EvolutionStage
from tuxemon.element import ElementTypesHandler
from tuxemon.event import get_event_bus
from tuxemon.monster.monster import Monster, decode_monsters, encode_monsters
from tuxemon.monster.stats import IndividualValues
from tuxemon.taste import Taste

if TYPE_CHECKING:
    from tuxemon.entity.npc import NPC


class Daycare:
    """
    A special 2-slot container for training and breeding monsters.

    Modes:
        - 1 monster           → training (EXP + cost)
        - 2 monsters compatible   → breeding + training (EXP + cost + newborn)
        - 2 monsters incompatible → training (EXP + cost)
    """

    MAX_PARENTS = 2

    def __init__(self, owner: NPC):
        self.owner = owner
        self.event_bus = get_event_bus()
        self.parents: list[Monster] = []
        self.progress_steps: float = 0.0
        self.required_steps: int = 10000

        # breeding milestone flags
        self.halfway_notified: bool = False
        self.ready_notified: bool = False

        # training tracking
        self.training_steps_start: float | None = None
        self.training_exp_rate: float = 0.25  # EXP per step
        self.training_cost_rate: float = 1.0  # money per EXP
        self.last_training_exp: int = 0
        self.last_training_cost: int = 0
        self.training_initialized: bool = False
        self._pending_exp: float = 0.0  # fractional EXP accumulator

    @property
    def is_empty(self) -> bool:
        return len(self.parents) == 0

    @property
    def is_full(self) -> bool:
        return len(self.parents) == self.MAX_PARENTS

    @property
    def is_training(self) -> bool:
        # 1 parent → training
        if len(self.parents) == 1:
            return True
        # 2 incompatible parents → training
        if len(self.parents) == 2 and not self._gender_pair_ok(*self.parents):
            return True
        return False

    @property
    def is_breeding(self) -> bool:
        return len(self.parents) == 2 and self._gender_pair_ok(*self.parents)

    @property
    def mode(self) -> str:
        if self.is_empty:
            return "empty"
        if self.is_training:
            return "training"
        if self.is_breeding:
            if self.ready():
                return "ready"
            halfway = self.required_steps // 2
            if self.progress_steps >= halfway:
                return "halfway"
            return "breeding"
        return "unknown"

    def add_parent(self, monster: Monster) -> bool:
        if len(self.parents) >= self.MAX_PARENTS:
            return False

        if not self._compatible(monster):
            return False

        if monster in self.owner.party.monsters:
            self.owner.party.remove_monster(monster)

        self.parents.append(monster)
        monster.set_owner(self.owner)

        # reset breeding progress when first monster is added
        if len(self.parents) == 1:
            self.progress_steps = 0
            self.halfway_notified = False
            self.ready_notified = False

        self.training_steps_start = self.owner.steps
        self.last_training_exp = 0
        self.last_training_cost = 0
        self.training_initialized = True
        self._pending_exp = 0.0

        return True

    def withdraw_parents(self) -> list[Monster]:
        withdrawn = self.parents[:]

        self.parents.clear()
        self.progress_steps = 0
        self.halfway_notified = False
        self.ready_notified = False
        self.training_steps_start = None
        self.training_initialized = False
        self._pending_exp = 0.0

        for m in withdrawn:
            self.owner.party.add_monster(m)

        return withdrawn

    def _compatible(self, monster: Monster) -> bool:
        """
        Basic eligibility to be stored in daycare.

        Gender compatibility is NOT enforced here so that
        incompatible pairs can still be trained together.
        """
        return True

    def _gender_pair_ok(self, a: Monster, b: Monster) -> bool:
        return (
            a.gender != b.gender
            and a.gender in ("male", "female")
            and b.gender in ("male", "female")
            and a.evolution_rank() > 1
            and b.evolution_rank() > 1
        )

    def on_steps(self, steps: float) -> None:
        # TRAINING MODE (1 parent OR 2 incompatible parents)
        if len(self.parents) == 1 or (
            len(self.parents) == 2 and not self._gender_pair_ok(*self.parents)
        ):
            # Accumulate fractional EXP so sub-1 rates (e.g. 0.25/step) work
            # correctly rather than being truncated to 0 on every step.
            self._pending_exp += steps * self.training_exp_rate
            gained_exp = int(self._pending_exp)

            if gained_exp <= 0:
                return

            self._pending_exp -= gained_exp
            gained_cost = int(gained_exp * self.training_cost_rate)


            # Check funds BEFORE applying EXP
            money = self.owner.money_controller.money_manager.get_money()
            if gained_cost > money:
                # Not enough money → training blocked; keep pending EXP for
                # the next step so we retry as soon as funds are available.
                self._pending_exp += gained_exp
                return

            # Deduct money
            if gained_cost > 0:
                self.owner.money_controller.money_manager.remove_money(
                    gained_cost
                )

            # Apply EXP
            for m in self.parents:
                m.give_experience(gained_exp)

            # Update totals
            self.last_training_exp += gained_exp
            self.last_training_cost += gained_cost

            # Update game variables
            self.owner.game_variables.set(
                "daycare_exp", self.last_training_exp
            )
            self.owner.game_variables.set(
                "daycare_cost", self.last_training_cost
            )

            return

        # BREEDING MODE (unchanged)
        if len(self.parents) != 2:
            return
        if not self._gender_pair_ok(self.parents[0], self.parents[1]):
            return

        self.progress_steps += steps
        halfway = self.required_steps // 2

        if not self.halfway_notified and self.progress_steps >= halfway:
            self.halfway_notified = True
            self.event_bus.publish("daycare_halfway", player=self.owner)

        if (
            not self.ready_notified
            and self.progress_steps >= self.required_steps
        ):
            self.ready_notified = True
            self.event_bus.publish("daycare_ready", player=self.owner)

    def ready(self) -> bool:
        return (
            len(self.parents) == 2
            and self._gender_pair_ok(self.parents[0], self.parents[1])
            and self.progress_steps >= self.required_steps
        )

    def produce_newborn(self) -> Monster:
        if not self.ready():
            raise ValueError("Breeding not complete")

        mother = next(m for m in self.parents if m.is_female)
        father = next(m for m in self.parents if m.is_male)

        seed = self._determine_seed(mother, father)
        other = father if seed is mother else mother
        name = self._determine_name(seed.name, other.name)

        # Determine base form
        seed_slug = seed.slug
        if seed.history:
            basic_forms = [
                element.slug
                for element in seed.history
                if element.stage == EvolutionStage.BASIC
            ]
            if basic_forms:
                seed_slug = random.choice(basic_forms)

        level = (father.level + mother.level) // 2

        # Create child
        child = Monster.spawn_base(seed_slug, level)
        child.name = name
        child.birthdate = self.owner.session.time.get_month_day()
        child.set_acquisition(Acquisition.BRED)

        # Inherit IVs: take the higher value from either parent per stat
        inherited_ivs = IndividualValues(
            **{
                stat: max(
                    getattr(mother.individual_values, stat),
                    getattr(father.individual_values, stat),
                )
                for stat in IndividualValues.names()
            }
        )
        child.individual_values = inherited_ivs

        # Inherit a random move from the non-seed parent
        other_moves = other.moves.get_moves()
        if other_moves:
            random_move = random.choice(other_moves)
            child.moves.add_move(random_move)

        # Inherit tastes
        warm, cold = self._determine_tastes(mother, father)
        child.taste_warm = warm
        child.taste_cold = cold

        child.set_stats()
        child.mother_iid = mother.instance_id
        child.father_iid = father.instance_id

        self.progress_steps = 0
        self.halfway_notified = False
        self.ready_notified = False

        return child

    def _determine_seed(self, mother: Monster, father: Monster) -> Monster:
        if mother.evolution_rank() > father.evolution_rank():
            return mother
        if father.evolution_rank() > mother.evolution_rank():
            return father

        if mother.base_stats.sum() > father.base_stats.sum():
            return mother
        if father.base_stats.sum() > mother.base_stats.sum():
            return father

        if mother.hp_ratio > father.hp_ratio:
            return mother
        if father.hp_ratio > mother.hp_ratio:
            return father

        m_aff = ElementTypesHandler.calculate_affinity_score(
            mother.types.current, father.types.current
        )
        f_aff = ElementTypesHandler.calculate_affinity_score(
            father.types.current, mother.types.current
        )
        if m_aff > f_aff:
            return mother
        if f_aff > m_aff:
            return father

        m_res = ElementTypesHandler.calculate_resistance_multiplier_for_types(
            mother.types.current, father.types.primary.slug
        )
        f_res = ElementTypesHandler.calculate_resistance_multiplier_for_types(
            father.types.current, mother.types.primary.slug
        )
        if m_res < f_res:
            return mother
        if f_res < m_res:
            return father

        return random.choice([mother, father])

    def _determine_tastes(
        self, mother: Monster, father: Monster
    ) -> tuple[str, str]:
        warm_slug = random.choice([mother.taste_warm, father.taste_warm])
        cold_slug = random.choice([mother.taste_cold, father.taste_cold])

        warm = Taste.get(warm_slug)
        cold = Taste.get(cold_slug)

        warm_slug = self._mutate_taste(warm, "warm")
        cold_slug = self._mutate_taste(cold, "cold")

        return warm_slug, cold_slug

    def _mutate_taste(
        self, taste: Taste, taste_type: str, base_mutation: float = 0.3
    ) -> str:
        rarity = min(max(taste.rarity_score or 1.0, 0.0), 1.0)
        mutation_chance = base_mutation * rarity
        if random.random() < mutation_chance:
            new_slug = Taste.get_random_taste_excluding(
                taste_type,
                exclude_slugs=[taste.slug, "tasteless"],
                use_rarity=True,
            )
            if new_slug:
                return new_slug
        return taste.slug

    def _determine_name(self, first: str, second: str) -> str:
        import re

        if not re.search(r"[aeiouy]", first) or not re.search(
            r"[aeiouy]", second
        ):
            mid1 = len(first) // 2
            mid2 = len(second) // 2
            result = first[:mid1] + second[mid2:]
        else:

            def find_vowel(word: str) -> int:
                mid = len(word) // 2
                best = 0
                dist = 999
                for i, c in enumerate(word):
                    if c in "aeiouy":
                        d = abs(i - mid)
                        if d < dist:
                            dist = d
                            best = i
                return best

            i1 = find_vowel(first)
            i2 = find_vowel(second)
            result = first[: i1 + 1] + second[i2:]

        result = "".join(
            [c for i, c in enumerate(result) if i == 0 or c != result[i - 1]]
        )
        if not result:
            result = first[:2] + second[-2:]
        return result.capitalize()

    def get_state(self) -> dict[str, Any]:
        return {
            "parents": encode_monsters(self.parents),
            "progress_steps": self.progress_steps,
            "required_steps": self.required_steps,
            "halfway_notified": self.halfway_notified,
            "ready_notified": self.ready_notified,
            "training_steps_start": self.training_steps_start,
            "last_training_exp": self.last_training_exp,
            "last_training_cost": self.last_training_cost,
            "training_initialized": self.training_initialized,
            "pending_exp": self._pending_exp,
        }

    def load_state(self, data: dict[str, Any]) -> None:
        self.parents = decode_monsters(data.get("parents", []))
        for m in self.parents:
            m.set_owner(self.owner)

        self.progress_steps = data.get("progress_steps", 0)
        self.required_steps = data.get("required_steps", 10000)
        self.halfway_notified = data.get("halfway_notified", False)
        self.ready_notified = data.get("ready_notified", False)
        self.training_steps_start = data.get("training_steps_start", None)
        self.last_training_exp = data.get("last_training_exp", 0)
        self.last_training_cost = data.get("last_training_cost", 0)
        self.training_initialized = data.get("training_initialized", False)
        self._pending_exp = data.get("pending_exp", 0.0)

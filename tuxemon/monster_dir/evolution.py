# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from tuxemon.db import (
    GenderType,
    LearningMethod,
    MonsterEvolutionItemModel,
    PartyConditionsModel,
    SeenStatus,
)
from tuxemon.locale import T
from tuxemon.tools import compare

if TYPE_CHECKING:
    from tuxemon.entity_dir.party import PartyHandler
    from tuxemon.monster import Monster

logger = logging.getLogger(__name__)


class Evolution:
    def __init__(self, monster: Monster):
        self.monster = monster

    def has_evolution_to(self, slug: str) -> bool:
        return any(
            evolution.monster_slug == slug
            for evolution in self.monster.evolutions
        )

    def has_history_to(self, slug: str) -> bool:
        return any(
            history.slug == slug
            or slug in history.evolves_from
            or slug in history.evolves_into
            for history in self.monster.history
        )

    def evolve_monster(self, new_monster: Monster) -> None:
        if not self.is_eligible_for_evolution():
            return

        owner = self.monster.get_owner()
        monster_index = owner.monsters.index(self.monster)
        self.update_new_monster_properties(new_monster)

        for move in new_monster.moves.moveset:
            if (
                move.learning_method
                and move.learning_method == LearningMethod.EVOLUTION
            ):
                new_monster.moves.learn_by_method(
                    new_monster.instance_id,
                    move.technique,
                    move.learning_method,
                )

        owner.party.remove_monster(self.monster)
        owner.party.add_monster(new_monster, monster_index)
        owner.tuxepedia.add_entry(new_monster.slug, SeenStatus.caught)

    def is_eligible_for_evolution(self) -> bool:
        return (
            self.monster.owner is not None
            and self.monster in self.monster.owner.monsters
        )

    def update_new_monster_properties(self, new_monster: Monster) -> None:
        new_monster.set_level(self.monster.level)
        new_monster.current_hp = min(self.monster.current_hp, new_monster.hp)
        new_monster.moves = self.monster.moves
        new_monster.status = self.monster.status
        new_monster.instance_id = self.monster.instance_id
        if self.monster.gender in new_monster.possible_genders:
            new_monster.gender = self.monster.gender
        else:
            new_monster.gender = random.choice(new_monster.possible_genders)
        new_monster.capture = self.monster.capture
        new_monster.capture_device = self.monster.capture_device
        new_monster.taste_cold = self.monster.taste_cold
        new_monster.taste_warm = self.monster.taste_warm
        new_monster.plague = self.monster.plague
        new_monster.name = (
            new_monster.name
            if self.monster.name == T.translate(self.monster.slug)
            else self.monster.name
        )
        # Copy flairs from old monster to new monster
        for flair_category, new_flair in new_monster.flairs.items():
            if flair_category in self.monster.flairs:
                new_monster.flairs[flair_category] = self.monster.flairs[
                    flair_category
                ]

    def can_evolve(
        self,
        evolution_item: MonsterEvolutionItemModel,
        context: dict[str, bool],
    ) -> bool:
        """
        Checks if a monster can evolve based on conditions.

        Parameters:
            evolution_item: The evolution item to apply.
            context: A dictionary containing the current context,
            including the map inside status.

        Returns:
            bool: True if the monster can evolve, False otherwise.

        Notes:
            The context dictionary is expected to contain keys (eg. 'map_inside').
        """
        if self.monster.owner is None:
            return False

        owner = self.monster.get_owner()

        # Check if the evolution is actually possible
        if evolution_item.monster_slug == self.monster.slug:
            return False

        conditions = []
        if evolution_item.at_level is not None:
            conditions.append(
                compare(
                    "greater_or_equal",
                    self.monster.level,
                    evolution_item.at_level,
                )
            )
        if evolution_item.gender is not None:
            conditions.append(evolution_item.gender == self.monster.gender)
        if evolution_item.inside is not None:
            conditions.append(
                evolution_item.inside == context.get("map_inside", False)
            )
        if evolution_item.element is not None:
            conditions.append(self.monster.has_type(evolution_item.element))
        if evolution_item.tech is not None:
            conditions.append(owner.party.has_tech(evolution_item.tech))
        if evolution_item.acquisition is not None:
            conditions.append(
                evolution_item.acquisition == self.monster.acquisition
            )
        if evolution_item.moves:
            moves_slugs = {mov.slug for mov in self.monster.moves.get_moves()}
            conditions.extend(
                monster in moves_slugs for monster in evolution_item.moves
            )

        if evolution_item.tastes:
            for taste_type, required_value in evolution_item.tastes.items():
                monster_taste = getattr(
                    self.monster, f"taste_{taste_type}", None
                )
                conditions.append(monster_taste == required_value)

        # Check if the monster's stats meet the evolution conditions
        if evolution_item.stats is not None:
            stat1 = self.monster.return_stat(evolution_item.stats.stat_type)
            operator = evolution_item.stats.comparison

            if evolution_item.stats.target_stat is not None:
                stat2 = self.monster.return_stat(
                    evolution_item.stats.target_stat
                )
            elif evolution_item.stats.target_value is not None:
                stat2 = evolution_item.stats.target_value
            else:
                raise ValueError(
                    "StatsComparison must have either target_stat or target_value."
                )

            conditions.append(compare(operator.value, stat1, stat2))

        # Check if the monster's game variables meet the evolution conditions
        if evolution_item.variables:
            for variable in evolution_item.variables:
                for key, value in variable.items():
                    conditions.append(
                        owner.game_variables.has(key)
                        and owner.game_variables.get(key) == value
                    )

        # Check if the monster has taken the required number of steps
        if evolution_item.steps is not None:
            result = evolution_item.steps - int(self.monster.steps)
            conditions.append(result == 0)
            self.monster.steps += 1
            self.monster.levelling_up = True
            self.monster.got_experience = True

        # Check if the party conditions
        if evolution_item.party_conditions is not None:
            conditions.append(
                check_party_conditions(
                    owner.party, evolution_item.party_conditions
                )
            )

        # Check if the monster's bond meets the evolution conditions
        if evolution_item.bond is not None:
            _operator = evolution_item.bond.comparison
            _value = evolution_item.bond.value
            _bond = self.monster.bond
            conditions.append(compare(_operator.value, _bond, _value))

        # Check if the monster is holding the required item for evolution
        if evolution_item.held_item is not None:
            held_item = self.monster.held_item.get_item()
            conditions.append(
                held_item is not None
                and held_item.slug == evolution_item.held_item
            )

        # If the evolution requires an item, do not evolve unless it's being used
        if evolution_item.item is not None and not context.get(
            "use_item", False
        ):
            return False

        # No conditions, only probability
        if not conditions and evolution_item.probability is not None:
            return random.random() <= evolution_item.probability

        # Conditions must all be met
        if all(conditions):
            # If probability is set, roll for it
            if evolution_item.probability is not None:
                return random.random() <= evolution_item.probability
            # Otherwise, guaranteed evolution
            return True

        # Conditions not met
        return False


def check_party_conditions(
    party_handler: PartyHandler, conditions_model: PartyConditionsModel
) -> bool:
    """
    Evaluates whether the player's party meets the specified evolution conditions.
    """
    conditions = []

    # Check party alignment
    if conditions_model.alignment is not None:
        alignment = party_handler.get_alignment()
        conditions.append(alignment == conditions_model.alignment)

    # Check required monster slugs
    if conditions_model.monster_slugs is not None:
        slug_counts: dict[str, int] = {}
        for mon in party_handler.monsters:
            slug_counts[mon.slug] = slug_counts.get(mon.slug, 0) + 1

        for slug, required_count in conditions_model.monster_slugs.items():
            conditions.append(slug_counts.get(slug, 0) >= required_count)

    # Check required monster types
    if conditions_model.monster_types is not None:
        type_counts: dict[str, int] = {}
        for mon in party_handler.monsters:
            types = mon.types.current
            for t in types:
                slug = t.slug
                type_counts[slug] = type_counts.get(slug, 0) + 1

        for type_, required_count in conditions_model.monster_types.items():
            conditions.append(type_counts.get(type_, 0) >= required_count)

    # Check required genders
    if conditions_model.genders is not None:
        gender_counts: dict[GenderType, int] = {}
        for mon in party_handler.monsters:
            gender = mon.gender
            gender_counts[gender] = gender_counts.get(gender, 0) + 1

        for gender, required_count in conditions_model.genders.items():
            conditions.append(gender_counts.get(gender, 0) >= required_count)

    return all(conditions)

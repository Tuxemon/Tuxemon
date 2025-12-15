# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from tuxemon.db import (
    LearningMethod,
    MonsterEvolutionItemModel,
    SeenStatus,
)
from tuxemon.monster_dir.evolution_conditions import (
    check_bond,
    check_location_items_moves,
    check_party_conditions,
    check_simple_conditions,
    check_stats,
    check_steps,
    check_tastes,
    check_variables,
)

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.monster_dir.evolution_registry import EvolutionRegistry

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

    def is_valid_evolution_target(self, target_slug: str) -> bool:
        """
        Checks if the target slug is a possible direct evolution from this
        monster or exists anywhere in its evolutionary history/future.
        """
        return self.has_evolution_to(target_slug) or self.has_history_to(
            target_slug
        )

    def confirm_pending_evolution(
        self, registry: EvolutionRegistry, evolution_slug: str
    ) -> None:
        """
        Handles all monster-side and registry cleanup when a pending evolution is confirmed.
        """
        registry.clear_missed(self.monster.instance_id, evolution_slug)
        registry.clear_pending(self.monster.instance_id)
        self.monster.experience_handler.reset_status_flags()

        logger.info(
            f"Confirmed evolution of {self.monster.name}. Registry cleanup complete."
        )

    def deny_pending_evolution(
        self, registry: EvolutionRegistry, evolution_slug: str
    ) -> None:
        """
        Handles all monster-side and registry cleanup when a pending evolution is denied.
        It logs the evolution as 'missed' and resets the monster's temporary status flags.
        """
        self.monster.experience_handler.reset_status_flags()
        registry.log_missed(
            self.monster.instance_id, evolution_slug, self.monster.level
        )
        registry.clear_pending(self.monster.instance_id)
        logger.info(
            f"Denied evolution of {self.monster.name}. Missed evolution logged at level {self.monster.level}."
        )

    def evolve_monster(self, new_monster: Monster) -> None:
        if not self.is_eligible_for_evolution():
            return

        owner = self.monster.get_owner()
        new_monster.transfer_properties_from(self.monster)

        for move in new_monster.moves.moveset:
            if move.learning_method == LearningMethod.EVOLUTION:
                new_monster.moves.learn_by_method(
                    new_monster,
                    move.technique,
                    move.learning_method,
                )

        if owner.party.replace_monster(self.monster, new_monster):
            owner.tuxepedia.add_entry(new_monster.slug, SeenStatus.caught)
            logger.info(f"{self.monster} evolved into {new_monster}")
        else:
            logger.warning(f"Failed to evolve {self.monster}")

    def is_eligible_for_evolution(self) -> bool:
        return (
            self.monster.owner is not None
            and self.monster in self.monster.owner.monsters
        )

    def can_evolve(
        self,
        evolution_item: MonsterEvolutionItemModel,
        context: dict[str, bool],
    ) -> bool:
        """
        Checks if a monster can evolve based on conditions.

        Parameters:
            evolution_item: The evolution item to apply.
            context: A dictionary containing the current context
                (e.g., location, item usage).

        Returns:
            bool: True if the monster can evolve, False otherwise.
        """
        if self.monster.owner is None:
            return False

        if evolution_item.monster_slug == self.monster.slug:
            return False

        owner = self.monster.get_owner()
        conditions: list[bool] = []

        check_simple_conditions(self.monster, evolution_item, conditions)
        check_location_items_moves(
            self.monster, evolution_item, context, conditions
        )
        check_tastes(self.monster, evolution_item, conditions)
        check_stats(self.monster, evolution_item, conditions)
        check_variables(self.monster, evolution_item, conditions)
        check_steps(self.monster, evolution_item, conditions)
        check_bond(self.monster, evolution_item, conditions)

        if evolution_item.party_conditions is not None:
            conditions.append(
                check_party_conditions(
                    owner.party, evolution_item.party_conditions
                )
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

    def get_possible_item_evolutions(
        self, item: Item, context: dict[str, bool]
    ) -> list[tuple[MonsterEvolutionItemModel, float]]:
        """
        Filters and returns evolution models possible with the given item,
        along with their weights.
        """
        possible_evolutions = []

        for evolution_model in self.monster.evolutions:
            item_weights = evolution_model.item

            if isinstance(item_weights, dict) and item.slug in item_weights:
                weight = item_weights[item.slug]

                if weight > 0.0 and self.can_evolve(evolution_model, context):
                    possible_evolutions.append((evolution_model, weight))

        return possible_evolutions

    def choose_evolution_model(
        self,
        possible_evolutions: list[tuple[MonsterEvolutionItemModel, float]],
    ) -> MonsterEvolutionItemModel:
        if len(possible_evolutions) == 1:
            return possible_evolutions[0][0]
        evolution_choices, weights = zip(*possible_evolutions)
        choices: list[MonsterEvolutionItemModel] = list(evolution_choices)
        return random.choices(choices, weights=list(weights), k=1)[0]

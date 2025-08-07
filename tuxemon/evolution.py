# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from uuid import UUID

from tuxemon.db import MonsterEvolutionItemModel, SeenStatus, StatType
from tuxemon.locale import T
from tuxemon.tools import compare

if TYPE_CHECKING:
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
            history.mon_slug == slug for history in self.monster.history
        )

    def evolve_monster(self, new_monster: Monster) -> None:
        if not self.is_eligible_for_evolution():
            return

        owner = self.monster.get_owner()
        monster_index = owner.monsters.index(self.monster)
        self.update_new_monster_properties(new_monster)
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
        new_monster.gender = self.monster.gender
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
        if evolution_item.party:
            monster_slugs = {mon.slug for mon in owner.monsters}
            conditions.extend(
                monster in monster_slugs for monster in evolution_item.party
            )
        if evolution_item.taste_cold is not None:
            conditions.append(
                self.monster.taste_cold == evolution_item.taste_cold
            )
        if evolution_item.taste_warm is not None:
            conditions.append(
                self.monster.taste_warm == evolution_item.taste_warm
            )

        # Check if the monster's stats meet the evolution conditions
        if evolution_item.stats is not None:
            params = evolution_item.stats.split(":")
            operator = params[1]
            stat1 = self.monster.return_stat(StatType(params[0]))
            stat2 = self.monster.return_stat(StatType(params[2]))
            conditions.append(compare(operator, stat1, stat2))

        # Check if the monster's game variables meet the evolution conditions
        if evolution_item.variables:
            for variable in evolution_item.variables:
                for key, value in variable.items():
                    conditions.append(
                        key in owner.game_variables
                        and owner.game_variables[key] == value
                    )

        # Check if the monster has taken the required number of steps
        if evolution_item.steps is not None:
            result = evolution_item.steps - int(self.monster.steps)
            conditions.append(result == 0)
            self.monster.steps += 1
            self.monster.levelling_up = True
            self.monster.got_experience = True

        # Check if the monster's bond meets the evolution conditions
        if evolution_item.bond is not None:
            parts = evolution_item.bond.split(":")
            operator, value = parts[:2]
            _bond = self.monster.bond
            conditions.append(compare(operator, _bond, int(value)))

        # If the evolution requires an item, do not evolve
        if evolution_item.item is not None:
            return context.get("use_item", False)

        return all(conditions)


class EvolutionRegistry:
    def __init__(self) -> None:
        self._missed_evolutions: dict[UUID, list[tuple[str, int, int]]] = {}
        self._pending_evolutions: dict[UUID, list[str]] = {}

    def log_missed(
        self, monster_id: UUID, evolution_slug: str, level: int
    ) -> None:
        evolutions = self._missed_evolutions.setdefault(monster_id, [])
        for i, (slug, lvl, count) in enumerate(evolutions):
            if slug == evolution_slug and lvl == level:
                evolutions[i] = (slug, lvl, count + 1)
                logger.debug(
                    f"Incremented refusal count for {slug} at level {lvl} (count={count + 1})"
                )
                return
        evolutions.append((evolution_slug, level, 1))
        logger.debug(
            f"Logged missed evolution: {evolution_slug} at level {level} (count=1)"
        )

    def get_retryable_missed(
        self, monster_id: UUID, max_attempts: int = 3
    ) -> list[str]:
        retryable = [
            slug
            for slug, lvl, count in self._missed_evolutions.get(monster_id, [])
            if count < max_attempts
        ]
        logger.debug(
            f"Retryable missed evolutions for {monster_id}: {retryable}"
        )
        return retryable

    def clear_missed(
        self, monster_id: UUID, evolution_slug: str | None = None
    ) -> None:
        if monster_id not in self._missed_evolutions:
            logger.debug(f"No missed evolutions to clear for {monster_id}")
            return
        if evolution_slug is None:
            del self._missed_evolutions[monster_id]
            logger.debug(f"Cleared all missed evolutions for {monster_id}")
        else:
            before = len(self._missed_evolutions[monster_id])
            self._missed_evolutions[monster_id] = [
                evo
                for evo in self._missed_evolutions[monster_id]
                if evo[0] != evolution_slug
            ]
            after = len(self._missed_evolutions[monster_id])
            logger.debug(
                f"Cleared missed evolution '{evolution_slug}' for {monster_id} ({before - after} removed)"
            )

    def add_pending(self, monster_id: UUID, evolution_slug: str) -> None:
        self._pending_evolutions.setdefault(monster_id, []).append(
            evolution_slug
        )
        logger.debug(
            f"Added pending evolution '{evolution_slug}' for {monster_id}"
        )

    def get_pending(self, monster_id: UUID) -> list[str]:
        pending = self._pending_evolutions.get(monster_id, [])
        logger.debug(f"Pending evolutions for {monster_id}: {pending}")
        return pending

    def clear_pending(self, monster_id: UUID) -> None:
        if monster_id in self._pending_evolutions:
            logger.debug(f"Cleared pending evolutions for {monster_id}")
        else:
            logger.debug(f"No pending evolutions to clear for {monster_id}")
        self._pending_evolutions.pop(monster_id, None)

    def encode_registry(self) -> Mapping[str, Any]:
        return {
            "missed": {
                str(monster_id): [
                    {"slug": slug, "level": level, "count": count}
                    for slug, level, count in evolutions
                ]
                for monster_id, evolutions in self._missed_evolutions.items()
            },
            "pending": {
                str(monster_id): slugs
                for monster_id, slugs in self._pending_evolutions.items()
            },
        }

    def decode_registry(self, data: Mapping[str, Any]) -> None:
        self._missed_evolutions.clear()
        self._pending_evolutions.clear()

        for monster_id_str, evolutions in data.get("missed", {}).items():
            monster_id = UUID(monster_id_str)
            self._missed_evolutions[monster_id] = [
                (evo["slug"], evo["level"], evo["count"]) for evo in evolutions
            ]

        for monster_id_str, slugs in data.get("pending", {}).items():
            monster_id = UUID(monster_id_str)
            self._pending_evolutions[monster_id] = slugs

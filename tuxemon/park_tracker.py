# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster

logger = logging.getLogger(__name__)


@dataclass
class ParkTracker:
    """
    Tracks unique monsters, sightings, failed captures, and successful captures in the park.
    """

    seen_monsters: set[str] = field(default_factory=set)
    failed_attempts: int = 0
    seen_counts: dict[str, int] = field(default_factory=dict)
    successful_captures: int = 0

    @property
    def unique_count(self) -> int:
        count = len(self.seen_monsters)
        logger.debug(f"Unique monster count calculated: {count}")
        return count

    def track_monster(self, monster: Monster) -> None:
        slug = monster.slug
        newly_seen = slug not in self.seen_monsters
        self.seen_monsters.add(slug)
        self.seen_counts[slug] = self.seen_counts.get(slug, 0) + 1
        logger.debug(
            f"Tracked monster: {slug}. Newly seen: {newly_seen}. Total sightings: {self.seen_counts[slug]}"
        )

    def record_failed_attempt(self) -> None:
        self.failed_attempts += 1
        logger.debug(
            f"Recorded failed capture attempt. Total failed: {self.failed_attempts}"
        )

    def record_successful_capture(self) -> None:
        self.successful_captures += 1
        logger.debug(
            f"Recorded successful capture. Total successful: {self.successful_captures}"
        )

    def clear_all(self) -> None:
        self.seen_monsters.clear()
        self.seen_counts.clear()
        self.failed_attempts = 0
        self.successful_captures = 0
        logger.debug("Cleared all park tracking data.")

    def get_most_frequent_sightings(self, n: int = 5) -> list[tuple[str, int]]:
        top_sightings = Counter(self.seen_counts).most_common(n)
        logger.debug(f"Top {n} sightings: {top_sightings}")
        return top_sightings

    def get_capture_rate(self) -> float:
        total_attempts = self.successful_captures + self.failed_attempts
        rate = (
            self.successful_captures / total_attempts
            if total_attempts > 0
            else 0.0
        )
        logger.debug(
            f"Calculated capture rate: {rate:.2f} from {self.successful_captures} successes out of {total_attempts} attempts"
        )
        return rate


class ParkSession:
    """
    Manages encounters and tracking during a park run.
    Combines behavior tracking and cumulative stats.
    """

    def __init__(self) -> None:
        self.tracker = ParkTracker()
        self.encounters: dict[str, ParkEncounter] = {}
        self.encounter_history: dict[str, list[ParkEncounter]] = {}
        self._is_active: bool = False

    @property
    def is_active(self) -> bool:
        """
        Returns True if the park session is currently active, False otherwise.
        """
        return self._is_active

    def activate_session(self) -> None:
        """Activates the park session."""
        if not self._is_active:
            self._is_active = True
            logger.info("Park session activated.")
        else:
            logger.debug("Park session is already active.")

    def deactivate_session(self) -> None:
        """Deactivates the park session."""
        if self._is_active:
            self._is_active = False
            logger.info("Park session deactivated.")
        else:
            logger.debug("Park session is already inactive.")

    def reset_session(self) -> None:
        self.tracker.clear_all()
        self.encounters.clear()
        self.encounter_history.clear()
        self._is_active = False
        logger.info("Park session reset and deactivated.")

    def record_capture(self) -> None:
        self.tracker.record_successful_capture()

    def record_failure(self) -> None:
        self.tracker.record_failed_attempt()

    def start_encounter(self, monster: Monster) -> ParkEncounter:
        slug = monster.slug
        encounter = ParkEncounter(monster)
        self.encounters[slug] = encounter
        self.tracker.track_monster(monster)
        logger.debug(
            f"Started encounter with {slug}. Turns remaining: {encounter.turns_remaining}"
        )
        return encounter

    def resolve_turn(self, slug: str) -> bool:
        """
        Runs one encounter turn. Returns True if monster fled.
        """
        encounter = self.encounters.get(slug)
        if not encounter:
            logger.warning(f"No encounter found for slug: {slug}")
            return False

        encounter.decrement_turns()
        if encounter.check_for_flee():
            logger.info(
                f"{slug} fled after {encounter.turns_remaining} turns."
            )
            return True
        return False

    def use_food(self, slug: str, item: Item) -> None:
        if slug in self.encounters:
            self.encounters[slug].apply_food_effect(item)
            logger.debug(
                f"Applied food effect to {slug} with item {item.slug}"
            )

    def use_doll(self, slug: str, item: Item) -> None:
        if slug in self.encounters:
            self.encounters[slug].apply_doll_effect(item)
            logger.debug(
                f"Applied doll effect to {slug} with item {item.slug}"
            )

    def archive_encounter(self, slug: str) -> None:
        """
        Moves an active encounter to the history log after it ends.
        Useful for analytics or resetting encounters.
        """
        encounter = self.encounters.pop(slug, None)
        if encounter:
            self.encounter_history.setdefault(slug, []).append(encounter)
            logger.debug(f"Archived encounter with {slug}")


class ParkEncounter:
    """
    Represents a specific monster encounter within the Park.

    This class wraps a Monster object and adds specific attributes and behaviors
    that are unique to wild encounters in the park, such as flee rates,
    attraction/aggression levels, and a "turns remaining" counter.
    """

    def __init__(self, monster: Monster, initial_turns: int = 30) -> None:
        self._monster: Monster = monster
        self.turns_remaining: int = initial_turns
        self.flee_rate: float = self._calculate_initial_flee_rate()
        self.attraction: float = self._calculate_initial_attraction()
        self.aggression: float = self._calculate_initial_aggression()

        # Store initial state for resets or comparison
        self._initial_flee_rate = self.flee_rate
        self._initial_attraction = self.attraction
        self._initial_aggression = self.aggression

    @property
    def monster(self) -> Monster:
        """Returns the underlying Monster object."""
        return self._monster

    def _calculate_initial_flee_rate(self) -> float:
        """
        Calculate an initial flee rate based on the monster's base stats.
        For example, faster monsters might be more likely to flee.
        """
        base_flee = 0.05
        if self.monster.speed > 80:
            base_flee += 0.05
        return min(base_flee, 1.0)

    def _calculate_initial_attraction(self) -> float:
        """Calculate the monster's attraction to food."""
        return 0.1  # Placeholder value, can be tuned

    def _calculate_initial_aggression(self) -> float:
        """Calculate the monster's aggression response to dolls."""
        return 0.1  # Placeholder value, can be tuned

    def decrement_turns(self, turns: int = 1) -> None:
        """Reduce the turns remaining for the encounter."""
        self.turns_remaining = max(0, self.turns_remaining - turns)

    def check_for_flee(self) -> bool:
        """
        Determine whether the monster flees this turn.
        Automatic flee if no turns remain.
        """
        if self.turns_remaining <= 0:
            return True
        return random.random() < self.flee_rate

    def apply_item_modifiers(self, item: Item) -> None:
        for modifier in item.modifiers.list_modifiers():
            if modifier.attribute == "flee_rate_reduction":
                self.flee_rate = max(0.0, self.flee_rate - modifier.multiplier)
            elif modifier.attribute == "attraction_increase":
                self.attraction += modifier.multiplier
            elif modifier.attribute == "aggression_reduction":
                self.aggression = max(
                    0.0, self.aggression - modifier.multiplier
                )

    def apply_food_effect(self, item: Item) -> None:
        """Modify flee rate and attraction when food is used based on item modifiers."""
        attraction_modifier = 0.0
        flee_modifier = 0.0

        for modifier in item.modifiers.list_modifiers():
            if modifier.attribute == "flee_rate_reduction":
                flee_modifier = modifier.multiplier
            if modifier.attribute == "flee_rate_reduction":
                attraction_modifier = modifier.multiplier

        self.flee_rate = max(0.0, self.flee_rate - flee_modifier)
        self.attraction += attraction_modifier

    def apply_doll_effect(self, item: Item) -> None:
        """Modify aggression and flee rate when a doll is used based on item modifiers."""
        aggression_modifier = 0.0
        flee_modifier = 0.0

        for modifier in item.modifiers.list_modifiers():
            if modifier.attribute == "aggression_reduction":
                aggression_modifier = modifier.multiplier
            if modifier.attribute == "flee_rate_reduction":
                flee_modifier = modifier.multiplier

        self.aggression = max(0.0, self.aggression - aggression_modifier)
        self.flee_rate = max(0.0, self.flee_rate - flee_modifier)

    def reset_behavior_modifiers(self) -> None:
        """
        Restore all behavior values to their original state.
        Useful if an encounter is restarted or replayed.
        """
        self.flee_rate = self._initial_flee_rate
        self.attraction = self._initial_attraction
        self.aggression = self._initial_aggression

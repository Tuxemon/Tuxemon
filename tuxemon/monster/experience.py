# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from tuxemon.database.rules import config_monster

logger = logging.getLogger(__name__)


class MonsterExperience:
    """
    Handles a monster's progression mechanics related to experience and level.

    This includes managing total experience, calculating requirements, and
    executing the level-up process.
    """

    def __init__(
        self,
        level: int = 1,
        total_experience: int = 0,
        exp_group_slug: str = "default",
    ) -> None:
        """
        Initializes the experience handler.

        Parameters:
            level: The monster's current level.
            total_experience: The monster's total accumulated experience.
            experience_modifier: A multiplier applied to experience gain.
            exp_group_slug: Identifier for the monster's experience growth group
                Determines how much experience is required to level up.
        """
        self.config_monster = config_monster
        self._level: int = level
        self._exp_group_slug: str = exp_group_slug
        self._total_experience: int = total_experience
        self._experience_modifier: float = 1.0
        self.got_experience: bool = False
        self.levelling_up: bool = False

    @classmethod
    def from_state(cls, save_data: Mapping[str, Any]) -> MonsterExperience:
        level = save_data.get("level", 1)
        total_experience = save_data.get("total_experience", 0)
        exp_group_slug = save_data.get("exp_group_slug", "default")

        return cls(
            level=level,
            total_experience=total_experience,
            exp_group_slug=exp_group_slug,
        )

    def get_state(self) -> Mapping[str, Any]:
        return {
            "level": self.level,
            "total_experience": self.total_experience,
            "exp_group_slug": self.exp_group_slug,
        }

    @property
    def level(self) -> int:
        return self._level

    @property
    def total_experience(self) -> int:
        return self._total_experience

    @property
    def exp_group_slug(self) -> str:
        return self._exp_group_slug

    @property
    def experience_modifier(self) -> float:
        return self._experience_modifier

    @property
    def is_maxed_out(self) -> bool:
        return self._level >= config_monster.level_range[1]

    @property
    def experience_current_level(self) -> int:
        """The total experience accumulated since reaching the current level."""
        if self.level <= 1:
            return self.total_experience
        exp_to_current = self.experience_required()
        return self._total_experience - exp_to_current

    @property
    def experience_for_next_level(self) -> int:
        """The total experience range between the current level and the next."""
        if self.is_maxed_out:
            return 0
        return self.experience_required(1) - self.experience_required()

    @property
    def experience_progress_percent(self) -> float:
        """The monster's progress toward the next level (0.0 to 1.0)."""
        if self.is_maxed_out:
            return 1.0  # Maxed out, so progress is full.

        earned = self.experience_current_level
        required = self.experience_for_next_level

        if required <= 0:
            return 0.0  # Avoid dividing by zero or negative XP requirements.

        progress = earned / required

        # Clamp between 0.0 and 1.0 to keep visuals sane.
        return max(0.0, min(1.0, progress))

    def set_level(self, level: int) -> None:
        """
        Sets the monster's level to an arbitrary value.

        Also updates the total experience to match the requirement for that level.

        Parameters:
            level: The level to set the monster to.
        """
        self._level = self._clamp_level(level)
        self._total_experience = self.experience_required()

    def experience_required(self, level_delta: int = 0) -> int:
        """
        Gets the experience requirement for the given level.

        Parameters:
            level_delta: Difference in levels with the current level.

        Returns:
            Required experience.
        """
        group = self.config_monster.experience_groups.get(
            self._exp_group_slug,
            self.config_monster.experience_groups["default"],
        )
        modifier = group["experience_coefficient"]
        multiplier = group.get("multiplier", 1.0)
        target_level = self._clamp_level(self._level + level_delta)

        required = multiplier * (target_level**modifier)
        return int(required)

    def give_experience(self, amount: int = 1) -> int:
        """
        Increase experience and levels up the monster if necessary.

        Note: This method *no longer* accepts the 'monster' parameter.
              It now relies on the calling method to update stats.

        Returns:
            int: The amount of levels earned.
        """
        if amount <= 0:
            return 0

        self.got_experience = True
        levels = 0
        effective_amount = int(amount * self._experience_modifier)
        self._total_experience += effective_amount

        while self._level < config_monster.level_range[
            1
        ] and self._total_experience >= self.experience_required(1):
            self._level_up()
            levels += 1

        # No cap on experience
        return levels

    def _clamp_level(self, level: int) -> int:
        return max(1, min(level, config_monster.level_range[1]))

    def _level_up(self) -> None:
        """Increases a Monster's level by one."""
        self.levelling_up = True
        self._level = self._clamp_level(self._level + 1)

    def set_exp_group(self, slug: str) -> None:
        if slug not in self.config_monster.experience_groups:
            raise ValueError(f"Invalid experience group: {slug}")
        self._exp_group_slug = slug

    def set_total_experience(self, total_experience: int) -> None:
        self._total_experience = max(0, total_experience)

    def set_experience_modifier(self, modifier: float) -> None:
        """Sets the experience gain multiplier."""
        if modifier < 0:
            logger.warning(
                f"Attempted to set negative experience modifier: {modifier}. Using 0.0 instead."
            )
            self._experience_modifier = 0.0
        else:
            self._experience_modifier = modifier

    def excess_experience(self) -> int:
        """
        Returns experience beyond the final level requirement.
        Only meaningful if monster is at MAX_LEVEL.
        """
        if not self.is_maxed_out:
            return 0
        return self._total_experience - self.experience_required()

    def reset_status_flags(self) -> None:
        """Resets the temporary flags used to signal experience/level activity."""
        self.got_experience = False
        self.levelling_up = False

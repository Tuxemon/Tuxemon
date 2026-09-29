# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import random
from collections.abc import Mapping
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from tuxemon.constants import paths
from tuxemon.database.yaml_utils import load_yaml
from tuxemon.db import PlagueType
from tuxemon.locale.locale import T

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster

logger = logging.getLogger(__name__)


class InfectionResult(Enum):
    INFECTED = auto()
    CARRIER = auto()
    MINOR_EFFECT = auto()
    RESISTED = auto()
    IMMUNE = auto()
    ALREADY_HAS = auto()
    UNKNOWN_PLAGUE = auto()


class InoculationResult(Enum):
    INOCULATED = auto()
    ALREADY_INOCULATED = auto()
    UNKNOWN_PLAGUE = auto()
    NOT_ELIGIBLE = auto()


class InoculationData(BaseModel):
    required_held_item: str | None = None
    eligible_types: list[str] | None = None
    eligible_shapes: list[str] | None = None


class CureData(BaseModel):
    chance: float = 0.0
    message_cured: str | None = None
    message_carrier_cured: str | None = None


class PlagueData(BaseModel):
    spreadness: float
    carrier_spreadness: float | None = None
    natural_recovery_chance: float = 0.0
    symptom_onset_chance: float = 0.0
    type_weights: dict[str, float] = Field(default_factory=dict)
    shape_weights: dict[str, float] = Field(default_factory=dict)
    status_weights: dict[str, float] = Field(default_factory=dict)
    resistance_modifiers: dict[str, dict[str, float]] = Field(
        default_factory=dict
    )
    weight_range: tuple[float, float] | None = None
    height_range: tuple[float, float] | None = None
    inoculation: InoculationData | None = None
    cure: CureData | None = None
    message_spread_success: str | None = None
    message_target_resists: str | None = None
    message_minor_effect: str | None = None
    message_target_infected: str | None = None
    message_user_suppressed: str | None = None
    message_symptom_onset: str | None = None


config = load_yaml(paths.mods_folder / "plagues.yaml")
plagues_raw = config["plagues"]
config_plagues = {
    name: PlagueData(**data) for name, data in plagues_raw.items()
}


class MonsterPlagueHandler:
    """
    Manages the various plagues affecting a monster.
    """

    def __init__(
        self,
        plagues: dict[str, PlagueType] | None = None,
        plague_data: dict[str, PlagueData] | None = None,
    ) -> None:
        self._plagues = plagues or {}
        self.plague_data = plague_data or config_plagues

    @property
    def current_plagues(self) -> dict[str, PlagueType]:
        return self._plagues

    def infect(self, plague_slug: str) -> None:
        if plague_slug not in self.plague_data:
            logger.error(f"Unknown plague slug: {plague_slug}")
            return
        self._plagues[plague_slug] = PlagueType.INFECTED

    def inoculate(self, plague_slug: str) -> None:
        if plague_slug not in self.plague_data:
            logger.error(f"Unknown plague slug: {plague_slug}")
            return
        self._plagues[plague_slug] = PlagueType.INOCULATED

    def can_be_infected_by(self, monster: Monster, plague_slug: str) -> bool:
        plague_config = self.get_plague_config(plague_slug)
        if plague_config is None:
            logger.error(f"Unknown plague slug: {plague_slug}")
            return False

        if not self.is_target_eligible(monster, plague_slug, plague_config):
            logger.debug(
                f"Monster '{monster.name}' is not eligible for plague '{plague_slug}'"
            )
            return False

        is_immune = self.is_inoculated_against(
            plague_slug
        ) or self.is_recovered_from(plague_slug)
        can_be_infected = not is_immune

        type_slugs = monster.types.get_type_slugs()
        type_weight = (
            sum(plague_config.type_weights.get(t, 0.0) for t in type_slugs)
            if type_slugs and plague_config.type_weights
            else 1.0
        )
        shape_weight = plague_config.shape_weights.get(
            monster.shape.slug, 1.0 if not plague_config.shape_weights else 0.0
        )
        modifier = type_weight * shape_weight

        resistance = 1.0

        # Type-based resistance
        for t in type_slugs:
            resistance *= plague_config.resistance_modifiers.get(
                "types", {}
            ).get(t, 1.0)

        # Shape-based resistance
        resistance *= plague_config.resistance_modifiers.get("shapes", {}).get(
            monster.shape.slug, 1.0
        )

        # Status-based resistance
        current_status = monster.status.current_status
        if current_status:
            resistance *= plague_config.resistance_modifiers.get(
                "statuses", {}
            ).get(current_status.slug, 1.0)

        final_chance = plague_config.spreadness * modifier * resistance
        chance = random.random() < final_chance

        logger.debug(
            f"Plague check for monster '{monster.name}': slug={plague_slug}, "
            f"spreadness={plague_config.spreadness}, modifier={modifier}, resistance={resistance}, "
            f"final_chance={final_chance}, chance={chance}, can_be_infected={can_be_infected}"
        )

        return can_be_infected and chance

    def is_target_eligible(
        self, monster: Monster, plague_slug: str, plague_config: PlagueData
    ) -> bool:
        # Weight range check
        if plague_config.weight_range:
            min_w, max_w = plague_config.weight_range
            if not (min_w <= monster.weight <= max_w):
                logger.debug(
                    f"Monster '{monster.name}' weight {monster.weight}kg is outside target range for plague '{plague_slug}': {plague_config.weight_range}"
                )
                return False

        # Height range check
        if plague_config.height_range:
            min_h, max_h = plague_config.height_range
            if not (min_h <= monster.height <= max_h):
                logger.debug(
                    f"Monster '{monster.name}' height {monster.height}m is outside target range for plague '{plague_slug}': {plague_config.height_range}"
                )
                return False

        # Type weight check
        if plague_config.type_weights:
            type_weight = sum(
                plague_config.type_weights.get(t, 0.0)
                for t in monster.types.get_type_slugs()
            )
            if type_weight == 0.0:
                logger.debug(
                    f"Monster '{monster.name}' has no matching types for plague '{plague_slug}': {plague_config.type_weights}"
                )
                return False

        # Shape weight check
        if plague_config.shape_weights:
            shape_weight = plague_config.shape_weights.get(
                monster.shape.slug, 0.0
            )
            if shape_weight == 0.0:
                logger.debug(
                    f"Monster '{monster.name}' shape '{monster.shape.slug}' not in shape weights for plague '{plague_slug}': {plague_config.shape_weights}"
                )
                return False

        return True

    def try_infect(
        self, monster: Monster, plague_slug: str
    ) -> InfectionResult:
        """
        Attempts to infect the given monster with the specified plague.
        Returns a string indicating the result:
        ('infected', 'carrier', 'minor_effect', 'resisted', 'immune', 'already_has').
        """
        if self.is_infected_with(plague_slug) or self.is_carrier_of(
            plague_slug
        ):
            return InfectionResult.ALREADY_HAS

        plague_config = self.get_plague_config(plague_slug)
        if plague_config is None:
            logger.error(f"Unknown plague slug: {plague_slug}")
            return InfectionResult.UNKNOWN_PLAGUE

        is_immune = self.is_inoculated_against(
            plague_slug
        ) or self.is_recovered_from(plague_slug)
        if is_immune or not self.is_target_eligible(
            monster, plague_slug, plague_config
        ):
            return InfectionResult.IMMUNE

        if self.can_be_infected_by(monster, plague_slug):
            self.infect(plague_slug)
            return InfectionResult.INFECTED
        else:
            return (
                InfectionResult.MINOR_EFFECT
                if plague_config.message_minor_effect
                else InfectionResult.RESISTED
            )

    def is_inoculation_eligible(
        self, monster: Monster, plague_slug: str, plague_config: PlagueData
    ) -> bool:
        """
        Determines if the monster is eligible to be inoculated against the given plague.
        Uses inoculation-specific rules from the plague config.
        """
        inoculation = plague_config.inoculation
        if inoculation is None:
            logger.debug(
                f"No inoculation config found for plague '{plague_slug}'."
            )
            return False

        # Check required held_item
        held_item = monster.held_item
        if inoculation.required_held_item is not None:
            if (
                not held_item
                or held_item.slug != inoculation.required_held_item
            ):
                logger.debug(
                    f"Monster '{monster.name}' must hold item '{inoculation.required_held_item}' to be eligible for inoculation against '{plague_slug}', but is holding '{held_item.slug if held_item else 'none'}'."
                )
                return False

        # Check eligible types
        if inoculation.eligible_types:
            if not any(
                t in inoculation.eligible_types
                for t in monster.types.get_type_slugs()
            ):
                logger.debug(
                    f"Monster '{monster.name}' types {monster.types.get_type_slugs()} not eligible for inoculation against '{plague_slug}'."
                )
                return False

        # Check eligible shapes
        if inoculation.eligible_shapes:
            if monster.shape.slug not in inoculation.eligible_shapes:
                logger.debug(
                    f"Monster '{monster.name}' shape '{monster.shape.slug}' not eligible for inoculation against '{plague_slug}'."
                )
                return False

        return True

    def try_inoculate(
        self, monster: Monster, plague_slug: str
    ) -> InoculationResult:
        """
        Attempts to inoculate the given monster against the specified plague.
        Returns True if inoculation occurred, False otherwise.
        """
        plague_config = self.get_plague_config(plague_slug)
        if plague_config is None:
            logger.error(f"Unknown plague slug: {plague_slug}")
            return InoculationResult.UNKNOWN_PLAGUE

        if self.is_inoculated_against(plague_slug):
            return InoculationResult.ALREADY_INOCULATED

        if self.is_inoculation_eligible(monster, plague_slug, plague_config):
            self.inoculate(plague_slug)
            return InoculationResult.INOCULATED

        return InoculationResult.NOT_ELIGIBLE

    def try_cure(
        self, monster: Monster, plague_slug: str
    ) -> tuple[bool, str | None]:
        """
        Attempts to cure a monster of a specific plague based on its cure configuration.
        If successful, the status changes to 'recovered' for immunity.
        """
        plague_config = self.get_plague_config(plague_slug)
        cure = plague_config.cure if plague_config else None

        was_infected = self.is_infected_with(plague_slug)
        was_carrier = self.is_carrier_of(plague_slug)

        if not was_infected and not was_carrier:
            return False, None

        if not cure:
            return False, None

        success = random.random() < cure.chance
        message = None

        if success:
            self._plagues[plague_slug] = PlagueType.RECOVERED

            if was_infected:
                message = cure.message_cured
            elif was_carrier:
                message = cure.message_carrier_cured

        return success, message

    def is_infected(self) -> bool:
        return any(
            plague_type == PlagueType.INFECTED
            for plague_type in self._plagues.values()
        )

    def remove_plague(self, plague_slug: str) -> None:
        if plague_slug in self._plagues:
            del self._plagues[plague_slug]

    def has_plague(self, plague_slug: str) -> bool:
        return plague_slug in self._plagues

    def get_plague_type(self, plague_slug: str) -> PlagueType | None:
        return self._plagues.get(plague_slug)

    def get_infected_slugs(self) -> list[str]:
        return [
            slug
            for slug, plague in self._plagues.items()
            if plague == PlagueType.INFECTED
        ]

    def is_infected_with(self, plague_slug: str) -> bool:
        return self.get_plague_type(plague_slug) == PlagueType.INFECTED

    def is_inoculated_against(self, plague_slug: str) -> bool:
        return self.get_plague_type(plague_slug) == PlagueType.INOCULATED

    def is_carrier_of(self, plague_slug: str) -> bool:
        return self.get_plague_type(plague_slug) == PlagueType.CARRIER

    def is_recovered_from(self, plague_slug: str) -> bool:
        return self.get_plague_type(plague_slug) == PlagueType.RECOVERED

    def clear_plagues(self) -> None:
        self._plagues.clear()

    def get_most_severe_plague_slug(self) -> str | None:
        active = [
            s
            for s in self._plagues
            if self.is_infected_with(s) and s in self.plague_data
        ]
        if not active:
            return None
        return max(active, key=lambda slug: self.plague_data[slug].spreadness)

    def get_suppressed_symptom_message(
        self, monster_name: str, plague_slug: str
    ) -> str | None:
        """
        Returns a suppressed symptom message if the monster is infected,
        using dynamic message key from plague config.
        """
        if self.is_infected():
            plague_config = self.get_plague_config(plague_slug)
            if plague_config is None:
                return None
            message_key = (
                plague_config.message_user_suppressed or "combat_state_plague1"
            )
            params = {"target": monster_name.upper()}
            return T.format(message_key, params)
        return None

    def get_plague_config(self, plague_slug: str) -> PlagueData | None:
        return self.plague_data.get(plague_slug)

    def get_combat_message_key(self, plague_slug: str) -> str:
        plague_config = self.get_plague_config(plague_slug)
        if plague_config is None:
            return "combat_state_plague3"  # fallback

        if self.is_infected_with(plague_slug):
            return (
                plague_config.message_target_infected or "combat_state_plague4"
            )
        else:
            return (
                plague_config.message_target_resists or "combat_state_plague3"
            )

    def progress_plagues(self) -> list[tuple[str, str]]:
        """
        Attempts natural progression for all active plagues (recovery, onset).
        Returns a list of tuples: (plague_slug, message_key).
        """
        progression_messages = []

        for slug, plague_type in list(self._plagues.items()):
            plague_config = self.get_plague_config(slug)
            if not plague_config:
                continue

            # Infected -> Recovered (Natural Recovery)
            if plague_type == PlagueType.INFECTED:
                if random.random() < plague_config.natural_recovery_chance:
                    self._plagues[slug] = PlagueType.RECOVERED
                    progression_messages.append(
                        (slug, "message_natural_recovery")
                    )

            # Symptom Onset (Carrier -> Infected)
            elif plague_type == PlagueType.CARRIER:
                if random.random() < plague_config.symptom_onset_chance:
                    self._plagues[slug] = PlagueType.INFECTED
                    message = (
                        plague_config.message_symptom_onset
                        or "message_symptom_onset_default"
                    )
                    progression_messages.append((slug, message))

        return progression_messages

    def encode_plagues(self) -> dict[str, str]:
        return {
            k: (v.value if isinstance(v, PlagueType) else str(v))
            for k, v in self._plagues.items()
        }

    def decode_plagues(self, json_data: Mapping[str, Any] | None) -> None:
        if not json_data or "plague" not in json_data:
            return
        for k, v in json_data["plague"].items():
            if isinstance(v, str):
                try:
                    self._plagues[k] = PlagueType(v)
                except ValueError:
                    logger.warning(
                        f"Unknown plague state '{v}' for '{k}' in save — skipping",
                    )
            else:
                self._plagues[k] = v

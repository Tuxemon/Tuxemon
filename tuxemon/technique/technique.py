# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from tuxemon.core.asset import get_assets
from tuxemon.core.core_effect import TechEffectResult
from tuxemon.core.core_processor import (
    ConditionProcessor,
    ConditionValidationResult,
    EffectProcessor,
)
from tuxemon.database.runtime import db
from tuxemon.db import (
    TechniqueModel,
)
from tuxemon.element import ElementTypesHandler
from tuxemon.locale.locale import T
from tuxemon.modifiers import ModifiersHandler
from tuxemon.monster.stats import BasicStats
from tuxemon.technique.cooldown import Cooldown
from tuxemon.technique.stats import (
    TechniqueBaseStats,
    TechniqueCurrentStats,
    TechniqueCustomBoosts,
)

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class Technique:
    """
    Particular skill that tuxemon monsters can use in battle.
    """

    def __init__(
        self,
        slug: str,
        db_data: TechniqueModel,
        instance_id: UUID | None = None,
        *,
        custom_boosts: TechniqueCustomBoosts | None = None,
        attempts: int = 0,
        successes: int = 0,
        failures: int = 0,
    ) -> None:
        self.slug = slug
        self.instance_id = instance_id or uuid4()

        self.tech_id = db_data.tech_id
        self.sort = db_data.sort
        self.tags = db_data.tags
        self.range = db_data.range
        self.behaviors = db_data.behaviors
        self.stat_modifiers = db_data.stat_modifiers
        self.target = db_data.target.model_dump()
        self.menu_actions_data = db_data.menu_actions

        self.speed = db_data.speed.numeric_value

        self.base_stats = TechniqueBaseStats(
            accuracy=db_data.accuracy,
            potency=db_data.potency,
            power=db_data.power,
            healing_power=db_data.healing_power,
        )

        self.custom_boosts = custom_boosts or TechniqueCustomBoosts()

        self.stats = self.compute_stats()

        self.core_assets = get_assets()
        self.types = ElementTypesHandler(db_data.types)
        self.modifiers = ModifiersHandler(db_data.modifiers)

        self.effect_defs = db_data.effects
        self.conditions = self.core_assets.parse_conditions(db_data.conditions)
        self.condition_handler = ConditionProcessor(self.conditions)

        self.cooldown = Cooldown()
        self._configure_cooldown(db_data)

        self.visuals = db_data.visuals
        self.sound = db_data.sound

        self.use_tech = T.maybe_translate(db_data.use_tech)
        self.use_success = T.maybe_translate(db_data.use_success)
        self.use_failure = T.maybe_translate(db_data.use_failure)
        self.confirm_text = T.translate(db_data.confirm_text)
        self.cancel_text = T.translate(db_data.cancel_text)

        self.attempts = attempts
        self.successes = successes
        self.failures = failures
        self.hit: bool = False
        self.temporary_stat_boosts = BasicStats()

    @classmethod
    def create(cls, slug: str) -> Technique:
        """Standard creation from DB."""
        db_data = TechniqueModel.lookup(slug, db)
        return cls(slug, db_data)

    @classmethod
    def from_save(cls, save_data: Mapping[str, Any]) -> Technique:
        """Reconstructs a technique from saved state."""
        slug = save_data["slug"]
        db_data = TechniqueModel.lookup(slug, db)

        instance_id = (
            UUID(save_data["instance_id"])
            if "instance_id" in save_data
            else None
        )

        custom_boosts = None
        if "custom_boosts" in save_data:
            custom_boosts = TechniqueCustomBoosts.from_dict(
                save_data["custom_boosts"]
            )

        return cls(
            slug,
            db_data,
            instance_id=instance_id,
            custom_boosts=custom_boosts,
            attempts=save_data.get("attempts", 0),
            successes=save_data.get("successes", 0),
            failures=save_data.get("failures", 0),
        )

    @property
    def name(self) -> str:
        return T.translate(self.slug)

    @property
    def description(self) -> str:
        return T.translate(f"{self.slug}_description")

    @property
    def is_recharging(self) -> bool:
        """Returns whether the technique is currently recharging."""
        return self.cooldown.is_recharging

    @property
    def power(self) -> float:
        return self.stats.power

    @power.setter
    def power(self, value: float) -> None:
        self.stats.power = value

    @property
    def potency(self) -> float:
        return self.stats.potency

    @potency.setter
    def potency(self, value: float) -> None:
        self.stats.potency = value

    @property
    def accuracy(self) -> float:
        return self.stats.accuracy

    @accuracy.setter
    def accuracy(self, value: float) -> None:
        self.stats.accuracy = value

    @property
    def healing_power(self) -> float:
        return self.stats.healing_power

    @healing_power.setter
    def healing_power(self, value: float) -> None:
        self.stats.healing_power = value

    @property
    def default_stats(self) -> TechniqueCurrentStats:
        """
        Returns the baseline stats (base + custom boosts),
        without any temporary battle modifiers.
        """
        return self.compute_stats()

    def _configure_cooldown(self, db_data: TechniqueModel) -> None:
        self.cooldown.duration = db_data.recharge
        self.cooldown.min_remaining = db_data.min_recharge
        self.cooldown.delay_turns = db_data.initial_delay
        self.cooldown.charge = db_data.starting_charge
        self.cooldown.multiplier = db_data.cooldown_multiplier

    def compute_stats(self) -> TechniqueCurrentStats:
        return TechniqueCurrentStats(
            power=self.base_stats.power + self.custom_boosts.power,
            potency=self.base_stats.potency + self.custom_boosts.potency,
            accuracy=self.base_stats.accuracy + self.custom_boosts.accuracy,
            healing_power=self.base_stats.healing_power
            + self.custom_boosts.healing_power,
        )

    def can_use(self, session: Session, target: Monster) -> bool:
        if self.is_recharging:
            return False
        return self.validate_monster(session, target)

    def validate_monster(self, session: Session, target: Monster) -> bool:
        """
        Check if the target meets all conditions that the technique has on its use.
        """
        return self.condition_handler.validate_monster(
            session=session, target=target
        ).passed

    def debug_validate_monster(
        self, session: Session, target: Monster
    ) -> ConditionValidationResult:
        """Developer API: returns full structured validation result."""
        return self.condition_handler.validate_monster(
            session=session, target=target
        )

    def recharge(self, amount: int = 1) -> None:
        self.cooldown.tick(amount)

    def full_recharge(self) -> None:
        self.cooldown.reset()

    def has_effect(self, effect_type: str) -> bool:
        return any(e.type == effect_type for e in self.effect_defs)

    def has_effect_param(self, effect_type: str, param_value: str) -> bool:
        """
        Returns True if the technique has an effect of the given type
        whose parameters contain the given value.
        """
        return any(
            rule.type == effect_type and param_value in rule.parameters
            for rule in self.effect_defs
        )

    def use(
        self, session: Session, user: Monster, target: Monster
    ) -> TechEffectResult:
        """
        Applies the technique's effects using EffectProcessor and returns the results.
        """
        self.attempts += 1
        self.effects = self.core_assets.parse_effects(self.effect_defs)
        self.effect_handler = EffectProcessor(self.effects)
        result = self.effect_handler.process_tech(
            session=session,
            source=self,
            user=user,
            target=target,
        )
        self.cooldown.trigger()
        if session.client:
            session.client.active_effect_manager.add_technique(self)
        if result.success:
            self.successes += 1
        else:
            self.failures += 1
        return result

    def has_type(self, type_slug: str) -> bool:
        """
        Returns TRUE if there is the type among the types.
        """
        return self.types.has_type(type_slug)

    def reset_current_stats(self) -> None:
        """
        Reset current stats to Base + Custom Boosts.
        Called after battle or when technique is refreshed.
        """
        self.stats = self.compute_stats()

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the technique to be saved to a file.
        """
        data = {
            "slug": self.slug,
            "instance_id": self.instance_id.hex,
            "attempts": self.attempts,
            "successes": self.successes,
            "failures": self.failures,
        }

        boosts = self.custom_boosts.to_dict()
        if any(boosts.values()):
            data["custom_boosts"] = boosts

        return data


def decode_moves(
    json_data: Sequence[Mapping[str, Any]] | None,
) -> list[Technique]:
    if not json_data:
        return []
    return [Technique.from_save(entry) for entry in json_data]


def encode_moves(techs: Sequence[Technique]) -> Sequence[Mapping[str, Any]]:
    return [tech.get_state() for tech in techs]

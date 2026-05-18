# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from tuxemon.core.asset import get_assets
from tuxemon.core.core_effect import StatusEffectResult
from tuxemon.core.core_processor import (
    ConditionProcessor,
    ConditionValidationResult,
    EffectProcessor,
)
from tuxemon.database.runtime import db
from tuxemon.db import EffectPhase, StatusModel
from tuxemon.locale.locale import T
from tuxemon.modifiers import ModifiersHandler
from tuxemon.monster.stats import BasicStats
from tuxemon.status.lifecycle import Lifecycle
from tuxemon.status.step_effect_engine import StepEffectEngine

if TYPE_CHECKING:
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


class Status:
    """
    Particular status that tuxemon monsters can be affected.
    """

    def __init__(
        self,
        host: Monster,
        db_data: StatusModel,
        instance_id: UUID | None = None,
        steps: float = 0.0,
    ) -> None:
        self._host = host
        self.slug = db_data.slug
        self.instance_id: UUID = instance_id or uuid4()

        self.sort = db_data.sort
        self.icon = db_data.icon
        self.behaviors = db_data.behaviors
        self.bond = db_data.bond
        self.category = db_data.category
        self.cond_id = db_data.cond_id
        self.visuals = db_data.visuals
        self.sound = db_data.sound
        self.on_tech_use = db_data.on_tech_use
        self.on_item_use = db_data.on_item_use
        self.on_positive_status = db_data.on_positive_status
        self.on_negative_status = db_data.on_negative_status

        self.core_assets = get_assets()
        self.conditions = self.core_assets.parse_conditions(db_data.conditions)
        self.condition_handler = ConditionProcessor(self.conditions)
        self.effect_defs = db_data.effects

        self.lifecycle = Lifecycle()
        self.lifecycle.duration = db_data.duration
        self.lifecycle.max_stacks = db_data.max_stacks

        self.step_engine = StepEffectEngine(initial_steps=steps)
        self.step_engine.interval = db_data.step_interval
        self.step_engine.effect_type = db_data.step_effect_type
        self.step_engine.value = db_data.step_effect_value
        self.stat_modifiers = db_data.stat_modifiers

        self.modifiers = ModifiersHandler(db_data.modifiers)
        self.temporary_stat_boosts = BasicStats()
        self._effect_applied: set[str] = set()
        self._linked_monster: Monster | None = None
        self.phase: EffectPhase = EffectPhase.DEFAULT

        self.gain_cond = T.maybe_translate(db_data.gain_cond)
        self.use_success = T.maybe_translate(db_data.use_success)
        self.use_failure = T.maybe_translate(db_data.use_failure)

    @classmethod
    def create(cls, slug: str, host: Monster, steps: float = 0.0) -> Status:
        db_data = StatusModel.lookup(slug, db)
        return cls(host=host, db_data=db_data, steps=steps)

    @classmethod
    def from_save(cls, host: Monster, save_data: Mapping[str, Any]) -> Status:
        slug = save_data["slug"]
        db_data = StatusModel.lookup(slug, db)

        instance_id = None
        if "instance_id" in save_data:
            instance_id = UUID(save_data["instance_id"])

        return cls(
            host=host,
            db_data=db_data,
            instance_id=instance_id,
            steps=save_data.get("steps", 0.0),
        )

    @property
    def name(self) -> str:
        return T.translate(self.slug)

    @property
    def description(self) -> str:
        return T.translate(f"{self.slug}_description")

    @property
    def host(self) -> Monster:
        """Returns the monster associated with this status."""
        return self._host

    @property
    def steps(self) -> float:
        return self.step_engine.steps

    @steps.setter
    def steps(self, value: float) -> None:
        self.step_engine.steps = value

    @property
    def linked_monster(self) -> Monster | None:
        """Returns the monster linked to this status effect."""
        return self._linked_monster

    @property
    def nr_turn(self) -> int:
        return self.lifecycle.turn

    def has_phase(self, phase: EffectPhase) -> bool:
        """Returns True if the current phase is equal to the provided phase, False otherwise."""
        return self.phase == phase

    def set_phase(self, phase: EffectPhase) -> None:
        """Sets the phase to the provided value."""
        self.phase = phase

    def advance_round(self) -> None:
        """Advance the counter for this status if used."""
        self.lifecycle.advance_use()

    def is_use_expired(self, max_uses: int = 1) -> bool:
        """
        Checks if the status has reached its use-based expiration threshold.
        """
        return self.lifecycle.is_use_expired(max_uses)

    def validate_monster(self, session: Session, target: Monster) -> bool:
        """
        Check if the target meets all conditions that the status has on its use.
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

    def set_linked_monster(self, monster: Monster) -> None:
        """Assigns a linked monster that benefits from this status."""
        self._linked_monster = monster

    def has_exceeded_duration(self) -> bool:
        """Checks if the status has lasted beyond its intended duration."""
        return self.lifecycle.has_exceeded_duration()

    def use(self, session: Session, phase: EffectPhase) -> StatusEffectResult:
        """
        Applies the status's effects using EffectProcessor and returns the results.
        """
        self.effects = self.core_assets.parse_effects(self.effect_defs)
        self.effect_handler = EffectProcessor(self.effects)
        self.set_phase(phase)
        result = self.effect_handler.process_status(
            session=session,
            source=self,
        )
        if session.client:
            session.client.active_effect_manager.add_status(self)
        return result

    def tick_turn(self) -> None:
        self.lifecycle.tick_turn()
        logger.debug(
            f"[Status Duration] {self.slug} turn {self.lifecycle.turn} "
            f"of {self.lifecycle.duration} at stack {self.lifecycle.stack_level}."
        )

    def stack(self) -> None:
        old, new = self.lifecycle.stack()
        logger.debug(
            f"Status '{self.slug}' stacked from {old} to {new}. "
            f"Duration/Uses refreshed."
        )

    def tick_steps(
        self, session: Session, steps: float
    ) -> StatusEffectResult | None:
        """
        Advance step counter and trigger effect if interval reached.
        """
        ticks = self.step_engine.add_steps(steps)
        if ticks <= 0:
            return None

        logger.debug(
            f"[Status Step Tick] {self.slug} triggered for {ticks} ticks."
        )

        self.step_engine.compute_hp_change(self.host, ticks)

        return self.use(session, EffectPhase.ON_STEP_INTERVAL)

    def is_already_applied(self, effect_name: str) -> bool:
        """Check if a specific core effect has already been triggered for this status."""
        return effect_name in self._effect_applied

    def mark_applied(self, effect_name: str) -> None:
        """Mark a core effect as applied so it doesn't run again."""
        self._effect_applied.add(effect_name)

    def get_state(self) -> Mapping[str, Any]:
        """Prepares a dictionary of the status to be saved."""
        return {
            "slug": self.slug,
            "steps": self.steps,
            "instance_id": self.instance_id.hex,
        }


def decode_status(
    json_data: Sequence[Mapping[str, Any]] | None, monster: Monster
) -> list[Status]:
    if not json_data:
        return []
    return [Status.from_save(host=monster, save_data=s) for s in json_data]


def encode_status(conds: Sequence[Status]) -> Sequence[Mapping[str, Any]]:
    return [cond.get_state() for cond in conds]

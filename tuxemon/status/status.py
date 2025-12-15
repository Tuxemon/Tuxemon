# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from tuxemon.core.asset import CoreAssetManager
from tuxemon.core.core_effect import StatusEffectResult
from tuxemon.core.core_processor import ConditionProcessor, EffectProcessor
from tuxemon.db import (
    CategoryStatus,
    EffectPhase,
    Range,
    ResponseStatus,
    SoundProperties,
    StatModel,
    StatusBehaviors,
    StatusModel,
    StepEffectType,
    VisualProperties,
    db,
)
from tuxemon.locale import T
from tuxemon.modifiers import ModifiersHandler
from tuxemon.surfanim import FlipAxes

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.plugin import PluginObject
    from tuxemon.session import Session

logger = logging.getLogger(__name__)


SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "steps",
)


class Status:
    """
    Particular status that tuxemon monsters can be affected.
    """

    MAX_STACKS: int = 5

    def __init__(
        self,
        host: Monster,
        steps: float = 0.0,
        save_data: Optional[Mapping[str, Any]] = None,
    ) -> None:
        save_data = save_data or {}
        self._host: Monster = host
        self._steps: float = steps
        self._linked_monster: Optional[Monster] = None
        self._nr_turn: int = 0

        self._effect_applied: set[str] = set()

        self.instance_id: UUID = uuid4()
        self.bond: bool = False
        self.counter: int = 0
        self.cond_id: int = 0
        self.category: Optional[CategoryStatus] = None
        self.visuals = VisualProperties(
            animation=None, flip_axes=FlipAxes.NONE, loop=-1
        )
        self.gain_cond: str = ""
        self.icon: str = ""
        self.duration: int = 0
        self.phase: EffectPhase = EffectPhase.DEFAULT
        self.range: Range = Range.melee
        self.stack_level: int = 1
        self.step_interval: int = 0
        self.step_effect_value: float = 0.0
        self.step_effect_type: StepEffectType = StepEffectType.NONE
        self._step_hp_change: int = 0
        self.on_positive_status: Optional[ResponseStatus] = None
        self.on_negative_status: Optional[ResponseStatus] = None
        self.on_tech_use: Optional[str] = None
        self.on_item_use: Optional[str] = None
        self.sound = SoundProperties(sfx=None, volume=1.5)
        self.sort: str = ""
        self.slug: str = ""
        self.use_success: str = ""
        self.use_failure: str = ""
        self.modifiers: ModifiersHandler = ModifiersHandler()
        self.behaviors: StatusBehaviors
        self.stat_modifiers: dict[str, StatModel] = {}

        self.core_assets = CoreAssetManager()
        self.effects: Sequence[PluginObject] = []
        self.conditions: Sequence[PluginObject] = []

        self.set_state(save_data)

    @classmethod
    def create(
        cls,
        slug: str,
        host: Monster,
        steps: float = 0.0,
        save_data: Optional[Mapping[str, Any]] = None,
    ) -> Status:
        method = cls(host, steps, save_data)
        method.load(slug)
        return method

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
        return self._steps

    @property
    def linked_monster(self) -> Optional[Monster]:
        """Returns the monster linked to this status effect."""
        return self._linked_monster

    @property
    def nr_turn(self) -> int:
        return self._nr_turn

    def load(self, slug: str) -> None:
        """
        Loads and sets this status's attributes from the status
        database. The status is looked up in the database by slug.

        Parameters:
            The slug of the status to look up in the database.
        """
        results = StatusModel.lookup(slug, db)
        self.slug = results.slug

        self.sort = results.sort

        # status use notifications (translated!)
        self.gain_cond = T.maybe_translate(results.gain_cond)
        self.use_success = T.maybe_translate(results.use_success)
        self.use_failure = T.maybe_translate(results.use_failure)

        self.icon = results.icon

        self.modifiers = ModifiersHandler(results.modifiers)
        self.behaviors = results.behaviors
        self.step_interval = results.step_interval
        self.step_effect_value = results.step_effect_value
        self.step_effect_type = results.step_effect_type
        # monster stats
        self.stat_modifiers = results.stat_modifiers

        # status fields
        self.duration = results.duration
        self.bond = results.bond
        self.category = results.category
        self.on_negative_status = results.on_negative_status
        self.on_positive_status = results.on_positive_status
        self.on_tech_use = results.on_tech_use
        self.on_item_use = results.on_item_use

        self.cond_id = results.cond_id

        self.effect_defs = results.effects
        self.conditions = self.core_assets.parse_conditions(results.conditions)
        self.condition_handler = ConditionProcessor(self.conditions)

        self.visuals = results.visuals
        self.sound = results.sound

    def has_phase(self, phase: EffectPhase) -> bool:
        """Returns True if the current phase is equal to the provided phase, False otherwise."""
        return self.phase == phase

    def set_phase(self, phase: EffectPhase) -> None:
        """Sets the phase to the provided value."""
        self.phase = phase

    def advance_round(self) -> None:
        """Advance the counter for this status if used."""
        self.counter += 1
        logger.debug(
            f"[Status Counter] {self.slug} used {self.counter} times."
        )

    def is_use_expired(self, max_uses: int = 1) -> bool:
        """
        Checks if the status has reached its use-based expiration threshold.
        """
        return self.counter >= max_uses

    def validate_monster(self, session: Session, target: Monster) -> bool:
        """
        Check if the target meets all conditions that the status has on its use.
        """
        return self.condition_handler.validate(session=session, target=target)

    def set_linked_monster(self, monster: Monster) -> None:
        """Assigns a linked monster that benefits from this status."""
        self._linked_monster = monster

    def has_exceeded_duration(self) -> bool:
        """Checks if the status has lasted beyond its intended duration."""
        return self._nr_turn > self.duration

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
            session.client.active_statuses.append(self)
        return result

    def tick_turn(self) -> None:
        """
        Advance the turn counter for this status.
        Only increments nr_turn if the status has a defined duration (> 0).
        """
        if self.duration > 0:
            self._nr_turn += 1
            logger.debug(
                f"[Status Duration] {self.slug} turn {self._nr_turn} "
                f"of {self.duration} at stack {self.stack_level}."
            )

    def stack(self) -> None:
        """
        Increments the status stack level up to MAX_STACKS and
        resets the turn counter (nr_turn) and the use counter (counter)
        to refresh the duration and uses.
        """
        old_stack = self.stack_level
        self.stack_level = min(old_stack + 1, self.MAX_STACKS)
        self._nr_turn = 0
        self.counter = 0
        logger.debug(
            f"Status '{self.slug}' stacked from {old_stack} to {self.stack_level}. "
            f"Duration/Uses refreshed."
        )

    def _calculate_step_hp_change(self, ticks: int) -> int:
        """
        Calculates the total HP change (damage or heal) applied by the
        status for the given number of steps/intervals (ticks).
        """
        if (
            self.step_effect_type == StepEffectType.NONE
            or self.step_effect_value == 0.0
        ):
            return 0

        value = self.step_effect_value
        monster = self.host
        hp_change_per_tick: float = 0.0

        if self.step_effect_type == StepEffectType.FLAT_DAMAGE:
            hp_change_per_tick = -value
        elif self.step_effect_type == StepEffectType.PERCENT_MAX_HP_DAMAGE:
            hp_change_per_tick = -(monster.hp * (value / 100))
        elif self.step_effect_type == StepEffectType.PERCENT_CURRENT_HP_DAMAGE:
            hp_change_per_tick = -(monster.current_hp * (value / 100))
        elif self.step_effect_type == StepEffectType.PERCENT_MAX_HP_HEAL:
            hp_change_per_tick = monster.hp * (value / 100)
        elif self.step_effect_type == StepEffectType.PERCENT_CURRENT_HP_HEAL:
            hp_change_per_tick = monster.current_hp * (value / 100)

        return round(hp_change_per_tick * ticks)

    def tick_steps(
        self, session: Session, steps: float
    ) -> Optional[StatusEffectResult]:
        """
        Advance the step counter and trigger the status effect if the interval
        is reached. Returns the result if the effect was triggered.
        """
        if self.step_interval <= 0:
            return None

        old_steps = self._steps
        self._steps += steps

        old_interval_count = old_steps // self.step_interval
        new_interval_count = self._steps // self.step_interval

        if new_interval_count > old_interval_count:
            ticks = int(new_interval_count - old_interval_count)
            logger.debug(
                f"[Status Step Tick] {self.slug} triggered after "
                f"{new_interval_count} intervals. Ticking {ticks} times."
            )
            self._step_hp_change = self._calculate_step_hp_change(ticks)
            return self.use(session, EffectPhase.ON_STEP_INTERVAL)

        return None

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the status to be saved to a file.
        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = self.instance_id.hex

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """Loads information from saved data."""
        if not save_data:
            return

        self.load(save_data["slug"])

        for key, value in save_data.items():
            if key == "instance_id" and value:
                self.instance_id = UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_status(
    json_data: Optional[Sequence[Mapping[str, Any]]], monster: Monster
) -> list[Status]:
    return [Status(host=monster, save_data=cond) for cond in json_data or {}]


def encode_status(
    conds: Sequence[Status],
) -> Sequence[Mapping[str, Any]]:
    return [cond.get_state() for cond in conds]

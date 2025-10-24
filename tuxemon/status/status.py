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
    StatModel,
    StatusBehaviors,
    StatusModel,
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

        self._effect_applied: set[str] = set()

        self.instance_id: UUID = uuid4()
        self.bond: bool = False
        self.counter: int = 0
        self.cond_id: int = 0
        self.animation: Optional[str] = None
        self.category: Optional[CategoryStatus] = None
        self.description: str = ""
        self.flip_axes: FlipAxes = FlipAxes.NONE
        self.gain_cond: str = ""
        self.icon: str = ""
        self.linked_monster: Optional[Monster] = None
        self.name: str = ""
        self.nr_turn: int = 0
        self.duration: int = 0
        self.phase: EffectPhase = EffectPhase.DEFAULT
        self.range: Range = Range.melee
        self.stack_level: int = 1
        self.on_positive_status: Optional[ResponseStatus] = None
        self.on_negative_status: Optional[ResponseStatus] = None
        self.on_tech_use: Optional[str] = None
        self.on_item_use: Optional[str] = None
        self.sfx: str = ""
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
    def host(self) -> Monster:
        return self._host

    @property
    def steps(self) -> float:
        return self._steps

    def load(self, slug: str) -> None:
        """
        Loads and sets this status's attributes from the status
        database. The status is looked up in the database by slug.

        Parameters:
            The slug of the status to look up in the database.
        """
        results = StatusModel.lookup(slug, db)
        self.slug = results.slug
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")

        self.sort = results.sort

        # status use notifications (translated!)
        self.gain_cond = T.maybe_translate(results.gain_cond)
        self.use_success = T.maybe_translate(results.use_success)
        self.use_failure = T.maybe_translate(results.use_failure)

        self.icon = results.icon

        self.modifiers = ModifiersHandler(results.modifiers)
        self.behaviors = results.behaviors
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

        self.effects = self.core_assets.parse_effects(results.effects)
        self.conditions = self.core_assets.parse_conditions(results.conditions)
        self.condition_handler = ConditionProcessor(self.conditions)
        self.effect_handler = EffectProcessor(self.effects)

        # Load the animation sprites that will be used for this status
        self.animation = results.animation
        self.flip_axes = results.flip_axes

        # Load the sound effect for this status
        self.sfx = results.sfx

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

    def get_host(self) -> Monster:
        """Returns the monster associated with this status."""
        return self._host

    def get_linked_monster(self) -> Optional[Monster]:
        """Returns the monster linked to this status effect."""
        return self.linked_monster

    def set_linked_monster(self, monster: Monster) -> None:
        """Assigns a linked monster that benefits from this status."""
        self.linked_monster = monster

    def has_reached_duration(self) -> bool:
        """Checks if the status has reached or exceeded its duration."""
        return self.nr_turn >= self.duration > 0

    def has_exceeded_duration(self) -> bool:
        """Checks if the status has lasted beyond its intended duration."""
        return self.nr_turn > self.duration

    def use(self, session: Session, phase: EffectPhase) -> StatusEffectResult:
        """
        Applies the status's effects using EffectProcessor and returns the results.
        """
        self.set_phase(phase)
        result = self.effect_handler.process_status(
            session=session,
            source=self,
        )
        return result

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

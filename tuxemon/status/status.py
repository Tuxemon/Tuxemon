# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional

from tuxemon.constants import paths
from tuxemon.core.core_condition import CoreCondition
from tuxemon.core.core_effect import StatusEffect, StatusEffectResult
from tuxemon.core.core_manager import ConditionManager, EffectManager
from tuxemon.core.core_processor import ConditionProcessor, EffectProcessor
from tuxemon.db import (
    CategoryStatus,
    Range,
    ResponseStatus,
    db,
)
from tuxemon.locale import T
from tuxemon.surfanim import FlipAxes

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.plugin import PluginObject
    from tuxemon.session import Session
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "steps",
)


class Status:
    """
    Particular status that tuxemon monsters can be affected.
    """

    effect_manager: Optional[EffectManager] = None
    condition_manager: Optional[ConditionManager] = None

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.instance_id = uuid.uuid4()
        self.steps = 0.0
        self.bond = False
        self.counter = 0
        self.cond_id = 0
        self.animation: Optional[str] = None
        self.category: Optional[CategoryStatus] = None
        self.combat_state: Optional[CombatState] = None
        self.description = ""
        self.flip_axes = FlipAxes.NONE
        self.gain_cond = ""
        self.icon = ""
        self.link: Optional[Monster] = None
        self.name = ""
        self.nr_turn = 0
        self.duration = 0
        self.phase: Optional[str] = None
        self.range = Range.melee
        self.repl_pos: Optional[ResponseStatus] = None
        self.repl_neg: Optional[ResponseStatus] = None
        self.repl_tech: Optional[str] = None
        self.repl_item: Optional[str] = None
        self.sfx = ""
        self.sort = ""
        self.slug = ""
        self.use_success = ""
        self.use_failure = ""

        if Status.effect_manager is None:
            Status.effect_manager = EffectManager(
                StatusEffect, paths.CORE_EFFECT_PATH
            )
        if Status.condition_manager is None:
            Status.condition_manager = ConditionManager(
                CoreCondition, paths.CORE_CONDITION_PATH
            )

        self.effects: Sequence[PluginObject] = []
        self.conditions: Sequence[PluginObject] = []

        self.set_state(save_data)

    def load(self, slug: str) -> None:
        """
        Loads and sets this status's attributes from the status
        database. The status is looked up in the database by slug.

        Parameters:
            The slug of the status to look up in the database.
        """
        try:
            results = db.lookup(slug, table="status")
        except KeyError:
            raise RuntimeError(f"Status {slug} not found")

        self.slug = results.slug  # a short English identifier
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")

        self.sort = results.sort

        # status use notifications (translated!)
        self.gain_cond = T.maybe_translate(results.gain_cond)
        self.use_success = T.maybe_translate(results.use_success)
        self.use_failure = T.maybe_translate(results.use_failure)

        self.icon = results.icon
        self.counter = self.counter
        self.steps = self.steps

        self.modifiers = results.modifiers
        # monster stats
        self.statspeed = results.statspeed
        self.stathp = results.stathp
        self.statarmour = results.statarmour
        self.statmelee = results.statmelee
        self.statranged = results.statranged
        self.statdodge = results.statdodge
        # status fields
        self.duration = results.duration
        self.bond = results.bond or self.bond
        self.category = results.category or self.category
        self.repl_neg = results.repl_neg or self.repl_neg
        self.repl_pos = results.repl_pos or self.repl_pos
        self.repl_tech = results.repl_tech or self.repl_tech
        self.repl_item = results.repl_item or self.repl_item

        self.range = results.range or Range.melee
        self.cond_id = results.cond_id or self.cond_id

        if self.effect_manager and results.effects:
            self.effects = self.effect_manager.parse_effects(results.effects)
        if self.condition_manager and results.conditions:
            self.conditions = self.condition_manager.parse_conditions(
                results.conditions
            )
        self.condition_handler = ConditionProcessor(self.conditions)
        self.effect_handler = EffectProcessor(self.effects)

        # Load the animation sprites that will be used for this status
        self.animation = results.animation
        self.flip_axes = results.flip_axes

        # Load the sound effect for this status
        self.sfx = results.sfx

    def advance_round(self) -> None:
        """
        Advance the counter for this status if used.

        """
        self.counter += 1

    def validate_monster(self, session: Session, target: Monster) -> bool:
        """
        Check if the target meets all conditions that the status has on its use.
        """
        return self.condition_handler.validate(session=session, target=target)

    def use(self, session: Session, target: Monster) -> StatusEffectResult:
        """
        Applies the status's effects using EffectProcessor and returns the results.
        """
        result = self.effect_handler.process_status(
            session=session,
            source=self,
            target=target,
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

        save_data["instance_id"] = str(self.instance_id.hex)

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        """
        if not save_data:
            return

        self.load(save_data["slug"])

        for key, value in save_data.items():
            if key == "instance_id" and value:
                self.instance_id = uuid.UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_status(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Status]:
    return [Status(save_data=cond) for cond in json_data or {}]


def encode_status(
    conds: Sequence[Status],
) -> Sequence[Mapping[str, Any]]:
    return [cond.get_state() for cond in conds]

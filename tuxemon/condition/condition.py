# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from tuxemon import plugin
from tuxemon.condition.condcondition import CondCondition
from tuxemon.condition.condeffect import CondEffect, CondEffectResult
from tuxemon.constants import paths
from tuxemon.db import CategoryCondition, Range, ResponseCondition, db
from tuxemon.locale import T

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "steps",
)


class Condition:
    """
    Particular condition that tuxemon monsters can be affected.

    """

    effects_classes: ClassVar[Mapping[str, type[CondEffect]]] = {}
    conditions_classes: ClassVar[Mapping[str, type[CondCondition]]] = {}

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.instance_id = uuid.uuid4()
        self.steps = 0.0
        self.bond = False
        self.counter = 0
        self.cond_id = 0
        self.animation: Optional[str] = None
        self.category: Optional[CategoryCondition] = None
        self.combat_state: Optional[CombatState] = None
        self.conditions: Sequence[CondCondition] = []
        self.description = ""
        self.effects: Sequence[CondEffect] = []
        self.flip_axes = ""
        self.gain_cond = ""
        self.icon = ""
        self.link: Optional[Monster] = None
        self.name = ""
        self.nr_turn = 0
        self.duration = 0
        self.phase: Optional[str] = None
        self.range = Range.melee
        self.repl_pos: Optional[ResponseCondition] = None
        self.repl_neg: Optional[ResponseCondition] = None
        self.repl_tech: Optional[str] = None
        self.repl_item: Optional[str] = None
        self.sfx = ""
        self.sort = ""
        self.slug = ""
        self.use_success = ""
        self.use_failure = ""

        # load effect and condition plugins if it hasn't been done already
        if not Condition.effects_classes:
            Condition.effects_classes = plugin.load_plugins(
                paths.COND_EFFECT_PATH,
                "effects",
                interface=CondEffect,
            )
            Condition.conditions_classes = plugin.load_plugins(
                paths.COND_CONDITION_PATH,
                "conditions",
                interface=CondCondition,
            )

        self.set_state(save_data)

    def load(self, slug: str) -> None:
        """
        Loads and sets this condition's attributes from the condition
        database. The condition is looked up in the database by slug.

        Parameters:
            The slug of the condition to look up in the database.
        """
        try:
            results = db.lookup(slug, table="condition")
        except KeyError:
            raise RuntimeError(f"Condition {slug} not found")

        self.slug = results.slug  # a short English identifier
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")

        self.sort = results.sort

        # condition use notifications (translated!)
        self.gain_cond = T.maybe_translate(results.gain_cond)
        self.use_success = T.maybe_translate(results.use_success)
        self.use_failure = T.maybe_translate(results.use_failure)

        self.icon = results.icon
        self.counter = self.counter
        self.steps = self.steps

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

        self.conditions = self.parse_conditions(results.conditions)
        self.effects = self.parse_effects(results.effects)
        self.target = results.target.model_dump()

        # Load the animation sprites that will be used for this condition
        self.animation = results.animation
        self.flip_axes = results.flip_axes

        # Load the sound effect for this condition
        self.sfx = results.sfx

    def parse_effects(
        self,
        raw: Sequence[str],
    ) -> Sequence[CondEffect]:
        """
        Convert effect strings to effect objects.

        Takes raw effects list from the condition's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw effects list pulled from the condition's db entry.

        Returns:
            Effects turned into a list of CondEffect objects.

        """
        effects = []

        for line in raw:
            parts = line.split(maxsplit=1)
            name = parts[0]
            params = parts[1].split(",") if len(parts) > 1 else []

            try:
                effect_class = Condition.effects_classes[name]
            except KeyError:
                logger.error(f'Error: CondEffect "{name}" not implemented')
            else:
                effects.append(effect_class(*params))

        return effects

    def parse_conditions(
        self,
        raw: Sequence[str],
    ) -> Sequence[CondCondition]:
        """
        Convert condition strings to condition objects.

        Takes raw condition list from the condition's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw conditions list pulled from the condition's db entry.

        Returns:
            Conditions turned into a list of CondCondition objects.

        """
        conditions = []

        for line in raw:
            parts = line.split(maxsplit=2)
            op = parts[0]
            name = parts[1]
            params = parts[2].split(",") if len(parts) > 2 else []

            try:
                condition_class = Condition.conditions_classes[name]
            except KeyError:
                logger.error(f'Error: CondCondition "{name}" not implemented')
                continue

            if op not in ["is", "not"]:
                raise ValueError(f"{op} must be 'is' or 'not'")

            condition = condition_class(*params)
            condition._op = op == "is"
            conditions.append(condition)

        return conditions

    def advance_round(self) -> None:
        """
        Advance the counter for this condition if used.

        """
        self.counter += 1

    def validate(self, target: Optional[Monster]) -> bool:
        """
        Check if the target meets all conditions that the condition has on its use.

        Parameters:
            target: The monster or object that we are using this condition on.

        Returns:
            Whether the condition may be used.

        """
        if not self.conditions:
            return True
        if not target:
            return False

        return all(
            (
                condition.test(target)
                if condition._op
                else not condition.test(target)
            )
            for condition in self.conditions
        )

    def use(self, target: Monster) -> CondEffectResult:
        """
        Apply the condition.

        Parameters:
            user: The Monster object that used this condition.
            target: Monster object that we are using this condition on.

        Returns:
            A dictionary with the effect name, success and misc properties.

        """
        # Defaults for the return. items can override these values in their
        # return.
        meta_result: CondEffectResult = {
            "name": self.name,
            "success": False,
            "condition": None,
            "technique": None,
            "extra": None,
        }

        # Loop through all the effects of this condition and execute the effect's function.
        for effect in self.effects:
            result = effect.apply(self, target)
            meta_result.update(result)

        return meta_result

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the condition to be saved to a file.

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


def decode_condition(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Condition]:
    return [Condition(save_data=cond) for cond in json_data or {}]


def encode_condition(
    conds: Sequence[Condition],
) -> Sequence[Mapping[str, Any]]:
    return [cond.get_state() for cond in conds]

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from tuxemon import plugin
from tuxemon.constants import paths
from tuxemon.db import ElementType, Range, db
from tuxemon.element import Element
from tuxemon.locale import T
from tuxemon.technique.techcondition import TechCondition
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "counter",
)


class Technique:
    """
    Particular skill that tuxemon monsters can use in battle.

    """

    effects_classes: ClassVar[Mapping[str, type[TechEffect]]] = {}
    conditions_classes: ClassVar[Mapping[str, type[TechCondition]]] = {}

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.instance_id = uuid.uuid4()
        self.counter = 0
        self.tech_id = 0
        self.accuracy = 0.0
        self.animation: Optional[str] = None
        self.combat_state: Optional[CombatState] = None
        self.conditions: Sequence[TechCondition] = []
        self.description = ""
        self.effects: Sequence[TechEffect] = []
        self.flip_axes = ""
        self.icon = ""
        self.hit = False
        self.is_fast = False
        self.randomly = True
        self.name = ""
        self.next_use = 0
        self.nr_turn = 0
        self.potency = 0.0
        self.power = 1.0
        self.range = Range.melee
        self.healing_power = 0.0
        self.recharge_length = 0
        self.sfx = ""
        self.sort = ""
        self.slug = ""
        self.types: list[Element] = []
        self.usable_on = False
        self.use_success = ""
        self.use_failure = ""
        self.use_tech = ""

        # load effect and condition plugins if it hasn't been done already
        if not Technique.effects_classes:
            Technique.effects_classes = plugin.load_plugins(
                paths.TECH_EFFECT_PATH,
                "effects",
                interface=TechEffect,
            )
            Technique.conditions_classes = plugin.load_plugins(
                paths.TECH_CONDITION_PATH,
                "conditions",
                interface=TechCondition,
            )

        self.set_state(save_data)

    def load(self, slug: str) -> None:
        """
        Loads and sets this technique's attributes from the technique
        database. The technique is looked up in the database by slug.

        Parameters:
            The slug of the technique to look up in the database.
        """
        try:
            results = db.lookup(slug, table="technique")
        except KeyError:
            raise RuntimeError(f"Technique {slug} not found")

        self.slug = results.slug  # a short English identifier
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")

        self.sort = results.sort

        # technique use notifications (translated!)
        self.use_tech = T.maybe_translate(results.use_tech)
        self.use_success = T.maybe_translate(results.use_success)
        self.use_failure = T.maybe_translate(results.use_failure)

        self.icon = results.icon
        self.counter = self.counter
        # types
        self.types = [Element(ele) for ele in results.types]
        # technique stats
        self.accuracy = results.accuracy or self.accuracy
        self.potency = results.potency or self.potency
        self.power = results.power or self.power

        self.default_potency = results.potency or self.potency
        self.default_power = results.power or self.power

        self.hit = self.hit
        self.is_fast = results.is_fast or self.is_fast
        self.randomly = results.randomly or self.randomly
        self.healing_power = results.healing_power or self.healing_power
        self.recharge_length = results.recharge or self.recharge_length
        self.range = results.range or Range.melee
        self.tech_id = results.tech_id or self.tech_id

        self.conditions = self.parse_conditions(results.conditions)
        self.effects = self.parse_effects(results.effects)
        self.target = results.target.model_dump()
        self.usable_on = results.usable_on or self.usable_on

        # Load the animation sprites that will be used for this technique
        self.animation = results.animation
        self.flip_axes = results.flip_axes

        # Load the sound effect for this technique
        self.sfx = results.sfx

    def parse_effects(
        self,
        raw: Sequence[str],
    ) -> Sequence[TechEffect]:
        """
        Convert effect strings to effect objects.

        Takes raw effects list from the technique's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw effects list pulled from the technique's db entry.

        Returns:
            Effects turned into a list of TechEffect objects.

        """
        effects = []

        for line in raw:
            parts = line.split(maxsplit=1)
            name = parts[0]
            params = parts[1].split(",") if len(parts) > 1 else []

            try:
                effect_class = Technique.effects_classes[name]
            except KeyError:
                logger.error(f'Error: TechEffect "{name}" not implemented')
            else:
                effects.append(effect_class(*params))

        return effects

    def parse_conditions(
        self,
        raw: Sequence[str],
    ) -> Sequence[TechCondition]:
        """
        Convert condition strings to condition objects.

        Takes raw condition list from the technique's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw conditions list pulled from the technique's db entry.

        Returns:
            Conditions turned into a list of TechCondition objects.

        """
        conditions = []

        for line in raw:
            parts = line.split(maxsplit=2)
            op = parts[0]
            name = parts[1]
            params = parts[2].split(",") if len(parts) > 2 else []

            try:
                condition_class = Technique.conditions_classes[name]
            except KeyError:
                logger.error(f'Error: TechCondition "{name}" not implemented')
                continue

            if op not in ["is", "not"]:
                raise ValueError(f"{op} must be 'is' or 'not'")

            condition = condition_class(*params)
            condition._op = op == "is"
            conditions.append(condition)

        return conditions

    def advance_round(self) -> None:
        """
        Advance the counter for this technique if used.

        """
        self.counter += 1

    def validate(self, target: Optional[Monster]) -> bool:
        """
        Check if the target meets all conditions that the technique has on its use.

        Parameters:
            target: The monster or object that we are using this technique on.

        Returns:
            Whether the technique may be used.

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

    def recharge(self) -> None:
        self.next_use -= 1

    def full_recharge(self) -> None:
        self.next_use = 0

    def use(self, user: Monster, target: Monster) -> TechEffectResult:
        """
        Apply the technique.

        Applies this technique's effects as defined in the "effect" column of
        the technique database. This method will execute a function with the
        same name as the effect defined in the database. If you want to add a
        new effect, simply create a new function under the Technique class
        with the name of the effect you define in monster.db.

        Parameters:
            user: The Monster object that used this technique.
            target: Monster object that we are using this technique on.

        Returns:
            A dictionary with the effect name, success and misc properties.

        Examples:

        >>> technique = Technique()
        >>> technique.load("technique_poison_sting")
        >>> bulbatux.learn(technique)
        >>>
        >>> bulbatux.moves[0].use(user=bulbatux, target=tuxmander)

        """
        # Loop through all the effects of this technique and execute the
        # effect's function.
        # TODO: more robust API
        # TODO: separate classes for each Technique
        # TODO: consider moving message templates to the JSON DB

        # Defaults for the return. items can override these values in their
        # return.
        meta_result: TechEffectResult = {
            "name": self.name,
            "success": False,
            "should_tackle": False,
            "damage": 0,
            "element_multiplier": 0.0,
            "extra": None,
        }

        self.next_use = self.recharge_length

        # Loop through all the effects of this technique and execute the effect's function.
        for effect in self.effects:
            result = effect.apply(self, user, target)
            meta_result["success"] = (
                meta_result["success"] or result["success"]
            )
            meta_result["should_tackle"] = (
                meta_result["should_tackle"] or result["should_tackle"]
            )
            meta_result["damage"] += result["damage"]
            meta_result["element_multiplier"] *= result["element_multiplier"]
            if result["extra"] is not None:
                meta_result["extra"] = result["extra"]

        return meta_result

    def has_type(self, element: Optional[ElementType]) -> bool:
        """
        Returns TRUE if there is the type among the types.
        """
        return (
            element in [ele.slug for ele in self.types] if element else False
        )

    def set_stats(self) -> None:
        """
        Reset technique stats default value.

        """
        self.potency = self.default_potency
        self.power = self.default_power

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the technique to be saved to a file.

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


def decode_moves(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Technique]:
    return [Technique(save_data=tech) for tech in json_data or {}]


def encode_moves(techs: Sequence[Technique]) -> Sequence[Mapping[str, Any]]:
    return [tech.get_state() for tech in techs]

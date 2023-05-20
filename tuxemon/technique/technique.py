# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
)

from tuxemon import plugin, prepare
from tuxemon.constants import paths
from tuxemon.db import (
    CategoryCondition,
    ElementType,
    Range,
    ResponseCondition,
    db,
    process_targets,
)
from tuxemon.graphics import animation_frame_files
from tuxemon.locale import T
from tuxemon.technique.techcondition import TechCondition
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "slug",
    "power",
    "potency",
    "accuracy",
    "counter",
    "counter_success",
)


class Technique:
    """
    Particular skill that tuxemon monsters can use in battle.

    """

    effects_classes: ClassVar[Mapping[str, Type[TechEffect[Any]]]] = {}
    conditions_classes: ClassVar[Mapping[str, Type[TechCondition[Any]]]] = {}

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        if save_data is None:
            save_data = dict()

        self.instance_id = uuid.uuid4()
        self.counter = 0
        self.counter_success = 0
        self.tech_id = 0
        self.accuracy = 0.0
        self.animation = Optional[str]
        self.category: Optional[CategoryCondition] = None
        self.combat_state: Optional[CombatState] = None
        self.conditions: Sequence[TechCondition[Any]] = []
        self.description = ""
        self.effects: Sequence[TechEffect[Any]] = []
        self.flip_axes = ""
        self.icon = ""
        self.images: Sequence[str] = []
        self.hit = False
        self.is_fast = False
        self.randomly = True
        self.link: Optional[Monster] = None
        self.name = ""
        self.next_use = 0
        self.potency = 0.0
        self.power = 1.0
        self.range = Range.melee
        self.healing_power = 0
        self.recharge_length = 0
        self.repl_pos: Optional[ResponseCondition] = None
        self.repl_neg: Optional[ResponseCondition] = None
        self.sfx = ""
        self.sort = ""
        self.slug = ""
        self.target: Sequence[str] = []
        self.types: List[ElementType] = []
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

        results = db.lookup(slug, table="technique")
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
        self.counter_success = self.counter_success
        self.types = list(results.types)
        # technique stats
        self.accuracy = results.accuracy or self.accuracy
        self.potency = results.potency or self.potency
        self.power = results.power or self.power

        self.default_potency = results.potency or self.potency
        self.default_power = results.power or self.power
        # monster stats
        self.statspeed = results.statspeed
        self.stathp = results.stathp
        self.statarmour = results.statarmour
        self.statmelee = results.statmelee
        self.statranged = results.statranged
        self.statdodge = results.statdodge
        # status fields
        self.category = results.category or self.category
        self.repl_neg = results.repl_neg or self.repl_neg
        self.repl_pos = results.repl_pos or self.repl_pos

        self.hit = self.hit
        self.is_fast = results.is_fast or self.is_fast
        self.randomly = results.randomly or self.randomly
        self.healing_power = results.healing_power or self.healing_power
        self.recharge_length = results.recharge or self.recharge_length
        self.range = results.range or Range.melee
        self.tech_id = results.tech_id or self.tech_id

        self.conditions = self.parse_conditions(results.conditions)
        self.effects = self.parse_effects(results.effects)
        self.target = process_targets(results.target)
        self.usable_on = results.usable_on or self.usable_on

        # Load the animation sprites that will be used for this technique
        self.animation = results.animation
        if self.animation:
            directory = prepare.fetch("animations", "technique")
            self.images = animation_frame_files(directory, self.animation)
            if self.animation and not self.images:
                logger.error(
                    f"Cannot find animation frames for: {self.animation}",
                )
        self.flip_axes = results.flip_axes

        # Load the sound effect for this technique
        self.sfx = results.sfx

    def parse_effects(
        self,
        raw: Sequence[str],
    ) -> Sequence[TechEffect[Any]]:
        """
        Convert effect strings to effect objects.

        Takes raw effects list from the technique's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw effects list pulled from the technique's db entry.

        Returns:
            Effects turned into a list of TechEffect objects.

        """
        ret = list()

        for line in raw:
            name = line.split()[0]
            if len(line.split()) > 1:
                params = line.split()[1].split(",")
            else:
                params = []
            try:
                effect = Technique.effects_classes[name]
            except KeyError:
                logger.error(f'Error: TechEffect "{name}" not implemented')
            else:
                ret.append(effect(*params))

        return ret

    def parse_conditions(
        self,
        raw: Sequence[str],
    ) -> Sequence[TechCondition[Any]]:
        """
        Convert condition strings to condition objects.

        Takes raw condition list from the technique's json and parses it into a
        form more suitable for the engine.

        Parameters:
            raw: The raw conditions list pulled from the technique's db entry.

        Returns:
            Conditions turned into a list of TechCondition objects.

        """
        ret = list()

        for line in raw:
            op = line.split()[0]
            name = line.split()[1]
            if len(line.split()) > 2:
                params = line.split()[2].split(",")
            else:
                params = []
            try:
                condition = Technique.conditions_classes[name]
                if op == "is":
                    condition._op = True
                elif op == "not":
                    condition._op = False
                else:
                    raise ValueError(f"{op} must be 'is' or 'not'")
            except KeyError:
                logger.error(f'Error: TechCondition "{name}" not implemented')
            else:
                ret.append(condition(*params))

        return ret

    def advance_round(self) -> None:
        """
        Advance the counter for this technique if used.

        """
        self.counter += 1

    def advance_counter_success(self) -> None:
        """
        Advance the counter for this technique if used successfully.

        """
        self.counter_success += 1

    def validate(self, target: Optional[Monster]) -> bool:
        """
        Check if the target meets all conditions that the technique has on it's use.

        Parameters:
            target: The monster or object that we are using this technique on.

        Returns:
            Whether the technique may be used.

        """
        if not self.conditions:
            return True
        if not target:
            return False

        result = True

        for condition in self.conditions:
            if condition._op is True:
                event = condition.test(target)
            else:
                event = not condition.test(target)
            result = result and event
        return result

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
        }

        # Loop through all the effects of this technique and execute the effect's function.
        for effect in self.effects:
            result = effect.apply(self, user, target)
            meta_result.update(result)

        self.next_use = self.recharge_length

        return meta_result

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
) -> List[Technique]:
    return [Technique(save_data=tech) for tech in json_data or {}]


def encode_moves(techs: Sequence[Technique]) -> Sequence[Mapping[str, Any]]:
    return [tech.get_state() for tech in techs]

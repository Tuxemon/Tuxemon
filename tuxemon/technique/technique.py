# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Mapping,
    Optional,
    Sequence,
    Type,
)

from tuxemon import plugin, prepare
from tuxemon.constants import paths
from tuxemon.db import ElementType, Range, db, process_targets
from tuxemon.graphics import animation_frame_files
from tuxemon.locale import T
from tuxemon.technique.techcondition import TechCondition
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)


class Technique:
    """
    Particular skill that tuxemon monsters can use in battle.

    Parameters:
        slug: Slug of the technique.
        carrier: Monster affected by a status technique.
        link: Additional monster linked to the effect of the status technique.
            For example, monster that obtains life with lifeleech.

    """

    effects_classes: ClassVar[Mapping[str, Type[TechEffect[Any]]]] = {}
    conditions_classes: ClassVar[Mapping[str, Type[TechCondition[Any]]]] = {}

    def __init__(
        self,
        slug: Optional[str] = None,
        carrier: Optional[Monster] = None,
        link: Optional[Monster] = None,
    ) -> None:
        # number of turns that this technique has been active
        self._combat_counter = 0
        self._life_counter = 0
        self.tech_id = 0
        self.accuracy = 0.0
        self.animation = ""
        self.can_apply_status = False
        self.carrier = carrier
        self.category = ""
        self.combat_state: Optional[CombatState] = None
        self.conditions: Sequence[TechCondition[Any]] = []
        self.effects: Sequence[TechEffect[Any]] = []
        self.flip_axes = ""
        self.icon = ""
        self.images: Sequence[str] = []
        self.is_area = False
        self.is_fast = False
        self.link = link
        self.name = "Pound"
        self.next_use = 0.0
        self.potency = 0.0
        self.power = 1.0
        self.range = Range.melee
        self.recharge_length = 0
        self.repl_pos = ""
        self.repl_neg = ""
        self.sfx = ""
        self.sort = ""
        self.slug = slug
        self.target: Sequence[str] = []
        self.type1 = ElementType.aether
        self.type2: Optional[ElementType] = None
        self.use_item = ""
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

        # If a slug of the technique was provided, autoload it.
        if slug:
            self.load(slug)

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

        self.sort = results.sort
        assert self.sort

        # technique use notifications (translated!)
        # NOTE: should be `self.use_tech`, but Technique and Item have
        # overlapping checks
        self.use_item = T.maybe_translate(results.use_tech)
        self.use_success = T.maybe_translate(results.use_success)
        self.use_failure = T.maybe_translate(results.use_failure)

        self.icon = results.icon
        self._combat_counter = 0
        self._life_counter = 0

        if results.types:
            self.type1 = results.types[0]
            if len(results.types) > 1:
                self.type2 = results.types[1]
            else:
                self.type2 = None
        else:
            self.type1 = self.type2 = None
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

        self.is_fast = results.is_fast or self.is_fast
        self.recharge_length = results.recharge or self.recharge_length
        self.is_area = results.is_area or self.is_area
        self.range = results.range or Range.melee
        self.tech_id = results.tech_id or self.tech_id

        self.conditions = self.parse_conditions(results.conditions)
        self.effects = self.parse_effects(results.effects)
        self.target = process_targets(results.target)

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
                params = None
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
            words = line.split()
            args = "".join(words[1:]).split(",")
            name = words[0]
            params = args[1:]
            try:
                condition = Technique.conditions_classes[name]
            except KeyError:
                logger.error(f'Error: TechCondition "{name}" not implemented')
            else:
                ret.append(condition(*params))

        return ret

    def advance_round(self, number: int = 1) -> None:
        """
        Advance the turn counters for this technique.

        Techniques have two counters currently, a "combat counter" and a
        "life counter".
        Combat counters should be reset with combat begins.
        Life counters will be set to zero when the Technique is created,
        but will never be reset.

        Calling this function will advance both counters.

        """
        self._combat_counter += 1
        self._life_counter += 1

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
            result = result and condition.test(target)

        return result

    def recharge(self) -> None:
        self.next_use -= 1

    def full_recharge(self) -> None:
        self.next_use = 0

    def reset_combat_counter(self) -> None:
        """Reset the combat counter."""
        self._combat_counter = 0

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

        >>> poison_tech = Technique("technique_poison_sting")
        >>> bulbatux.learn(poison_tech)
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
            "capture": False,
            "statuses": [],
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

    def get_state(self) -> Optional[str]:
        return self.slug

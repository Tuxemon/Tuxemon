#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
# Leif Theden <leif.theden@gmail.com>
# Andy Mender <andymenderunix@gmail.com>
#
#
#
#

from __future__ import annotations

import logging
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
from tuxemon.db import Range, db, process_targets
from tuxemon.graphics import animation_frame_files
from tuxemon.locale import T
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.states.combat.combat import CombatState

logger = logging.getLogger(__name__)


RANGES = {
    Range.melee: {
        "accuracy": 1,
        "potency": 1,
        "power": 1,
    },
    Range.ranged: {
        "accuracy": 2,
        "potency": 2,
        "power": 2,
    },
    Range.reach: {
        "accuracy": 3,
        "potency": 3,
        "power": 3,
    },
    Range.reliable: {
        "accuracy": 4,
        "potency": 4,
        "power": 4,
    },
    Range.special: {
        "accuracy": 5,
        "potency": 5,
        "power": 5,
    },
    Range.status: {
        "accuracy": 6,
        "potency": 6,
        "power": 6,
    },
    Range.touch: {
        "accuracy": 7,
        "potency": 7,
        "power": 7,
    },
}


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
        self.combat_state: Optional[CombatState] = None
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
        self.sfx = ""
        self.sort = ""
        self.slug = slug
        self.target: Sequence[str] = []
        self.type1: Optional[str] = "aether"
        self.type2: Optional[str] = None
        self.use_item = ""
        self.use_success = ""
        self.use_failure = ""
        self.use_tech = ""

        # load plugins if it hasn't been done already
        if not Technique.effects_classes:
            Technique.effects_classes = plugin.load_plugins(
                paths.TECH_EFFECT_PATH,
                "effects",
                interface=TechEffect,
            )

        # If a slug of the technique was provided, autoload it.
        if slug:
            self.load(slug)
            self.set_stats()

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

        self.statspeed = results.statspeed
        self.stathp = results.stathp
        self.statarmour = results.statarmour
        self.statmelee = results.statmelee
        self.statranged = results.statranged
        self.statdodge = results.statdodge

        self.is_fast = results.is_fast or self.is_fast
        self.recharge_length = results.recharge or self.recharge_length
        self.is_area = results.is_area or self.is_area
        self.range = results.range or Range.melee
        self.tech_id = results.tech_id or self.tech_id
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
                ret.append(effect(self, self.link or self.carrier, params))

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
            result = effect.apply(user, target)
            meta_result.update(result)

        self.next_use = self.recharge_length

        return meta_result

    def get_state(self) -> Optional[str]:
        return self.slug

    def set_stats(self) -> None:
        """
        Set or improve stats.
        """
        ranges = RANGES[self.range]
        self.accuracy = ranges["accuracy"]
        self.potency = ranges["potency"]
        self.power = ranges["power"]

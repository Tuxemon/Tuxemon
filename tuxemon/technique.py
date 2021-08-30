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
import random


from tuxemon import formula
from tuxemon import prepare
from tuxemon.db import db, process_targets
from tuxemon.graphics import animation_frame_files
from tuxemon.locale import T
from typing import Optional, Sequence, TYPE_CHECKING, TypedDict, List, Tuple

if TYPE_CHECKING:
    from tuxemon.monster import Monster

logger = logging.getLogger(__name__)

class EffectResult(TypedDict, total=False):
    damage: int
    element_multiplier: float
    success: bool
    should_tackle: bool
    status: Optional[Technique]


class TechniqueResult(EffectResult):
    name: str
    # Related Mypy bug: https://github.com/python/mypy/issues/8714
    success: bool
    should_tackle: bool
    capture: bool
    statuses: List[Optional[Technique]]


def merge_results(result: EffectResult, meta_result: TechniqueResult) -> TechniqueResult:
    status = result.pop("status", None)
    if status:
        meta_result["statuses"].append(status)
    # Known Mypy bug: https://github.com/python/mypy/issues/6462
    meta_result.update(result)
    return meta_result


class Technique:
    """A technique object is a particular skill that tuxemon monsters can use
    in battle.
    """
    def __init__(
        self,
        slug: Optional[str] = None,
        carrier: Optional[Monster] = None,
        link: Optional[Monster] = None,
    ) -> None:
        self._combat_counter = 0  # number of turns that this technique has been active
        self._life_counter = 0
        self.accuracy = 0.0
        self.animation = ""
        self.can_apply_status = False
        self.carrier = carrier
        self.category = "attack"
        self.effect: Sequence[str] = []
        self.icon = ""
        self.images: Sequence[str] = []
        self.is_area = False
        self.is_fast = False
        self.link = link
        self.name = "Pound"
        self.next_use = 0.0
        self.potency = 0.0
        self.power = 1.0
        self.statspeed: Sequence[str] = []
        self.stathp: Sequence[str] = []
        self.statranged: Sequence[str] = []
        self.statarmour: Sequence[str]= []
        self.statmelee: Sequence[str] = []
        self.statdodge: Sequence[str] = []
        self.range: Optional[str] = None
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


        # If a slug of the technique was provided, autoload it.
        if slug:
            self.load(slug)

    def load(self, slug: str) -> None:
        """Loads and sets this technique's attributes from the technique
        database. The technique is looked up in the database by slug.

        :param slug: The slug of the technique to look up in the database.

        :type slug: String

        :rtype: None
        """

        results = db.lookup(slug, table="technique")
        self.slug = results["slug"]  # a short English identifier
        self.name = T.translate(self.slug)  # locale-specific string

        self.sort = results["sort"]

        # technique use notifications (translated!)
        # NOTE: should be `self.use_tech`, but Technique and Item have overlapping checks
        self.use_item = T.maybe_translate(results.get("use_tech"))
        self.use_success = T.maybe_translate(results.get("use_success"))
        self.use_failure = T.maybe_translate(results.get("use_failure"))

        self.category = results["category"]
        self.icon = results["icon"]
        self._combat_counter = 0
        self._life_counter = 0

        if results.get("types"):
            self.type1 = results["types"][0]
            if len(results["types"]) > 1:
                self.type2 = results["types"][1]
            else:
                self.type2 = None
        else:
            self.type1 = self.type2 = None

        self.power = results.get("power", self.power)


        self.statspeed = results.get("statspeed")
        self.stathp = results.get("stathp")
        self.statarmour = results.get("statarmour")
        self.statmelee = results.get("statmelee")
        self.statranged = results.get("statranged")
        self.statdodge = results.get("statdodge")

        self.is_fast = results.get("is_fast", self.is_fast)
        self.recharge_length = results.get("recharge", self.recharge_length)
        self.is_area = results.get("is_area", self.is_area)
        self.range = results.get("range", self.range)
        self.accuracy = results.get("accuracy", self.accuracy)
        self.potency = results.get("potency", self.potency)
        self.effect = results["effects"]
        self.target = process_targets(results["target"])

        # Load the animation sprites that will be used for this technique
        self.animation = results["animation"]
        if self.animation:
            directory = prepare.fetch("animations", "technique")
            self.images = animation_frame_files(directory, self.animation)
            if self.animation and not self.images:
                logger.error(f"Cannot find animation frames for: {self.animation}")

        # Load the sound effect for this technique
        self.sfx = results["sfx"]

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

    def use(self, user: Monster, target: Monster) -> TechniqueResult:
        
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
        # Loop through all the effects of this technique and execute the effect's function.
        # TODO: more robust API
        # TODO: separate classes for each Technique
        # TODO: consider moving message templates to the JSON DB

        # defaults for the return. items can override these values in their return.
        meta_result: TechniqueResult = {
            "name": self.name,
            "success": False,
            "should_tackle": False,
            "capture": False,
            "statuses": [],
        }
        # TODO: handle conflicting values from multiple technique actions
        # TODO: for example, how to handle one saying success, and another not?
       
        for effect in self.effect:
            if effect == "damage":
                result = self.damage(user, target)
            elif effect == "poison":
                result = self.apply_status("status_poison", target)
            elif effect == "statchange":
                result = self.changestats(user, target)
            elif effect == "lifeleech":
                result = self.apply_lifeleech(user, target)
            elif effect == "recover":
                result = self.apply_status("status_recover", user)
            elif effect == "status":
                for category in self.category:
                    if category == "poison":
                        result = self.poison(target)
                    elif category == "lifeleech":
                        result = self.lifeleech(target)
                    elif category == "recover":
                        result = self.recover(target)
                    else:
                        result = getattr(self, self.category)(target)
            else:
                result = getattr(self, str(effect))(user, target)
            meta_result = merge_results(result, meta_result)

        self.next_use = self.recharge_length

        return meta_result
    def changestats(self, user: Monster, target: Monster) -> EffectResult:
        statsmaster = [self.statspeed, self.stathp, self.statarmour, self.statmelee, self.statranged, self.statdodge]
        statslugs = ['speed', 'hp', 'armour', 'melee', 'ranged', 'dodge']
        if None not in statsmaster and [] not in statsmaster:
            for stat, slug in zip(statsmaster, statslugs):
                value = stat['value']
                dividing = stat['dividing']
                override = stat['overridetofull']
                basestatvalue = getattr(target, slug)
                if value > 0 and override == False:
                    if dividing == False:
                        newstatvalue = basestatvalue + value
                    else:
                        newstatvalue = basestatvalue // value
                    success = True
                    setattr(target, slug, newstatvalue)
                if override == True and slug == 'hp':
                    success = True
                    target.current_hp = target.hp
        return {
            "success": bool(stat)
        }
    def calculate_damage(
        self,
        user: Monster,
        target: Monster,
    ) -> Tuple[int, float]:
        """
        Calculate damage for the damage technique.

        Parameters:
            user: The Monster object that used this technique.
            target: The Monster object that we are using this technique on.

        Returns:
            A tuple (damage, multiplier).

        """
        return formula.simple_damage_calculate(self, user, target)

    def damage(self, user: Monster, target: Monster) -> EffectResult:
        """
        Apply damage.

        This effect applies damage to a target monster. Damage calculations
        are based upon the original Pokemon battle damage formula. This
        effect will be applied if "damage" is defined in this technique's
        effect list.

        Parameters:
            user: The Monster object that used this technique.
            target: The Monster object that we are using this technique on.

        Returns:
            Dict summarizing the result.

        """
        hit = self.accuracy >= random.random()
        if hit or self.is_area:
            self.can_apply_status = True
            damage, mult = self.calculate_damage(user, target)
            if not hit:
                damage //= 2
            target.current_hp -= damage
        else:
            damage = 0
            mult = 1

        return {
            "damage": damage,
            "element_multiplier": mult,
            "should_tackle": bool(damage),
            "success": bool(damage),
        }

    def apply_status(self, slug: str, target: Monster) -> EffectResult:
        """
        This effect has a chance to apply a status effect to a target monster.

        Parameters:
            slug: Name of the status effect.
            target: The Monster object that we are using this technique on.

        Returns:
            Dict summarizing the result.

        """
        
        already_applied = any(t for t in target.status if t.slug == slug)
        success = not already_applied and self.can_apply_status self.potency >= random.random()
        tech = None
        if success:
            tech = Technique(slug, carrier=target)
            target.apply_status(tech)

        return {
            "status": tech,
        }

    def apply_lifeleech(self, user: Monster, target: Monster) -> EffectResult:
        """
        This effect has a chance to apply the lifeleech status effect.

        Parameters:
            user: The Monster object that used this technique.
            target: The Monster object that we are using this technique on.

        Returns:
            Dict summarizing the result.

        """
        already_applied = any(t for t in target.status if t.slug == "status_lifeleech")
        success = not already_applied and self.potency >= random.random()
        tech = None
        if success:
            tech = Technique("status_lifeleech", carrier=target, link=user)
            target.apply_status(tech)
        return {
            "status": tech,
        }

    def poison(self, target: Monster) -> EffectResult:
        damage = formula.simple_poison(self, self.link, target)
        target.current_hp -= damage
        return {
            "damage": damage,
            "should_tackle": bool(damage),
            "success": bool(damage),
        }

    def recover(self, target: Monster) -> EffectResult:
        heal = formula.simple_recover(self, target)
        target.current_hp += heal
        return {
            "damage": heal,
            "should_tackle": False,
            "success": bool(heal),
        }

    def lifeleech(self, target: Monster) -> EffectResult:
        user = self.link
        assert user
        damage = formula.simple_lifeleech(self, user, target)
        target.current_hp -= damage
        user.current_hp += damage
        return {
            "damage": damage,
            "should_tackle": bool(damage),
            "success": bool(damage),
        }

    def faint(self, user: Monster, target: Monster) -> EffectResult:
        """
        Faint this monster.

        Typically, called by combat to faint self, not others.

        Parameters:
            user: The Monster object that used this technique.
            target: The Monster object that we are using this technique on.

        Returns:
            Dict summarizing the result.

        """
        # TODO: implement into the combat state, currently not used

        already_fainted = any(t for t in target.status if t.name == "status_faint")

        if already_fainted:
            raise RuntimeError

        target.apply_status(Technique("status_faint"))

        return {
            "should_tackle": False,
            "success": True,
        }

    def swap(self, user: Monster, target: Monster) -> EffectResult:
        """
        Used just for combat: change order of monsters.

        Position of monster in party will be changed.

        Returns:
            Dict summarizing the result.

        """
        # TODO: implement actions as events, so that combat state can find them
        # TODO: relies on setting "combat_state" attribute.  maybe clear it up later
        # TODO: these values are set in combat_menus.py

        def swap_add() -> None:
            # TODO: make accommodations for battlefield positions
            combat_state.add_monster_into_play(user, target)

        # TODO: find a way to pass values. this will only work for SP games with one monster party
        combat_state = self.combat_state
        # get the original monster to be swapped out
        original_monster = combat_state.monsters_in_play[user][0]

        # rewrite actions to target the new monster.  must be done before original is removed
        combat_state.rewrite_action_queue_target(original_monster, target)

        # remove the old monster and all their actions
        combat_state.remove_monster_from_play(user, original_monster)

        # give a slight delay
        combat_state.task(swap_add, 0.75)
        combat_state.suppress_phase_change(0.75)

        return {
            "success": True,
            "should_tackle": False,
        }
    def get_state(self) -> Optional[str]:
        return self.slug

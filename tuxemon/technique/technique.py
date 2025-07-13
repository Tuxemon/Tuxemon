# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from tuxemon.constants import paths
from tuxemon.core.core_condition import CoreCondition
from tuxemon.core.core_effect import CoreEffect, TechEffectResult
from tuxemon.core.core_manager import ConditionManager, EffectManager
from tuxemon.core.core_processor import ConditionProcessor, EffectProcessor
from tuxemon.db import Range, TechniqueModel, db
from tuxemon.element import ElementTypesHandler
from tuxemon.locale import T
from tuxemon.modifiers import ModifiersHandler
from tuxemon.surfanim import FlipAxes

if TYPE_CHECKING:
    from tuxemon.monster import Monster
    from tuxemon.plugin import PluginObject
    from tuxemon.session import Session
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

    effect_manager: Optional[EffectManager] = None
    condition_manager: Optional[ConditionManager] = None

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        save_data = save_data or {}

        self.instance_id: UUID = uuid4()
        self.counter: int = 0
        self.tech_id: int = 0
        self.accuracy: float = 0.0
        self.animation: Optional[str] = None
        self.combat_state: Optional[CombatState] = None
        self.description: str = ""
        self.flip_axes: FlipAxes = FlipAxes.NONE
        self.hit: bool = False
        self.speed: int = 0
        self.randomly: bool = True
        self.name: str = ""
        self.next_use: int = 0
        self.potency: float = 0.0
        self.power: float = 1.0
        self.default_potency: float = 0.0
        self.default_power: float = 1.0
        self.range: Range = Range.melee
        self.healing_power: float = 0.0
        self.recharge_length: int = 0
        self.sfx: str = ""
        self.sort: str = ""
        self.slug: str = ""
        self.types: ElementTypesHandler = ElementTypesHandler()
        self.modifiers: ModifiersHandler = ModifiersHandler()
        self.usable_on: bool = False
        self.use_success: str = ""
        self.use_failure: str = ""
        self.use_tech: str = ""
        self.confirm_text: str = ""
        self.cancel_text: str = ""

        if Technique.effect_manager is None:
            Technique.effect_manager = EffectManager(
                CoreEffect, paths.CORE_EFFECT_PATH
            )
        if Technique.condition_manager is None:
            Technique.condition_manager = ConditionManager(
                CoreCondition, paths.CORE_CONDITION_PATH
            )

        self.effects: Sequence[PluginObject] = []
        self.conditions: Sequence[PluginObject] = []

        self.set_state(save_data)

    @classmethod
    def create(
        cls, slug: str, save_data: Optional[Mapping[str, Any]] = None
    ) -> Technique:
        method = cls(save_data)
        method.load(slug)
        return method

    @property
    def is_recharging(self) -> bool:
        """Returns whether the technique is currently recharging."""
        return self.next_use > 0

    def load(self, slug: str) -> None:
        """
        Loads and sets this technique's attributes from the technique
        database. The technique is looked up in the database by slug.

        Parameters:
            The slug of the technique to look up in the database.
        """
        results = TechniqueModel.lookup(slug, db)
        self.slug = results.slug  # a short English identifier
        self.name = T.translate(self.slug)
        self.description = T.translate(f"{self.slug}_description")

        self.sort = results.sort

        # technique use notifications (translated!)
        self.use_tech = T.maybe_translate(results.use_tech)
        self.use_success = T.maybe_translate(results.use_success)
        self.use_failure = T.maybe_translate(results.use_failure)
        self.confirm_text = T.translate(results.confirm_text)
        self.cancel_text = T.translate(results.cancel_text)

        # types
        self.types = ElementTypesHandler(results.types)
        # technique stats
        self.accuracy = results.accuracy
        self.potency = results.potency
        self.power = results.power

        self.default_potency = results.potency
        self.default_power = results.power

        self.speed = results.speed.numeric_value
        self.randomly = results.randomly
        self.healing_power = results.healing_power
        self.recharge_length = results.recharge
        self.range = results.range
        self.tech_id = results.tech_id

        if self.effect_manager and results.effects:
            self.effects = self.effect_manager.parse_effects(results.effects)
        if self.condition_manager and results.conditions:
            self.conditions = self.condition_manager.parse_conditions(
                results.conditions
            )
        self.condition_handler = ConditionProcessor(self.conditions)
        self.effect_handler = EffectProcessor(self.effects)
        self.target = results.target.model_dump()
        self.usable_on = results.usable_on
        self.modifiers = ModifiersHandler(results.modifiers)

        # Load the animation sprites that will be used for this technique
        self.animation = results.animation
        self.flip_axes = results.flip_axes

        # Load the sound effect for this technique
        self.sfx = results.sfx

    def get_combat_state(self) -> CombatState:
        """Returns the CombatState."""
        if not self.combat_state:
            raise ValueError("No CombatState.")
        return self.combat_state

    def set_combat_state(self, combat_state: Optional[CombatState]) -> None:
        """Sets the CombatState."""
        self.combat_state = combat_state

    def advance_round(self) -> None:
        """
        Advance the counter for this technique if used.
        """
        self.counter += 1

    def validate_monster(self, session: Session, target: Monster) -> bool:
        """
        Check if the target meets all conditions that the technique has on its use.
        """
        return self.condition_handler.validate(session=session, target=target)

    def recharge(self) -> None:
        self.next_use -= 1

    def full_recharge(self) -> None:
        self.next_use = 0

    def execute_tech_action(
        self,
        session: Session,
        combat_instance: CombatState,
        user: Monster,
        target: Monster,
    ) -> TechEffectResult:
        """Executes the tech action and returns the result."""
        self.set_combat_state(combat_instance)
        return self.use(session, user, target)

    def use(
        self, session: Session, user: Monster, target: Monster
    ) -> TechEffectResult:
        """
        Applies the technique's effects using EffectProcessor and returns the results.
        """
        result = self.effect_handler.process_tech(
            session=session,
            source=self,
            user=user,
            target=target,
        )
        self.next_use = self.recharge_length
        return result

    def has_type(self, type_slug: str) -> bool:
        """
        Returns TRUE if there is the type among the types.
        """
        return self.types.has_type(type_slug)

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
                self.instance_id = UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)


def decode_moves(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> list[Technique]:
    return [Technique(save_data=tech) for tech in json_data or {}]


def encode_moves(techs: Sequence[Technique]) -> Sequence[Mapping[str, Any]]:
    return [tech.get_state() for tech in techs]

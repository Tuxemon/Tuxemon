# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Union

from tuxemon.core.core_condition import CoreCondition
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.plugin import PluginObject
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult
from tuxemon.technique.techeffect import TechEffect, TechEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


class EffectProcessor:
    """
    Class to handle processing of effects for objects.
    """

    def __init__(self, effects: Sequence[PluginObject]) -> None:
        self.effects = effects

    def process_tech(
        self,
        source: Technique,
        user: Monster,
        target: Monster,
        meta_result: TechEffectResult,
    ) -> TechEffectResult:
        for effect in self.effects:
            if isinstance(effect, TechEffect):
                result = effect.apply(source, user, target)
                self._merge_results_technique(meta_result, result)
        return meta_result

    def process_item(
        self,
        source: Item,
        target: Optional[Monster],
        meta_result: ItemEffectResult,
    ) -> ItemEffectResult:
        for effect in self.effects:
            if isinstance(effect, ItemEffect):
                result = effect.apply(source, target)
                self._merge_results_item(meta_result, result)
        return meta_result

    def process_status(
        self, source: Status, target: Monster, meta_result: StatusEffectResult
    ) -> StatusEffectResult:
        for effect in self.effects:
            if isinstance(effect, StatusEffect):
                result = effect.apply(source, target)
                self._merge_results_status(meta_result, result)
        return meta_result

    @staticmethod
    def _merge_results_technique(
        meta_result: TechEffectResult, result: TechEffectResult
    ) -> None:
        meta_result.success |= result.success
        meta_result.damage += result.damage
        meta_result.element_multiplier += result.element_multiplier
        meta_result.should_tackle |= result.should_tackle
        meta_result.extras.extend(result.extras)

    @staticmethod
    def _merge_results_item(
        meta_result: ItemEffectResult, result: ItemEffectResult
    ) -> None:
        meta_result.success |= result.success
        meta_result.num_shakes += result.num_shakes
        meta_result.extras.extend(result.extras)

    @staticmethod
    def _merge_results_status(
        meta_result: StatusEffectResult, result: StatusEffectResult
    ) -> None:
        meta_result.success |= result.success
        meta_result.statuses.extend(result.statuses)
        meta_result.techniques.extend(result.techniques)
        meta_result.extras.extend(result.extras)


class ConditionProcessor:
    """
    Class to handle validation of conditions for objects.
    """

    def __init__(self, conditions: Sequence[PluginObject]) -> None:
        self.conditions = conditions

    def _validate_condition(
        self,
        condition: PluginObject,
        target: Union[Monster, Item, Status, Technique],
    ) -> bool:
        """
        Validate conditions dynamically based on the target's attributes.
        """
        if not isinstance(condition, CoreCondition):
            return False

        target_type = target.__class__.__name__.lower()
        test_method_name = f"test_with_{target_type}"

        try:
            test_method = getattr(condition, test_method_name)
            return condition._op == bool(test_method(target))
        except AttributeError:
            logger.error(
                f"Missing required method: {test_method_name} for {target_type}"
            )
            return False

    def validate(
        self, target: Optional[Union[Monster, Item, Status, Technique]]
    ) -> bool:
        if not self.conditions:
            return True
        if target is None:
            return False

        return all(
            self._validate_condition(condition, target)
            for condition in self.conditions
        )

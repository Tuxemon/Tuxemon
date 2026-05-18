# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tuxemon.core.core_condition import CoreCondition
from tuxemon.core.core_effect import (
    CoreEffect,
    EffectResult,
    ItemEffectResult,
    StatusEffectResult,
    TechEffectResult,
)
from tuxemon.plugin import PluginObject

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster.monster import Monster
    from tuxemon.session import Session
    from tuxemon.status.status import Status
    from tuxemon.technique.technique import Technique

logger = logging.getLogger(__name__)


@dataclass
class ConditionValidationResult:
    passed: bool
    missing_methods: list[str]
    errors: list[str]


class EffectProcessor:
    """
    Class to handle processing of effects for objects.
    """

    def __init__(self, effects: Sequence[PluginObject]) -> None:
        self.effects = effects

    def update(self, session: Session, dt: float) -> None:
        if not self.effects:
            return
        for effect in self.effects:
            if isinstance(effect, CoreEffect):
                effect.update(session, dt)
        self.prune_finished()

    def is_finished(self) -> bool:
        if not self.effects:
            return True
        for effect in self.effects:
            if isinstance(effect, CoreEffect) and not effect.is_finished():
                return False
        return True

    def prune_finished(self) -> None:
        self.effects = [
            effect
            for effect in self.effects
            if not (isinstance(effect, CoreEffect) and effect.is_finished())
        ]

    def process_globally(
        self,
        session: Session,
    ) -> EffectResult:
        meta_result = EffectResult()
        if not self.effects:
            return meta_result

        for effect in self.effects:
            if isinstance(effect, CoreEffect):
                if effect.should_run_global(session):
                    result = effect.apply_globally(session)
                    self._merge_results_global(meta_result, result)
                else:
                    logger.debug(
                        f"Global effect {effect.name} skipped by should_run()"
                    )

        return meta_result

    def process_tech(
        self,
        session: Session,
        source: Technique,
        user: Monster | None,
        target: Monster | None,
    ) -> TechEffectResult:
        meta_result = TechEffectResult(name=source.name)
        if not self.effects:
            return meta_result

        for effect in self.effects:
            if isinstance(effect, CoreEffect):
                # Technique with target
                if user and target:
                    if effect.should_run_tech(session, source, user, target):
                        result = effect.apply_tech_target(
                            session, source, user, target
                        )
                        self._merge_results_technique(meta_result, result)
                    else:
                        logger.debug(
                            f"Tech effect {effect.name} skipped by should_run()"
                        )

                # Technique without target
                elif user is None and target is None:
                    if effect.should_run_tech(session, source, None, None):
                        result = effect.apply_tech(session, source)
                        self._merge_results_technique(meta_result, result)
                    else:
                        logger.debug(
                            f"Tech effect {effect.name} (no target) skipped by should_run()"
                        )

        return meta_result

    def process_item(
        self,
        session: Session,
        source: Item,
        target: Monster | None,
    ) -> ItemEffectResult:
        meta_result = ItemEffectResult(name=source.name)
        if not self.effects:
            return meta_result

        for effect in self.effects:
            if isinstance(effect, CoreEffect):
                if target:
                    if effect.should_run_item(session, source, target, target):
                        result = effect.apply_item_target(
                            session, source, target
                        )
                        self._merge_results_item(meta_result, result)
                    else:
                        logger.debug(
                            f"Item effect {effect.name} skipped by should_run()"
                        )

                else:
                    if effect.should_run_item(session, source, None, None):
                        result = effect.apply_item(session, source)
                        self._merge_results_item(meta_result, result)
                    else:
                        logger.debug(
                            f"Item effect {effect.name} (no target) skipped by should_run()"
                        )

        return meta_result

    def process_status(
        self,
        session: Session,
        source: Status,
    ) -> StatusEffectResult:
        meta_result = StatusEffectResult(name=source.name)
        if not self.effects:
            return meta_result

        for effect in self.effects:
            if isinstance(effect, CoreEffect):
                if effect.should_run_status(session, source):
                    result = effect.apply_status(session, source)
                    self._merge_results_status(meta_result, result)
                else:
                    logger.debug(
                        f"Status effect {effect.name} skipped by should_run()"
                    )

        return meta_result

    @staticmethod
    def _merge_results_global(
        meta_result: EffectResult, result: EffectResult
    ) -> None:
        meta_result.success |= result.success

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

    def _call(
        self,
        session: Session,
        condition: CoreCondition,
        method_name: str,
        target: object,
    ) -> bool:
        method = getattr(condition, method_name, None)
        if method is None:
            logger.error(
                f"Missing required method: {method_name} in {condition}"
            )
            return False
        return condition.is_expected == bool(method(session, target))

    def _validate(
        self,
        session: Session,
        target: object,
        method_name: str,
    ) -> ConditionValidationResult:
        result = ConditionValidationResult(True, [], [])

        for cond in self.conditions:
            if not isinstance(cond, CoreCondition):
                result.passed = False
                result.errors.append("Condition is not a CoreCondition")
                continue

            method = getattr(cond, method_name, None)
            if method is None:
                result.passed = False
                result.missing_methods.append(method_name)
                continue

            try:
                ok = bool(method(session, target))
            except Exception as e:
                result.passed = False
                result.errors.append(str(e))
                continue

            if cond.is_expected != ok:
                result.passed = False

        return result

    def validate(self, session: Session) -> ConditionValidationResult:
        return self._validate(session, None, "test")

    def validate_monster(
        self, session: Session, target: Monster | None
    ) -> ConditionValidationResult:
        return self._validate(session, target, "test_with_monster")

    def validate_item(
        self, session: Session, target: Item | None
    ) -> ConditionValidationResult:
        return self._validate(session, target, "test_with_item")

    def validate_tech(
        self, session: Session, target: Technique | None
    ) -> ConditionValidationResult:
        return self._validate(session, target, "test_with_tech")

    def validate_status(
        self, session: Session, target: Status | None
    ) -> ConditionValidationResult:
        return self._validate(session, target, "test_with_status")

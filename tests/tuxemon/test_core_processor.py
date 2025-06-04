# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, Mock

from tuxemon.core.core_condition import CoreCondition
from tuxemon.core.core_effect import (
    CoreEffect,
    ItemEffectResult,
    StatusEffectResult,
    TechEffectResult,
)
from tuxemon.core.core_processor import ConditionProcessor, EffectProcessor
from tuxemon.monster import Monster
from tuxemon.session import Session


class TestEffectProcessor(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.user = Mock()
        self.target = Mock()
        self.technique = Mock()
        self.technique.name = "Fireball"

        self.tech_effect = Mock(spec=CoreEffect)
        self.tech_effect.apply_tech_target.return_value = TechEffectResult(
            name="Fireball",
            success=True,
            damage=15,
            element_multiplier=1.5,
            should_tackle=False,
            extras=["Burn"],
        )

        self.processor = EffectProcessor([self.tech_effect])

    def test_process_tech(self):
        result = self.processor.process_tech(
            self.session, self.technique, self.user, self.target
        )

        self.assertTrue(result.success)
        self.assertEqual(result.damage, 15)
        self.assertEqual(result.element_multiplier, 1.5)
        self.assertListEqual(result.extras, ["Burn"])


class TestEffectProcessorItem(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.target = Mock()
        self.item = Mock()
        self.item.name = "Potion"

        self.item_effect = Mock(spec=CoreEffect)
        self.item_effect.apply_item_target.return_value = ItemEffectResult(
            name="Potion", success=True, num_shakes=3, extras=["Healing Boost"]
        )

        self.processor = EffectProcessor([self.item_effect])

    def test_process_item(self):
        result = self.processor.process_item(
            self.session, self.item, self.target
        )

        self.assertTrue(result.success)
        self.assertEqual(result.num_shakes, 3)
        self.assertListEqual(result.extras, ["Healing Boost"])


class TestEffectProcessorStatus(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.target = Mock()
        self.status = Mock()
        self.status.name = "Poison"

        self.status_effect = Mock(spec=CoreEffect)
        self.status_effect.apply_status_target.return_value = (
            StatusEffectResult(
                name="Poison",
                success=True,
                statuses=["Poisoned"],
                techniques=["Weaken"],
                extras=["Extended Duration"],
            )
        )

        self.processor = EffectProcessor([self.status_effect])

    def test_process_status(self):
        result = self.processor.process_status(
            self.session, self.status, self.target
        )

        self.assertTrue(result.success)
        self.assertListEqual(result.statuses, ["Poisoned"])
        self.assertListEqual(result.techniques, ["Weaken"])
        self.assertListEqual(result.extras, ["Extended Duration"])


class TestConditionProcessor(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.core_condition = MagicMock(spec=CoreCondition)
        self.target_monster = MagicMock(spec=Monster)

    def test_no_conditions(self):
        processor = ConditionProcessor(conditions=[])
        self.assertTrue(processor.validate(self.session, self.target_monster))

    def test_no_target(self):
        processor = ConditionProcessor(conditions=[self.core_condition])
        self.assertFalse(processor.validate(self.session, None))

    def test_condition_passes_with_op(self):
        self.core_condition.is_expected = True
        self.core_condition.test_with_monster.return_value = True

        processor = ConditionProcessor(conditions=[self.core_condition])
        self.assertTrue(processor.validate(self.session, self.target_monster))

    def test_condition_fails_with_op(self):
        self.core_condition.is_expected = True
        self.core_condition.test_with_monster.return_value = False

        processor = ConditionProcessor(conditions=[self.core_condition])
        self.assertFalse(processor.validate(self.session, self.target_monster))

    def test_condition_passes_without_op(self):
        self.core_condition.is_expected = False
        self.core_condition.test_with_monster.return_value = False

        processor = ConditionProcessor(conditions=[self.core_condition])
        self.assertTrue(processor.validate(self.session, self.target_monster))

    def test_condition_fails_without_op(self):
        self.core_condition.is_expected = False
        self.core_condition.test_with_monster.return_value = True

        processor = ConditionProcessor(conditions=[self.core_condition])
        self.assertFalse(processor.validate(self.session, self.target_monster))

    def test_invalid_condition_type(self):
        invalid_condition = MagicMock()
        processor = ConditionProcessor(conditions=[invalid_condition])
        self.assertFalse(processor.validate(self.session, self.target_monster))

    def test_multiple_conditions_all_pass(self):
        self.core_condition.is_expected = True
        self.core_condition.test_with_monster.return_value = True

        another_condition = MagicMock(spec=CoreCondition)
        another_condition.is_expected = True
        another_condition.test_with_monster.return_value = True

        processor = ConditionProcessor(
            conditions=[self.core_condition, another_condition]
        )
        self.assertTrue(processor.validate(self.session, self.target_monster))

    def test_multiple_conditions_one_fails(self):
        self.core_condition.is_expected = True
        self.core_condition.test_with_monster.return_value = True

        another_condition = MagicMock(spec=CoreCondition)
        another_condition.is_expected = True
        another_condition.test_with_monster.return_value = False

        processor = ConditionProcessor(
            conditions=[self.core_condition, another_condition]
        )
        self.assertFalse(processor.validate(self.session, self.target_monster))

    def test_method_invocation_count(self):
        self.core_condition.is_expected = True
        self.core_condition.test_with_monster.return_value = True
        processor = ConditionProcessor(conditions=[self.core_condition])
        processor.validate(self.session, self.target_monster)
        self.core_condition.test_with_monster.assert_called_once_with(
            self.session, self.target_monster
        )

    def test_empty_conditions_with_none_target(self):
        processor = ConditionProcessor(conditions=[])
        self.assertTrue(processor.validate(self.session, None))

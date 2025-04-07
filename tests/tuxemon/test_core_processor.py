# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, Mock

from tuxemon.core.core_processor import ConditionProcessor, EffectProcessor
from tuxemon.item.item import Item
from tuxemon.item.itemcondition import ItemCondition
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult
from tuxemon.monster import Monster
from tuxemon.status.status import Status
from tuxemon.status.statuscondition import StatusCondition
from tuxemon.status.statuseffect import StatusEffect, StatusEffectResult
from tuxemon.technique.techcondition import TechCondition
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class TestEffectProcessor(unittest.TestCase):
    def setUp(self):
        self.user = Mock(spec=Monster)
        self.target = Mock(spec=Monster)

        self.technique = Mock(spec=Technique)
        self.technique.name = ""
        self.item = Mock(spec=Item)
        self.item.name = ""
        self.status = Mock(spec=Status)
        self.status.name = ""

        self.tech_effect = Mock(spec=TechEffect)
        self.item_effect = Mock(spec=ItemEffect)
        self.status_effect = Mock(spec=StatusEffect)

        self.effects = [self.tech_effect, self.item_effect, self.status_effect]
        self.processor = EffectProcessor(self.effects)

    def test_process_tech(self):
        self.tech_effect.apply.return_value = TechEffectResult(
            name="Technique",
            success=True,
            damage=10,
            element_multiplier=1.2,
            should_tackle=False,
            extras=["Critical"],
        )

        meta_result = TechEffectResult(
            name=self.technique.name,
            success=False,
            damage=0,
            element_multiplier=0.0,
            should_tackle=False,
            extras=[],
        )

        final_result = self.processor.process_tech(
            source=self.technique,
            user=self.user,
            target=self.target,
            meta_result=meta_result,
        )

        self.assertTrue(final_result.success)
        self.assertEqual(final_result.damage, 10)
        self.assertEqual(final_result.element_multiplier, 1.2)
        self.assertListEqual(final_result.extras, ["Critical"])

    def test_process_item(self):
        self.item_effect.apply.return_value = ItemEffectResult(
            name="Healing Item",
            success=True,
            num_shakes=2,
            extras=["Heal Boost"],
        )

        meta_result = ItemEffectResult(
            name=self.item.name, success=False, num_shakes=0, extras=[]
        )

        final_result = self.processor.process_item(
            source=self.item, target=self.target, meta_result=meta_result
        )

        self.assertTrue(final_result.success)
        self.assertEqual(final_result.num_shakes, 2)
        self.assertListEqual(final_result.extras, ["Heal Boost"])

    def test_process_status(self):
        self.status_effect.apply.return_value = StatusEffectResult(
            name="Poison Status",
            success=True,
            statuses=["Poison"],
            techniques=["Weaken"],
            extras=["Duration Boost"],
        )

        meta_result = StatusEffectResult(
            name=self.status.name,
            success=False,
            statuses=[],
            techniques=[],
            extras=[],
        )

        final_result = self.processor.process_status(
            source=self.status, target=self.target, meta_result=meta_result
        )

        self.assertTrue(final_result.success)
        self.assertListEqual(final_result.statuses, ["Poison"])
        self.assertListEqual(final_result.techniques, ["Weaken"])
        self.assertListEqual(final_result.extras, ["Duration Boost"])


class TestConditionProcessor(unittest.TestCase):
    def setUp(self):
        self.status_condition = MagicMock(spec=StatusCondition)
        self.tech_condition = MagicMock(spec=TechCondition)
        self.item_condition = MagicMock(spec=ItemCondition)
        self.target_monster = MagicMock(spec=Monster)

    def test_no_conditions(self):
        processor = ConditionProcessor(conditions=[])
        self.assertTrue(processor.validate(self.target_monster))

    def test_no_target(self):
        processor = ConditionProcessor(conditions=[self.status_condition])
        self.assertFalse(processor.validate(None))

    def test_condition_passes_with_op(self):
        self.status_condition._op = True
        self.status_condition.test.return_value = True

        processor = ConditionProcessor(conditions=[self.status_condition])
        self.assertTrue(processor.validate(self.target_monster))

    def test_condition_fails_with_op(self):
        self.status_condition._op = True
        self.status_condition.test.return_value = False

        processor = ConditionProcessor(conditions=[self.status_condition])
        self.assertFalse(processor.validate(self.target_monster))

    def test_condition_passes_without_op(self):
        self.status_condition._op = False
        self.status_condition.test.return_value = False

        processor = ConditionProcessor(conditions=[self.status_condition])
        self.assertTrue(processor.validate(self.target_monster))

    def test_condition_fails_without_op(self):
        self.status_condition._op = False
        self.status_condition.test.return_value = True

        processor = ConditionProcessor(conditions=[self.status_condition])
        self.assertFalse(processor.validate(self.target_monster))

    def test_multiple_conditions_all_pass(self):
        self.status_condition._op = True
        self.status_condition.test.return_value = True
        self.tech_condition._op = False
        self.tech_condition.test.return_value = False

        processor = ConditionProcessor(
            conditions=[self.status_condition, self.tech_condition]
        )
        self.assertTrue(processor.validate(self.target_monster))

    def test_multiple_conditions_one_fails(self):
        self.status_condition._op = True
        self.status_condition.test.return_value = True
        self.tech_condition._op = False
        self.tech_condition.test.return_value = True

        processor = ConditionProcessor(
            conditions=[self.status_condition, self.tech_condition]
        )
        self.assertFalse(processor.validate(self.target_monster))

    def test_invalid_condition_type(self):
        invalid_condition = MagicMock()
        processor = ConditionProcessor(conditions=[invalid_condition])
        self.assertFalse(processor.validate(self.target_monster))

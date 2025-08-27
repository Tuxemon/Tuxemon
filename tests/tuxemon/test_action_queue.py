# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock, call

from tuxemon.combat.action_queue import EnqueuedAction
from tuxemon.combat.sort_manager import SortManager
from tuxemon.monster import Monster
from tuxemon.technique.technique import Technique


class TestGetActionSortKey(unittest.TestCase):
    def setUp(self):
        self.monster = MagicMock(spec=Monster)
        self.monster.speed = 10.0
        self.monster.dodge = 5.0
        self.tech = MagicMock(spec=Technique)
        self.tech.speed = 0
        self.tech.sort = "damage"

    def test_none_method(self):
        action = EnqueuedAction(user=None, method=None, target=self.monster)
        self.assertEqual(SortManager.get_action_sort_key(action), (0, 0))

    def test_none_user(self):
        action = EnqueuedAction(
            user=None, method=self.tech, target=self.monster
        )
        self.assertEqual(SortManager.get_action_sort_key(action), (0, 0))

    def test_meta_action(self):
        self.tech.sort = "meta"
        action = EnqueuedAction(
            user=self.monster, method=self.tech, target=self.monster
        )
        self.assertEqual(
            SortManager.get_action_sort_key(action),
            (SortManager.SORT_ORDER.index("meta"), 0),
        )

    def test_potion_action(self):
        self.tech.sort = "potion"
        action = EnqueuedAction(
            user=self.monster, method=self.tech, target=self.monster
        )
        self.assertEqual(
            SortManager.get_action_sort_key(action),
            (SortManager.SORT_ORDER.index("potion"), 0),
        )

    def test_potion_action_with_none_user(self):
        self.tech.sort = "potion"
        action = EnqueuedAction(
            user=None, method=self.tech, target=self.monster
        )
        self.assertEqual(SortManager.get_action_sort_key(action), (0, 0))

    def test_damage_action(self):
        self.tech.sort = "damage"
        action = EnqueuedAction(
            user=self.monster, method=self.tech, target=self.monster
        )
        self.assertGreaterEqual(
            SortManager.get_action_sort_key(action),
            (SortManager.SORT_ORDER.index("potion"), 0),
        )

    def test_get_sort_index(self):
        self.assertEqual(SortManager.get_sort_index("potion"), 0)
        self.assertEqual(SortManager.get_sort_index("utility"), 1)
        self.assertEqual(SortManager.get_sort_index("quest"), 2)
        self.assertEqual(SortManager.get_sort_index("meta"), 3)
        self.assertEqual(SortManager.get_sort_index("damage"), 4)
        self.assertEqual(SortManager.get_sort_index("unknown"), 5)

        class TestSortManager(SortManager):
            SORT_ORDER = []

        self.assertEqual(TestSortManager.get_sort_index("unknown"), 0)

    def test_get_sort_index_empty_string(self):
        self.assertEqual(
            SortManager.get_sort_index(""), len(SortManager.SORT_ORDER)
        )

    def test_get_sort_index_whitespace_string(self):
        self.assertEqual(
            SortManager.get_sort_index("   "), len(SortManager.SORT_ORDER)
        )


class TestActionQueue(unittest.TestCase):
    def setUp(self):
        self.queue = MagicMock()
        self.monster1 = MagicMock(name="Monster1", current_hp=100)
        self.monster2 = MagicMock(name="Monster2", current_hp=100)
        self.tech1 = MagicMock(name="Technique1")
        self.item1 = MagicMock(name="Item1")
        self.condition1 = MagicMock(name="Condition1")
        self.action1 = MagicMock(
            user=self.monster1, method=self.tech1, target=self.monster2
        )
        self.action2 = MagicMock(
            user=self.monster2, method=self.item1, target=self.monster1
        )
        self.action3 = MagicMock(
            user=self.monster1, method=self.condition1, target=self.monster2
        )
        self.npc1 = MagicMock(name="NPC1")

    def test_enqueue(self):
        self.queue.enqueue(self.action1, 1)
        self.queue.enqueue.assert_called_once_with(self.action1, 1)

    def test_dequeue(self):
        self.queue.dequeue(self.action1)
        self.queue.dequeue.assert_called_once_with(self.action1)

    def test_pop(self):
        self.queue.pop()
        self.queue.pop.assert_called_once()

    def test_is_empty(self):
        self.queue.is_empty()
        self.queue.is_empty.assert_called_once()

    def test_clear_queue(self):
        self.queue.clear_queue()
        self.queue.clear_queue.assert_called_once()

    def test_clear_history(self):
        self.queue.clear_history()
        self.queue.clear_history.assert_called_once()

    def test_clear_pending(self):
        self.queue.clear_pending()
        self.queue.clear_pending.assert_called_once()

    def test_sort(self):
        self.queue.sort()
        self.queue.sort.assert_called_once()

    def test_swap(self):
        self.queue.swap(self.monster2, self.monster1)
        self.queue.swap.assert_called_once_with(self.monster2, self.monster1)

    def test_rewrite(self):
        self.queue.rewrite(self.monster1, self.tech1)
        self.queue.rewrite.assert_called_once_with(self.monster1, self.tech1)

    def test_get_last_action_user(self):
        self.queue.get_last_action(2, self.monster2, "user")
        self.queue.get_last_action.assert_called_once_with(
            2, self.monster2, "user"
        )

    def test_get_last_action_target(self):
        self.queue.get_last_action(1, self.monster2, "target")
        self.queue.get_last_action.assert_called_once_with(
            1, self.monster2, "target"
        )

    def test_get_all_actions_by_turn(self):
        self.queue.get_all_actions_by_turn(1)
        self.queue.get_all_actions_by_turn.assert_called_once_with(1)

    def test_add_pending(self):
        self.queue.add_pending(self.action1, 1)
        self.queue.add_pending.assert_called_once_with(self.action1, 1)

    def test_add_pending_multiple(self):
        self.queue.add_pending(self.action1, 1)
        self.queue.add_pending(self.action2, 2)
        self.assertEqual(
            self.queue.add_pending.call_args_list,
            [call(self.action1, 1), call(self.action2, 2)],
        )

    def test_autoclean_pending(self):
        self.queue.autoclean_pending()
        self.queue.autoclean_pending.assert_called_once()

    def test_from_pending_to_action(self):
        self.queue.from_pending_to_action(1)
        self.queue.from_pending_to_action.assert_called_once_with(1)

    def test_from_pending_to_action_multiple(self):
        self.queue.from_pending_to_action(1)
        self.queue.from_pending_to_action.assert_called_once_with(1)

    def test_sort_with_different_methods(self):
        self.queue.sort()
        self.queue.sort.assert_called_once()

    def test_swap_no_match(self):
        self.queue.swap(MagicMock(), MagicMock())
        self.queue.swap.assert_called_once()

    def test_rewrite_no_match(self):
        self.queue.rewrite(MagicMock(), MagicMock())
        self.queue.rewrite.assert_called_once()


class TestActionHistory(unittest.TestCase):
    def setUp(self):
        self.history = MagicMock()
        self.monster1 = MagicMock(name="Monster1")
        self.monster2 = MagicMock(name="Monster2")
        self.tech1 = MagicMock(name="Technique1")
        self.action1 = MagicMock(
            user=self.monster1, method=self.tech1, target=self.monster2
        )
        self.action2 = MagicMock(
            user=self.monster2,
            method=MagicMock(name="Item1"),
            target=self.monster1,
        )
        self.action3 = MagicMock(
            user=self.monster1,
            method=MagicMock(name="Condition1"),
            target=self.monster2,
        )

    def test_add_action(self):
        self.history.add_action(1, self.action1)
        self.history.add_action.assert_called_once_with(1, self.action1)

    def test_get_actions_by_turn(self):
        self.history.get_actions_by_turn.return_value = [
            self.action1,
            self.action3,
        ]
        self.history.get_actions_by_turn(1)
        self.history.get_actions_by_turn.assert_called_once_with(1)

    def test_clear(self):
        self.history.clear()
        self.history.clear.assert_called_once()

    def test_get_actions_by_turn_range(self):
        self.history.get_actions_by_turn_range.return_value = [
            self.action1,
            self.action2,
        ]
        self.history.get_actions_by_turn_range(1, 2)
        self.history.get_actions_by_turn_range.assert_called_once_with(1, 2)

    def test_count_actions(self):
        self.history.count_actions.return_value = 3
        count = self.history.count_actions()
        self.assertEqual(count, 3)
        self.history.count_actions.assert_called_once()

    def test_get_last_action(self):
        self.history.get_last_action.return_value = self.action3
        last_action = self.history.get_last_action()
        self.assertEqual(last_action, self.action3)
        self.history.get_last_action.assert_called_once()

    def test_get_last_action_empty(self):
        self.history.get_last_action.return_value = None
        last_action = self.history.get_last_action()
        self.assertIsNone(last_action)
        self.history.get_last_action.assert_called_once()

    def test_repr(self):
        expected_repr = f"ActionHistory(count=3, sample=[(1, {self.action1}), (2, {self.action2}), (3, {self.action3})])"
        self.history.__repr__ = MagicMock(return_value=expected_repr)
        repr_str = repr(self.history)
        self.assertEqual(repr_str, expected_repr)

    def test_repr_less_than_3(self):
        expected_repr = f"ActionHistory(count=2, sample=[(1, {self.action1}), (2, {self.action2})])"
        self.history.__repr__ = MagicMock(return_value=expected_repr)
        repr_str = repr(self.history)
        self.assertEqual(repr_str, expected_repr)

    def test_repr_empty(self):
        expected_repr = "ActionHistory(count=0, sample=[])"
        self.history.__repr__ = MagicMock(return_value=expected_repr)
        repr_str = repr(self.history)
        self.assertEqual(repr_str, expected_repr)

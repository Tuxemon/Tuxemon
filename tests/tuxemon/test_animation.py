# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from collections.abc import Callable
from unittest.mock import Mock, call

import pygame

from tuxemon.animation import Task

DEFAULT_INTERVAL = 1.0


class TestAnimation(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_callback = Mock(spec=Callable)
        self.other_mock_callback = Mock(spec=Callable)

    def test_task_run_callback_after_interval(self):
        task = Task(self.mock_callback, DEFAULT_INTERVAL)

        task.update(0.5)
        self.mock_callback.assert_not_called()

        task.update(0.5)
        self.mock_callback.assert_called()

    def test_raise_value_error_when_times_is_0(self):
        times = 0
        with self.assertRaises(ValueError):
            Task(self.mock_callback, DEFAULT_INTERVAL, times)

    def test_raise_value_error_when_callback_is_not_callable(self):
        with self.assertRaises(ValueError):
            Task("not callable", DEFAULT_INTERVAL)

    def test_task_run_callback_immediately_when_no_interval(self):
        task = Task(self.mock_callback, 0)

        task.update(0)

        self.mock_callback.assert_called()

    def test_task_run_callback_twice_when_times_is_2(self):
        times = 2
        task = Task(self.mock_callback, DEFAULT_INTERVAL, times)

        task.update(DEFAULT_INTERVAL)
        task.update(DEFAULT_INTERVAL)

        self.mock_callback.assert_has_calls([call(), call()])

    def test_raise_runtime_error_when_calling_update_after_task_finished(self):
        task = Task(self.mock_callback, DEFAULT_INTERVAL)

        task.update(DEFAULT_INTERVAL)
        with self.assertRaises(RuntimeError):
            task.update(DEFAULT_INTERVAL)

    def test_add_chained_callback_to_group_when_original_task_finished(self):
        task = Task(self.mock_callback, DEFAULT_INTERVAL)
        task.chain(self.other_mock_callback, DEFAULT_INTERVAL)
        task_group = pygame.sprite.Group()
        task_group.add(task)

        task_group.update(DEFAULT_INTERVAL)
        self.mock_callback.assert_called()
        self.other_mock_callback.assert_not_called()

        task_group.update(DEFAULT_INTERVAL)
        self.other_mock_callback.assert_called()

    def test_is_finish_return_true_when_task_finished(self):
        task = Task(self.mock_callback, DEFAULT_INTERVAL)

        task.update(DEFAULT_INTERVAL)
        self.assertTrue(task.is_finish())

    def test_is_finish_return_false_when_task_in_progress(self):
        task = Task(self.mock_callback, DEFAULT_INTERVAL)

        task.update(0.5)
        self.assertFalse(task.is_finish())

    def test_reset_delay_when_new_delay_is_greater_than_interval(self):
        task = Task(self.mock_callback, DEFAULT_INTERVAL)
        greater_delay = DEFAULT_INTERVAL * 2

        task.reset_delay(greater_delay)

        self.assertEqual(greater_delay, task._interval)

    def test_reset_delay_when_new_delay_is_greater_than_time_left(self):
        task = Task(self.mock_callback, DEFAULT_INTERVAL)
        same_delay = DEFAULT_INTERVAL
        task.update(0.5)  # Time left is decreasing

        task.reset_delay(same_delay)

        self.assertEqual(same_delay, task._interval)

    def test_dont_change_delay_when_new_delay_is_lower_than_time_left(self):
        task = Task(self.mock_callback, DEFAULT_INTERVAL)
        lower_delay = DEFAULT_INTERVAL / 2

        task.reset_delay(lower_delay)

        self.assertEqual(DEFAULT_INTERVAL, task._interval)

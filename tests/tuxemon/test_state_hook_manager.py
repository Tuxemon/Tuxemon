# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import MagicMock

from tuxemon.state import HookManager, State, StateManager, StateRepository


class TestHookManager(unittest.TestCase):
    def setUp(self):
        self.hook_manager = HookManager()
        self.mock_callback = MagicMock()
        self.mock_callback1 = MagicMock()
        self.mock_callback2 = MagicMock()

    def test_register_hook(self):
        self.hook_manager.register_hook(
            "test_hook", self.mock_callback, priority=10
        )
        self.assertIn("test_hook", self.hook_manager._hooks)
        self.assertEqual(
            self.hook_manager._hooks["test_hook"], [(10, self.mock_callback)]
        )

    def test_unregister_hook(self):
        self.hook_manager.register_hook(
            "test_hook", self.mock_callback, priority=10
        )
        self.hook_manager.unregister_hook("test_hook", self.mock_callback)
        self.assertNotIn("test_hook", self.hook_manager._hooks)

    def test_unregister_hook_with_priority(self):
        self.hook_manager.register_hook(
            "test_hook", self.mock_callback, priority=10
        )
        self.hook_manager.register_hook(
            "test_hook", self.mock_callback, priority=5
        )
        self.hook_manager.unregister_hook(
            "test_hook", self.mock_callback, priority=10
        )
        self.assertIn("test_hook", self.hook_manager._hooks)
        self.assertEqual(
            self.hook_manager._hooks["test_hook"], [(5, self.mock_callback)]
        )

    def test_trigger_hook(self):
        self.hook_manager.register_hook(
            "test_hook", self.mock_callback, priority=10
        )
        self.hook_manager.trigger_hook("test_hook", "arg1", kwarg1="value1")
        self.mock_callback.assert_called_once_with("arg1", kwarg1="value1")

    def test_reset_hooks(self):
        self.hook_manager.register_hook(
            "test_hook", self.mock_callback, priority=10
        )
        self.assertTrue(self.hook_manager._hooks)
        self.hook_manager.reset_hooks()
        self.assertFalse(self.hook_manager._hooks)

    def test_unregister_nonexistent_hook(self):
        with self.assertRaises(ValueError):
            self.hook_manager.unregister_hook(
                "nonexistent_hook", self.mock_callback
            )

    def test_trigger_nonexistent_hook(self):
        with self.assertRaises(ValueError):
            self.hook_manager.trigger_hook("nonexistent_hook")


class TestStateManagerHooks(unittest.TestCase):

    def setUp(self):
        self.manager = StateManager("test", HookManager(), StateRepository())
        self.mock_callback = MagicMock()
        self.mock_callback1 = MagicMock()
        self.mock_callback2 = MagicMock()

    def test_global_hooks(self):
        self.manager.register_global_hook(
            "pre_state_update", self.mock_callback
        )
        self.manager.update(0.1)
        self.mock_callback.assert_called_once_with(0.1)
        self.mock_callback.reset_mock()

        self.manager.register_global_hook(
            "post_state_update", self.mock_callback
        )
        self.manager.update(0.1)
        self.mock_callback.assert_called()
        self.mock_callback.reset_mock()

        self.manager.unregister_global_hook(
            "pre_state_update", self.mock_callback
        )
        self.manager.update(0.1)
        self.mock_callback.assert_called_once_with(0.1)

    def test_global_hooks_multiple_callbacks(self):
        self.manager.register_global_hook(
            "pre_state_update", self.mock_callback1
        )
        self.manager.register_global_hook(
            "pre_state_update", self.mock_callback2
        )
        self.manager.update(0.1)

        self.mock_callback1.assert_called_once_with(0.1)
        self.mock_callback2.assert_called_once_with(0.1)

    def test_global_hooks_unregister_nonexistent(self):
        self.manager.hook_manager.reset_hooks()
        with self.assertRaises(ValueError):
            self.manager.unregister_global_hook(
                "pre_state_update", self.mock_callback
            )

    def test_reset_hooks(self):
        self.manager.register_global_hook(
            "test_hook", self.mock_callback, priority=10
        )
        self.assertTrue(self.manager.hook_manager._hooks)

        self.manager.hook_manager.reset_hooks()
        self.assertFalse(self.manager.hook_manager._hooks)

    def test_global_hooks_unregister_correct_callback(self):
        self.manager.register_global_hook(
            "pre_state_update", self.mock_callback1
        )
        self.manager.register_global_hook(
            "pre_state_update", self.mock_callback2
        )
        self.manager.unregister_global_hook(
            "pre_state_update", self.mock_callback1
        )
        self.manager.update(0.1)
        self.mock_callback1.assert_not_called()
        self.mock_callback2.assert_called_once()


class TestStateHooks(unittest.TestCase):

    def setUp(self):
        self.state = State()
        self.state.client = MagicMock()
        self.state.client.hook_manager = HookManager()
        self.mock_callback = MagicMock()
        self.mock_surface = MagicMock()
        self.mock_callback1 = MagicMock()
        self.mock_callback2 = MagicMock()

        self.state.client.hook_manager.register_hook(
            "state_update", lambda time_delta: None
        )
        self.state.client.hook_manager.register_hook(
            "state_draw", lambda surface: None
        )
        self.state.client.hook_manager.register_hook(
            "state_resume", lambda: None
        )
        self.state.client.hook_manager.register_hook(
            "state_pause", lambda: None
        )
        self.state.client.hook_manager.register_hook(
            "state_shutdown", lambda: None
        )

    def test_state_hooks(self):
        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback
        )
        self.state.update(0.1)
        self.mock_callback.assert_called_once_with(0.1)
        self.mock_callback.reset_mock()

        self.state.client.hook_manager.register_hook(
            "state_draw", self.mock_callback
        )
        self.state.draw(self.mock_surface)
        self.mock_callback.assert_called_once_with(self.mock_surface)
        self.mock_callback.reset_mock()

        self.state.client.hook_manager.register_hook(
            "state_resume", self.mock_callback
        )
        self.state.resume()
        self.mock_callback.assert_called_once()
        self.mock_callback.reset_mock()

        self.state.client.hook_manager.register_hook(
            "state_pause", self.mock_callback
        )
        self.state.pause()
        self.mock_callback.assert_called_once()
        self.mock_callback.reset_mock()

        self.state.client.hook_manager.register_hook(
            "state_shutdown", self.mock_callback
        )
        self.state.shutdown()
        self.mock_callback.assert_called_once()
        self.mock_callback.reset_mock()

        self.state.client.hook_manager.unregister_hook(
            "state_update", self.mock_callback
        )
        self.state.update(0.1)
        self.mock_callback.assert_not_called()

    def test_state_hooks_multiple_callbacks(self):
        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback1
        )
        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback2
        )
        self.state.update(0.1)

        self.mock_callback1.assert_called_once_with(0.1)
        self.mock_callback2.assert_called_once_with(0.1)

    def test_state_hooks_unregister_nonexistent(self):
        self.state.client.hook_manager.unregister_hook(
            "state_update", self.mock_callback
        )

    def test_state_hooks_unregister_correct_callback(self):
        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback1
        )
        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback2
        )
        self.state.client.hook_manager.unregister_hook(
            "state_update", self.mock_callback1
        )
        self.state.update(0.1)
        self.mock_callback1.assert_not_called()
        self.mock_callback2.assert_called_once()

    def test_state_hooks_with_priorities(self):
        self.state.replace_hooks(
            "state_update",
            [(10, self.mock_callback1), (5, self.mock_callback2)],
        )

        self.state.update(0.1)
        self.mock_callback1.assert_called_once_with(0.1)
        self.mock_callback2.assert_called_once_with(0.1)

        hooks = self.state.client.hook_manager._hooks["state_update"]
        expected = [(10, self.mock_callback1), (5, self.mock_callback2)]
        self.assertEqual(hooks, expected)

    def test_trigger_unregistered_hook(self):
        self.assertFalse(
            self.state.client.hook_manager.is_hook_registered(
                "unregistered_hook"
            )
        )

    def test_dynamic_hook_creation(self):
        self.state.client.hook_manager.register_hook(
            "dynamic_hook", self.mock_callback
        )
        self.state.client.hook_manager.trigger_hook("dynamic_hook", "test_arg")

        self.mock_callback.assert_called_once_with("test_arg")

    def test_hook_execution_timing(self):
        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback
        )
        self.state.client.hook_manager.register_hook(
            "state_pause", self.mock_callback2
        )

        self.state.update(0.1)
        self.mock_callback.assert_called_once_with(0.1)

        self.state.pause()
        self.mock_callback2.assert_called_once()
        self.mock_callback.assert_called_once()

    def test_reset_hooks(self):
        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback1
        )
        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback2
        )
        self.state.client.hook_manager.reset_hooks()
        self.assertFalse(
            self.state.client.hook_manager.is_hook_registered("state_update")
        )
        self.state.trigger_hook("state_update", 0.1)

    def test_invalid_hook_arguments(self):
        with self.assertRaises(ValueError):
            self.state.client.hook_manager.register_hook(
                "", self.mock_callback
            )

        with self.assertRaises(ValueError):
            self.state.client.hook_manager.register_hook("state_update", None)

    def test_multiple_states_interacting(self):
        state2 = State()
        state2.client = MagicMock()
        state2.client.hook_manager = HookManager()
        state2.client.hook_manager.register_hook(
            "state_update", self.mock_callback2
        )

        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback1
        )

        self.state.update(0.1)
        state2.update(0.2)

        self.mock_callback1.assert_called_once_with(0.1)
        self.mock_callback2.assert_called_once_with(0.2)

    def test_concurrent_hooks(self):
        self.state.client.hook_manager.register_hook(
            "state_draw", self.mock_callback1
        )
        self.state.client.hook_manager.register_hook(
            "state_update", self.mock_callback2
        )

        self.state.draw(self.mock_surface)
        self.state.update(0.1)

        self.mock_callback1.assert_called_once_with(self.mock_surface)
        self.mock_callback2.assert_called_once_with(0.1)

    def test_error_handling_in_hooks(self):
        def error_callback(*args, **kwargs):
            raise RuntimeError("Error in callback")

        self.state.client.hook_manager.register_hook(
            "state_update", error_callback
        )

        with self.assertRaises(RuntimeError):
            self.state.update(0.1)

    def test_hook_persistence_across_lifecycle(self):
        self.state.client.hook_manager.register_hook(
            "state_resume", self.mock_callback
        )
        self.state.client.hook_manager.register_hook(
            "state_pause", self.mock_callback2
        )

        self.state.resume()
        self.mock_callback.assert_called_once()

        self.state.pause()
        self.mock_callback2.assert_called_once()

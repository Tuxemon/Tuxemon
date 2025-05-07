# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import unittest
from unittest.mock import Mock

from tuxemon.state import StateRepository


class TestStateRepository(unittest.TestCase):
    def setUp(self):
        self.state_repository = StateRepository()
        self.mock_state1 = Mock()
        self.mock_state1.__name__ = "State1"
        self.mock_state2 = Mock()
        self.mock_state2.__name__ = "State2"

    def test_add_state(self):
        self.state_repository.add_state(self.mock_state1)
        self.assertIn("State1", self.state_repository._state_dict)
        self.assertEqual(
            self.state_repository._state_dict["State1"], self.mock_state1
        )

    def test_add_duplicate_state_strict(self):
        self.state_repository.add_state(self.mock_state1)
        with self.assertRaises(ValueError):
            self.state_repository.add_state(self.mock_state1, True)

    def test_add_duplicate_state_no_strict(self):
        self.state_repository.add_state(self.mock_state1)
        self.state_repository.add_state(self.mock_state1, False)

    def test_get_state(self):
        self.state_repository.add_state(self.mock_state1)
        retrieved_state = self.state_repository.get_state("State1")
        self.assertEqual(retrieved_state, self.mock_state1)

    def test_get_nonexistent_state(self):
        with self.assertRaises(ValueError):
            self.state_repository.get_state("NonexistentState")

    def test_all_states(self):
        self.state_repository.add_state(self.mock_state1)
        self.state_repository.add_state(self.mock_state2)
        states = self.state_repository.all_states()
        self.assertEqual(len(states), 2)
        self.assertIn("State1", states)
        self.assertIn("State2", states)

    def test_add_multiple_states(self):
        self.state_repository.add_state(self.mock_state1)
        self.state_repository.add_state(self.mock_state2)
        self.assertIn("State1", self.state_repository._state_dict)
        self.assertIn("State2", self.state_repository._state_dict)

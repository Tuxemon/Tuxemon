# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import random
import unittest
from unittest.mock import MagicMock, patch

from tuxemon.formula import (
    CaptureDeviceConfig,
    CaptureDevicesConfig,
    Loader,
    calculate_capdev_modifier,
    calculate_status_modifier,
    capture,
    config_capdev,
    shake_check,
)
from tuxemon.monster import Monster


class TestShakeCheck(unittest.TestCase):

    @patch("random.uniform")
    def test_shake_check_basic(self, mock_uniform):
        target = MagicMock(spec=Monster)
        target.hp = 100
        target.current_hp = 50
        target.catch_rate = 100
        target.lower_catch_resistance = 0.9
        target.upper_catch_resistance = 1.1
        mock_uniform.return_value = 1.0
        status_modifier = 1.0
        tuxeball_modifier = 1.0
        result = shake_check(target, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    @patch("random.uniform")
    def test_shake_check_different_values(self, mock_uniform):
        mock_uniform.return_value = 0.5
        target = MagicMock(spec=Monster)
        target.hp = 150
        target.current_hp = 25
        target.catch_rate = 200
        target.lower_catch_resistance = 0.8
        target.upper_catch_resistance = 1.2
        status_modifier = 1.5
        tuxeball_modifier = 2.0
        result = shake_check(target, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)

    @patch("random.uniform")
    def test_shake_check_edge_cases(self, mock_uniform):
        mock_uniform.return_value = 1.0
        target = MagicMock(spec=Monster)
        target.hp = 100
        target.current_hp = 50
        target.catch_rate = 100
        target.lower_catch_resistance = 0.9
        target.upper_catch_resistance = 1.1
        status_modifier = 1.0
        tuxeball_modifier = 1.0
        result = shake_check(target, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)

        target2 = MagicMock(spec=Monster)
        target2.hp = 1000
        target2.current_hp = 1
        target2.catch_rate = 255
        target2.lower_catch_resistance = 1.0
        target2.upper_catch_resistance = 1.0
        result = shake_check(target2, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)

    @patch("random.uniform")
    def test_shake_check_zero_hp(self, mock_uniform):
        mock_uniform.return_value = 1.0
        target = MagicMock(spec=Monster)
        target.hp = 100
        target.current_hp = 0
        target.catch_rate = 100
        target.lower_catch_resistance = 1.0
        target.upper_catch_resistance = 1.0
        status_modifier = 1.0
        tuxeball_modifier = 1.0
        result = shake_check(target, status_modifier, tuxeball_modifier)
        self.assertIsInstance(result, float)


class TestCapture(unittest.TestCase):
    def setUp(self):
        config_capture = Loader.get_config_capture("config_capture.yaml")
        self.max_shake_rate = config_capture.shake_divisor
        self.total_shake = config_capture.total_shakes

    @patch("random.randint")
    def test_capture_success(self, mock_randint):
        mock_randint.return_value = self.max_shake_rate // 2
        shake_check = self.max_shake_rate
        captured, shakes = capture(shake_check)
        self.assertTrue(captured)
        self.assertEqual(shakes, self.total_shake)

    @patch("random.randint")
    def test_capture_failure_first_shake(self, mock_randint):
        mock_randint.return_value = self.max_shake_rate
        shake_check = 0
        captured, shakes = capture(shake_check)
        self.assertFalse(captured)
        self.assertEqual(shakes, 1)

    @patch("random.randint")
    def test_capture_failure_middle_shake(self, mock_randint):
        mock_randint.side_effect = [
            self.max_shake_rate // 4,
            self.max_shake_rate // 4,
            self.max_shake_rate,
        ]
        shake_check = self.max_shake_rate // 4
        captured, shakes = capture(shake_check)
        self.assertFalse(captured)
        self.assertEqual(shakes, 3)

    @patch("random.randint")
    def test_capture_failure_last_shake(self, mock_randint):
        mock_randint.side_effect = [
            self.max_shake_rate // 4,
            self.max_shake_rate // 4,
            self.max_shake_rate // 4,
            self.max_shake_rate,
        ]
        shake_check = self.max_shake_rate // 4
        captured, shakes = capture(shake_check)
        self.assertFalse(captured)
        self.assertEqual(shakes, self.total_shake)

    @patch("random.randint")
    def test_capture_edge_case_shake_check_zero(self, mock_randint):
        mock_randint.return_value = self.max_shake_rate // 2
        shake_check = 0
        captured, shakes = capture(shake_check)
        self.assertFalse(captured)
        self.assertEqual(shakes, 1)

    @patch("random.randint")
    def test_capture_edge_case_shake_check_max(self, mock_randint):
        mock_randint.return_value = self.max_shake_rate // 2
        shake_check = self.max_shake_rate
        captured, shakes = capture(shake_check)
        self.assertTrue(captured)
        self.assertEqual(shakes, self.total_shake)


class TestCalculateStatusModifier(unittest.TestCase):
    def setUp(self):
        self.item = MagicMock(slug="example")
        self.target = MagicMock()

    def test_no_config_or_status(self):
        self.target.status = None
        result = calculate_status_modifier(self.item, self.target)
        self.assertEqual(result, 1.0)

    def test_no_target_status(self):
        self.target.status = None
        result = calculate_status_modifier(self.item, self.target)
        self.assertEqual(result, 1.0)

    def test_negative_category_modifier_applied(self):
        self.target.status = [MagicMock(slug="unknown", category="negative")]
        result = calculate_status_modifier(self.item, self.target)
        self.assertEqual(result, 1.2)

    def test_positive_category_modifier_applied(self):
        self.target.status = [MagicMock(slug="unknown", category="positive")]
        result = calculate_status_modifier(self.item, self.target)
        self.assertEqual(result, 1.0)

    def test_multiple_status_modifiers(self):
        self.target.status = [
            MagicMock(slug="unknown", category="negative"),
            MagicMock(slug="name_status", category="positive"),
        ]
        result = calculate_status_modifier(self.item, self.target)
        expected = 0.8 * 1.2
        self.assertEqual(result, expected)

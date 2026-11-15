# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import Mock, patch

import pytest

from tuxemon.platform.joystick_detector import JoystickDetector


@pytest.fixture
def detector():
    return JoystickDetector()


def test_detect_no_joysticks(detector):
    with patch("tuxemon.platform.joystick_detector.get_count", return_value=0):
        result = detector.detect()
        assert result == []


def test_detect_single_joystick_allowed(detector):
    mock_js = Mock()
    mock_js.get_name.return_value = "Generic Gamepad"

    with (
        patch("tuxemon.platform.joystick_detector.get_count", return_value=1),
        patch(
            "tuxemon.platform.joystick_detector.Joystick", return_value=mock_js
        ),
    ):
        result = detector.detect()
        assert result == [mock_js]


def test_detect_blacklisted_joystick(detector):
    mock_js = Mock()
    mock_js.get_name.return_value = "Microsoft Wireless Transceiver"

    with (
        patch("tuxemon.platform.joystick_detector.get_count", return_value=1),
        patch(
            "tuxemon.platform.joystick_detector.Joystick", return_value=mock_js
        ),
    ):
        result = detector.detect()
        assert result == []


def test_detect_multiple_mixed(detector):
    js_good = Mock()
    js_good.get_name.return_value = "Logitech F310"

    js_bad = Mock()
    js_bad.get_name.return_value = "Synaptics TouchPad"

    def fake_joystick(i):
        return [js_good, js_bad][i]

    with (
        patch("tuxemon.platform.joystick_detector.get_count", return_value=2),
        patch(
            "tuxemon.platform.joystick_detector.Joystick",
            side_effect=fake_joystick,
        ),
    ):
        result = detector.detect()
        assert result == [js_good]


def test_detect_initialization_failure(detector):
    with (
        patch("tuxemon.platform.joystick_detector.get_count", return_value=1),
        patch(
            "tuxemon.platform.joystick_detector.Joystick",
            side_effect=Exception("boom"),
        ),
    ):
        result = detector.detect()
        assert result == []

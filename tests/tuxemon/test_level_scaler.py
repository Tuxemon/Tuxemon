# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import random

import pytest

from tuxemon.encounter import LevelScaler


class DummyEncounterItem:
    def __init__(
        self, level_range, level_offset_range=None, scaling_enabled=False
    ):
        self.level_range = level_range
        self.level_offset_range = level_offset_range
        self.level_offset = 0
        self.scaling_enabled = scaling_enabled
        self.override_level_range = None
        self.scaling_offset_range = None


class DummyEncounterData:
    def __init__(
        self,
        scaling_zone=False,
        scale_multiplier=1.0,
        override_level_range=None,
        scale_offset_range=None,
    ):
        self.scaling_zone = scaling_zone
        self.scale_multiplier = scale_multiplier
        self.override_level_range = override_level_range
        self.scale_offset_range = scale_offset_range


@pytest.mark.parametrize(
    "avg_level, level_range, offset_range, scaling_enabled, scaling_zone, override_range, scale_multiplier, expected_min, expected_max",
    [
        pytest.param(
            10,
            [5, 10],
            None,
            False,
            False,
            None,
            1.0,
            5,
            10,
            id="no_scaling_basic_range",
        ),
        pytest.param(
            10,
            [1, 20],
            None,
            True,
            True,
            None,
            1.0,
            8,
            12,
            id="scaling_enabled_zone_enabled",
        ),
        pytest.param(
            1,
            [1, 5],
            (-5, -5),
            True,
            True,
            None,
            1.0,
            1,
            1,
            id="offset_clamped_minimum",
        ),
        pytest.param(
            5,
            [1, 10],
            None,
            False,
            False,
            None,
            1.0,
            1,
            10,
            id="no_scaling_full_range",
        ),
        pytest.param(
            10,
            [1, 50],
            None,
            True,
            True,
            [1, 99],
            2.0,
            18,
            22,
            id="override_range_with_multiplier",
        ),
    ],
)
def test_level_scaler_edge_cases(
    monkeypatch,
    avg_level,
    level_range,
    offset_range,
    scaling_enabled,
    scaling_zone,
    override_range,
    scale_multiplier,
    expected_min,
    expected_max,
):
    monkeypatch.setattr(random, "randint", lambda a, b: a)

    item = DummyEncounterItem(
        level_range=level_range,
        level_offset_range=offset_range,
        scaling_enabled=scaling_enabled,
    )

    zone = DummyEncounterData(
        scaling_zone=scaling_zone,
        scale_multiplier=scale_multiplier,
        override_level_range=override_range,
    )

    level = LevelScaler.get_scaled_level(avg_level, item, zone)
    assert expected_min <= level <= expected_max

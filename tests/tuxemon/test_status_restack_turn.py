# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.core.asset import init_assets
from tuxemon.monster.status import MonsterStatusHandler
from tuxemon.status.status import Status


def make_status(slug, host, duration):
    """Build a real Status from a mocked db model (avoids loading the db)."""
    init_assets()
    model = MagicMock()
    model.slug = slug
    model.conditions = []
    model.effects = []
    model.modifiers = []
    model.duration = duration
    model.max_stacks = 5
    model.step_interval = 0
    model.step_effect_value = 0.0
    model.gain_cond = None
    model.use_success = None
    model.use_failure = None
    model.on_positive_status = None
    model.on_negative_status = None
    model.category = None
    with patch("tuxemon.status.status.StatusModel.lookup", return_value=model):
        return Status.create(slug, host)


def make_host():
    monster = MagicMock()
    monster.name = "Rockitten"
    monster.held_item = None
    monster.status = MonsterStatusHandler()
    return monster


@pytest.mark.parametrize(
    "duration, rounds_survived",
    [
        pytest.param(3, 1, id="durationed_one_round"),
        pytest.param(5, 3, id="durationed_three_rounds"),
        pytest.param(0, 2, id="endless"),
    ],
)
def test_restacked_status_matches_fresh_status(duration, rounds_survived):
    session = MagicMock()

    fresh_host = make_host()
    fresh_host.status.apply_status(
        session, make_status("noddingoff", fresh_host, duration)
    )
    fresh = fresh_host.status.current_status

    restacked_host = make_host()
    restacked_host.status.apply_status(
        session, make_status("noddingoff", restacked_host, duration)
    )
    restacked = restacked_host.status.current_status
    for _ in range(rounds_survived):
        restacked.tick_turn()
    restacked_host.status.apply_status(
        session, make_status("noddingoff", restacked_host, duration)
    )

    assert restacked_host.status.current_status is restacked
    assert restacked.nr_turn == fresh.nr_turn

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

from tuxemon.cloning import make_clone
from tuxemon.db import Acquisition


def test_make_clone():
    wild_state = {
        "slug": "bellsprout",
        "level": 7,
        "current_hp": 3,
        "instance_id": "wild-001",
        "status": "PARALYZED",
        "mother_iid": "mom-001",
        "father_iid": "dad-001",
        "gender": "male",
        "moves": ["vine-whip", "acid"],
        "individual_values": {"hp": 10, "atk": 20, "def": 30, "spd": 40},
    }

    wild = MagicMock()
    wild.get_state.return_value = wild_state

    clone = MagicMock()
    clone.hp = 120

    with (
        patch(
            "tuxemon.cloning.Monster.from_save", return_value=clone
        ) as mock_from_save,
        patch("tuxemon.cloning.today_month_day", return_value=(11, 23)),
    ):
        result = make_clone(wild)

    # 1. from_save called once with every key except instance_id, status, mother_iid, father_iid
    mock_from_save.assert_called_once()
    passed_state = mock_from_save.call_args[0][0]

    expected_keys = {
        "slug",
        "level",
        "current_hp",
        "gender",
        "moves",
        "individual_values",
    }
    excluded_keys = {"instance_id", "status", "mother_iid", "father_iid"}

    assert set(passed_state.keys()) == expected_keys
    assert not (excluded_keys & set(passed_state.keys()))

    # Copied values unchanged
    assert passed_state["slug"] == "bellsprout"
    assert passed_state["level"] == 7
    assert passed_state["current_hp"] == 3
    assert passed_state["gender"] == "male"
    assert passed_state["moves"] == ["vine-whip", "acid"]
    assert passed_state["individual_values"] == {
        "hp": 10,
        "atk": 20,
        "def": 30,
        "spd": 40,
    }

    # 2. Returned clone is the patched object
    assert result is clone

    # 3. clone.wild is False
    assert clone.wild is False

    # 4. clone.current_hp == 120 (full health, not the wild's 3)
    assert clone.current_hp == 120

    # 5. clone.capture_date == (11, 23)
    assert clone.capture_date == (11, 23)

    # 6. set_acquisition called once with Acquisition.CLONED
    clone.set_acquisition.assert_called_once_with(Acquisition.CLONED)

    # 7. Wild monster not modified: only get_state was called
    assert wild.method_calls == [call.get_state()]

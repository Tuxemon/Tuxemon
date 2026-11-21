# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch
from uuid import uuid4

from tuxemon.event.actions.dojo_method import DojoMethodAction
from tuxemon.monster.stats import BasicStats, TrainingPoints


def make_action(option="tp"):
    action = DojoMethodAction(variable_name="mon", option=option)
    action.client = MagicMock()
    action.player = MagicMock()
    action.monster = MagicMock()
    action.monster.name = "agnite"
    action.monster.training_points = TrainingPoints(
        armour=40, speed=30, hp=20, melee=10
    )
    return action


def test_reset_tps_single_stat():
    action = make_action()

    with patch(
        "tuxemon.event.actions.dojo_method.open_dialog"
    ) as open_dialog, patch(
        "tuxemon.event.actions.dojo_method.T"
    ) as mock_t:
        mock_t.translate.side_effect = lambda key: key
        mock_t.format.side_effect = lambda key, params: f"{key}:{params}"
        action.reset_tps("armour")

    tp = action.monster.training_points
    assert tp.armour == 0
    assert tp.speed == 30 and tp.hp == 20 and tp.melee == 10
    action.monster.set_stats.assert_called_once()
    action.client.pop_state.assert_called_once()
    # Feedback dialog is shown after the reset, with the stat label.
    mock_t.format.assert_called_once_with(
        "dojo_tp_reset_done", {"stat": "armour"}
    )
    open_dialog.assert_called_once()
    assert open_dialog.call_args.args[1] == [
        "dojo_tp_reset_done:{'stat': 'armour'}"
    ]


def test_reset_tps_all_stats():
    action = make_action()

    with patch(
        "tuxemon.event.actions.dojo_method.open_dialog"
    ) as open_dialog, patch(
        "tuxemon.event.actions.dojo_method.T"
    ) as mock_t:
        mock_t.translate.side_effect = lambda key: key
        mock_t.format.side_effect = lambda key, params: f"{key}:{params}"
        action.reset_tps(None)

    assert action.monster.training_points.sum() == 0
    action.monster.set_stats.assert_called_once()
    action.client.pop_state.assert_called_once()
    # "all stats" label is used when resetting everything.
    mock_t.format.assert_called_once_with(
        "dojo_tp_reset_done", {"stat": "dojo_tp_all_stats"}
    )
    open_dialog.assert_called_once()


def make_session(monster):
    session = MagicMock()
    session.player.game_variables = {"mon": uuid4().hex}
    session.client.get_monster_by_iid.return_value = monster
    return session


def test_tp_option_builds_menu_with_all_stats():
    action = make_action()
    monster = action.monster
    session = make_session(monster)

    captured = {}

    def fake_create(actions):
        captured["keys"] = list(actions.keys())
        return []

    with patch(
        "tuxemon.event.actions.dojo_method.create_choice_options",
        side_effect=fake_create,
    ), patch(
        "tuxemon.event.actions.dojo_method.open_choice_dialog"
    ) as open_dialog:
        action.start(session)

    assert captured["keys"] == BasicStats.names() + ["dojo_tp_all"]
    open_dialog.assert_called_once()


def test_invalid_option_stops():
    action = make_action(option="bogus")
    monster = action.monster
    session = make_session(monster)

    action.start(session)

    assert action._done is True


def test_tp_update_waits_for_choice_menu():
    action = make_action()
    session = MagicMock()
    session.client.active_state_names = ["WorldState", "ChoiceState"]

    action.update(session, 0.0)

    assert action._done is False


def test_tp_update_waits_for_confirmation_dialog():
    action = make_action()
    session = MagicMock()
    session.client.active_state_names = ["WorldState", "DialogState"]

    action.update(session, 0.0)

    assert action._done is False


def test_tp_update_stops_when_menu_and_dialog_closed():
    action = make_action()
    session = MagicMock()
    session.client.active_state_names = ["WorldState"]

    action.update(session, 0.0)

    assert action._done is True


def test_monster_update_still_stops_without_dialog():
    # Existing behaviour for the other options is unchanged.
    action = make_action(option="monster")
    session = MagicMock()
    session.client.active_state_names = ["WorldState", "ChoiceState"]

    action.update(session, 0.0)

    assert action._done is True

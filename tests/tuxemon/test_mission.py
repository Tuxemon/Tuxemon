# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import (
    GameCondition,
    MissionModel,
    MissionStatus,
    MissionStepModel,
)
from tuxemon.entity.bag import BagHandler
from tuxemon.entity.npc import NPC
from tuxemon.entity.party import PartyHandler
from tuxemon.game_variables import GameVariablesManager
from tuxemon.mission.controller import MissionController
from tuxemon.mission.manager import MissionManager
from tuxemon.mission.mission import Mission, check_items, check_monsters


@pytest.fixture
def character(mission_manager):
    c = MagicMock(spec=NPC)
    c.slug = "test_character"
    c.variable_manager = GameVariablesManager()
    c.mission_controller = MissionController(c, mission_manager)
    return c


@pytest.fixture
def mission():
    model = MissionModel(
        slug="empty",
        description="empty",
        prerequisites=[],
        connected_missions=[],
        failure_conditions=[],
        required_items={},
        required_monsters={},
        required_missions=[],
        steps={},
        repeatable=False,
    )
    return Mission(db_data=model)


@pytest.fixture
def mission_manager():
    return MissionManager()


@pytest.fixture
def controller(character, mission_manager):
    return MissionController(character, mission_manager)


def test_add_mission(mission_manager, mission):
    mission_manager.add_mission(mission)
    assert mission_manager.missions == {mission.slug: mission}


def test_remove_mission(mission_manager, mission):
    mission_manager.add_mission(mission)
    mission_manager.remove_mission(mission)
    assert mission_manager.missions == {}


def test_remove_mission_not_found(mission_manager, mission):
    mission_manager.remove_mission(mission)
    assert mission_manager.get_mission_count() == 0


def test_find_mission(mission_manager, mission):
    mission.slug = "test_mission"
    mission_manager.add_mission(mission)
    assert mission_manager.find_mission("test_mission") is mission


def test_find_mission_not_found(mission_manager):
    assert mission_manager.find_mission("missing") is None


def test_get_mission_count(mission_manager, mission):
    assert mission_manager.get_mission_count() == 0
    mission_manager.add_mission(mission)
    assert mission_manager.get_mission_count() == 1


def test_add_duplicate_mission(mission_manager, mission):
    mission_manager.add_mission(mission)
    mission_manager.add_mission(mission)
    assert mission_manager.get_mission_count() == 1


def test_large_mission_list(mission_manager):
    for i in range(1000):
        m = MagicMock()
        m.slug = f"mission_{i}"
        mission_manager.add_mission(m)
    assert mission_manager.get_mission_count() == 1000


@pytest.mark.parametrize(
    "initial, new, expected",
    [
        pytest.param(
            MissionStatus.PENDING,
            MissionStatus.COMPLETED,
            MissionStatus.COMPLETED,
            id="pending_to_completed",
        ),
        pytest.param(
            MissionStatus.PENDING,
            MissionStatus.PENDING,
            MissionStatus.PENDING,
            id="pending_to_pending",
        ),
    ],
)
def test_update_status(mission, initial, new, expected):
    mission.status = initial
    mission.update_status(new)
    assert mission.status == expected


def test_check_all_prerequisites(
    character, controller, mission_manager, mission
):
    mission.prerequisites = [GameCondition(key="key", value="value")]
    mission_manager.add_mission(mission)

    character.game_variables = character.variable_manager.player
    character.game_variables.set("key", "value")
    assert controller.check_all_prerequisites()

    character.game_variables.set("key", "wrong_value")
    assert not controller.check_all_prerequisites()


def test_check_all_prerequisites_with_no_missions(controller):
    assert controller.check_all_prerequisites()


def test_check_all_prerequisites_with_unmet_conditions(
    character, controller, mission_manager, mission
):
    mission.prerequisites = [GameCondition(key="key", value="required_value")]
    mission_manager.add_mission(mission)

    character.game_variables = character.variable_manager.player
    character.game_variables.set("key", "incorrect_value")
    assert not controller.check_all_prerequisites()


@pytest.mark.parametrize(
    "potion_qty, lotion_state, expected",
    [
        pytest.param(1, 2, True, id="enough_items"),
        pytest.param(1, 1, False, id="not_enough_lotion"),
        pytest.param(1, "missing", False, id="lotion_missing"),
    ],
)
def test_check_required_items(
    character, mission, potion_qty, lotion_state, expected
):
    mission.required_items = {"potion": None, "lotion": 2}

    item1 = MagicMock(slug="potion", quantity=potion_qty)
    item2 = (
        None
        if lotion_state == "missing"
        else MagicMock(slug="lotion", quantity=lotion_state)
    )

    character.bag = MagicMock(spec=BagHandler)
    character.bag.find_item.side_effect = lambda slug: (
        item1 if slug == "potion" else item2
    )

    assert check_items(character, mission.required_items) is expected


@pytest.mark.parametrize(
    "lvl1, lvl2, expected",
    [
        pytest.param(3, 5, True, id="both_meet_requirements"),
        pytest.param(3, 4, False, id="second_too_low"),
        pytest.param(3, None, False, id="second_missing"),
    ],
)
def test_check_required_monsters(character, mission, lvl1, lvl2, expected):
    mission.required_monsters = {"monster1": None, "monster2": 5}

    monster1 = MagicMock(slug="monster1", level=lvl1)
    monster2 = (
        MagicMock(slug="monster2", level=lvl2) if lvl2 is not None else None
    )

    character.party = MagicMock(spec=PartyHandler)
    character.party.find_monster.side_effect = lambda slug: (
        monster1 if slug == "monster1" else monster2
    )

    assert check_monsters(character, mission.required_monsters) is expected


def test_encode_missions(mission_manager, controller, mission):
    mission.slug = "mission1"
    mission.status = MissionStatus.PENDING
    mission_manager.add_mission(mission)

    encoded = controller.encode_missions()
    assert isinstance(encoded, list)
    assert len(encoded) == 1
    assert encoded[0]["slug"] == "mission1"
    assert encoded[0]["status"] == MissionStatus.PENDING


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(True, id="connected_true"),
        pytest.param(False, id="connected_false"),
    ],
)
def test_check_connected_missions(
    mission_manager, controller, mission, result
):
    mission.check_connected_missions = MagicMock(return_value=result)
    mission_manager.add_mission(mission)
    assert controller.check_connected_missions() is result


@pytest.fixture
def mission_with_steps():
    steps = {
        "start": MissionStepModel(
            slug="start",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=1,
            next_steps=["mid"],
            optional=False,
        ),
        "mid": MissionStepModel(
            slug="mid",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=2,
            next_steps=["end"],
            optional=False,
        ),
        "end": MissionStepModel(
            slug="end",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=3,
            next_steps=[],
            optional=False,
        ),
    }
    model = MissionModel(
        slug="agnite",
        description="agnite",
        prerequisites=[],
        connected_missions=[],
        failure_conditions=[],
        required_items={},
        required_monsters={},
        required_missions=[],
        steps=steps,
        repeatable=False,
    )
    return Mission(db_data=model)


def test_root_step_unlocked(mission_with_steps):
    assert mission_with_steps.is_step_unlocked("start")


def test_child_locked_initially(mission_with_steps):
    assert not mission_with_steps.is_step_unlocked("mid")


def test_child_unlocked_after_parent(mission_with_steps):
    mission_with_steps.mark_step_completed("start")
    assert mission_with_steps.is_step_unlocked("mid")


def test_auto_complete_step(character):
    step = MissionStepModel(
        slug="rockitten",
        conditions=GameCondition(key="x", value="1"),
        description="",
        order=1,
        next_steps=[],
        optional=False,
        auto_complete=True,
        any_of=[],
        all_of=[],
    )

    model = MissionModel(
        slug="agnite",
        description="agnite",
        prerequisites=[],
        connected_missions=[],
        failure_conditions=[],
        required_items={},
        required_monsters={},
        required_missions=[],
        steps={"rockitten": step},
        repeatable=False,
    )

    mission = Mission(db_data=model)

    character.game_variables = character.variable_manager.player
    character.game_variables.set("x", "1")

    mission.check_step_conditions(character)

    assert "rockitten" in mission.completed_steps


def test_progress_ignores_optional_steps():
    steps = {
        "rockitten": MissionStepModel(
            slug="rockitten",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=1,
            next_steps=[],
            optional=False,
        ),
        "pairagrin": MissionStepModel(
            slug="pairagrin",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=2,
            next_steps=[],
            optional=True,
        ),
    }
    model = MissionModel(
        slug="agnite",
        description="agnite",
        prerequisites=[],
        connected_missions=[],
        failure_conditions=[],
        required_items={},
        required_monsters={},
        required_missions=[],
        steps=steps,
        repeatable=False,
    )
    mission = Mission(db_data=model)

    mission.mark_step_completed("rockitten")

    assert mission.get_progress() == 100.0


def test_repeatable_mission_resets(character):
    steps = {
        "rockitten": MissionStepModel(
            slug="rockitten",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=1,
            next_steps=[],
            optional=False,
        ),
    }

    model = MissionModel(
        slug="agnite",
        description="agnite",
        prerequisites=[],
        connected_missions=[],
        failure_conditions=[],
        required_items={},
        required_monsters={},
        required_missions=[],
        steps=steps,
        repeatable=True,
    )

    mission = Mission(db_data=model)

    mission.mark_step_completed("rockitten")
    mission.update_progress(character)

    assert mission.status == MissionStatus.PENDING
    assert mission.completed_steps == set()


def test_graph_valid():
    steps = {
        "rockitten": MissionStepModel(
            slug="rockitten",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=1,
            next_steps=["pairagrin"],
        ),
        "pairagrin": MissionStepModel(
            slug="pairagrin",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=2,
            next_steps=[],
        ),
    }
    mission = Mission(
        db_data=MissionModel(
            slug="agnite",
            description="agnite",
            prerequisites=[],
            connected_missions=[],
            failure_conditions=[],
            required_items={},
            required_monsters={},
            required_missions=[],
            steps=steps,
            repeatable=False,
        )
    )
    mission.validate_graph()  # should not raise


def test_graph_cycle():
    steps = {
        "rockitten": MissionStepModel(
            slug="rockitten",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=1,
            next_steps=["pairagrin"],
        ),
        "pairagrin": MissionStepModel(
            slug="pairagrin",
            conditions=GameCondition(key="x", value=1),
            description="",
            order=2,
            next_steps=["rockitten"],
        ),
    }
    mission = Mission(
        db_data=MissionModel(
            slug="agnite",
            description="agnite",
            prerequisites=[],
            connected_missions=[],
            failure_conditions=[],
            required_items={},
            required_monsters={},
            required_missions=[],
            steps=steps,
            repeatable=False,
        )
    )
    with pytest.raises(ValueError):
        mission.validate_graph()


def test_required_missions(character, mission_manager):
    m1 = Mission(
        db_data=MissionModel(
            slug="pairagrin",
            description="pairagrin",
            prerequisites=[],
            connected_missions=[],
            failure_conditions=[],
            required_items={},
            required_monsters={},
            required_missions=[],
            steps={},
            repeatable=False,
        )
    )
    m2 = Mission(
        db_data=MissionModel(
            slug="rockitten",
            description="rockitten",
            prerequisites=[],
            connected_missions=[],
            failure_conditions=[],
            required_items={},
            required_monsters={},
            required_missions=["pairagrin"],
            steps={},
            repeatable=False,
        )
    )

    mission_manager.add_mission(m1)
    mission_manager.add_mission(m2)

    character.mission_controller.mission_manager = mission_manager

    assert m2.check_required_missions(character)


def test_connected_missions_logic(character, mission_manager):
    m1 = Mission(
        db_data=MissionModel(
            slug="rockitten",
            description="rockitten",
            prerequisites=[],
            connected_missions=[],
            failure_conditions=[],
            required_items={},
            required_monsters={},
            required_missions=[],
            steps={},
            repeatable=False,
        )
    )
    m2 = Mission(
        db_data=MissionModel(
            slug="pairagrin",
            description="pairagrin",
            prerequisites=[],
            connected_missions=[{"slug": "rockitten"}],
            failure_conditions=[],
            required_items={},
            required_monsters={},
            required_missions=[],
            steps={},
            repeatable=False,
        )
    )

    mission_manager.add_mission(m1)
    mission_manager.add_mission(m2)

    character.mission_controller.mission_manager = mission_manager

    assert m2.check_connected_missions(character)

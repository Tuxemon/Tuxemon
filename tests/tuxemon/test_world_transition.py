# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, call

import pytest

from tuxemon.client import LocalPygameClient
from tuxemon.movement import MovementManager
from tuxemon.world.transition import WorldTransition


@pytest.fixture
def mock_world():
    world = MagicMock()
    world.client = MagicMock(spec=LocalPygameClient)
    world.client.movement_manager = MagicMock(spec=MovementManager)
    world.player = MagicMock()
    return world


@pytest.fixture
def transition(mock_world):
    return WorldTransition(
        mock_world, mock_world.client.movement_manager, (800, 600)
    )


@pytest.fixture
def fake_surface(monkeypatch):
    mock_surface = MagicMock()
    monkeypatch.setattr(
        "pygame.Surface",
        lambda *args, **kwargs: mock_surface,
    )
    return mock_surface


def test_initial_state(transition):
    assert transition.transition_surface is None
    assert transition.transition_alpha == 0
    assert transition.in_transition is False


@pytest.mark.parametrize(
    "state",
    [
        pytest.param(True, id="state_true"),
        pytest.param(False, id="state_false"),
    ],
)
def test_transition_state_changes(transition, state):
    transition.set_transition_state(state)
    assert transition.in_transition is state


@pytest.mark.parametrize(
    "color",
    [
        pytest.param((0, 0, 0, 255), id="black"),
        pytest.param((255, 0, 0, 255), id="red"),
    ],
)
def test_set_transition_surface(monkeypatch, transition, color):
    transition.set_transition_surface(color)
    assert transition.transition_surface is not None
    assert transition.transition_surface.get_size() == (800, 600)
    assert transition.transition_surface.get_at((0, 0)) == color


def test_draw_no_action_when_not_in_transition(transition):
    surface = MagicMock()
    transition.set_transition_state(False)
    transition.transition_alpha = 128
    transition.draw(surface)
    surface.blit.assert_not_called()


def test_draw_with_transition(transition, fake_surface):
    surface = MagicMock()
    transition.set_transition_surface((0, 0, 0, 255))
    transition.set_transition_state(True)
    transition.transition_surface = fake_surface
    transition.transition_alpha = 100
    transition.draw(surface)
    fake_surface.set_alpha.assert_called_with(100)
    surface.blit.assert_called_with(fake_surface, (0, 0))


def test_draw_with_zero_alpha_does_not_blit(transition, fake_surface):
    surface = MagicMock()
    transition.set_transition_surface((0, 0, 0, 255))
    transition.set_transition_state(True)
    transition.transition_surface = fake_surface
    transition.transition_alpha = 0
    transition.draw(surface)
    fake_surface.set_alpha.assert_called_with(0)
    surface.blit.assert_not_called()


@pytest.mark.parametrize(
    "method, initial, final",
    [
        pytest.param("fade_out", 0, 255, id="fade_out"),
        pytest.param("fade_in", 255, 0, id="fade_in"),
    ],
)
def test_fade_alpha_animation(
    monkeypatch, transition, mock_world, method, initial, final
):
    monkeypatch.setattr("pygame.Surface", MagicMock())
    color = (0, 0, 0, 255)
    getattr(transition, method)(1.0, color)
    mock_world.animate.assert_called_with(
        transition,
        transition_alpha=final,
        initial=initial,
        duration=1.0,
        round_values=True,
    )


@pytest.mark.parametrize(
    "duration",
    [
        pytest.param(1.0, id="duration_positive"),
        pytest.param(0.0, id="duration_zero"),
        pytest.param(-1.0, id="duration_negative"),
    ],
)
@pytest.mark.parametrize(
    "with_character",
    [
        pytest.param(True, id="with_character"),
        pytest.param(False, id="no_character"),
    ],
)
def test_fade_out_edge_cases(
    monkeypatch, transition, mock_world, duration, with_character
):
    monkeypatch.setattr("pygame.Surface", MagicMock())
    color = (0, 0, 0, 255)
    character = mock_world.player if with_character else None
    transition.fade_out(duration, color, character)
    mock_world.animate.assert_called_with(
        transition,
        transition_alpha=255,
        initial=0,
        duration=duration,
        round_values=True,
    )
    mm = mock_world.client.movement_manager
    if with_character:
        mm.stop_char.assert_called_with(character)
        mm.lock_controls.assert_called_with(character)
    else:
        mm.stop_char.assert_not_called()
        mm.lock_controls.assert_not_called()
    assert transition.in_transition is True


@pytest.mark.parametrize(
    "duration",
    [
        pytest.param(1.0, id="duration_positive"),
        pytest.param(0.0, id="duration_zero"),
        pytest.param(-1.0, id="duration_negative"),
    ],
)
@pytest.mark.parametrize(
    "with_character",
    [
        pytest.param(True, id="with_character"),
        pytest.param(False, id="no_character"),
    ],
)
def test_fade_in_edge_cases(
    monkeypatch, transition, mock_world, duration, with_character
):
    monkeypatch.setattr("pygame.Surface", MagicMock())
    color = (0, 0, 0, 255)
    character = mock_world.player if with_character else None
    transition.fade_in(duration, color, character)
    mock_world.animate.assert_called_with(
        transition,
        transition_alpha=0,
        initial=255,
        duration=duration,
        round_values=True,
    )
    assert mock_world.task.call_count == 1
    _, kwargs = mock_world.task.call_args_list[0]
    assert kwargs["interval"] == max(duration, 0)
    assert transition.in_transition is False


def test_fade_out_call_order(monkeypatch, transition, mock_world):
    monkeypatch.setattr("pygame.Surface", MagicMock())
    color = (0, 0, 0, 255)
    character = mock_world.player
    transition.fade_out(1.0, color, character)
    filtered = [
        c
        for c in mock_world.mock_calls
        if c[0]
        in (
            "animate",
            "client.movement_manager.stop_char",
            "client.movement_manager.lock_controls",
        )
    ]
    expected = [
        call.animate(
            transition,
            transition_alpha=255,
            initial=0,
            duration=1.0,
            round_values=True,
        ),
        call.client.movement_manager.stop_char(character),
        call.client.movement_manager.lock_controls(character),
    ]
    assert filtered == expected


def test_fade_in_call_order(monkeypatch, transition, mock_world):
    monkeypatch.setattr("pygame.Surface", MagicMock())
    color = (0, 0, 0, 255)
    character = mock_world.player
    transition.fade_in(1.0, color, character)
    assert mock_world.animate.call_count == 1
    assert mock_world.task.call_count == 1
    animate_call_index = next(
        i for i, c in enumerate(mock_world.mock_calls) if c[0] == "animate"
    )
    task_call_indices = [
        i for i, c in enumerate(mock_world.mock_calls) if c[0] == "task"
    ]
    assert all(animate_call_index < idx for idx in task_call_indices)


def test_fade_and_teleport_call_order(monkeypatch, transition, mock_world):
    monkeypatch.setattr("pygame.Surface", MagicMock())
    color = (0, 0, 0, 255)
    teleport = MagicMock()
    transition.fade_and_teleport(1.0, color, mock_world.player, teleport)
    mock_world.animate.assert_called_with(
        transition,
        transition_alpha=255,
        initial=0,
        duration=1.0,
        round_values=True,
    )
    mock_world.task.assert_called_with(teleport, interval=1.0)
    chained = mock_world.task.return_value.chain
    chained.assert_called()
    next(i for i, c in enumerate(mock_world.mock_calls) if c[0] == "task")
    chain_call_index = next(
        i
        for i, c in enumerate(mock_world.task.return_value.mock_calls)
        if c[0] == "chain"
    )
    assert chain_call_index >= 0


def test_no_draw_when_not_in_transition(transition):
    surface = MagicMock()
    transition.set_transition_state(False)
    transition.draw(surface)
    surface.blit.assert_not_called()

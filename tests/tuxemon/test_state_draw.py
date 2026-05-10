# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.platform.const.graphics import GREEN_COLOR, RED_COLOR
from tuxemon.state.draw import EventDebugDrawer, Renderer, StateDrawer


@pytest.fixture
def screen():
    return MagicMock()


@pytest.fixture
def debug_drawer():
    return MagicMock()


@pytest.fixture
def state_drawer():
    return MagicMock()


@pytest.fixture
def config():
    cfg = MagicMock()
    cfg.window_caption = "Test Caption"
    cfg.vsync = False
    return cfg


@pytest.fixture
def renderer(screen, state_drawer, config, debug_drawer):
    return Renderer(screen, state_drawer, config, debug_drawer)


# TestRenderer


def test_init(renderer, screen, state_drawer, config):
    assert renderer.screen is screen
    assert renderer.state_drawer is state_drawer
    assert renderer.caption == config.window_caption
    assert renderer.frames == 0
    assert renderer.fps_timer == 0.0


def test_draw(renderer, state_drawer):
    renderer.draw()
    state_drawer.draw.assert_called_once()


def test_draw_debug(renderer, debug_drawer):
    events = [MagicMock()]
    renderer.draw_debug(events)
    debug_drawer.draw_event_debug.assert_called_once_with(events)


@patch("pygame.image.save")
def test_save_frame(mock_save, renderer, screen):
    renderer.save_frame(42)
    mock_save.assert_called_once_with(screen, "snapshot00042.tga")


def test_update(renderer):
    renderer.frames = 59
    renderer.fps_timer = 1.0
    renderer.update(0.0)

    assert renderer.frames == 0
    assert renderer.fps_timer == 0.0


def test_update_accumulates_and_resets(renderer):
    for _ in range(61):
        renderer.update(0.0165)

    assert renderer.frames == 0
    assert renderer.fps_timer == 0.0


def test_update_accumulates_without_reset(renderer):
    for _ in range(60):
        renderer.update(0.016)

    assert renderer.frames == 60
    assert pytest.approx(renderer.fps_timer, rel=1e-2) == 0.96


@patch("pygame.display.set_caption")
def test_update_sets_caption_with_vsync(mock_caption, renderer, config):
    config.vsync = True
    renderer.vsync = True
    renderer.frames = 60
    renderer.fps_timer = 1.0

    renderer.update(0.0)

    mock_caption.assert_called_once()
    assert "VSync ON" in mock_caption.call_args[0][0]


@patch("pygame.display.set_caption")
def test_update_sets_caption_without_vsync(mock_caption, renderer, config):
    config.vsync = False
    renderer.vsync = False
    renderer.frames = 60
    renderer.fps_timer = 1.0

    renderer.update(0.0)

    mock_caption.assert_called_once()
    assert "VSync OFF" in mock_caption.call_args[0][0]


@patch("pygame.image.save")
def test_save_frame_filename_format(mock_save, renderer, screen):
    renderer.save_frame(7)
    mock_save.assert_called_once_with(screen, "snapshot00007.tga")


def test_draw_debug_with_empty_events(renderer, debug_drawer):
    renderer.draw_debug([])
    debug_drawer.draw_event_debug.assert_called_once_with([])


# TestStateDrawer


@pytest.fixture
def sd_surface():
    return MagicMock()


@pytest.fixture
def sd_state_manager():
    return MagicMock()


@pytest.fixture
def sd_config():
    return MagicMock()


@pytest.fixture
def sd(sd_surface, sd_state_manager, sd_config):
    return StateDrawer(sd_surface, sd_state_manager, sd_config)


def test_state_drawer_init(sd, sd_surface, sd_state_manager, sd_config):
    assert sd.surface is sd_surface
    assert sd.state_manager is sd_state_manager
    assert sd.config is sd_config


def test_state_drawer_draw(sd, sd_state_manager, sd_surface):
    s1 = MagicMock()
    s2 = MagicMock()
    sd_state_manager.active_states = [s1, s2]

    sd.draw()

    s1.draw.assert_called_once_with(sd_surface)
    s2.draw.assert_called_once_with(sd_surface)


def test_state_drawer_draw_with_transparency(sd, sd_state_manager, sd_surface):
    s1 = MagicMock()
    s1.transparent = False
    s1.rect = MagicMock(return_value=(0, 0, 100, 100))

    s2 = MagicMock()

    sd_state_manager.active_states = [s1, s2]

    sd.draw()

    s1.draw.assert_called_once_with(sd_surface)
    s2.draw.assert_called_once_with(sd_surface)


def test_state_drawer_draw_full_screen(sd, sd_state_manager, sd_surface):
    s1 = MagicMock()
    s1.transparent = False
    s1.force_draw = False
    s1.rect = MagicMock(return_value=(0, 0, 100, 100))

    s2 = MagicMock()

    sd_surface.get_rect.return_value = (0, 0, 100, 100)
    sd_state_manager.active_states = [s1, s2]

    sd.draw()

    s1.draw.assert_called_once_with(sd_surface)
    s2.draw.assert_called_once_with(sd_surface)


# TestEventDebugDrawer


@pytest.fixture
def debug_context():
    ctx = MagicMock()
    ctx.screen = MagicMock()
    ctx.scaling = MagicMock()
    ctx.scaling.scale_sequence.return_value = (1, 1)
    ctx.scaling.scale_int.return_value = 15
    return ctx


def test_event_debug_drawer_init(debug_context):
    drawer = EventDebugDrawer(debug_context)

    assert drawer.screen is debug_context.screen
    assert drawer.scaling is debug_context.scaling
    assert drawer.max_width == 1000
    assert drawer.x_offset == 20
    assert drawer.y_offset == 200
    assert drawer.initial_x == 4
    assert drawer.initial_y == 20
    assert drawer.success_color == GREEN_COLOR
    assert drawer.failure_color == RED_COLOR


def test_draw_event_debug(debug_context):
    drawer = EventDebugDrawer(debug_context)

    event1 = [(True, MagicMock()), (False, MagicMock())]
    event1[0][1].parameters = ["param1", "param2"]
    event1[1][1].parameters = ["param3", "param4"]

    event2 = [(True, MagicMock()), (False, MagicMock())]
    event2[0][1].parameters = ["param5", "param6"]
    event2[1][1].parameters = ["param7", "param8"]

    drawer.draw_event_debug([event1, event2])

    assert debug_context.screen.blit.called


def test_render_text(debug_context):
    drawer = EventDebugDrawer(debug_context)
    drawer.render_text("Test text", (255, 0, 0), (10, 20), 15)

    assert debug_context.screen.blit.called

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from dataclasses import dataclass
from unittest.mock import Mock, patch

import pygame

from tuxemon.entity.appearance import AppearanceManager, RuntimeAppearance


@dataclass
class DummyTemplate:
    sprite_name: str = "npc_default"
    combat_sheet: str = "combat_default"
    combat_frame_width: int = 32
    combat_frame_height: int = 32
    is_static_prop: bool = False


def test_from_template():
    template = DummyTemplate()
    app = RuntimeAppearance.from_template(template)

    assert app.sprite_name == "npc_default"
    assert app.combat_sheet == "combat_default"


def test_from_dict_full_override():
    template = DummyTemplate()
    data = {"sprite_name": "saved_sprite", "combat_sheet": "saved_combat"}

    app = RuntimeAppearance.from_dict(data, template)

    assert app.sprite_name == "saved_sprite"
    assert app.combat_sheet == "saved_combat"


def test_from_dict_partial_fallback():
    template = DummyTemplate()
    data = {"sprite_name": "saved_sprite"}

    app = RuntimeAppearance.from_dict(data, template)

    assert app.sprite_name == "saved_sprite"
    assert app.combat_sheet == "combat_default"


def test_to_dict_roundtrip():
    app = RuntimeAppearance("sprite_x", "combat_y")
    d = app.to_dict()

    assert d == {
        "sprite_name": "sprite_x",
        "combat_sheet": "combat_y",
        "outfit": None,
        "accessory": None,
        "palette": None,
        "color": None,
        "combat_frame_width": None,
        "combat_frame_height": None,
    }


def make_dummy_npc(template=None):
    """Helper to create a fake NPC with mocks."""
    npc = Mock()
    npc.template = template or DummyTemplate()
    npc.sprite_controller = Mock()
    npc.game_variables = {}
    return npc


def test_manager_initializes_from_template():
    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    assert manager.state.sprite_name == "npc_default"
    assert manager.state.combat_sheet == "combat_default"


def test_manager_update_changes_state_and_calls_renderer():
    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    manager.update("new_sprite", "new_sheet")

    assert manager.state.sprite_name == "new_sprite"
    assert manager.state.combat_sheet == "new_sheet"
    npc.sprite_controller.update_appearance.assert_called_once()


def test_manager_reset_to_default_uses_race_mapping():
    npc = make_dummy_npc()
    npc.game_variables["race_choice"] = "white_male"

    manager = AppearanceManager(npc)
    manager.reset_to_default()

    assert manager.state.sprite_name == "adventurer"
    assert manager.state.combat_sheet == "adventurer"
    npc.sprite_controller.update_appearance.assert_called()


def test_manager_reset_to_default_falls_back_to_template():
    npc = make_dummy_npc()
    npc.game_variables["race_choice"] = "unknown_race"

    manager = AppearanceManager(npc)
    manager.state.sprite_name = "changed"
    manager.state.combat_sheet = "changed"

    manager.reset_to_default()

    assert manager.state.sprite_name == "npc_default"
    assert manager.state.combat_sheet == "combat_default"
    npc.sprite_controller.update_appearance.assert_called()


def test_manager_load_state_mutates_existing_instance():
    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    old_state = manager.state  # reference should remain the same

    manager.load_state(
        {"sprite_name": "loaded_sprite", "combat_sheet": "loaded_sheet"}
    )

    assert manager.state is old_state
    assert manager.state.sprite_name == "loaded_sprite"
    assert manager.state.combat_sheet == "loaded_sheet"
    npc.sprite_controller.update_appearance.assert_called()


def test_update_does_not_override_combat_sheet_when_none():
    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    manager.state.combat_sheet = "initial_sheet"

    manager.update("new_sprite", None)

    assert manager.state.sprite_name == "new_sprite"
    assert manager.state.combat_sheet == "initial_sheet"
    npc.sprite_controller.update_appearance.assert_called_once()


def test_reset_to_default_preserves_state_instance():
    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    old_state = manager.state
    manager.reset_to_default()

    assert manager.state is old_state
    npc.sprite_controller.update_appearance.assert_called()


def test_reset_to_default_ignores_invalid_race_values():
    npc = make_dummy_npc()
    npc.game_variables["race_choice"] = "not_a_real_race"

    manager = AppearanceManager(npc)
    manager.state.sprite_name = "changed"
    manager.state.combat_sheet = "changed"

    manager.reset_to_default()

    assert manager.state.sprite_name == "npc_default"
    assert manager.state.combat_sheet == "combat_default"
    npc.sprite_controller.update_appearance.assert_called()


def test_load_state_partial_update():
    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    manager.state.sprite_name = "old_sprite"
    manager.state.combat_sheet = "old_sheet"

    manager.load_state({"sprite_name": "loaded_sprite"})

    assert manager.state.sprite_name == "loaded_sprite"
    assert manager.state.combat_sheet == "combat_default"
    npc.sprite_controller.update_appearance.assert_called()


def test_load_state_preserves_state_instance():
    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    old_state = manager.state
    manager.load_state({"sprite_name": "x", "combat_sheet": "y"})

    assert manager.state is old_state
    npc.sprite_controller.update_appearance.assert_called()


def test_race_mapping_all_keys_exist():
    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    for race, (sprite, sheet) in manager.DEFAULT_RACE_MAPPING.items():
        npc.game_variables["race_choice"] = race
        manager.reset_to_default()
        assert manager.state.sprite_name == sprite
        assert manager.state.combat_sheet == sheet


def test_manager_updates_layer_fields():
    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    manager.state.outfit = "coat_red"
    manager.state.accessory = "hat_blue"
    manager.state.palette = "palette_dark"

    assert manager.state.outfit == "coat_red"
    assert manager.state.accessory == "hat_blue"
    assert manager.state.palette == "palette_dark"


def make_surface(color=(0, 0, 0), size=(32, 32)):
    """Utility to create a dummy surface."""
    surf = pygame.Surface(size)
    surf.fill(color)
    return surf


@patch("tuxemon.entity.appearance.load_and_scale_with_cache")
def test_build_composited_sheet_base_only(mock_load):
    base = make_surface((10, 10, 10))
    mock_load.return_value = base

    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    result = manager.build_composited_sheet()

    assert result is not base
    assert result.get_size() == base.get_size()
    assert result.get_at((0, 0)) == base.get_at((0, 0))
    mock_load.assert_called_once()


@patch("tuxemon.entity.appearance.load_and_scale_with_cache")
def test_build_composited_sheet_with_outfit(mock_load):
    base = make_surface((10, 10, 10))
    outfit = make_surface((200, 0, 0))

    mock_load.side_effect = [base, outfit]

    npc = make_dummy_npc()
    manager = AppearanceManager(npc)
    manager.state.outfit = "coat_red"

    result = manager.build_composited_sheet()

    assert result.get_at((0, 0)) == outfit.get_at((0, 0))
    assert mock_load.call_count == 2


@patch("tuxemon.entity.appearance.load_and_scale_with_cache")
def test_build_composited_sheet_with_all_layers(mock_load):
    base = make_surface((10, 10, 10))
    outfit = make_surface((100, 0, 0))
    accessory = make_surface((0, 100, 0))
    palette = make_surface((0, 0, 100))

    mock_load.side_effect = [base, outfit, accessory, palette]

    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    manager.state.outfit = "coat"
    manager.state.accessory = "hat"
    manager.state.palette = "dark"

    result = manager.build_composited_sheet()

    assert result.get_at((0, 0)) == palette.get_at((0, 0))
    assert mock_load.call_count == 4


@patch("tuxemon.entity.appearance.load_and_scale_with_cache")
def test_build_composited_sheet_ignores_none_layers(mock_load):
    base = make_surface((10, 10, 10))
    mock_load.return_value = base

    npc = make_dummy_npc()
    manager = AppearanceManager(npc)

    result = manager.build_composited_sheet()

    assert mock_load.call_count == 1
    assert result.get_at((0, 0)) == base.get_at((0, 0))

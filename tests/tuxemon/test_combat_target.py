# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections import defaultdict
from unittest.mock import MagicMock

import pytest

from tuxemon.states.combat_target import CombatTargetMenuState


@pytest.fixture
def state():
    state = CombatTargetMenuState.__new__(CombatTargetMenuState)

    state.character = MagicMock()
    state.monster = MagicMock()

    state.client = MagicMock()
    state.combat = MagicMock()
    state.combat_session = MagicMock()

    state.technique = MagicMock()

    state.targeting_map = defaultdict(list)

    state.menu_items = MagicMock()

    state._external_on_selection = None
    state._external_is_valid_entry = None

    return state


def test_initialize_items_bypass_enemy_target(state):
    enemy = MagicMock()

    player = state.character
    opponent = MagicMock()

    state.technique.behaviors.bypasses_selection = True
    state.technique.target = {
        "enemy_monster": True,
    }

    state.combat_session.field_monsters.get_all_monsters.return_value = {
        player: [],
        opponent: [enemy],
    }

    state._create_menu_item = MagicMock(return_value="enemy-item")

    items = list(state.initialize_items())

    assert items == ["enemy-item"]

    state._create_menu_item.assert_called_once_with(enemy)


def test_initialize_items_bypass_self_target(state):
    monster = state.monster

    state.technique.behaviors.bypasses_selection = True
    state.technique.target = {
        "enemy_monster": False,
    }

    state._create_menu_item = MagicMock(return_value="self-item")

    items = list(state.initialize_items())

    assert items == ["self-item"]

    state._create_menu_item.assert_called_once_with(monster)


def test_initialize_items_enemy_targets(state):
    own = MagicMock()
    enemy = MagicMock()

    player = object()
    opponent = object()

    state.character = player

    state.technique.behaviors.bypasses_selection = False
    state.technique.target = {
        "enemy_monster": True,
    }
    state.technique.targets_enemy.return_value = True

    state.combat_session.field_monsters.get_all_monsters.return_value = {
        player: [own],
        opponent: [enemy],
    }

    state._create_menu_item = MagicMock(return_value="enemy-item")

    items = list(state.initialize_items())

    assert items == ["enemy-item"]

    state._create_menu_item.assert_called_once_with(enemy)

    assert own in state.targeting_map["own_monster"]
    assert enemy in state.targeting_map["enemy_monster"]


def test_initialize_items_own_targets(state):
    own = MagicMock()

    player = state.character
    opponent = MagicMock()

    state.technique.behaviors.bypasses_selection = False

    state.technique.target = {
        "own_monster": True,
    }

    state.combat_session.field_monsters.get_all_monsters.return_value = {
        player: [own],
        opponent: [],
    }

    state._create_menu_item = MagicMock(return_value="own-item")

    items = list(state.initialize_items())

    assert items == ["own-item"]

    assert own in state.targeting_map["own_monster"]


def test_create_menu_item_raises_without_sprite(state):
    monster = MagicMock()
    monster.name = "MissingSprite"

    state.combat.sprite_map.get_sprite.return_value = None

    with pytest.raises(KeyError):
        state._create_menu_item(monster)


def test_determine_target_selects_first_enabled_target(
    state,
):
    monster = MagicMock()

    menu_item = MagicMock()
    menu_item.enabled = True

    state.technique.target = {
        "enemy_monster": True,
    }

    state.targeting_map = {
        "enemy_monster": [monster],
    }

    state.search_items = MagicMock(return_value=menu_item)

    state.menu_items = MagicMock()
    state.menu_items.sprites.return_value = [menu_item]

    state.determine_target()

    assert state.selected_index == 0


def test_determine_target_skips_disabled_targets(
    state,
):
    monster = MagicMock()

    menu_item = MagicMock()
    menu_item.enabled = False

    state.technique.target = {
        "enemy_monster": True,
    }

    state.targeting_map = {
        "enemy_monster": [monster],
    }

    state.search_items = MagicMock(return_value=menu_item)

    state.determine_target()

    assert not hasattr(
        state,
        "selected_index",
    )


def test_refresh_layout_calls_determine_target(
    state,
    mocker,
):
    state.determine_target = MagicMock()

    refresh = mocker.patch(
        "tuxemon.states.combat_menus.Menu.refresh_layout",
        return_value="layout",
    )

    result = state.refresh_layout()

    state.determine_target.assert_called_once()

    refresh.assert_called_once()

    assert result == "layout"


def test_update_cursor_visibility_hides_cursor(
    state,
):
    state.hide_cursor = MagicMock()

    state.update_cursor_visibility()

    state.hide_cursor.assert_called_once()


def test_on_open_auto_selects_single_enabled_item(
    state,
):
    item = MagicMock()
    item.enabled = True

    state.menu_items = [item]

    state.on_menu_selection = MagicMock()

    state.on_open()

    state.on_menu_selection.assert_called_once_with(item)


def test_on_open_does_not_select_multiple_items(
    state,
):
    item1 = MagicMock(enabled=True)
    item2 = MagicMock(enabled=True)

    state.menu_items = [item1, item2]

    state.on_menu_selection = MagicMock()

    state.on_open()

    state.on_menu_selection.assert_not_called()


def test_on_open_ignores_no_enabled_items(
    state,
):
    item = MagicMock(enabled=False)

    state.menu_items = [item]

    state.on_menu_selection = MagicMock()

    state.on_open()

    state.on_menu_selection.assert_not_called()


def test_on_menu_selection_delegates_callback(
    state,
):
    callback = MagicMock()

    state._external_on_selection = callback

    item = MagicMock()

    state.on_menu_selection(item)

    callback.assert_called_once_with(item)


def test_on_menu_selection_without_callback(
    state,
):
    state._external_on_selection = None

    item = MagicMock()

    assert state.on_menu_selection(item) is None


@pytest.mark.parametrize(
    "monster,expected",
    [
        pytest.param(
            None,
            False,
            id="none",
        ),
        pytest.param(
            MagicMock(),
            True,
            id="monster",
        ),
    ],
)
def test_is_valid_entry_default(
    state,
    monster,
    expected,
):
    state._external_is_valid_entry = None

    assert state.is_valid_entry(monster) is expected


def test_is_valid_entry_external_validator(
    state,
):
    validator = MagicMock(return_value=False)

    state._external_is_valid_entry = validator

    monster = MagicMock()

    assert state.is_valid_entry(monster) is False

    validator.assert_called_once_with(monster)


def test_determine_target_selects_implicitly_allowed_enemy(state):
    enemy = MagicMock()
    menu_item = MagicMock(enabled=True)

    state.technique.target = {"enemy_monster": False}
    state.technique.targets_enemy.return_value = True
    state.targeting_map = {"enemy_monster": [enemy]}
    state.search_items = MagicMock(return_value=menu_item)
    state.menu_items.sprites.return_value = [menu_item]

    state.determine_target()

    assert state.selected_index == 0

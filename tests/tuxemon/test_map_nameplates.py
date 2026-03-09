# SPDX-License-Identifier: GPL-3.0
from types import SimpleNamespace

from tuxemon.map.view import (
    LOCAL_PLAYER_NAME_COLOR,
    MapRenderer,
    REMOTE_PLAYER_NAME_COLOR,
)


def test_name_color_is_violet_for_local_player() -> None:
    renderer = MapRenderer.__new__(MapRenderer)
    local_player = SimpleNamespace()
    npc = local_player
    npc.session = SimpleNamespace(player=local_player)

    color = MapRenderer._get_name_color(renderer, npc)

    assert color == LOCAL_PLAYER_NAME_COLOR


def test_name_color_is_white_for_remote_player() -> None:
    renderer = MapRenderer.__new__(MapRenderer)
    local_player = SimpleNamespace()
    remote_npc = SimpleNamespace(session=SimpleNamespace(player=local_player))

    color = MapRenderer._get_name_color(renderer, remote_npc)

    assert color == REMOTE_PLAYER_NAME_COLOR

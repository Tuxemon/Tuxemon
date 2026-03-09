# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

from tuxemon.network.manager import NetworkManager


def test_update_skips_client_placement_when_no_active_map() -> None:
    parent = MagicMock()
    parent.get_map_name.side_effect = ValueError(
        "Name of the map requested when no map is active"
    )

    manager = NetworkManager(parent)
    manager.client = MagicMock(listening=True, registry={})
    manager.server = MagicMock(listening=False)

    manager.update(0.016)

    manager.client.update.assert_called_once()
    parent.npc_manager.add_clients_to_map.assert_not_called()


def test_update_places_clients_when_map_is_available() -> None:
    parent = MagicMock()
    parent.get_map_name.return_value = "start-town"

    manager = NetworkManager(parent)
    manager.client = MagicMock(listening=True, registry={"abc": {}})
    manager.server = MagicMock(listening=False)

    manager.update(0.016)

    parent.npc_manager.add_clients_to_map.assert_called_once_with(
        {"abc": {}}, "start-town"
    )

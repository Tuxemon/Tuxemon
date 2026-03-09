# SPDX-License-Identifier: GPL-3.0
from unittest.mock import MagicMock

import tuxemon.main as main_module


def test_headless_sets_local_session_client(monkeypatch) -> None:
    fake_client = MagicMock()
    fake_client.network_manager.server = MagicMock()

    monkeypatch.setattr(main_module.log, "configure", MagicMock())
    monkeypatch.setattr(main_module, "HeadlessClient", MagicMock(return_value=fake_client))

    set_client = MagicMock()
    monkeypatch.setattr(main_module.local_session, "set_client", set_client)

    config = MagicMock()
    context = MagicMock()

    main_module.headless(config=config, context=context, host_server=True, server_port=40081)

    set_client.assert_called_once_with(fake_client)
    fake_client.push_state.assert_called_once_with("HeadlessServerState")
    fake_client.main.assert_called_once()

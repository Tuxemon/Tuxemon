# SPDX-License-Identifier: GPL-3.0
import asyncio
import logging

import tuxemon.network.websocket_client as websocket_client_module
from tuxemon.network.websocket_client import WebsocketClientWrapper


class _RefusedConnect:
    async def __aenter__(self):
        raise ConnectionRefusedError()

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_connect_refused_logs_uri_and_side_hint(caplog, monkeypatch):
    client = WebsocketClientWrapper(port=40081)
    client._running.set()

    monkeypatch.setattr(
        websocket_client_module.websockets,
        "connect",
        lambda uri: _RefusedConnect(),
    )

    with caplog.at_level(logging.ERROR):
        asyncio.run(client._connect_and_listen("127.0.0.1", 40081))

    assert "local server-side refusal" in (client.last_error or "")
    assert "ws://127.0.0.1:40081" in caplog.text
    assert "Ensure a websocket server is listening" in caplog.text

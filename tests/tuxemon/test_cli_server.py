# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from tuxemon.cli.deps import get_processor, get_processor_ws
from tuxemon.cli.server import app


@dataclass
class FakeSnapshot:
    hour: int = 8
    day: int = 1
    month: int = 1
    year: int = 1
    season: str = "spring"
    stage_of_day: str = "morning"


@pytest.fixture
def mock_processor():
    processor = MagicMock()

    player = processor.session.player
    player.name = "Ash"
    player.instance_id = "uuid-1234"
    player.current_map = "test_map"
    player.tile_pos = [1, 2]
    player.game_variables.has.return_value = True
    player.game_variables.get.return_value = "test_value"
    player.game_variables.get_state.return_value = {"key": "value"}
    player.money_controller.money_manager.money = 100
    player.money_controller.money_manager.bank_account = 500
    player.monsters = []
    player.party.monsters = []
    player.party.party_size = 0
    player.party.party_limit = 6
    player.party.level_lowest = None
    player.party.level_highest = None
    player.party.level_average = None
    player.party.alignment = None
    player.party.is_fainted = False
    player.party.is_healed = True

    processor.commands = []
    processor.session.time.get_time_variables.return_value = FakeSnapshot()

    return processor


@pytest.fixture
def client(mock_processor):
    app.dependency_overrides[get_processor] = lambda: mock_processor
    app.dependency_overrides[get_processor_ws] = lambda: mock_processor
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "Tuxemon CLI API"


def test_shutdown(client, mock_processor):
    r = client.post("/shutdown")
    assert r.status_code == 200
    assert r.json()["status"] == "shutdown_initiated"
    mock_processor.client.queue_command.assert_called_once()


def test_session_player(client):
    r = client.get("/session/player")
    data = r.json()
    assert data["name"] == "Ash"
    assert data["money"] == 100
    assert data["current_map"] == "test_map"
    assert data["bank_account"] == 500
    assert data["party_size"] == 0


def test_session_party_empty(client):
    r = client.get("/session/party")
    assert r.status_code == 200
    assert r.json() == []


def test_print_variables_no_params(client):
    r = client.get("/session/vars/print")
    assert r.status_code == 200
    assert "output" in r.json()


def test_print_variables_with_var(client):
    r = client.get("/session/vars/print?variables=some_var")
    assert r.status_code == 200
    output = r.json()["output"]
    assert any("some_var" in line for line in output)
    assert any("test_value" in line for line in output)


def test_print_variables_empty_string(client):
    r = client.get("/session/vars/print?variables=:::")
    assert r.status_code == 422


def test_help_empty(client):
    r = client.get("/help")
    assert r.status_code == 200
    assert r.json() == []


def test_help_unknown_command(client):
    r = client.get("/help?name=nonexistent")
    assert r.status_code == 404


def test_run_command(client, mock_processor):
    mock_processor.execute.return_value = {
        "status": "queued",
        "command": "test",
        "args": "",
    }
    r = client.post("/run", json={"line": "test"})
    assert r.status_code == 200
    assert r.json()["status"] == "queued"
    mock_processor.execute.assert_called_once_with("test")


def test_run_command_error(client, mock_processor):
    mock_processor.execute.side_effect = RuntimeError("boom")
    r = client.post("/run", json={"line": "bad"})
    assert r.status_code == 400
    assert "boom" in r.json()["detail"]


def test_print_variables_not_found(client, mock_processor):
    mock_processor.session.player.game_variables.has.return_value = False
    r = client.get("/session/vars/print?variables=missing_var")
    assert r.status_code == 200
    assert any("has not been set" in line for line in r.json()["output"])


def test_session_snapshot(client):
    r = client.get("/session/snapshot")
    assert r.status_code == 200
    data = r.json()
    assert data["hour"] == 8
    assert data["season"] == "spring"
    assert data["stage_of_day"] == "morning"

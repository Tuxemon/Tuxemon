# SPDX-License-Identifier: GPL-3.0
from __future__ import annotations

from pathlib import Path
import sqlite3

from tuxemon.network.state_store import ServerStateStore


def test_upsert_and_load_player_state(tmp_path: Path) -> None:
    store = ServerStateStore(tmp_path / "state.db")
    payload = {
        "cuuid": "abc",
        "wallet_address": "WalletXYZ",
        "map_name": "forest",
        "char_dict": {
            "name": "PlayerOne",
            "tile_pos": [1, 2],
            "facing": "DOWN",
            "running": False,
            "monsters": [],
            "inventory": [],
        },
        "updated_at": "2026-01-01T00:00:00",
    }

    store.upsert_player_state("WalletXYZ", payload)

    loaded = store.load_player_states()
    assert "WalletXYZ" in loaded
    assert loaded["WalletXYZ"]["map_name"] == "forest"
    assert loaded["WalletXYZ"]["char_dict"]["name"] == "PlayerOne"


def test_append_state_event_persists_rows(tmp_path: Path) -> None:
    store = ServerStateStore(tmp_path / "state.db")
    store.append_state_event(
        state_key="WalletXYZ",
        event_type="STATE_SNAPSHOT",
        event_payload={"map_name": "forest"},
        created_at="2026-01-01T00:00:00",
    )

    with sqlite3.connect(tmp_path / "state.db") as conn:
        row = conn.execute("SELECT COUNT(*) FROM state_events").fetchone()
    assert row is not None
    assert row[0] == 1

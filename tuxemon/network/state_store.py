# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class ServerStateStore:
    """SQLite-backed persistence for multiplayer server state."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS player_states (
                    state_key TEXT PRIMARY KEY,
                    cuuid TEXT NOT NULL,
                    wallet_address TEXT NOT NULL,
                    map_name TEXT NOT NULL,
                    char_dict_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS state_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state_key TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def upsert_player_state(self, state_key: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO player_states (
                    state_key, cuuid, wallet_address, map_name, char_dict_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(state_key) DO UPDATE SET
                    cuuid=excluded.cuuid,
                    wallet_address=excluded.wallet_address,
                    map_name=excluded.map_name,
                    char_dict_json=excluded.char_dict_json,
                    updated_at=excluded.updated_at
                """,
                (
                    state_key,
                    str(payload.get("cuuid", "")),
                    str(payload.get("wallet_address", "")),
                    str(payload.get("map_name", "")),
                    json.dumps(payload.get("char_dict") or {}),
                    str(payload.get("updated_at", "")),
                ),
            )

    def append_state_event(
        self,
        state_key: str,
        event_type: str,
        event_payload: dict[str, Any],
        created_at: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO state_events (state_key, event_type, event_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (state_key, event_type, json.dumps(event_payload), created_at),
            )

    def load_player_states(self) -> dict[str, dict[str, Any]]:
        loaded: dict[str, dict[str, Any]] = {}
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT state_key, cuuid, wallet_address, map_name, char_dict_json, updated_at
                FROM player_states
                """
            ).fetchall()

        for row in rows:
            loaded[row["state_key"]] = {
                "cuuid": row["cuuid"],
                "wallet_address": row["wallet_address"],
                "map_name": row["map_name"],
                "char_dict": json.loads(row["char_dict_json"]),
                "updated_at": row["updated_at"],
            }
        return loaded

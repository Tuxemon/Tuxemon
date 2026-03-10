#!/usr/bin/env python3
"""Inspect persisted multiplayer server state.

Shows latest player snapshots from `server/state.db` and fallback JSON file.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def main() -> None:
    server_dir = Path("server")
    db_path = server_dir / "state.db"
    json_path = server_dir / "characters.json"

    print(f"sqlite: {db_path.resolve()}")
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT state_key, wallet_address, map_name, updated_at FROM player_states ORDER BY updated_at DESC"
            ).fetchall()
            print(f"player_states rows: {len(rows)}")
            for row in rows[:20]:
                print(f"- key={row[0]} wallet={row[1]} map={row[2]} updated_at={row[3]}")

            events = conn.execute("SELECT COUNT(*) FROM state_events").fetchone()
            print(f"state_events rows: {events[0] if events else 0}")
    else:
        print("state.db not found")

    print()
    print(f"json: {json_path.resolve()}")
    if json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        print(f"characters.json entries: {len(payload) if isinstance(payload, dict) else 0}")
    else:
        print("characters.json not found")


if __name__ == "__main__":
    main()

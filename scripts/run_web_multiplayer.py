"""Run a browser-playable multiplayer SolaMon prototype.

Starts:
- a static HTTP server for the web client
- a WebSocket server that synchronizes player movement
"""

from __future__ import annotations

import argparse
import asyncio
import json
import secrets
from dataclasses import dataclass, field
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

import websockets


@dataclass
class Player:
    """Server-side player state."""

    pid: str
    name: str
    x: float
    y: float
    color: str


@dataclass
class MultiplayerState:
    """Holds active players and sockets."""

    players: dict[str, Player] = field(default_factory=dict)
    sockets: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "type": "state",
            "players": {
                pid: {
                    "name": player.name,
                    "x": player.x,
                    "y": player.y,
                    "color": player.color,
                }
                for pid, player in self.players.items()
            },
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http-port", type=int, default=8080)
    parser.add_argument("--ws-port", type=int, default=8765)
    return parser.parse_args()


def start_static_server(http_port: int) -> ThreadingHTTPServer:
    web_root = Path(__file__).resolve().parent.parent / "web"

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(web_root), **kwargs)

    server = ThreadingHTTPServer(("0.0.0.0", http_port), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[web] Static client available at http://localhost:{http_port}")
    return server


async def broadcast_state(state: MultiplayerState) -> None:
    if not state.sockets:
        return

    payload = json.dumps(state.snapshot())
    dead: list[str] = []
    for pid, ws in state.sockets.items():
        try:
            await ws.send(payload)
        except Exception:
            dead.append(pid)

    for pid in dead:
        state.sockets.pop(pid, None)
        state.players.pop(pid, None)


def random_color() -> str:
    palette = [
        "#ff6b6b",
        "#4ecdc4",
        "#ffe66d",
        "#5f27cd",
        "#1dd1a1",
        "#54a0ff",
        "#ff9f43",
    ]
    return secrets.choice(palette)


async def handler(websocket: Any, state: MultiplayerState) -> None:
    player_id = secrets.token_hex(4)
    state.sockets[player_id] = websocket
    state.players[player_id] = Player(
        pid=player_id,
        name=f"Trainer-{player_id[:4]}",
        x=400,
        y=250,
        color=random_color(),
    )

    await websocket.send(json.dumps({"type": "welcome", "id": player_id}))
    await broadcast_state(state)

    try:
        async for msg in websocket:
            data = json.loads(msg)
            msg_type = data.get("type")
            player = state.players.get(player_id)
            if not player:
                continue

            if msg_type == "move":
                player.x = max(20, min(780, float(data.get("x", player.x))))
                player.y = max(20, min(480, float(data.get("y", player.y))))
            elif msg_type == "rename":
                name = str(data.get("name", "")).strip()
                player.name = name[:16] or player.name

            await broadcast_state(state)
    finally:
        state.sockets.pop(player_id, None)
        state.players.pop(player_id, None)
        await broadcast_state(state)


async def run_ws_server(ws_port: int) -> None:
    state = MultiplayerState()
    async with websockets.serve(
        lambda ws: handler(ws, state),
        "0.0.0.0",
        ws_port,
    ):
        print(f"[websocket] Multiplayer server listening on ws://localhost:{ws_port}")
        await asyncio.Future()


def main() -> None:
    args = parse_args()
    static_server = start_static_server(args.http_port)

    try:
        asyncio.run(run_ws_server(args.ws_port))
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        static_server.shutdown()


if __name__ == "__main__":
    main()

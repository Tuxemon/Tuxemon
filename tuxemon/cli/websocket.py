# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, WebSocket
from starlette.websockets import WebSocketDisconnect

from tuxemon.cli.deps import get_processor_ws

if TYPE_CHECKING:
    from tuxemon.cli.processor import CommandProcessor

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard"])


@router.websocket("/live/session")
async def live_session(
    websocket: WebSocket,
    proc: CommandProcessor = Depends(get_processor_ws),
) -> None:
    await websocket.accept()
    logger.info("WebSocket client connected to /live/session")

    state_lock = asyncio.Lock()

    async def build_snapshot() -> dict[str, Any] | None:
        """Return a full dashboard snapshot of the current game state."""
        session = proc.session
        if session is None:
            return None

        player = session.player

        return {
            "player": {
                "name": player.name,
                "map": player.current_map,
                "tile_pos": player.tile_pos,
                "money": player.money_controller.money_manager.money,
                "bank_account": player.money_controller.money_manager.bank_account,
                "party_size": len(player.monsters),
                "variables": player.variable_manager.player.get_state(),
                "world_variables": player.variable_manager.world.get_state(),
            },
            "party": [
                {
                    "name": m.name,
                    "species": m.species_name,
                    "level": m.level,
                    "gender": m.gender_symbol,
                    "hp": {
                        "current": m.current_hp,
                        "max": m.hp,
                        "ratio": m.hp_ratio,
                    },
                    "exp": {"progress": m.experience_progress_percent},
                }
                for m in player.party.monsters
            ],
            "party_stats": {
                "size": player.party.party_size,
                "limit": player.party.party_limit,
                "level_lowest": player.party.level_lowest,
                "level_highest": player.party.level_highest,
                "level_average": player.party.level_average,
                "alignment": player.party.alignment,
                "is_fainted": player.party.is_fainted,
                "is_healed": player.party.is_healed,
            },
            "time": asdict(session.time.get_time_variables()),
        }

    async def broadcast_updates() -> None:
        """Pushes game state to the dashboard every second."""
        try:
            while True:
                async with state_lock:
                    snapshot = await build_snapshot()

                if snapshot is None:
                    logger.warning(
                        "No active session; stopping WebSocket stream."
                    )
                    break

                try:
                    await websocket.send_json(snapshot)
                except Exception:
                    logger.warning(
                        "Failed to send snapshot; stopping broadcast."
                    )
                    break

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Broadcast task cancelled.")
            raise

    async def receive_updates() -> None:
        """Receive variable mutation commands from the dashboard."""
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                except WebSocketDisconnect:
                    break
                except Exception:
                    logger.warning("Invalid WebSocket message; ignoring.")
                    continue

                action = data.get("action")
                scope = data.get("scope")
                key = data.get("key")
                value = data.get("value")

                manager = proc.session.player.variable_manager
                target = manager.player if scope == "player" else manager.world

                async with state_lock:
                    if action == "set" and key:
                        target.set(key, value)
                        logger.info(f"Dashboard: Set {scope}.{key} = {value}")

                    elif action == "remove" and key:
                        target.remove(key)
                        logger.info(f"Dashboard: Removed {scope}.{key}")

        except asyncio.CancelledError:
            logger.info("Receive task cancelled.")
            raise

    # Run broadcast + receive concurrently
    broadcast_task = asyncio.create_task(broadcast_updates())
    receive_task = asyncio.create_task(receive_updates())

    done, pending = await asyncio.wait(
        {broadcast_task, receive_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    # Cancel the other task
    for task in pending:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    logger.info("WebSocket client disconnected cleanly.")

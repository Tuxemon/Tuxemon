# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tuxemon.cli.routers import commands, debug, session, system
from tuxemon.cli.websocket import router as ws_router

if TYPE_CHECKING:
    from tuxemon.cli.processor import CommandProcessor

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tuxemon CLI API",
    description="HTTP interface for interacting with the Tuxemon command processor.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(commands.router)
app.include_router(debug.router)
app.include_router(system.router)
app.include_router(ws_router)


def start_api(
    processor: CommandProcessor, host: str = "127.0.0.1", port: int = 8000
) -> None:
    app.state.processor = processor
    logger.info("Starting Tuxemon CLI API on %s:%d", host, port)

    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)
    server.run()

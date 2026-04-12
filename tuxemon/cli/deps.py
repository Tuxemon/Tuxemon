# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from fastapi import Request, WebSocket

from tuxemon.cli.processor import CommandProcessor


def get_processor(request: Request) -> CommandProcessor:
    proc = request.app.state.processor
    assert isinstance(proc, CommandProcessor)
    return proc


def get_processor_ws(websocket: WebSocket) -> CommandProcessor:
    proc = websocket.app.state.processor
    assert isinstance(proc, CommandProcessor)
    return proc

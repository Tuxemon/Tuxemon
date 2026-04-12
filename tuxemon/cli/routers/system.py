# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from tuxemon.cli.deps import get_processor

if TYPE_CHECKING:
    from tuxemon.cli.processor import CommandProcessor

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])


@router.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "message": "Tuxemon CLI API",
        "docs": "/docs",
        "dashboard": "/dashboard",
    }


@router.post(
    "/shutdown",
    summary="Shutdown the game",
    description="Queues a shutdown command for the Tuxemon client.",
    response_description="A confirmation message.",
)
async def shutdown(
    proc: CommandProcessor = Depends(get_processor),
) -> dict[str, str]:
    proc.client.queue_command(lambda: proc.client.quit())
    logger.info("Shutdown initiated via API.")
    return {"status": "shutdown_initiated", "message": "The game is closing."}


@router.get("/dashboard", include_in_schema=False)
async def dashboard() -> HTMLResponse:
    html_path = Path(__file__).parent.parent / "dashboard.html"
    if not html_path.exists():
        raise HTTPException(
            status_code=404, detail="Dashboard file not found."
        )
    return HTMLResponse(html_path.read_text(encoding="utf-8"))

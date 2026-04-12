# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from tuxemon.cli.context import InvokeContext
from tuxemon.cli.deps import get_processor

if TYPE_CHECKING:
    from tuxemon.cli.processor import CommandProcessor

router = APIRouter(tags=["Commands"])


class Cmd(BaseModel):
    """Represents a CLI command sent to the Tuxemon engine."""

    line: str = Field(description="The raw command string to execute.")


@router.get(
    "/help",
    summary="List available commands",
    description="Returns all CLI commands or details for a specific command.",
    response_description="A list of commands or a detailed command description.",
)
async def list_commands(
    proc: CommandProcessor = Depends(get_processor),
    name: str | None = None,
) -> Any:
    ctx = InvokeContext(
        processor=proc,
        session=proc.session,
        root_command=proc.root_command,
        current_command=proc.root_command,
        formatter=proc.formatter,
    )

    if name:
        cmd = next((c for c in proc.commands if c.name == name), None)
        if not cmd:
            raise HTTPException(
                status_code=404, detail=f"Command '{name}' not found"
            )
        return {
            "name": cmd.name,
            "description": cmd.description,
            "example": cmd.example,
            "parameters": [p.name for p in cmd.get_parameters(ctx)],
        }

    return [
        {"name": c.name, "description": c.description} for c in proc.commands
    ]


@router.post(
    "/run",
    summary="Execute a CLI command",
    description="Runs a command through the Tuxemon CommandProcessor.",
    response_description="The result of the executed command.",
)
async def run_command(
    cmd: Cmd,
    proc: CommandProcessor = Depends(get_processor),
) -> Any:
    try:
        return proc.execute(cmd.line)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

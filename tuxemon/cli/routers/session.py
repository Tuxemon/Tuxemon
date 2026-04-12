# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException

from tuxemon.cli.deps import get_processor

if TYPE_CHECKING:
    from tuxemon.cli.processor import CommandProcessor

router = APIRouter(prefix="/session", tags=["Session"])


@router.get(
    "/vars/print",
    summary="Print game variables",
    description="Replicates the Tuxemon 'print' event action, returning variable values.",
    response_description="A dictionary containing printed variable output.",
)
async def print_variables(
    proc: CommandProcessor = Depends(get_processor),
    variables: str | None = None,
) -> dict[str, Any]:
    player = proc.session.player
    output_lines = []

    if variables:
        vars_list = [v for v in variables.split(":") if v]
        if not vars_list:
            raise HTTPException(
                status_code=422, detail="No valid variable names provided."
            )
        for var in vars_list:
            if player.game_variables.has(var):
                output_lines.append(f"{var}: {player.game_variables.get(var)}")
            else:
                output_lines.append(
                    f"'{var}' has not been set yet by map actions."
                )
    else:
        state = player.game_variables.get_state()
        output_lines.append(
            str(state) if state else "No game variables have been set."
        )

    return {"output": output_lines}


@router.get(
    "/party",
    summary="Get player's party",
    description="Returns all monsters currently in the player's party.",
    response_description="A list of monsters with stats and moves.",
)
async def get_party(
    proc: CommandProcessor = Depends(get_processor),
) -> list[dict[str, Any]]:
    return [
        {
            "name": m.name,
            "gender": m.gender_symbol,
            "type": [element.name for element in m.types.current],
            "level": m.level,
            "hp": m.current_hp,
            "max_hp": m.hp,
            "exp": m.total_experience,
            "moves": [move.name for move in m.moves.moves],
        }
        for m in proc.session.player.monsters
    ]


@router.get(
    "/player",
    summary="Get player session info",
    description="Returns player identity, map, position, money, and party size.",
    response_description="A dictionary containing player session data.",
)
async def session_player(
    proc: CommandProcessor = Depends(get_processor),
) -> dict[str, Any]:
    p = proc.session.player
    return {
        "name": p.name,
        "uuid": p.instance_id,
        "current_map": p.current_map,
        "tile_pos": p.tile_pos,
        "money": p.money_controller.money_manager.money,
        "bank_account": p.money_controller.money_manager.bank_account,
        "party_size": len(p.monsters),
    }


@router.get(
    "/snapshot",
    summary="Get world time snapshot",
    description="Returns the current in-game time including hour, date, season, and day stage.",
    response_description="A dictionary containing the current time snapshot.",
)
async def session_snapshot(
    proc: CommandProcessor = Depends(get_processor),
) -> dict[str, Any]:
    return asdict(proc.session.time.get_time_variables())

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from tuxemon.cli.deps import get_processor

if TYPE_CHECKING:
    from tuxemon.cli.processor import CommandProcessor

router = APIRouter(tags=["Debug"])


class Cmd(BaseModel):
    """Represents a CLI command sent to the Tuxemon engine."""

    line: str = Field(description="The raw command string to execute.")


@router.post(
    "/test",
    summary="Test a condition string",
    description=(
        "Parses and evaluates a Tuxemon condition expression. "
        "The input is treated as the right-hand side of an 'is' condition — "
        "do not include the 'is' prefix yourself."
    ),
    response_description="The condition and its evaluation result.",
)
async def test_condition(
    cmd: Cmd,
    proc: CommandProcessor = Depends(get_processor),
) -> dict[str, Any]:
    from tuxemon.db import BoundingBox, Operator, SpatialCondition
    from tuxemon.script.parser import parse_condition_string
    from tuxemon.tools import safe_enum_value

    line = f"is {cmd.line}"
    try:
        opr, typ, args = parse_condition_string(line)
        operator = safe_enum_value(Operator, opr, default=Operator.IS)
        cond = SpatialCondition(
            type=typ,
            parameters=args,
            box=BoundingBox(x=0, y=0, width=1, height=1),
            operator=operator,
            name="API_REQUEST",
        )
        result = proc.session.client.evaluator.evaluate(cond)
        return {"condition": cmd.line, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

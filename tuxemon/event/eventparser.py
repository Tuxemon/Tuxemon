# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from tuxemon.db import (
    Behavior,
    BoundingBox,
    EventObject,
    Operator,
    ParameterizableRule,
    SpatialCondition,
)
from tuxemon.script.parser import (
    parse_action_string,
    parse_behav_string,
    parse_condition_string,
)
from tuxemon.tools import safe_enum_value

if TYPE_CHECKING:
    from tuxemon.db import BoundingBox

logger = logging.getLogger(__name__)


class EventParser:
    """Parses raw event data from TMX or YAML files into game objects."""

    def create_event_object(
        self,
        event_data: dict[str, Any],
        name: str,
        box: BoundingBox,
        priority: int = 0,
        timeout: float | None = None,
        delay: float | None = None,
    ) -> EventObject:
        """
        Creates an EventObject from a dictionary of event data.

        Expected keys:
        - "behav": list of behavior strings
        - "conditions": list of condition strings
        - "actions": list of action strings

        This method centralizes parsing logic from TMX or YAML sources.
        """
        event_id = uuid4().int
        conditions: list[SpatialCondition] = []
        actions: list[ParameterizableRule] = []
        logger.debug(f"Creating event object: {name} at ({box})")

        # Parse behaviors first, as they add both conditions and actions
        # NOTE: Conditions use structured lists; actions require joined strings.
        # This reflects how the engine parses behavior logic.
        behavs_raw = event_data.get("behav") or []
        behaviors: list[Behavior] = []

        for key, value in enumerate(behavs_raw, start=1):
            behav_type, args = parse_behav_string(value)
            behaviors.append(
                Behavior(
                    type=behav_type,
                    args=args,
                    name=f"behav{key * 10}",
                )
            )

        # Parse conditions
        conds = event_data.get("conditions") or []
        for key, value in enumerate(conds, start=1):
            logger.debug(f"Parsing condition {key}: {value}")
            _operator, cond_type, args = parse_condition_string(value)
            logger.debug(
                f" → operator: {_operator}, type: {cond_type}, args: {args}"
            )

            operator = safe_enum_value(
                Operator, _operator, default=Operator.IS
            )

            condition = SpatialCondition(
                type=cond_type,
                parameters=args,
                box=box,
                operator=operator,
                name=f"cond{key * 10}",
            )
            conditions.append(condition)

        # Parse actions
        acts = event_data.get("actions") or []
        for key, value in enumerate(acts, start=1):
            logger.debug(f"Parsing action {key}: {value}")
            act_type, args = parse_action_string(value)
            logger.debug(f" → type: {act_type}, args: {args}")
            actions.append(
                ParameterizableRule(
                    type=act_type,
                    parameters=args,
                    name=f"act{key * 10}",
                )
            )

        return EventObject(
            id=event_id,
            name=name,
            box=box,
            priority=priority,
            timeout=timeout,
            delay=delay,
            conds=conditions,
            acts=actions,
            behavs=behaviors,
        )

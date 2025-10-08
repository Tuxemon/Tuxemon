# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from tuxemon.event import EventObject, MapAction, MapCondition
from tuxemon.script.parser import (
    parse_action_string,
    parse_behav_string,
    parse_condition_string,
)

logger = logging.getLogger(__name__)


class EventParser:
    """Parses raw event data from TMX or YAML files into game objects."""

    def create_event_object(
        self,
        event_data: dict[str, Any],
        source_type: str,
        name: str,
        x: int,
        y: int,
        w: int,
        h: int,
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
        conditions: list[MapCondition] = []
        actions: list[MapAction] = []
        logger.debug(f"Creating event object: {name} at ({x}, {y}, {w}, {h})")

        # Parse behaviors first, as they add both conditions and actions
        # NOTE: Conditions use structured lists; actions require joined strings.
        # This reflects how the engine parses behavior logic.
        behavs = event_data.get("behav") or []
        for key, value in enumerate(behavs, start=1):
            logger.debug(f"Parsing behavior {key}: {value}")
            behav_type, args = parse_behav_string(value)
            logger.debug(f" → type: {behav_type}, args: {args}")

            # Create a behavior condition
            conditions.insert(
                0,
                MapCondition(
                    "behav",
                    [behav_type, *args],
                    x,
                    y,
                    w,
                    h,
                    "is",
                    f"behav{str(key*10)}",
                ),
            )
            # Create a behavior action
            actions.insert(
                0,
                MapAction(
                    "behav",
                    [":".join([behav_type, *args])],
                    f"behav{str(key*10)}",
                ),
            )

        # Parse conditions
        conds = event_data.get("conditions") or []
        for key, value in enumerate(conds, start=1):
            logger.debug(f"Parsing condition {key}: {value}")
            operator, cond_type, args = parse_condition_string(value)
            logger.debug(
                f" → operator: {operator}, type: {cond_type}, args: {args}"
            )
            conditions.append(
                MapCondition(
                    type=cond_type,
                    parameters=args,
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    operator=operator,
                    name=f"cond{str(key*10)}",
                )
            )

        # Parse actions
        acts = event_data.get("actions") or []
        for key, value in enumerate(acts, start=1):
            logger.debug(f"Parsing action {key}: {value}")
            act_type, args = parse_action_string(value)
            logger.debug(f" → type: {act_type}, args: {args}")
            actions.append(MapAction(act_type, args, f"act{str(key*10)}"))

        return EventObject(event_id, name, x, y, w, h, conditions, actions)

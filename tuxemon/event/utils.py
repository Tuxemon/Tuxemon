# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuxemon.db import EventObject, ParameterizableRule, SpatialCondition
    from tuxemon.session import Session


logger = logging.getLogger(__name__)


@contextmanager
def add_error_context(
    event: EventObject,
    item: SpatialCondition | ParameterizableRule,
    session: Session,
) -> Generator[None, None, None]:
    """
    Add error information about the involved condition or action.

    This should be used as a context manager for code that may
    fail associated with a particular condition or action.

    Parameters:
        event: Event associated with the condition or action.
        item: Condition or action that produces the error.
        session: Object containing the session information.
    """
    try:
        yield
    except Exception as original_exc:
        from lxml import etree

        file_name = session.client.map_manager.get_map_filepath()
        try:
            tree = etree.parse(file_name)
            event_node = tree.find(f"//object[@id='{event.id}']")
        except Exception as parse_exc:
            logger.error(
                f"Failed to parse map file '{file_name}': {parse_exc}"
            )
            raise original_exc

        msg_lines = [f"\nError in map file: {file_name}"]

        if event_node is not None:
            event_summary = (
                etree.tostring(event_node).decode().split("\n")[0].strip()
            )
            msg_lines.append(f"Event: {event_summary}")
            msg_lines.append(f"Line: {event_node.sourceline}")

            if item.name:
                child_node = event_node.find(
                    f".//property[@name='{item.name}']"
                )
                if child_node is not None:
                    child_summary = etree.tostring(child_node).decode().strip()
                    msg_lines.append(f"Property: {child_summary}")
                    msg_lines.append(f"Line: {child_node.sourceline}")
        else:
            msg_lines.append(f"Event with ID '{event.id}' not found in XML.")

        print(dedent("\n".join(msg_lines)))
        raise original_exc

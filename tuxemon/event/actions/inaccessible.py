# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world import WorldState


@final
@dataclass
class InaccessibleAction(EventAction):
    """
    Area inaccessible (added to the collision zone).

    Script usage:
        .. code-block::

            inaccessible <event_id>

    Script parameters:
        event_id: The id of the event.

    """

    name = "inaccessible"
    event_id: int

    def start(self) -> None:
        world = self.session.client.get_state_by_name(WorldState)
        events = self.session.client.events
        for ele in events:
            if ele.id == self.event_id:
                # retrieves data
                x, y = ele.x, ele.y
                w, h = ele.w, ele.h
                # defines area
                for i in range(w):
                    vertex = x + i
                    loc = (x + i, y)
                    world.collision_map[tuple(loc)] = None
                    if h != 1:
                        for i in range(h):
                            loc = (vertex, y + i)
                            world.collision_map[tuple(loc)] = None

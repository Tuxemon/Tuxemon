# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, final

from tuxemon.event.eventaction import EventAction


@final
@dataclass
class RemoveStateAction(EventAction):
    """
    Remove the specified state.

    Script usage:
        .. code-block::

            remove_state <state_name>

    Script parameters:
        state_name: The state name to remove (e.g. PCState)

    """

    name = "remove_state"
    state_name: Union[str, None] = None

    def start(self) -> None:
        # Don't override previous state if we are still in the state.
        current_state = self.session.client.current_state
        if current_state is None:
            # obligatory "should not happen"
            raise RuntimeError
        if not self.state_name:
            for name in self.session.client.active_state_names:
                if name not in ["WorldState", "BackgroundState"]:
                    self.session.client.remove_state_by_name(name)
        if (
            self.state_name
            and self.state_name in self.session.client.active_state_names
        ):
            self.session.client.pop_state()

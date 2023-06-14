# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Union, final

from tuxemon.event.eventaction import EventAction
from tuxemon.monster import Monster
from tuxemon.states.journal import MonsterInfoState


@final
@dataclass
class ChangeStateAction(EventAction):
    """
    Change to the specified state.

    Script usage:
        .. code-block::

            change_state <state_name>[,optional]

    Script parameters:
        state_name: The state name to switch to (e.g. PCState).
        optional: Variable related to specific states (eg slug for MonsterInfo).

    """

    name = "change_state"
    state_name: str
    optional: Union[str, None] = None

    def start(self) -> None:
        # Don't override previous state if we are still in the state.
        current_state = self.session.client.current_state
        if current_state is None:
            # obligatory "should not happen"
            raise RuntimeError
        if current_state.name != self.state_name:
            if self.state_name == "JournalInfoState":
                if self.optional:
                    mon = Monster()
                    mon.load_from_db(self.optional)
                    self.session.client.push_state(
                        self.state_name, kwargs={"monster": mon}
                    )
            elif self.state_name == "MonsterInfoState":
                if self.optional:
                    mon = Monster()
                    mon.load_from_db(self.optional)
                    self.session.client.push_state(
                        MonsterInfoState(monster=mon)
                    )
            else:
                self.session.client.push_state(self.state_name)

    def update(self) -> None:
        try:
            self.session.client.get_state_by_name(self.state_name)
        except ValueError:
            self.stop()

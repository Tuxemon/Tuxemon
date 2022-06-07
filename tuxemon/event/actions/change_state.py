#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction


class ChangeStateActionParameters(NamedTuple):
    state_name: str


@final
class ChangeStateAction(EventAction[ChangeStateActionParameters]):
    """
    Change to the specified state.

    Script usage:
        .. code-block::

            change_state <state_name>

    Script parameters:
        state_name: The state name to switch to (e.g. PCState).

    """

    name = "change_state"
    param_class = ChangeStateActionParameters

    def start(self) -> None:
        # Don't override previous state if we are still in the state.
        current_state = self.session.client.current_state
        if current_state is None:
            # obligatory "should not happen"
            raise RuntimeError
        if current_state.name != self.parameters.state_name:
            self.session.client.push_state(self.parameters.state_name)

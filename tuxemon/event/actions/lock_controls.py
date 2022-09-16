from __future__ import annotations

from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.sink import SinkState


class LockControlsActionParameters(NamedTuple):
    pass


@final
class LockControlsAction(
    EventAction[LockControlsActionParameters],
):
    """
    Lock player controls

    Script usage:
        .. code-block::

            lock_controls

    """

    name = "lock_controls"

    param_class = LockControlsActionParameters

    def start(self) -> None:
        self.session.client.push_state(SinkState())

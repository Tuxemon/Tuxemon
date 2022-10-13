from __future__ import annotations

from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.sink import SinkState


class UnlockControlsActionParameters(NamedTuple):
    pass


@final
class UnlockControlsAction(
    EventAction[UnlockControlsActionParameters],
):
    """
    Unlock player controls

    Script usage:
        .. code-block::

            unlock_controls

    """

    name = "unlock_controls"

    param_class = UnlockControlsActionParameters

    def start(self) -> None:
        sink_state = self.session.client.get_state_by_name(SinkState)

        if sink_state:
            self.session.client.remove_state(sink_state)

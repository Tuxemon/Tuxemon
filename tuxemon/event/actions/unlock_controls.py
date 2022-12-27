from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.sink import SinkState


@final
@dataclass
class UnlockControlsAction(
    EventAction,
):
    """
    Unlock player controls

    Script usage:
        .. code-block::

            unlock_controls

    """

    name = "unlock_controls"

    def start(self) -> None:
        sink_state = self.session.client.get_state_by_name(SinkState)

        if sink_state:
            self.session.client.remove_state(sink_state)

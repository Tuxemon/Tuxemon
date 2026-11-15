# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class InputPlaybackAction(EventAction):
    """
    Start or stop playback of a named recording.

    Script usage:
        .. code-block::

            input_playback <action> <name>
    """

    name = "input_playback"
    action: str
    recording_name: str

    def start(self, session: Session) -> None:
        recorder = session.client.input_recorder
        bus = session.client.event_bus
        player = session.player

        if self.action == "start":
            initial_state = recorder.get_recording_state(self.recording_name)
            if initial_state:
                if (
                    "map" in initial_state
                    and "player_x" in initial_state
                    and "player_y" in initial_state
                ):
                    params = [
                        "player",
                        str(initial_state["map"]),
                        str(initial_state["player_x"]),
                        str(initial_state["player_y"]),
                    ]
                    session.client.current_music.stop()
                    session.client.event_engine.execute_action(
                        "teleport", params
                    )
                    logger.debug(
                        f"Teleported player to {initial_state['map']} "
                        f"({initial_state['player_x']}, {initial_state['player_y']})"
                    )

                if "direction" in initial_state:
                    player.set_facing(initial_state["direction"])
                    logger.debug(
                        f"Set player facing direction to {initial_state['direction']}"
                    )

                logger.info(
                    f"Player reset to initial state for recording '{self.recording_name}'"
                )

            recorder.start_playback_named(self.recording_name)
            bus.publish("input.playback_started", name=self.recording_name)

        elif self.action == "stop":
            recorder.stop_playback()
            bus.publish("input.playback_stopped", name=self.recording_name)
            logger.info(
                f"Playback stopped for recording '{self.recording_name}'"
            )

        else:
            logger.error(f"Unknown input_playback action: {self.action}")

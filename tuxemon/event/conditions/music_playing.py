# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from tuxemon.db import MusicStatus
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


@dataclass
class MusicPlayingCondition(EventCondition):
    """
    Check to see if a particular piece of music is playing or not.

    Script usage:
        .. code-block::

            is music_playing <music_filename>

    Script parameters:
        music_filename: Name of the music.
    """

    name: ClassVar[str] = "music_playing"
    music_filename: str

    def test(self, session: Session) -> bool:
        combat_states = {"FlashTransition", "CombatState"}
        if any(
            state in combat_states
            for state in session.client.active_state_names
        ):
            return True

        if session.client.current_music.status == MusicStatus.PAUSED:
            return True
        else:
            return (
                session.client.current_music.current_song
                == self.music_filename
                and session.client.current_music.is_playing()
            )

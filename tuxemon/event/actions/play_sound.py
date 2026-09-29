# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.platform.const.sizes import SOUND_RANGE
from tuxemon.session import Session


@final
@dataclass
class PlaySoundAction(EventAction):
    """
    Plays a short sound effect from the "resources/sounds/" folder.

    Script usage:
        .. code-block::

            play_sound <filename>[,volume]

    Script parameters:
        filename: The sound file to load (must exist in the sounds database).
        volume: A float between 0.0 and 1.0 representing the relative volume level.
            This value is multiplied by the user's configured sound volume.

    Example:
        If volume=0.5 and the player's sound setting is also 0.5,
        the resulting effective playback volume will be 0.25.

    Note:
        This is intended for short non-looping sound effects (e.g., cues, UI feedback),
        not for ambient or background music.
    """

    name = "play_sound"
    filename: str
    volume: float | None = None

    def start(self, session: Session) -> None:
        client = session.client
        sound_manager = client.sound_manager
        user_volume = client.config.sound_volume

        if self.volume is not None:
            lower, upper = SOUND_RANGE
            if not (lower <= self.volume <= upper):
                raise ValueError(
                    f"Volume must be between {lower} and {upper}",
                )

        effective_volume = (
            self.volume * user_volume
            if self.volume is not None
            else user_volume
        )

        sound_manager.set_volume(effective_volume)
        sound_manager.play(self.filename)

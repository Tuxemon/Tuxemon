# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class PlaySoundAction(EventAction):
    """
    Play a sound from "resources/sounds/".

    Script usage:
        .. code-block::

            play_sound <filename>[,volume]

    Script parameters:
        filename: Sound file to load.
        volume: Number between 0.0 and 1.0.

        Attention!
        The volume will be based on the main value
        in the options menu.
        e.g. if you set volume = 0.5 here, but the
        player has 0.5 among its options, then it'll
        result into 0.25 (0.5*0.5)

    """

    name = "play_sound"
    filename: str
    volume: Optional[float] = None

    def start(self) -> None:
        client = self.session.client
        sound_volume = client.config.sound_volume

        if self.volume is not None:
            lower, upper = prepare.SOUND_RANGE
            if not (lower <= self.volume <= upper):
                raise ValueError(
                    f"Volume must be between {lower} and {upper}",
                )
        volume = (
            self.volume * sound_volume
            if self.volume is not None
            else sound_volume
        )

        client.sound_manager.play_sound(self.filename, volume)

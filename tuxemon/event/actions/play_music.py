# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


@final
@dataclass
class PlayMusicAction(EventAction):
    """
    Play a music file from "resources/music/".

    Script usage:
        .. code-block::

            play_music <filename>[,volume][,loop][,fade_ms]

    Script parameters:
        filename: The name of the music file to play.
        volume: A value between 0.0 and 1.0 that adjusts the music
            volume.
        loop: The number of times to loop the music. Default is to loop
            forever.
        fade_ms: The time in milliseconds to fade in the music before
            reaching maximum volume.

    Note:
        The volume will be based on the main value in the options menu.
        e.g. if you set volume = 0.5 here, but the player has 0.5 among
        its options, then it'll result into 0.25 (0.5*0.5)

    """

    name = "play_music"
    filename: str
    volume: Optional[float] = None
    loop: Optional[int] = None
    fade_ms: Optional[int] = None

    def start(self) -> None:
        client = self.session.client
        loop = prepare.MUSIC_LOOP if self.loop is None else self.loop
        fade_ms = (
            prepare.MUSIC_FADEIN if self.fade_ms is None else self.fade_ms
        )
        music_volume = client.config.music_volume
        if not self.volume:
            volume = music_volume
        else:
            lower, upper = prepare.MUSIC_RANGE
            if lower <= self.volume <= upper:
                volume = self.volume * music_volume
            else:
                raise ValueError(
                    f"{self.volume} must be between {lower} and {upper}",
                )

        # Keep track of what song we're currently playing
        client.current_music.play(self.filename, volume, loop, fade_ms)

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

from tuxemon import prepare
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction
from tuxemon.platform import mixer

logger = logging.getLogger(__name__)


@final
@dataclass
class PlayMusicAction(EventAction):
    """
    Play a music file from "resources/music/".

    Script usage:
        .. code-block::

            play_music <filename>[,volume][,loop]

    Script parameters:
        filename: Music file to load.
        volume: Number between 0.0 and 1.0.
        loop: How many times loop, default forever.

        Attention!
        The volume will be based on the main value
        in the options menu.
        e.g. if you set volume = 0.5 here, but the
        player has 0.5 among its options, then it'll
        result into 0.25 (0.5*0.5)

    """

    name = "play_music"
    filename: str
    volume: Optional[float] = None
    loop: Optional[int] = None

    def start(self) -> None:
        player = self.session.player
        loop = -1 if self.loop is None else self.loop
        base_volume = prepare.MUSIC_VOLUME
        if player:
            base_volume = float(
                player.game_variables.get("music_volume", base_volume)
            )

        # Validate and calculate the volume
        if self.volume is None:
            volume = base_volume
        else:
            lower, upper = prepare.MUSIC_RANGE
            if not (lower <= self.volume <= upper):
                raise ValueError(f"Volume must be between {lower} and {upper}")
            volume = self.volume * base_volume

        try:
            # Load and play the music
            path = prepare.fetch(
                "music", db.lookup_file("music", self.filename)
            )
            mixer.music.load(path)
            mixer.music.set_volume(volume)
            mixer.music.play(loop)

            # Update the current music status
            client = self.session.client
            if client.current_music["song"]:
                client.current_music["previoussong"] = client.current_music[
                    "song"
                ]
            client.current_music["status"] = "playing"
            client.current_music["song"] = self.filename
        except Exception as e:
            logger.error(f"Error playing music: {e}")

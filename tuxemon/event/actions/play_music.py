# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union, final

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

            play_music <filename>[,volume]

    Script parameters:
        filename: Music file to load.
        volume: Number between 0.0 and 1.0.
        Attention!
        The volume will be based on the main value
        in the options menu.
        e.g. volume = 0.5, main 0.5 -> 0.25

    """

    name = "play_music"
    filename: str
    volume: Union[float, None] = None

    def start(self) -> None:
        player = self.session.player
        volume: float = 0.0
        if not self.volume:
            volume = float(player.game_variables["music_volume"])
        else:
            if 0.0 <= self.volume <= 1.0:
                volume = self.volume * float(
                    player.game_variables["music_volume"]
                )
            else:
                raise ValueError(
                    f"{self.volume} must be between 0.0 and 1.0",
                )
        try:
            path = prepare.fetch(
                "music", db.lookup_file("music", self.filename)
            )
            mixer.music.load(path)
            mixer.music.set_volume(volume)
            mixer.music.play(-1)
        except Exception as e:
            logger.error(e)
            logger.error("unable to play music")

        # Keep track of what song we're currently playing
        if self.session.client.current_music["song"]:
            self.session.client.current_music[
                "previoussong"
            ] = self.session.client.current_music["song"]
        self.session.client.current_music["status"] = "playing"
        self.session.client.current_music["song"] = self.filename

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

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

            play_music <filename>

    Script parameters:
        filename: Music file to load.

    """

    name = "play_music"
    filename: str

    def start(self) -> None:
        try:
            path = prepare.fetch(
                "music", db.lookup_file("music", self.filename)
            )
            mixer.music.load(path)
            mixer.music.set_volume(prepare.CONFIG.music_volume)
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

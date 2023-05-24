# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Union, final

from tuxemon import audio
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


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
        e.g. volume = 0.5, main 0.5 -> 0.25

    """

    name = "play_sound"
    filename: str
    volume: Union[float, None] = None

    def start(self) -> None:
        player = self.session.player
        volume: float = 0.0
        if not self.volume:
            volume = float(player.game_variables["sound_volume"])
        else:
            if 0.0 <= self.volume <= 1.0:
                volume = self.volume * float(
                    player.game_variables["sound_volume"]
                )
            else:
                logger.error(f"{self.volume} must be between 0.0 and 1.0")
                raise ValueError()
        sound = audio.load_sound(self.filename, volume)
        sound.play()

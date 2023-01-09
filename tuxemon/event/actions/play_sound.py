# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import final

from tuxemon import audio
from tuxemon.event.eventaction import EventAction


@final
@dataclass
class PlaySoundAction(EventAction):
    """
    Play a sound from "resources/sounds/".

    Script usage:
        .. code-block::

            play_sound <filename>

    Script parameters:
        filename: Sound file to load.

    """

    name = "play_sound"
    filename: str

    def start(self) -> None:
        sound = audio.load_sound(self.filename)
        sound.play()

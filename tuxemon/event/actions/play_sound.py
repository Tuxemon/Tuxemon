# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, final

import pygame
from pygame import mixer

from tuxemon import prepare
from tuxemon.db import db
from tuxemon.event.eventaction import EventAction

logger = logging.getLogger(__name__)


class DummySound:
    def play(self) -> None:
        pass


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
        player = self.session.player
        base_volume = prepare.SOUND_VOLUME
        if player:
            base_volume = float(
                player.game_variables.get("music_volume", base_volume)
            )

        if self.volume is None:
            volume = base_volume
        else:
            lower, upper = prepare.SOUND_RANGE
            if not (lower <= self.volume <= upper):
                raise ValueError(f"Volume must be between {lower} and {upper}")
            volume = self.volume * base_volume

        try:
            sound_path = prepare.fetch(
                "sounds", db.lookup_file("sounds", self.filename)
            )
            sound = mixer.Sound(sound_path)
            sound.set_volume(volume)
            sound.play()
        except (MemoryError, pygame.error) as e:
            # pick one:
            # * there is no mixer
            # * sound has invalid path
            # * mixer has no output (device ok, no speakers)
            logger.error(f"Error playing sound: {e}")
            logger.error("Unable to load sound")
            DummySound().play()
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

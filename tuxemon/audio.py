# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os.path
from typing import Optional, Protocol

import pygame
from pygame import mixer

from tuxemon import prepare
from tuxemon.db import db
from tuxemon.tools import transform_resource_filename

logger = logging.getLogger(__name__)


class SoundProtocol(Protocol):
    def play(self) -> object:
        pass


class DummySound:
    def play(self) -> None:
        pass


def get_sound_filename(slug: Optional[str]) -> Optional[str]:
    """
    Get the filename of a sound slug.

    Parameters:
        slug: Slug of the file record.

    Returns:
        Filename if the sound is found.

    """
    if slug is None or slug == "":
        return None

    # Get the filename from the db
    filename = db.lookup_file("sounds", slug)
    filename = transform_resource_filename("sounds", filename)

    # On some platforms, pygame will silently fail loading
    # a sound if the filename is incorrect so we check here
    if not os.path.exists(filename):
        logger.error(f"audio file does not exist: {filename}")
        return None

    return filename


def load_sound(slug: Optional[str]) -> SoundProtocol:
    """
    Load a sound from disk, identified by it's slug in the db.

    Parameters:
        slug: Slug for the file record to load.

    Returns:
        Loaded sound, or a placeholder silent sound if it is
        not found.

    """

    filename = get_sound_filename(slug)
    if filename is None:
        return DummySound()

    try:
        sound = mixer.Sound(filename)
        mixer.Sound.set_volume(sound, prepare.CONFIG.sound_volume)
        return sound
    except MemoryError:
        # raised on some systems if there is no mixer
        logger.error("memoryerror, unable to load sound")
        return DummySound()
    except pygame.error as e:
        # pick one:
        # * there is no mixer
        # * sound has invalid path
        # * mixer has no output (device ok, no speakers)
        logger.error(e)
        logger.error("unable to load sound")
        return DummySound()

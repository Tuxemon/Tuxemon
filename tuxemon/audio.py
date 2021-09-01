from __future__ import annotations
import logging
import os.path

import pygame
from pygame import mixer

from tuxemon.db import db
from tuxemon.tools import transform_resource_filename
from typing import Protocol, Any

logger = logging.getLogger(__name__)


class SoundProtocol(Protocol):

    def play(self) -> object:
        pass


class DummySound():

    def play(self) -> None:
        pass


def load_sound(slug: str) -> SoundProtocol:
    """
    Load a sound from disk, identified by it's slug in the db.

    Parameters:
        slug: slug for the file record to load

    Returns:
        Loaded sound, or a placeholder silent sound if it is
        not found.

    """

    if slug is None or slug == '':
        return DummySound()

    # get the filename from the db
    filename = db.lookup_file("sounds", slug)
    filename = transform_resource_filename("sounds", filename)

    # on some platforms, pygame will silently fail loading
    # a sound if the filename is incorrect so we check here
    if not os.path.exists(filename):
        msg = f"audio file does not exist: {filename}"
        logger.error(msg)
        return DummySound()

    try:
        return mixer.Sound(filename)
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

import logging
import os.path

import pygame
from pygame import mixer

from tuxemon.core.db import db
from tuxemon.core.tools import transform_resource_filename

logger = logging.getLogger(__name__)


def load_sound(slug):
    """ Load a sound from disk, identified by it's slug in the db

    :param slug: slug for the file record to load
    :type slug: String
    :rtype: tuxemon.core.platform.mixer.Sound
    """

    class DummySound:
        def play(self):
            pass

    if slug is None:
        return DummySound()

    # get the filename from the db
    filename = db.lookup_file("sounds", slug)
    filename = transform_resource_filename("sounds", filename)

    # on some platforms, pygame will silently fail loading
    # a sound if the filename is incorrect so we check here
    if not os.path.exists(filename):
        msg = 'audio file does not exist: {}'.format(filename)
        logger.error(msg)
        return DummySound()

    try:
        return mixer.Sound(filename)
    except MemoryError:
        # raised on some systems if there is no mixer
        logger.error('memoryerror, unable to load sound')
        return DummySound()
    except pygame.error as e:
        # pick one:
        # * there is no mixer
        # * sound has invalid path
        # * mixer has no output (device ok, no speakers)
        logger.error(e)
        logger.error('unable to load sound')
        return DummySound()

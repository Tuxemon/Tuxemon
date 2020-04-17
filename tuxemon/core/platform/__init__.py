"""
Put platform specific fixes here
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os.path

__all__ = ('android', 'init', 'mixer', 'get_config_dir')

logger = logging.getLogger(__name__)

_pygame = False
mixer = None
android = None

# TODO: more graceful handling of android and pygame deps.
try:
    import android
    import android.mixed as mixer
except ImportError:
    pass

if mixer is None:
    try:
        import pygame.mixer as mixer
        _pygame = True
    except ImportError:
        pass


def init():
    """ Must be called before pygame.init() to enable low latency sound
    """
    # reduce sound latency.  the pygame defaults were ok for 2001,
    # but these values are more acceptable for faster computers
    if _pygame:
        logger.debug("pre-init pygame mixer")
        mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)


def get_config_dir():
    if android:
        return "/sdcard/org.tuxemon"
    else:
        return os.path.join(os.path.expanduser("~"), ".tuxemon")

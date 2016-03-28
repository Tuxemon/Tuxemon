"""
Put platform specific fixes here
"""
__all__ = ('android', 'init', 'mixer')

from os.path import expanduser

_pygame = False

# Import the android module and android specific components. If we can't import, set to None - this
# lets us test it, and check to see if we want android-specific behavior.
android = None
try:
    import android
except ImportError:
    pass

# Import the android mixer if on the android platform
try:
    import pygame.mixer as mixer

    global _pygame
    _pygame = True
except ImportError:
    import android
    import android.mixer as mixer

def init():
    """ Must be called before pygame.init() to enable low latency sound
    """
    # reduce sound latency.  the pygame defaults were ok for 2001,
    # but these values are more acceptable for faster computers
    if _pygame:
        mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)

def get_config_path():
    if android:
        return "/sdcard/org.tuxemon"
    else:
        return expanduser("~")


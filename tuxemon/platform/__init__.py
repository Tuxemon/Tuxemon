"""
Put platform specific fixes here
"""
from __future__ import annotations
import logging
import os.path
from typing import Optional, Sequence
import types
import pygame

__all__ = ("android", "init", "mixer", "get_user_storage_dir")

logger = logging.getLogger(__name__)

_pygame = False
android = None

# TODO: more graceful handling of android and pygame deps.
try:
    import android
    import android.mixer
    mixer = android.mixer
except ImportError:
    pass

if android is None:
    try:
        import pygame.mixer
        mixer = pygame.mixer
        _pygame = True
    except ImportError:
        pass


def init() -> None:
    """Must be called before pygame.init() to enable low latency sound"""
    # reduce sound latency.  the pygame defaults were ok for 2001,
    # but these values are more acceptable for faster computers
    if _pygame:
        logger.debug("pre-init pygame mixer")
        mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)


def get_user_storage_dir() -> str:
    """

    Mutable storage for things like config, save games, mods, cache

    """
    if android:
        from android import storage

        return storage.app_storage_path()
    else:
        return os.path.join(os.path.expanduser("~"), ".tuxemon")


def get_system_storage_dirs() -> Sequence[str]:
    """

    Should be immutable storage for things like system installed code/mods

    Android storage is still WIP.  should be immutable, but its not...

    The primary user of this storage are packages for operating systems
    that will install the mods into a folder like /usr/share/tuxemon

    """
    if android:
        from android import storage

        paths = list()
        for root in filter(
            None,
            [
                storage.primary_external_storage_path(),
                storage.secondary_external_storage_path(),
            ],
        ):
            path = os.path.join(root, "Tuxemon")
            paths.append(path)

        # try to guess sd cards
        blacklist = "emulated"
        for name in os.listdir("/storage"):
            if name not in blacklist:
                path = os.path.join("storage", name, "Tuxemon")
                paths.append(path)
        return paths
    else:
        return ["/usr/share/tuxemon/"]

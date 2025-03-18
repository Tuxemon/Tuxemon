"""
Put platform specific fixes here
"""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from pathlib import Path

__all__ = ("android", "init", "mixer", "get_user_storage_dir")

logger = logging.getLogger(__name__)

_pygame = False
android = None

try:
    import android
    import android.mixer as android_mixer

    mixer = android_mixer
except ImportError:
    pass
else:
    logger.info("Using Android mixer")

if android is None:
    try:
        import pygame.mixer as pygame_mixer

        mixer = pygame_mixer
        _pygame = True
    except ImportError:
        logger.error("Neither Android nor Pygame mixer found")
    else:
        logger.info("Using Pygame mixer")


def init() -> None:
    """Must be called before pygame.init() to enable low latency sound."""
    # reduce sound latency.  the pygame defaults were ok for 2001,
    # but these values are more acceptable for faster computers
    if _pygame:
        logger.debug("pre-init pygame mixer")
        try:
            mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
        except Exception as e:
            logger.error(f"Failed to initialize Pygame mixer: {e}")


def get_user_storage_dir() -> str:
    """
    Returns the user storage directory.
    Mutable storage for things like config, save games, mods, cache.
    """
    if is_android():
        paths = _get_android_storage_paths()
        if paths:
            return paths[0]
    return str(Path.home() / ".tuxemon")


def is_android() -> bool:
    """Checks if the platform is Android."""
    try:
        import android

        return True
    except ImportError:
        return False


def _get_android_storage_paths() -> list[str]:
    """Helper function to get Android storage paths."""
    paths: list[str] = []

    if is_android():
        paths.extend(_get_android_storage_paths())
    else:
        paths.append("/usr/share/tuxemon/")
        paths.append("/usr/local/share/tuxemon/")
        try:
            xdg_data_dirs = os.environ.get("XDG_DATA_DIRS", "")
            if xdg_data_dirs:
                for data_dir in xdg_data_dirs.split(":"):
                    path = Path(data_dir) / "tuxemon"
                    if path.exists():
                        paths.append(str(path))
                    else:
                        logger.debug(f"Checking XDG data directory: {path}")

        except Exception as e:
            logger.error(f"Error handling XDG_DATA_DIRS: {e}")

    return paths


def get_system_storage_dirs() -> Sequence[str]:
    """
    Returns a sequence of system storage directories.
    Should be immutable storage for things like system installed code/mods.
    Android storage is still WIP.  should be immutable, but it's not...
    The primary user of this storage are packages for operating systems
    that will install the mods into a folder like /usr/share/tuxemon.
    """
    paths: list[str] = []

    if is_android():
        paths.extend(_get_android_storage_paths())
    else:
        paths.append("/usr/share/tuxemon/")
        paths.append("/usr/local/share/tuxemon/")
        try:
            xdg_data_dirs = os.environ.get("XDG_DATA_DIRS", "")
            if xdg_data_dirs:
                for data_dir in xdg_data_dirs.split(":"):
                    path = Path(data_dir) / "tuxemon"
                    if path.exists():
                        paths.append(str(path))
                    else:
                        logger.debug(f"Checking XDG data directory: {path}")

        except Exception as e:
            logger.error(f"Error handling XDG_DATA_DIRS: {e}")

    return paths

# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Platform-specific implementations and configurations.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from pathlib import Path

__all__ = (
    "init",
    "mixer",
    "get_user_storage_dir",
    "get_system_storage_dirs",
    "is_android",
)

logger = logging.getLogger(__name__)

_pygame = False
android_module = None

try:
    import android
    import android.mixer as android_mixer

    mixer = android_mixer
    android_module = android
except ImportError:
    pass
else:
    logger.info("Using Android mixer")

if android_module is None:
    try:
        import pygame.mixer as pygame_mixer

        mixer = pygame_mixer
        _pygame = True
    except ImportError:
        logger.error("Neither Android nor Pygame mixer found")
    else:
        logger.info("Using Pygame mixer")


def init() -> None:
    """
    Initializes the sound system to enable low latency sound.

    This function must be called before pygame.init() to take effect.
    It adjusts the sound settings to reduce latency, making it more
    suitable for modern computers. The default Pygame settings were
    optimized for slower computers in 2001, but these updated values
    provide better performance on faster machines.
    """
    if _pygame:
        logger.debug("pre-init pygame mixer")
        try:
            mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
        except Exception as e:
            logger.error(f"Failed to initialize Pygame mixer: {e}")


def get_user_storage_dir() -> Path:
    """
    Returns the user storage directory.
    Mutable storage for things like config, save games, mods, cache.
    """
    if is_android():
        if android_module is not None:
            return Path(
                android_module.context.getExternalFilesDir(None).getPath()
            )
    logger.error("Android module is not available or not running on Android")
    return Path.home() / ".tuxemon"


def is_android() -> bool:
    """Checks if the platform is Android."""
    return android_module is not None


def get_system_storage_dirs() -> Sequence[Path]:
    """
    Returns a sequence of system storage directories.
    Should be immutable storage for things like system installed code/mods.
    Android storage is still WIP.  should be immutable, but it's not...
    The primary user of this storage are packages for operating systems
    that will install the mods into a folder like /usr/share/tuxemon.
    """
    paths: list[Path] = []

    if not is_android():
        paths.extend(
            [
                Path("/usr/share/tuxemon/"),
                Path("/usr/local/share/tuxemon/"),
            ]
        )

        try:
            xdg_data_dirs = os.environ.get("XDG_DATA_DIRS", "")
            if xdg_data_dirs:
                for data_dir in xdg_data_dirs.split(":"):
                    path = Path(data_dir) / "tuxemon"
                    if path.exists():
                        paths.append(path)
                    else:
                        logger.debug(f"Checking XDG data directory: {path}")

        except Exception as e:
            logger.error(f"Error handling XDG_DATA_DIRS: {e}")

    # You need to implement the android logic here
    # For now, I'm just returning the paths
    return paths

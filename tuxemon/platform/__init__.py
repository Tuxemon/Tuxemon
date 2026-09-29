# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Unified platform abstraction for Tuxemon.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any, BinaryIO, Protocol

logger = logging.getLogger(__name__)


class MusicProtocol(Protocol):
    def load(self, filename: str) -> None: ...
    def play(
        self, loops: int = 0, start: float = 0.0, fade_ms: int = 0
    ) -> None: ...
    def stop(self) -> None: ...
    def pause(self) -> None: ...
    def unpause(self) -> None: ...
    def fadeout(self, time: int) -> None: ...
    def set_volume(self, volume: float) -> None: ...
    def get_volume(self) -> float: ...
    def get_busy(self) -> bool: ...


class MixerProtocol(Protocol):
    def pre_init(
        self, *, frequency: int, size: int, channels: int, buffer: int
    ) -> None: ...

    music: MusicProtocol


class AndroidPathLike(Protocol):
    def getPath(self) -> str: ...


class AndroidAssetsLike(Protocol):
    def open(self, name: str) -> BinaryIO: ...
    def list(self, path: str) -> list[str]: ...


class AndroidContextProtocol(Protocol):
    def getExternalFilesDir(self, arg: str | None) -> AndroidPathLike: ...
    def getObbDir(self) -> AndroidPathLike: ...
    def getAssets(self) -> AndroidAssetsLike: ...


class AndroidModuleProtocol(Protocol):
    context: AndroidContextProtocol


class DummyMusic(MusicProtocol):
    def load(self, filename: str) -> None:
        pass

    def play(
        self, loops: int = 0, start: float = 0.0, fade_ms: int = 0
    ) -> None:
        pass

    def stop(self) -> None:
        pass

    def pause(self) -> None:
        pass

    def unpause(self) -> None:
        pass

    def fadeout(self, time: int) -> None:
        pass

    def set_volume(self, volume: float) -> None:
        pass

    def get_volume(self) -> float:
        return 0.0

    def get_busy(self) -> bool:
        return False


class DummyMixer(MixerProtocol):
    music: MusicProtocol = DummyMusic()

    def pre_init(self, *args: Any, **kwargs: Any) -> None:
        pass


ASSET_ROOT = "<asset-root>"


class ResourceHandle:
    """
    Represents either a filesystem path or an Android asset.
    """

    def __init__(self, *, path: Path | None = None, asset: str | None = None):
        self.path = path
        self.asset = asset

    def is_asset(self) -> bool:
        return self.asset is not None

    def exists(self, android: AndroidModuleProtocol | None) -> bool:
        if self.path is not None:
            return self.path.exists()

        if self.asset is None:
            return False

        if self.asset == ASSET_ROOT:
            return True  # virtual directory

        if android is None:
            return False

        assets = android.context.getAssets()
        try:
            dirname, _, filename = self.asset.rpartition("/")
            entries = assets.list(dirname)
            return filename in entries
        except Exception as e:
            logger.error(
                f"Error checking Android asset existence for {self.asset}: {e}"
            )
            return False

    def open(self, android: AndroidModuleProtocol | None) -> Any:
        if self.path is not None:
            return self.path.open("rb")

        if self.asset is None:
            raise RuntimeError(
                "ResourceHandle has neither a path nor an asset name"
            )

        if self.asset == ASSET_ROOT:
            raise IsADirectoryError("Cannot open asset root")

        if android is None:
            raise RuntimeError(
                "Attempted to open an Android asset without Android context"
            )

        return android.context.getAssets().open(self.asset)

    def __repr__(self) -> str:
        if self.path:
            return f"<Resource path={self.path}>"
        return f"<Resource asset={self.asset}>"


class SystemStorage:
    """
    Immutable storage for built-in resources.
    """

    def __init__(self, android: AndroidModuleProtocol | None):
        self.android = android

    def system_dirs(self) -> Sequence[ResourceHandle]:
        """
        Return all system-level resource roots.
        On desktop: real filesystem paths.
        On Android: asset root + OBB directory (if present).
        Always returns a list, never None.
        """
        dirs: list[ResourceHandle] = []

        # Desktop / Linux
        if self.android is None:
            # Standard installation paths
            for base in ("/usr/share/tuxemon", "/usr/local/share/tuxemon"):
                dirs.append(ResourceHandle(path=Path(base)))

            # XDG_DATA_DIRS
            try:
                xdg = os.environ.get("XDG_DATA_DIRS", "")
                for entry in xdg.split(":"):
                    p = Path(entry) / "tuxemon"
                    if p.is_dir():
                        dirs.append(ResourceHandle(path=p))
            except Exception as e:
                logger.error(f"Error reading XDG_DATA_DIRS: {e}")
            return dirs

        # Android
        # Asset root (virtual)
        dirs.append(ResourceHandle(asset=ASSET_ROOT))

        # OBB directory
        try:
            obb_path = Path(self.android.context.getObbDir().getPath())
            if obb_path.is_dir():
                dirs.append(ResourceHandle(path=obb_path))
        except Exception as e:
            logger.error(f"Error reading Android OBB dir: {e}")

        return dirs

    def resolve(self, name: str) -> ResourceHandle | None:
        """
        Resolve a resource name into a ResourceHandle.
        Searches:
          - filesystem dirs (desktop + Android OBB)
          - Android assets (if available)
        """
        # Filesystem search
        for base in self.system_dirs():
            if base.path is not None:
                candidate = base.path / name
                if candidate.exists():
                    return ResourceHandle(path=candidate)

        # Android assets
        if self.android is not None:
            assets = self.android.context.getAssets()
            try:
                dirname, _, filename = name.rpartition("/")
                entries = assets.list(dirname)
                if filename in entries:
                    return ResourceHandle(asset=name)
            except Exception as e:
                logger.error(f"Error listing Android assets for {name}: {e}")

        return None


class UserStorage:
    """
    Mutable storage for saves, configs, mods, cache.
    """

    def __init__(self, android: AndroidModuleProtocol | None):
        self.android = android

    def user_dir(self) -> Path:
        fallback = Path.home() / ".tuxemon"

        if self.android is None:
            return fallback

        try:
            return Path(
                self.android.context.getExternalFilesDir(None).getPath()
            )
        except Exception as e:
            logger.error(f"Error reading Android user storage: {e}")
            return fallback

    def ensure_dirs(self) -> None:
        base = self.user_dir()
        for sub in ["saves", "config", "mods", "cache"]:
            (base / sub).mkdir(parents=True, exist_ok=True)


class PlatformError(Exception):
    pass


class Platform:
    """
    Unified platform abstraction.
    """

    def __init__(self) -> None:
        self.android: AndroidModuleProtocol | None = None
        self.mixer: MixerProtocol = DummyMixer()
        self._pygame_mixer_in_use: bool = False

        self._system_storage: SystemStorage | None = None
        self._user_storage: UserStorage | None = None

    @property
    def system_storage(self) -> SystemStorage:
        if self._system_storage is None:
            self._system_storage = SystemStorage(self.android)
        return self._system_storage

    @property
    def user_storage(self) -> UserStorage:
        if self._user_storage is None:
            self._user_storage = UserStorage(self.android)
        return self._user_storage

    def init(self) -> None:
        self._detect_android()
        self._init_mixer()
        self._pre_init_sound()

        # Refresh storage after detection
        self._system_storage = SystemStorage(self.android)
        self._user_storage = UserStorage(self.android)

    def _detect_android(self) -> None:
        try:
            import android

            # More robust detection
            if hasattr(android, "context") or hasattr(android, "activity"):
                self.android = android
                logger.info("Android platform detected")
            else:
                logger.warning(
                    "Android module found but missing context/activity; falling back to desktop"
                )
                self.android = None

        except ImportError:
            self.android = None
            logger.info("Running on desktop platform")

    def is_android(self) -> bool:
        return self.android is not None

    def _init_mixer(self) -> None:
        if self.android is not None:
            try:
                import android.mixer as android_mixer

                self.mixer = android_mixer
                self._pygame_mixer_in_use = False
                logger.info("Using Android mixer")
                return
            except ImportError:
                logger.error(
                    "Android detected but android.mixer not available"
                )

        try:
            import pygame.mixer as pygame_mixer

            self.mixer = pygame_mixer
            self._pygame_mixer_in_use = True
            logger.info("Using Pygame mixer")
        except ImportError:
            logger.error("No mixer available; using DummyMixer")
            self.mixer = DummyMixer()
            self._pygame_mixer_in_use = False

    def _pre_init_sound(self) -> None:
        if self._pygame_mixer_in_use:
            try:
                self.mixer.pre_init(
                    frequency=44100,
                    size=-16,
                    channels=2,
                    buffer=1024,
                )
            except Exception as e:
                logger.error(f"Failed to pre-init pygame mixer: {e}")


platform = Platform()

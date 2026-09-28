# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

import pygame

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.database.runtime import db
from tuxemon.db import MusicStatus
from tuxemon.platform import platform
from tuxemon.platform.const.sizes import (
    MUSIC_FADEIN,
    MUSIC_FADEOUT,
    MUSIC_LOOP,
)
from tuxemon.tools import transform_resource_filename
from tuxemon.user_config import CONFIG

logger = logging.getLogger(__name__)


class MusicPlayerState:
    def __init__(self) -> None:
        self.status = MusicStatus.STOPPED
        self.current_song: str | None = None
        self.previous_song: str | None = None
        self.cache: dict[str, str] = {}

        self.muted: bool = False
        self._user_volume = CONFIG.music_volume

    def load(
        self, filename: str, volume: float, loop: int, fade_ms: int
    ) -> None:
        try:
            path = self.get_path(filename)
            platform.mixer.music.load(path)
            platform.mixer.music.set_volume(volume)
            platform.mixer.music.play(loops=loop, fade_ms=fade_ms)
        except Exception as e:
            logger.error(f"Error loading music: {e}")

    def play(
        self,
        song: str,
        volume: float = CONFIG.music_volume,
        loop: int = MUSIC_LOOP,
        fade_ms: int = MUSIC_FADEIN,
        *,
        fade_previous: bool = False,
    ) -> None:
        if self.is_playing_same_song(song):
            return

        if fade_previous and self.current_song and self.is_playing():
            try:
                platform.mixer.music.fadeout(MUSIC_FADEOUT)
            except Exception as e:
                logger.error(f"Error during fadeout: {e}")

        self.previous_song = self.current_song
        self.current_song = song
        self.status = MusicStatus.PLAYING

        self._user_volume = volume

        physical_volume = 0.0 if self.muted else self._user_volume

        self.load(song, physical_volume, loop, fade_ms)

    def get_path(self, filename: str) -> str:
        if filename in self.cache:
            return self.cache[filename]

        path = fetch_asset("music", db.get_entry("music", filename))
        self.cache[filename] = path
        return path

    def pause(self) -> None:
        if self.status == MusicStatus.PLAYING:
            self.status = MusicStatus.PAUSED
            platform.mixer.music.pause()
        elif self.status == MusicStatus.PAUSED:
            logger.warning("Music is already paused.")
        else:
            logger.warning("Music cannot be paused, none is playing.")

    def unpause(self) -> None:
        if self.status == MusicStatus.PAUSED:
            self.status = MusicStatus.PLAYING
            platform.mixer.music.unpause()
        elif self.status == MusicStatus.STOPPED:
            logger.warning("Music is stopped, cannot unpause.")
        else:
            logger.warning(
                "Music cannot be unpaused, none is paused or not playing."
            )

    def stop(self, fadeout_time: int = MUSIC_FADEOUT) -> None:
        if self.status in (MusicStatus.PLAYING, MusicStatus.PAUSED):
            if fadeout_time > 0:
                self.fadeout(fadeout_time)
            self.status = MusicStatus.STOPPED
            self.current_song = None
            platform.mixer.music.stop()
        else:
            logger.warning("Music cannot be stopped, none is playing.")

    def fadeout(self, time: int) -> None:
        platform.mixer.music.fadeout(time)

    def is_playing(self) -> bool:
        return bool(platform.mixer.music.get_busy())

    def is_playing_same_song(self, song: str) -> bool:
        return self.status == MusicStatus.PLAYING and self.current_song == song

    def set_volume(self, volume: float) -> None:
        volume = max(0.0, min(1.0, volume))

        # UI mute button sets volume=0 → treat as mute
        if volume == 0.0:
            self.mute()
            return

        # Otherwise it's a real volume change
        self._user_volume = volume

        if not self.muted and self.status == MusicStatus.PLAYING:
            platform.mixer.music.set_volume(self._user_volume)

    def decrease_volume(self, amount: float = 0.1) -> None:
        if self.status == MusicStatus.PLAYING:
            current_volume = platform.mixer.music.get_volume()
            new_volume = max(0.0, current_volume - amount)
            self.set_volume(new_volume)
        else:
            logger.warning(
                "Music is not playing, volume adjustment not applied."
            )

    def increase_volume(self, amount: float = 0.1) -> None:
        if self.status == MusicStatus.PLAYING:
            current_volume = platform.mixer.music.get_volume()
            new_volume = min(1.0, current_volume + amount)
            self.set_volume(new_volume)
        else:
            logger.warning(
                "Music is not playing, volume adjustment not applied."
            )

    def get_volume(self) -> float:
        return 0.0 if self.muted else self._user_volume

    def mute(self) -> None:
        self.muted = True
        platform.mixer.music.set_volume(0.0)

    def unmute(self) -> None:
        self.muted = False
        platform.mixer.music.set_volume(self._user_volume)

    def toggle_mute(self) -> None:
        if self.muted:
            self.unmute()
        else:
            self.mute()

    def __repr__(self) -> str:
        return f"MusicPlayerState(status={self.status}, current_song={self.current_song}, previous_song={self.previous_song})"


class SoundProtocol(Protocol):
    def play(self) -> None:
        pass

    def set_volume(self, volume: float) -> None:
        pass


class SoundWrapper(SoundProtocol):
    def __init__(self, sound: pygame.mixer.Sound | None = None):
        self.sound = sound

    def play(self) -> None:
        if self.sound:
            self.sound.play()

    def set_volume(self, volume: float) -> None:
        if self.sound:
            self.sound.set_volume(volume)


class SoundManager:
    def __init__(self) -> None:
        self.sounds: dict[str, SoundProtocol] = {}
        self._user_volume: float = CONFIG.sound_volume
        self.muted: bool = False

    def get_sound_filename(self, slug: str) -> Path | None:
        if not slug:
            return None

        filename = db.get_entry("sounds", slug)
        filename = transform_resource_filename("sounds", filename)
        path = Path(filename)

        if not path.exists():
            logger.error(f"Audio file does not exist: {filename}")
            logger.debug(
                f"Sound '{slug}' failed to resolve to a valid file path."
            )
            return None

        return path

    def load_sound(self, slug: str) -> SoundProtocol:
        if slug in self.sounds:
            return self.sounds[slug]

        filename = self.get_sound_filename(slug)
        if filename is None:
            return SoundWrapper()

        try:
            sound = pygame.mixer.Sound(filename)

            # Apply physical volume based on mute state
            physical_volume = 0.0 if self.muted else self._user_volume
            sound.set_volume(physical_volume)

            wrapper = SoundWrapper(sound)
            self.sounds[slug] = wrapper
            return wrapper

        except (MemoryError, pygame.error) as e:
            logger.error(f"Failed to load sound '{slug}': {e}")
            return SoundWrapper()

    def play(self, slug: str) -> None:
        sound = self.load_sound(slug)
        sound.play()

    def set_volume(self, volume: float) -> None:
        volume = max(0.0, min(1.0, volume))

        if volume == 0.0:
            self.mute()
            return

        self._user_volume = volume

        if not self.muted:
            for wrapper in self.sounds.values():
                wrapper.set_volume(self._user_volume)

    def get_volume(self) -> float:
        return 0.0 if self.muted else self._user_volume

    def mute(self) -> None:
        self.muted = True
        for wrapper in self.sounds.values():
            wrapper.set_volume(0.0)

    def unmute(self) -> None:
        self.muted = False
        for wrapper in self.sounds.values():
            wrapper.set_volume(self._user_volume)

    def toggle_mute(self) -> None:
        if self.muted:
            self.unmute()
        else:
            self.mute()

    def unload_sound(self, slug: str) -> None:
        if slug in self.sounds:
            del self.sounds[slug]
            logger.debug(f"Unloaded sound '{slug}' from cache.")

    def unload_all_sounds(self) -> None:
        self.sounds.clear()
        logger.debug("All sounds unloaded from SoundManager cache.")

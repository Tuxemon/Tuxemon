# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os.path
from typing import Optional, Protocol

import pygame

from tuxemon import prepare
from tuxemon.db import MusicStatus, db
from tuxemon.platform import mixer as mixer2
from tuxemon.tools import transform_resource_filename

logger = logging.getLogger(__name__)


class MusicPlayerState:
    def __init__(self) -> None:
        self.status = MusicStatus.stopped
        self.current_song: Optional[str] = None
        self.previous_song: Optional[str] = None
        self.cache: dict[str, str] = {}

    def load(
        self, filename: str, volume: float, loop: int, fade_ms: int
    ) -> None:
        try:
            path = self.get_path(filename)
            mixer2.music.load(path)
            mixer2.music.set_volume(volume)
            mixer2.music.play(loops=loop, fade_ms=fade_ms)
        except Exception as e:
            logger.error(f"Error loading music: {e}")

    def play(
        self,
        song: str,
        volume: float = prepare.CONFIG.music_volume,
        loop: int = prepare.MUSIC_LOOP,
        fade_ms: int = prepare.MUSIC_FADEIN,
    ) -> None:
        if self.is_playing_same_song(song):
            return
        self.previous_song = self.current_song
        self.status = MusicStatus.playing
        self.current_song = song
        self.load(song, volume, loop, fade_ms)

    def get_path(self, filename: str) -> str:
        if filename in self.cache:
            return self.cache[filename]
        else:
            path = prepare.fetch("music", db.lookup_file("music", filename))
            self.cache[filename] = path
            return path

    def pause(self) -> None:
        if self.status == MusicStatus.playing:
            self.status = MusicStatus.paused
            mixer2.music.pause()
        elif self.status == MusicStatus.paused:
            logger.warning("Music is already paused.")
        else:
            logger.warning("Music cannot be paused, none is playing.")

    def unpause(self) -> None:
        if self.status == MusicStatus.paused:
            self.status = MusicStatus.playing
            mixer2.music.unpause()
        elif self.status == MusicStatus.stopped:
            logger.warning("Music is stopped, cannot unpause.")
        else:
            logger.warning(
                "Music cannot be unpaused, none is paused or not playing."
            )

    def stop(self, fadeout_time: int = prepare.MUSIC_FADEOUT) -> None:
        if self.status in (MusicStatus.playing, MusicStatus.paused):
            if fadeout_time > 0:
                self.fadeout(fadeout_time)
            self.status = MusicStatus.stopped
            self.current_song = None
            mixer2.music.stop()
        else:
            logger.warning("Music cannot be stopped, none is playing.")

    def fadeout(self, time: int) -> None:
        mixer2.music.fadeout(time)

    def is_playing(self) -> bool:
        return bool(mixer2.music.get_busy())

    def is_playing_same_song(self, song: str) -> bool:
        return self.status == MusicStatus.playing and self.current_song == song

    def set_volume(self, volume: float) -> None:
        if self.status == MusicStatus.playing:
            mixer2.music.set_volume(volume)
        else:
            logger.warning("Music is not playing, set volume not applied.")

    def decrease_volume(self, amount: float = 0.1) -> None:
        if self.status == MusicStatus.playing:
            current_volume = mixer2.music.get_volume()
            new_volume = max(0.0, current_volume - amount)
            self.set_volume(new_volume)
        else:
            logger.warning(
                "Music is not playing, volume adjustment not applied."
            )

    def increase_volume(self, amount: float = 0.1) -> None:
        if self.status == MusicStatus.playing:
            current_volume = mixer2.music.get_volume()
            new_volume = min(1.0, current_volume + amount)
            self.set_volume(new_volume)
        else:
            logger.warning(
                "Music is not playing, volume adjustment not applied."
            )

    def get_volume(self) -> Optional[float]:
        if self.status == MusicStatus.playing:
            return float(mixer2.music.get_volume())
        else:
            logger.warning("Music is not playing, cannot get volume.")
            return None

    def __repr__(self) -> str:
        return f"MusicPlayerState(status={self.status}, current_song={self.current_song}, previous_song={self.previous_song})"


class SoundProtocol(Protocol):
    def play(self) -> None:
        pass

    def set_volume(self, volume: float) -> None:
        pass


class SoundWrapper(SoundProtocol):
    def __init__(self, sound: Optional[pygame.mixer.Sound] = None):
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

    def get_sound_filename(self, slug: str) -> Optional[str]:
        if slug is None or slug == "":
            return None

        filename = db.lookup_file("sounds", slug)
        filename = transform_resource_filename("sounds", filename)

        if not os.path.exists(filename):
            logger.error(f"audio file does not exist: {filename}")
            return None

        return filename

    def load_sound(
        self, slug: str, value: float = prepare.CONFIG.sound_volume
    ) -> SoundProtocol:
        if slug in self.sounds:
            return self.sounds[slug]

        filename = self.get_sound_filename(slug)
        if filename is None:
            return SoundWrapper()

        try:
            sound = pygame.mixer.Sound(filename)
            sound.set_volume(value)
            self.sounds[slug] = SoundWrapper(sound)
            return self.sounds[slug]
        except (MemoryError, pygame.error) as e:
            logger.error(f"Failed to load sound '{slug}': {e}")
            return SoundWrapper()

    def play_sound(
        self, slug: str, value: float = prepare.CONFIG.sound_volume
    ) -> None:
        sound = self.load_sound(slug, value)
        sound.play()

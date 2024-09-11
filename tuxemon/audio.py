# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os.path
from typing import Optional, Protocol

import pygame
from pygame import mixer

from tuxemon import prepare
from tuxemon.db import MusicStatus, db
from tuxemon.platform import mixer as mixer2
from tuxemon.session import local_session
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
        volume: float = prepare.MUSIC_VOLUME,
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

    def __repr__(self) -> str:
        return f"MusicPlayerState(status={self.status}, current_song={self.current_song}, previous_song={self.previous_song})"


class SoundProtocol(Protocol):
    def play(self) -> object:
        pass


class DummySound:
    def play(self) -> None:
        pass


def get_sound_filename(slug: Optional[str]) -> Optional[str]:
    """
    Get the filename of a sound slug.

    Parameters:
        slug: Slug of the file record.

    Returns:
        Filename if the sound is found.

    """
    if slug is None or slug == "":
        return None

    # Get the filename from the db
    filename = db.lookup_file("sounds", slug)
    filename = transform_resource_filename("sounds", filename)

    # On some platforms, pygame will silently fail loading
    # a sound if the filename is incorrect so we check here
    if not os.path.exists(filename):
        logger.error(f"audio file does not exist: {filename}")
        return None

    return filename


def load_sound(slug: Optional[str], value: Optional[float]) -> SoundProtocol:
    """
    Load a sound from disk, identified by its slug in the db.

    Parameters:
        slug: Slug for the file record to load.

    Returns:
        Loaded sound, or a placeholder silent sound if it is
        not found.

    """

    filename = get_sound_filename(slug)
    if filename is None:
        return DummySound()
    volume = prepare.SOUND_VOLUME
    if value is None:
        if local_session.player:
            player = local_session.player
            volume = float(player.game_variables.get("sound_volume", volume))
    else:
        volume = value
    try:
        sound = mixer.Sound(filename)
        mixer.Sound.set_volume(sound, volume)
        return sound
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

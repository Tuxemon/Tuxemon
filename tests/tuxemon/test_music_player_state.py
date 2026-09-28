# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.audio import MusicPlayerState
from tuxemon.db import MusicStatus


class DummyMixer:
    """Minimal stub for pygame.mixer.music."""

    def __init__(self):
        self.loaded = None
        self.volume = 1.0
        self.play_calls = []
        self.busy = False

    def load(self, path):
        self.loaded = path

    def set_volume(self, v):
        self.volume = v

    def play(self, loops, fade_ms):
        self.play_calls.append((loops, fade_ms))
        self.busy = True

    def pause(self):
        self.busy = False

    def unpause(self):
        self.busy = True

    def stop(self):
        self.busy = False

    def fadeout(self, t):
        self.busy = False

    def get_busy(self):
        return self.busy


@pytest.fixture
def mixer(monkeypatch):
    dummy = DummyMixer()
    monkeypatch.setattr("tuxemon.platform.platform.mixer.music", dummy)
    return dummy


@pytest.fixture(autouse=True)
def mock_music_db(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.audio.db.get_entry", lambda table, slug: "dummy.ogg"
    )
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    monkeypatch.setattr(
        "tuxemon.audio.fetch_asset", lambda category, filename: "dummy.ogg"
    )


@pytest.fixture
def player():
    return MusicPlayerState()


def test_play_sets_state_and_loads_track(player, mixer):
    player.play("battle_theme")
    assert player.status == MusicStatus.PLAYING
    assert player.current_song == "battle_theme"
    assert mixer.loaded is not None
    assert mixer.busy is True


def test_play_respects_mute(player, mixer):
    player.mute()
    player.play("battle_theme")
    assert mixer.volume == 0.0


def test_unmute_restores_volume(player, mixer):
    player.mute()
    player.unmute()
    assert mixer.volume == player._user_volume


def test_toggle_mute(player, mixer):
    player.toggle_mute()
    assert player.muted is True
    player.toggle_mute()
    assert player.muted is False


def test_set_volume_updates_logical_volume(player, mixer):
    player.set_volume(0.7)
    assert player._user_volume == 0.7


def test_set_volume_zero_triggers_mute(player, mixer):
    player.set_volume(0.0)
    assert player.muted is True
    assert mixer.volume == 0.0


def test_play_same_song_no_reload(player, mixer):
    player.play("track")
    mixer.loaded = None
    player.play("track")
    assert mixer.loaded is None  # no reload


def test_pause_and_unpause(player, mixer):
    player.play("track")
    player.pause()
    assert mixer.busy is False
    player.unpause()
    assert mixer.busy is True


def test_stop_resets_state(player, mixer):
    player.play("track")
    player.stop()
    assert player.status == MusicStatus.STOPPED
    assert player.current_song is None
    assert mixer.busy is False

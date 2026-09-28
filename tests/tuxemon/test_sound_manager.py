# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.audio import SoundManager


class DummySound:
    def __init__(self):
        self.volume = 1.0
        self.played = False

    def play(self):
        self.played = True

    def set_volume(self, v):
        self.volume = v


@pytest.fixture
def dummy_sound(monkeypatch):
    def fake_load(path):
        return DummySound()

    monkeypatch.setattr("pygame.mixer.Sound", fake_load)
    return fake_load


@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.audio.db.get_entry", lambda table, slug: "dummy.wav"
    )
    # Pretend the file exists
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)


@pytest.fixture
def manager():
    return SoundManager()


def test_load_sound_caches(manager, dummy_sound, monkeypatch):
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    s1 = manager.load_sound("hit")
    s2 = manager.load_sound("hit")
    assert s1 is s2


def test_play_sound_uses_cached_sound(manager, dummy_sound, monkeypatch):
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    wrapper = manager.load_sound("hit")
    manager.play("hit")
    assert wrapper.sound.played is True


def test_set_volume_updates_all_sounds(manager, dummy_sound, monkeypatch):
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    s1 = manager.load_sound("hit")
    s2 = manager.load_sound("step")

    manager.set_volume(0.4)
    assert s1.sound.volume == 0.4
    assert s2.sound.volume == 0.4


def test_mute_sets_all_sounds_to_zero(manager, dummy_sound, monkeypatch):
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    s1 = manager.load_sound("hit")
    s2 = manager.load_sound("step")

    manager.mute()
    assert s1.sound.volume == 0.0
    assert s2.sound.volume == 0.0
    assert manager.muted is True


def test_unmute_restores_volume(manager, dummy_sound, monkeypatch):
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    s1 = manager.load_sound("hit")

    manager.set_volume(0.3)
    manager.mute()
    manager.unmute()

    assert s1.sound.volume == 0.3
    assert manager.muted is False


def test_toggle_mute(manager, dummy_sound, monkeypatch):
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    manager.toggle_mute()
    assert manager.muted is True
    manager.toggle_mute()
    assert manager.muted is False


def test_unload_sound(manager, dummy_sound, monkeypatch):
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    manager.load_sound("hit")
    manager.unload_sound("hit")
    assert "hit" not in manager.sounds


def test_unload_all_sounds(manager, dummy_sound, monkeypatch):
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    manager.load_sound("hit")
    manager.load_sound("step")
    manager.unload_all_sounds()
    assert manager.sounds == {}

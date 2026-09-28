# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import json

import pytest

from tuxemon.platform.events import PlayerInput
from tuxemon.platform.input_manager import InputManager
from tuxemon.platform.input_recorder import InputRecorder


class DummyPlayer:
    def __init__(self):
        self.tile_pos = (5, 10)
        self.facing = "north"


class DummyClient:
    def __init__(self):
        self._map_name = "test_map"

    def get_map_name(self):
        return self._map_name


class DummySession:
    def __init__(self):
        self.player = DummyPlayer()
        self.client = DummyClient()


class DummyConfig:
    def __init__(self):
        self.controller = type(
            "C",
            (),
            {
                "type": None,
                "overlay": False,
                "hide_mouse": True,
                "show_input_visualizer": False,
                "combo_window_seconds": 5.0,
            },
        )()
        self.input = type("I", (), {"keyboard_button_map": {}})()


class DummyAFKManager:
    def reset(self):
        pass

    def update(self, dt):
        pass


@pytest.fixture
def recorder():
    return InputRecorder()


@pytest.fixture
def session():
    return DummySession()


@pytest.fixture
def tmpdir_path(tmp_path):
    return tmp_path


def make_event(button=1, value=1.0, ts=123.456):
    return PlayerInput(button=button, value=value, timestamp=ts)


def test_start_and_stop_recording(recorder, session):
    recorder.start_recording(session)
    assert recorder._is_recording

    recorder.record_event(make_event())
    events = recorder.stop_recording("test")

    assert not recorder._is_recording
    assert len(events) == 1
    assert "test" in recorder.list_recordings()
    assert recorder.get_recording_state("test")["map"] == "test_map"


def test_stop_recording_without_start(recorder):
    assert recorder.stop_recording("unused") == []


def test_start_playback_and_next_event(recorder):
    e1 = make_event(button=1)
    e2 = make_event(button=2)
    recorder._recordings["play"] = [e1, e2]

    recorder.start_playback_named("play")
    assert recorder._is_playing_back

    assert recorder.next_playback_event().button == 1
    assert recorder.next_playback_event().button == 2
    assert recorder.next_playback_event() is None
    assert not recorder._is_playing_back


def test_start_playback_while_recording(recorder, session):
    recorder.start_recording(session)
    recorder.start_playback([make_event()])
    assert not recorder._is_playing_back


def test_save_and_load_file(recorder, session, tmpdir_path):
    recorder.start_recording(session)
    recorder.record_event(make_event())
    recorder.stop_recording("filetest")

    path = tmpdir_path / "recording.json"
    assert recorder.save_to_file(path, "filetest")
    assert path.exists()

    loaded = recorder.load_from_file(path, "loaded")
    assert len(loaded) == 1
    assert "loaded" in recorder.list_recordings()
    assert "map" in recorder.get_recording_state("loaded")


def test_save_without_events(recorder, tmpdir_path):
    path = tmpdir_path / "empty.json"
    assert not recorder.save_to_file(path, "nonexistent")
    assert not path.exists()


def test_load_nonexistent_file(recorder, tmpdir_path):
    path = tmpdir_path / "missing.json"
    assert recorder.load_from_file(path, "missing") is None


@pytest.mark.parametrize(
    "btn1,btn2",
    [
        pytest.param(1, 2, id="recordings_btn1_1_btn2_2"),
        pytest.param(5, 9, id="recordings_btn1_5_btn2_9"),
    ],
)
def test_multiple_recordings(recorder, session, btn1, btn2):
    recorder.start_recording(session)
    recorder.record_event(make_event(button=btn1))
    recorder.stop_recording("rec1")

    recorder.start_recording(session)
    recorder.record_event(make_event(button=btn2))
    recorder.stop_recording("rec2")

    assert "rec1" in recorder.list_recordings()
    assert "rec2" in recorder.list_recordings()
    assert (
        recorder.get_recording("rec1")[0].button
        != recorder.get_recording("rec2")[0].button
    )


def test_record_event_clones(recorder, session):
    recorder.start_recording(session)
    e = make_event(button=99)
    recorder.record_event(e)
    e.button = 42
    events = recorder.stop_recording("clone_test")
    assert events[0].button == 99


def test_stop_playback_resets_state(recorder):
    e = make_event()
    recorder._recordings["play"] = [e]
    recorder.start_playback_named("play")
    recorder.stop_playback()

    assert not recorder._is_playing_back
    assert recorder._current_playback_data is None
    assert recorder._playback_index == 0


def test_save_load_round_trip(recorder, session, tmpdir_path):
    recorder.start_recording(session)
    recorder.record_event(make_event(button=7))
    recorder.stop_recording("roundtrip")

    path = tmpdir_path / "roundtrip.json"
    recorder.save_to_file(path, "roundtrip")

    loaded = recorder.load_from_file(path, "roundtrip_loaded")
    assert loaded[0].button == 7
    assert (
        recorder.get_recording_state("roundtrip_loaded")["map"] == "test_map"
    )


def test_empty_initial_state(recorder, tmpdir_path):
    recorder._initial_state = None
    recorder._recorded_events = [make_event()]

    path = tmpdir_path / "no_state.json"
    assert recorder.save_to_file(path)

    data = json.loads(path.read_text())
    assert data["initial_state"] == {}


@pytest.fixture
def manager():
    return InputManager(
        DummyConfig(), DummyAFKManager(), InputRecorder(), (1, 1)
    )


def test_playback_events_flow_through_manager(manager):
    recorder = manager.recorder
    e1 = make_event(button=10, ts=0.0)
    e2 = make_event(button=20, ts=0.0)

    recorder._recordings["demo"] = [e1, e2]
    recorder.start_playback_named("demo")

    events = list(manager.process_events())
    assert events[0].button == 10

    events = list(manager.process_events())
    assert events[0].button == 20

    assert list(manager.process_events()) == []
    assert not recorder._is_playing_back

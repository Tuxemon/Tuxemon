# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest
from pygame.surface import Surface

from tuxemon.surfanim import (
    PlayMode,
    State,
    SurfaceAnimation,
    SurfaceAnimationCollection,
    clip,
)


@pytest.fixture
def frames():
    return [(Surface((10, 10)), 1.0), (Surface((20, 20)), 2.0)]


@pytest.fixture
def animation(frames):
    return SurfaceAnimation(frames)


def test_init(animation):
    assert animation.loop == -1
    assert animation.state is State.STOPPED


@pytest.mark.parametrize(
    "index, expected",
    [
        pytest.param(0, (10, 10), id="frame0_size"),
        pytest.param(1, (20, 20), id="frame1_size"),
        pytest.param(2, (0, 0), id="frame2_size"),
    ],
)
def test_get_frame(animation, index, expected):
    assert animation.get_frame(index).get_size() == expected
    assert animation.duration == 3.0


def test_get_current_frame(animation):
    animation.play()
    assert animation.get_current_frame().get_size() == (10, 10)
    animation.update(1.5)
    assert animation.get_current_frame().get_size() == (20, 20)


def test_is_finished(frames):
    anim = SurfaceAnimation(frames, loop=0)
    assert not anim.is_finished()
    anim.play()
    anim.update(3.0)
    assert anim.is_finished()


def test_play_sets_state(animation):
    animation.play()
    assert animation.state is State.PLAYING


def test_pause_only_when_playing(animation):
    animation.pause()
    assert animation.state is State.STOPPED

    animation.play()
    animation.pause()
    assert animation.state is State.PAUSED


def test_stop_sets_state(animation):
    animation.stop()
    assert animation.state is State.STOPPED


def test_update(animation):
    animation.play()
    animation.update(1.5)
    assert pytest.approx(animation.elapsed, rel=1e-3) == 1.5


def test_elapsed(animation):
    animation.play()
    animation.update(1.5)
    assert pytest.approx(animation.elapsed, rel=1e-3) == 1.5
    animation.seek_to_time(2.5)
    assert pytest.approx(animation.elapsed, rel=1e-3) == 2.5


def test_frames_played(animation):
    animation.play()
    animation.update(1.5)
    assert animation.frames_played == 1
    animation.frames_played = 0
    assert animation.frames_played == 0


def test_rate(animation):
    assert animation.rate == 1.0
    animation.rate = 2.0
    assert animation.rate == 2.0


def test_get_rect(animation):
    rect = animation.get_rect()
    assert (rect.width, rect.height) == (20, 20)


def test_flip(animation):
    animation.flip("x")
    assert animation.get_frame(0).get_size() == (10, 10)
    assert animation.get_frame(1).get_size() == (20, 20)


@pytest.mark.parametrize(
    "value, low, high, expected",
    [
        pytest.param(5, 2, 10, 5, id="within_range"),
        pytest.param(1, 2, 10, 2, id="below_range_clipped"),
        pytest.param(11, 2, 10, 10, id="above_range_clipped"),
    ],
)
def test_clip(value, low, high, expected):
    assert clip(value, low, high) == expected


def test_rewind(animation):
    animation.play()
    animation.update(2.0)
    assert animation.elapsed > 0
    animation.rewind()
    assert pytest.approx(animation.elapsed, abs=1e-3) == 0.0
    assert animation.frames_played == 0


def test_rewind_while_paused(animation):
    animation.play()
    animation.update(1.0)
    animation.pause()
    animation.rewind()
    assert pytest.approx(animation.elapsed, abs=1e-3) == 0.0
    assert animation.state is State.PAUSED


def test_frames_played_backward(animation):
    animation.play_mode = PlayMode.BACKWARD
    animation.play()
    animation.update(1.5)
    assert animation.frames_played == 0


def test_frames_played_ping_pong(animation):
    animation.play_mode = PlayMode.PING_PONG
    animation.play()
    animation.update(1.0)
    assert animation.frames_played == 1
    animation.update(2.5)
    assert animation.frames_played == 0


def test_completion_callback_triggered(animation):
    triggered = []

    def callback():
        triggered.append(True)

    animation.loop = 0
    animation._on_completion_callback = callback
    animation.play()
    animation.update(3.1)
    _ = animation.state
    assert triggered
    assert animation.state is State.STOPPED


def test_callback_only_triggers_once(animation):
    calls = []

    def callback():
        calls.append("called")

    animation.loop = 0
    animation._on_completion_callback = callback
    animation.play()
    animation.update(3.1)
    _ = animation.state
    _ = animation.state
    _ = animation.state
    assert len(calls) == 1


def test_empty_animation_raises():
    with pytest.raises(ValueError, match="Must contain at least one frame"):
        SurfaceAnimation([])


def test_zero_duration_frame_raises():
    frames = [(Surface((5, 5)), 0.0), (Surface((15, 15)), 0.0)]
    with pytest.raises(ValueError, match="duration must be greater than zero"):
        SurfaceAnimation(frames)


def test_looping_resets_elapsed(animation):
    animation.loop = -1
    animation.play()
    animation.update(3.5)
    assert animation.state is State.PLAYING
    assert animation.elapsed < animation.duration


def test_seek_out_of_bounds_internal(animation):
    animation.seek_to_time(10.0)
    expected = animation._internal_clock - (
        animation.duration / animation.rate
    )
    assert pytest.approx(animation._playing_start_time, abs=1e-5) == expected


def test_seek_while_stopped(animation):
    animation.seek_to_time(10.0)
    assert animation.state is State.PAUSED
    assert animation.elapsed == 0.0


@pytest.fixture
def collection(animation):
    return SurfaceAnimationCollection(animation)


def test_collection_init():
    c = SurfaceAnimationCollection()
    assert c._animations == []
    assert c._state is State.STOPPED


def test_add_single_animation(animation):
    c = SurfaceAnimationCollection(animation)
    assert c._animations == [animation]


def test_add_sequence_of_animations(animation):
    seq = [animation] * 3
    c = SurfaceAnimationCollection(*seq)
    assert c._animations == seq


def test_add_mapping_of_animations(animation):
    mapping = {"a": animation, "b": animation}
    c = SurfaceAnimationCollection(mapping)
    assert c._animations == list(mapping.values())


def test_add_multiple_animations(animation):
    seq = [animation] * 3
    c = SurfaceAnimationCollection()
    c.add(*seq)
    assert c._animations == seq


@pytest.mark.parametrize(
    "method, state",
    [
        pytest.param("play", State.PLAYING, id="play_sets_playing"),
        pytest.param("pause", State.PAUSED, id="pause_sets_paused"),
        pytest.param("stop", State.STOPPED, id="stop_sets_stopped"),
    ],
)
def test_collection_state_transitions(collection, method, state):
    getattr(collection, method)()
    assert collection._state is state


def test_state_property(collection):
    assert collection.state is State.STOPPED


def test_remove(animation):
    seq = [animation] * 3
    c = SurfaceAnimationCollection(*seq)
    assert len(c.animations) == 3
    c.remove(animation)
    assert len(c.animations) == 2


def test_clear(animation):
    seq = [animation] * 3
    c = SurfaceAnimationCollection(*seq)
    assert len(c.animations) == 3
    c.clear()
    assert len(c.animations) == 0


def test_copy_creates_independent_instance(animation):
    animation.play()
    animation.update(1.0)
    clone = animation.copy()
    assert clone is not animation
    assert clone._frame_manager is animation._frame_manager
    assert clone.state is State.STOPPED
    assert clone.elapsed == 0.0
    assert clone._playing_start_time != animation._playing_start_time
    clone.play()
    assert animation.state is State.PLAYING
    assert clone.state is State.PLAYING
    clone.pause()
    assert animation.state is State.PLAYING
    assert clone.state is State.PAUSED


def test_copy_preserves_configuration(animation):
    animation.loop = 2
    animation.play_mode = PlayMode.PING_PONG
    animation.rate = 1.5
    triggered = []
    animation.on_completion(lambda: triggered.append(True))
    clone = animation.copy()
    assert clone.loop == 2
    assert clone.play_mode == PlayMode.PING_PONG
    assert clone.rate == 1.5
    assert clone._on_completion_callback is animation._on_completion_callback


def test_copy_has_independent_internal_clock(animation):
    animation.update(2.0)
    clone = animation.copy()
    assert clone._internal_clock == animation._internal_clock
    animation.update(1.0)
    assert animation._internal_clock != clone._internal_clock


def test_copy_does_not_share_playback_progress(animation):
    animation.play()
    animation.update(1.0)
    clone = animation.copy()
    clone.frames_played = 0
    assert animation.frames_played != clone.frames_played
    assert animation.elapsed != clone.elapsed


@pytest.mark.parametrize(
    "start, action, expected",
    [
        pytest.param(
            State.STOPPED, "pause", State.STOPPED, id="stopped_pause_illegal"
        ),
        pytest.param(
            State.STOPPED, "stop", State.STOPPED, id="stopped_stop_idempotent"
        ),
        pytest.param(State.STOPPED, "play", State.PLAYING, id="stopped_play"),
        pytest.param(
            State.PLAYING, "play", State.PLAYING, id="playing_play_idempotent"
        ),
        pytest.param(State.PLAYING, "pause", State.PAUSED, id="playing_pause"),
        pytest.param(State.PLAYING, "stop", State.STOPPED, id="playing_stop"),
        pytest.param(
            State.PAUSED, "pause", State.PAUSED, id="paused_pause_idempotent"
        ),
        pytest.param(State.PAUSED, "stop", State.STOPPED, id="paused_stop"),
        pytest.param(State.PAUSED, "play", State.PLAYING, id="paused_play"),
    ],
)
def test_state_machine_matrix(animation, start, action, expected):
    if start == State.PLAYING:
        animation.play()
    elif start == State.PAUSED:
        animation.play()
        animation.pause()

    getattr(animation, action)()
    assert animation.state is expected


def test_seek_clamps_and_sets_paused(animation):
    animation.seek_to_time(-5)
    assert animation.elapsed == 0.0
    assert animation.state is State.PAUSED
    animation.seek_to_time(999)
    assert animation.elapsed in (0.0, animation.duration)


@pytest.mark.parametrize(
    "initial",
    [
        pytest.param(State.STOPPED, id="stopped"),
        pytest.param(State.PLAYING, id="playing"),
        pytest.param(State.PAUSED, id="paused"),
    ],
)
def test_rewind_preserves_state(animation, initial):
    if initial == State.PLAYING:
        animation.play()
        animation.update(1.0)
    elif initial == State.PAUSED:
        animation.play()
        animation.update(1.0)
        animation.pause()

    before = animation.state
    animation.rewind()

    assert animation.state is before
    assert pytest.approx(animation.elapsed, abs=1e-3) == 0.0


def test_elapsed_wraps_when_looping(animation):
    animation.loop = -1
    animation.play()
    animation.update(animation.duration * 3.2)

    assert animation.state is State.PLAYING
    assert 0 <= animation.elapsed < animation.duration


def test_backward_mode_frame_order(animation):
    animation.play_mode = PlayMode.BACKWARD
    animation.play()
    assert animation.frames_played == len(animation._frame_manager.images) - 1
    animation.update(1.0)
    assert animation.frames_played <= len(animation._frame_manager.images) - 1


def test_ping_pong_forward_then_backward(animation):
    animation.play_mode = PlayMode.PING_PONG
    animation.play()
    half = animation.duration / 2
    animation.update(half * 0.9)
    forward_frame = animation.frames_played
    animation.update(half * 0.9)
    backward_frame = animation.frames_played
    assert backward_frame < forward_frame


def test_progress_monotonic(animation):
    animation.play()
    last = animation.progress
    for _ in range(10):
        animation.update(0.1)
        assert animation.progress >= last
        last = animation.progress


def test_frames_played_matches_start_times(animation):
    animation.play()
    for t in [0.0, 0.5, 1.0, 1.5, 2.9]:
        animation.seek_to_time(t)
        idx = animation.frames_played
        start = animation._frame_manager.start_times[idx]
        assert start <= animation.elapsed <= animation.duration


def test_copy_independent_playback(animation):
    clone = animation.copy()
    clone.play()
    clone.update(1.0)
    assert animation.elapsed == 0.0
    assert clone.elapsed > 0.0


def test_copy_callback_not_shared_state(animation):
    calls = []
    animation.on_completion(lambda: calls.append("orig"))
    clone = animation.copy()
    clone.on_completion(lambda: calls.append("clone"))
    clone.loop = 0
    clone.play()
    clone.update(animation.duration + 0.1)
    _ = clone.state
    assert calls == ["clone"]

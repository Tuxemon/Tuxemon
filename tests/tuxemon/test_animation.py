# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock
from weakref import ref

import pytest

from tuxemon.animation import Animation, AnimationState, ScheduleType


@pytest.fixture
def sprite():
    return MagicMock()


@pytest.fixture
def ani():
    return Animation(x=100, y=100, duration=1000)


def test_init(ani):
    assert ani.props == {"x": 100, "y": 100}
    assert ani.delay == 0
    assert ani._duration == 1000
    assert ani._relative is False


def test_init_with_targets(sprite):
    ani = Animation(sprite, x=100, y=100, duration=1000)
    assert ani._targets == [ref(sprite)]


def test_start(ani, sprite):
    ani.start(sprite)
    assert ani._state is AnimationState.RUNNING
    assert isinstance(ani._targets[0], ref)
    assert ani._targets[0]() is sprite


def test_start_multiple_times(ani, sprite):
    ani.start(sprite)
    with pytest.raises(RuntimeError):
        ani.start(sprite)


def test_update(ani, sprite):
    ani.start(sprite)
    ani.update(500)
    assert ani._elapsed == 500


def test_update_before_start(ani):
    ani.update(500)
    assert ani._elapsed == 0


def test_finish(ani, sprite):
    ani.start(sprite)
    ani.finish()
    assert ani._state is AnimationState.FINISHED


def test_abort(ani, sprite):
    ani.start(sprite)
    ani.abort()
    assert ani._state is AnimationState.ABORTED


def test_get_value(ani, sprite):
    sprite.x = 50
    assert ani._get_value(sprite, "x") == 50


def test_get_value_callable(ani, sprite):
    sprite.x = lambda: 50
    assert ani._get_value(sprite, "x") == 50


def test_set_value(ani, sprite):
    ani._set_value(sprite, "x", 100)
    sprite.x.assert_called_once_with(100)


def test_set_value_callable(ani, sprite):
    sprite.x = MagicMock()
    ani._set_value(sprite, "x", 100)
    sprite.x.assert_called_once_with(100)


def test_callback(ani):
    cb = MagicMock()
    ani.schedule(cb, ScheduleType.ON_FINISH)
    ani.start(MagicMock())
    ani.finish()
    cb.assert_called_once()


def test_update_callback(ani):
    cb = MagicMock()
    ani.schedule(cb, ScheduleType.ON_UPDATE)
    ani.start(MagicMock())
    ani.update(1000)
    assert cb.call_count > 0


def test_delay(sprite):
    ani = Animation(x=100, duration=1000)
    ani.delay = 1000
    ani.start(sprite)

    for _ in range(11):
        ani.update(100)

    assert ani._elapsed > 0


def test_relative(sprite):
    ani = Animation(x=100, y=100, duration=1000, relative=True, initial=0)
    ani.start(sprite)
    ani.finish()
    sprite.x.assert_called_with(100)
    sprite.y.assert_called_with(100)


def test_round_values(sprite):
    ani = Animation(x=100.5, y=100.5, duration=1, round_values=True)
    ani.start(sprite)
    ani.finish()
    assert sprite.x.call_args.args[0] == 100
    assert sprite.y.call_args.args[0] == 100


def test_custom_transition(sprite):
    ani = Animation(sprite, x=100, duration=1000, transition=lambda p: p**2)
    ani.update(500)
    prop = ani.targets[0].properties["x"]
    expected = prop.initial * 0.75 + prop.final * 0.25
    assert sprite.x.call_args.args[0] == pytest.approx(expected, rel=1e-5)


def test_multiple_properties_update(sprite):
    ani = Animation(sprite, x=100, y=200, duration=1000)
    ani.update(500)
    props = ani.targets[0].properties
    assert "x" in props and "y" in props
    assert sprite.x.called or sprite.y.called


def test_garbage_collected_target():
    import gc

    temp = MagicMock()
    ani = Animation(temp, x=100, duration=1000)
    ref_to_sprite = ani.targets[0].target_ref
    del temp
    gc.collect()
    ani.update(500)
    assert ref_to_sprite() is None


def test_finish_after_delay(sprite):
    ani = Animation(sprite, x=100, duration=100, delay=200)
    for _ in range(5):
        ani.update(100)
    assert ani._state is AnimationState.FINISHED


def test_abort_before_delay_expires(sprite):
    ani = Animation(x=100, duration=100, delay=500)
    ani.abort()
    assert ani._state is AnimationState.ABORTED


def test_zero_duration(sprite):
    ani = Animation(x=200, duration=0)
    ani.start(sprite)
    ani.update(1)
    assert ani._state is AnimationState.FINISHED
    sprite.x.assert_called_with(200)


def test_negative_duration(sprite):
    with pytest.raises(ValueError):
        Animation(sprite, x=200, duration=-100)


def test_invalid_transition_type(sprite):
    with pytest.raises(TypeError):
        Animation(sprite, x=200, transition=123)


def test_no_properties(sprite):
    with pytest.raises(ValueError):
        Animation(sprite)


def test_yoyo_infinite(sprite):
    ani = Animation(x=200, duration=100, yoyo=True, yoyo_loops=-1)
    ani.start(sprite)
    ani.update(100)
    assert ani._state is AnimationState.RUNNING
    ani.update(50)
    assert ani._state is AnimationState.RUNNING


def test_yoyo_finite(sprite):
    ani = Animation(x=200, duration=100, yoyo=True, yoyo_loops=1)
    ani.start(sprite)
    ani.update(100)
    ani.update(100)
    assert ani._state is AnimationState.FINISHED


def test_abort_after_finish(ani, sprite):
    ani.start(sprite)
    ani.finish()
    ani.abort()
    assert ani._state is AnimationState.FINISHED


def test_multiple_callbacks(ani, sprite):
    cb1, cb2 = MagicMock(), MagicMock()
    ani.schedule(cb1, ScheduleType.ON_FINISH)
    ani.schedule(cb2, ScheduleType.ON_FINISH)
    ani.start(sprite)
    ani.finish()
    cb1.assert_called_once()
    cb2.assert_called_once()


def test_abort_callback_runs(sprite):
    ani = Animation(x=100, duration=100)
    cb = MagicMock()
    ani.schedule(cb, ScheduleType.ON_ABORT)
    ani.start(sprite)
    ani.abort()
    cb.assert_called_once()


def test_update_callback_stops_after_finish(sprite):
    ani = Animation(x=100, duration=10)
    cb = MagicMock()
    ani.schedule(cb, ScheduleType.ON_UPDATE)
    ani.start(sprite)
    ani.update(10)
    cb_count = cb.call_count
    ani.update(10)
    assert cb.call_count == cb_count


def test_delay_consumed_once(sprite):
    ani = Animation(x=100, duration=100, delay=100)
    ani.start(sprite)
    ani.update(100)
    elapsed_after_delay = ani._elapsed
    ani.update(50)
    assert ani._elapsed == elapsed_after_delay + 50


def test_relative_yoyo(sprite):
    sprite.x = 10
    ani = Animation(x=5, duration=100, relative=True, yoyo=True, yoyo_loops=1)
    ani.update(100)
    ani.update(100)
    assert sprite.x == 10


def test_yoyo_swaps_values(sprite):
    ani = Animation(x=100, duration=100, yoyo=True, yoyo_loops=1)
    ani.start(sprite)
    prop = ani.targets[0].properties["x"]
    first_initial = prop.initial
    first_final = prop.final
    ani._reverse_cycle()
    assert prop.initial == first_final
    assert prop.final == first_initial


def test_start_rejects_kwargs(ani, sprite):
    with pytest.raises(TypeError):
        ani.start(sprite, foo=123)


def test_start_with_no_targets_but_props():
    ani = Animation(x=100, duration=100)
    ani.start()
    ani.update(50)
    assert ani._state is AnimationState.RUNNING


def test_gc_before_start():
    import gc

    temp = MagicMock()
    ani = Animation(x=100, duration=100)
    del temp
    gc.collect()
    ani.start()
    ani.update(50)


def test_reverse_cycle_swaps_initial_and_final(sprite):
    ani = Animation(x=100, duration=100)
    ani.start(sprite)
    prop = ani.targets[0].properties["x"]
    initial_before = prop.initial
    final_before = prop.final
    ani._reverse_cycle()

    assert prop.initial == final_before
    assert prop.final == initial_before


def test_reverse_cycle_toggles_reverse_flag(sprite):
    ani = Animation(x=100, duration=100)
    ani.start(sprite)
    flag_before = ani._is_yoyo_reverse
    ani._reverse_cycle()
    assert ani._is_yoyo_reverse is not flag_before


def test_reverse_cycle_preserves_true_initial_and_true_final(sprite):
    ani = Animation(x=100, duration=100)
    ani.start(sprite)
    prop = ani.targets[0].properties["x"]
    true_initial_before = prop.true_initial
    true_final_before = prop.true_final
    ani._reverse_cycle()
    assert prop.true_initial == true_initial_before
    assert prop.true_final == true_final_before


def test_reverse_cycle_does_not_change_structure(sprite):
    ani = Animation(x=100, y=200, duration=100)
    ani.start(sprite)
    target_count_before = len(ani.targets)
    prop_count_before = len(ani.targets[0].properties)
    ani._reverse_cycle()
    assert len(ani.targets) == target_count_before
    assert len(ani.targets[0].properties) == prop_count_before


def test_reverse_cycle_multiple_times(sprite):
    ani = Animation(x=100, duration=100)
    ani.start(sprite)
    prop = ani.targets[0].properties["x"]
    initial = prop.initial
    final = prop.final
    ani._reverse_cycle()
    ani._reverse_cycle()
    assert prop.initial == initial
    assert prop.final == final

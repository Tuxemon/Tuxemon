# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest
from pygame.sprite import Group

from tuxemon.animation import ScheduleType, Task, TaskBase

DEFAULT_INTERVAL = 1.0


@pytest.fixture
def cb():
    return MagicMock()


@pytest.fixture
def cb2():
    return MagicMock()


def test_task_runs_callback_after_interval(cb):
    task = Task(cb, DEFAULT_INTERVAL)

    task.update(0.5)
    cb.assert_not_called()

    task.update(0.5)
    cb.assert_called_once()


@pytest.mark.parametrize(
    "times",
    [pytest.param(0, id="zero_times"), pytest.param(-5, id="negative_times")],
)
def test_times_must_be_positive_or_minus_one(cb, times):
    with pytest.raises(ValueError):
        Task(cb, DEFAULT_INTERVAL, times)


@pytest.mark.parametrize(
    "callback",
    [
        pytest.param("not callable", id="string_not_callable"),
        pytest.param(123, id="integer_not_callable"),
        pytest.param(None, id="none_not_callable"),
    ],
)
def test_callback_must_be_callable(callback):
    with pytest.raises(TypeError):
        Task(callback, DEFAULT_INTERVAL)


@pytest.mark.parametrize(
    "dt", [pytest.param(0, id="zero_int"), pytest.param(0.0, id="zero_float")]
)
def test_task_runs_immediately_when_interval_zero(cb, dt):
    task = Task(cb, 0)
    task.update(dt)
    cb.assert_called_once()


@pytest.mark.parametrize(
    "times",
    [
        pytest.param(1, id="once"),
        pytest.param(2, id="twice"),
        pytest.param(3, id="thrice"),
    ],
)
def test_task_runs_correct_number_of_times(cb, times):
    task = Task(cb, DEFAULT_INTERVAL, times)

    for _ in range(times):
        task.update(DEFAULT_INTERVAL)

    assert cb.call_count == times


def test_update_after_finish_raises(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.update(DEFAULT_INTERVAL)

    with pytest.raises(RuntimeError):
        task.update(DEFAULT_INTERVAL)


def test_chained_task_added_to_group(cb, cb2):
    task = Task(cb, DEFAULT_INTERVAL)
    task.chain(cb2, DEFAULT_INTERVAL)

    g = Group()
    g.add(task)

    g.update(DEFAULT_INTERVAL)
    cb.assert_called_once()
    cb2.assert_not_called()

    g.update(DEFAULT_INTERVAL)
    cb2.assert_called_once()


def test_is_finish_true(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.update(DEFAULT_INTERVAL)
    assert task.is_finish()


def test_is_finish_false(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.update(0.5)
    assert not task.is_finish()


@pytest.mark.parametrize(
    "new_delay",
    [
        pytest.param(2.0, id="delay_2_seconds"),
        pytest.param(5.0, id="delay_5_seconds"),
    ],
)
def test_reset_delay_when_greater_than_interval(cb, new_delay):
    task = Task(cb, DEFAULT_INTERVAL)
    task.reset_delay(new_delay)
    assert task._interval == new_delay


def test_reset_delay_when_greater_than_time_left(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.update(0.5)
    task.reset_delay(DEFAULT_INTERVAL)
    assert task._interval == DEFAULT_INTERVAL


def test_reset_delay_does_not_change_when_lower(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    lower = DEFAULT_INTERVAL / 2
    task.reset_delay(lower)
    assert task._interval == DEFAULT_INTERVAL


def test_negative_dt_is_ignored(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.update(-1)
    cb.assert_not_called()


def test_large_dt_triggers_multiple_intervals(cb):
    task = Task(cb, DEFAULT_INTERVAL, times=3)
    task.update(3.5)
    assert cb.call_count == 1


def test_chaining_multiple_tasks(cb, cb2):
    t1 = Task(cb, DEFAULT_INTERVAL)
    t2 = t1.chain(cb2, DEFAULT_INTERVAL)
    t2.chain(lambda: None, DEFAULT_INTERVAL)

    g = Group()
    g.add(t1)

    g.update(DEFAULT_INTERVAL)
    assert cb.call_count == 1
    assert cb2.call_count == 0

    g.update(DEFAULT_INTERVAL)
    assert cb2.call_count == 1


def test_abort_triggers_abort_callback(cb):
    abort_cb = MagicMock()
    task = Task(cb, DEFAULT_INTERVAL)
    task.schedule(abort_cb, when="on abort")

    task.abort()
    abort_cb.assert_called_once()


def test_abort_prevents_further_updates(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.abort()

    with pytest.raises(RuntimeError):
        task.update(DEFAULT_INTERVAL)


def test_schedule_accepts_valid_string_schedule(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    finish_cb = MagicMock()
    task.schedule(finish_cb, when="on finish")
    task.update(DEFAULT_INTERVAL)
    finish_cb.assert_called_once()


def test_schedule_rejects_invalid_string_schedule(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    with pytest.raises(ValueError):
        task.schedule(cb, when="not a real schedule")


def test_schedule_none_with_no_valid_schedules_raises():
    class EmptyTask(TaskBase):
        _valid_schedules = ()

        def update(self, dt):
            pass

        def finish(self):
            pass

        def abort(self):
            pass

    t = EmptyTask()
    with pytest.raises(RuntimeError):
        t.schedule(lambda: None)


def test_on_update_callback_runs(cb):
    task = Task(lambda: None, DEFAULT_INTERVAL)
    update_cb = MagicMock()
    task._callbacks[ScheduleType.ON_UPDATE].append((update_cb, (), {}))
    task.update(0.1)
    update_cb.assert_called_once()


def test_on_update_does_not_run_after_finish(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    update_cb = MagicMock()
    task._callbacks[ScheduleType.ON_UPDATE].append((update_cb, (), {}))
    task.update(DEFAULT_INTERVAL)
    with pytest.raises(RuntimeError):
        task.update(0.1)

    update_cb.assert_called_once()


def test_multiple_small_dt_calls_trigger_once(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.update(0.3)
    task.update(0.3)
    task.update(0.3)
    task.update(0.3)
    assert cb.call_count == 1


def test_large_dt_single_loop_finishes(cb):
    task = Task(cb, DEFAULT_INTERVAL, times=1)
    task.update(5.0)
    assert cb.call_count == 1
    assert task.is_finish()


def test_large_dt_infinite_loop_triggers_once(cb):
    task = Task(cb, DEFAULT_INTERVAL, times=-1)
    task.update(10.0)
    assert cb.call_count == 1


def test_chaining_to_infinite_loop_raises(cb):
    task = Task(cb, DEFAULT_INTERVAL, times=-1)
    with pytest.raises(RuntimeError):
        task.chain(lambda: None)


def test_chained_task_inherits_multiple_groups(cb, cb2):
    task = Task(cb, DEFAULT_INTERVAL)
    chained = task.chain(cb2, DEFAULT_INTERVAL)
    g1 = Group()
    g2 = Group()
    g1.add(task)
    g2.add(task)
    task.update(DEFAULT_INTERVAL)
    assert chained in g1 and chained in g2


def test_chained_task_not_started_if_parent_aborted(cb, cb2):
    task = Task(cb, DEFAULT_INTERVAL)
    chained = task.chain(cb2, DEFAULT_INTERVAL)
    task.abort()
    assert chained not in task.groups()


def test_abort_before_any_update(cb):
    abort_cb = MagicMock()
    task = Task(cb, DEFAULT_INTERVAL)
    task.schedule(abort_cb, when="on abort")
    task.abort()
    abort_cb.assert_called_once()


def test_abort_midway(cb):
    abort_cb = MagicMock()
    task = Task(cb, DEFAULT_INTERVAL, times=3)
    task.schedule(abort_cb, when="on abort")
    task.update(DEFAULT_INTERVAL)
    task.abort()
    abort_cb.assert_called_once()
    assert cb.call_count == 1


def test_callbacks_cleared_after_finish(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.update(DEFAULT_INTERVAL)
    assert not task._callbacks


def test_callbacks_cleared_after_abort(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.abort()
    assert not task._callbacks


def test_chain_cleared_after_finish(cb):
    task = Task(cb, DEFAULT_INTERVAL)
    task.chain(lambda: None)
    task.update(DEFAULT_INTERVAL)
    assert task._chain == []


def test_finish_twice_does_not_call_callbacks_again(cb):
    finish_cb = MagicMock()
    task = Task(cb, DEFAULT_INTERVAL)
    task.schedule(finish_cb, when="on finish")
    task.update(DEFAULT_INTERVAL)
    task.finish()
    assert finish_cb.call_count == 1


def test_abort_twice_does_not_call_callbacks_again(cb):
    abort_cb = MagicMock()
    task = Task(cb, DEFAULT_INTERVAL)
    task.schedule(abort_cb, when="on abort")
    task.abort()
    task.abort()
    assert abort_cb.call_count == 1


def test_finish_after_abort_does_nothing(cb):
    finish_cb = MagicMock()
    task = Task(cb, DEFAULT_INTERVAL)
    task.schedule(finish_cb, when="on finish")
    task.abort()
    task.finish()
    finish_cb.assert_not_called()


def test_infinite_zero_interval_runs_once_per_update(cb):
    task = Task(cb, 0, times=-1)
    task.update(0)
    assert cb.call_count == 1


def test_extremely_small_interval(cb):
    task = Task(cb, 1e-12)
    task.update(1e-12)
    assert cb.call_count == 1


def test_on_update_can_be_scheduled(cb):
    task = Task(lambda: None, DEFAULT_INTERVAL)
    task.schedule(cb, when=ScheduleType.ON_UPDATE)
    task.update(0.1)
    cb.assert_called_once()

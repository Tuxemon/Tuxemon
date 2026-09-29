# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.animation import (
    AnimationState,
    DelayTask,
    ScheduleType,
)


class CallbackRecorder:
    def __init__(self):
        self.called = []

    def cb(self, name):
        self.called.append(name)


def test_delay_runs_for_specified_duration():
    d = DelayTask(2.0)
    d.start()
    d.update(1.0)
    assert d._state == AnimationState.RUNNING
    d.update(1.0)
    assert d._state == AnimationState.FINISHED


def test_delay_finishes_immediately_when_zero():
    d = DelayTask(0.0)
    d.start()
    assert d._state == AnimationState.FINISHED


def test_delay_negative_duration_raises():
    with pytest.raises(ValueError):
        DelayTask(-1.0)


def test_delay_accumulates_time():
    d = DelayTask(3.0)
    d.start()
    d.update(0.5)
    d.update(0.5)
    assert d._elapsed == 1.0
    assert d._state == AnimationState.RUNNING
    d.update(2.0)
    assert d._state == AnimationState.FINISHED


def test_delay_large_dt_finishes_immediately():
    d = DelayTask(1.0)
    d.start()
    d.update(5.0)
    assert d._state == AnimationState.FINISHED


def test_delay_executes_update_callbacks():
    d = DelayTask(1.0)
    rec = CallbackRecorder()
    d.schedule(lambda: rec.cb("update"), ScheduleType.ON_UPDATE)
    d.start()
    d.update(0.5)
    assert "update" in rec.called


def test_delay_executes_finish_callbacks():
    d = DelayTask(1.0)
    rec = CallbackRecorder()
    d.schedule(lambda: rec.cb("finish"), ScheduleType.ON_FINISH)
    d.start()
    d.update(1.0)
    assert "finish" in rec.called


def test_delay_abort_sets_state_and_calls_callback():
    d = DelayTask(1.0)
    rec = CallbackRecorder()
    d.schedule(lambda: rec.cb("abort"), ScheduleType.ON_ABORT)
    d.start()
    d.abort()
    assert d._state == AnimationState.ABORTED
    assert "abort" in rec.called


def test_delay_kill_clears_state():
    d = DelayTask(1.0)
    d.start()
    d.kill()
    assert d._state in (AnimationState.FINISHED, AnimationState.ABORTED)


def test_delay_update_before_start_does_nothing():
    d = DelayTask(1.0)
    d.update(1.0)
    assert d._elapsed == 0.0
    assert d._state == AnimationState.NOT_STARTED


@pytest.mark.parametrize(
    "duration",
    [
        pytest.param(0.0, id="duration_0_0"),
        pytest.param(0.1, id="duration_0_1"),
        pytest.param(1.0, id="duration_1_0"),
        pytest.param(5.0, id="duration_5_0"),
    ],
)
def test_delay_parametrized(duration):
    d = DelayTask(duration)
    d.start()
    d.update(duration + 0.5)
    assert d._state == AnimationState.FINISHED

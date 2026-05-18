# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.animation import (
    AnimationState,
    ScheduleType,
    TaskBase,
    TaskParallel,
)


class DummyTask(TaskBase):
    _valid_schedules = (
        ScheduleType.ON_UPDATE,
        ScheduleType.ON_FINISH,
        ScheduleType.ON_ABORT,
    )

    def __init__(self):
        super().__init__()
        self.updated = 0
        self.finished = False
        self.aborted = False
        self._state = AnimationState.RUNNING

    def update(self, dt):
        self.updated += 1
        if self.updated >= 2:
            self.finish()

    def finish(self):
        self._state = AnimationState.FINISHED
        self.finished = True
        self._execute_callbacks(ScheduleType.ON_FINISH)

    def abort(self):
        self._state = AnimationState.ABORTED
        self.aborted = True
        self._execute_callbacks(ScheduleType.ON_ABORT)


def test_parallel_runs_all_tasks():
    t1 = DummyTask()
    t2 = DummyTask()
    par = TaskParallel(t1, t2)
    par.update(1)
    assert t1.updated == 1
    assert t2.updated == 1
    par.update(1)
    assert t1.finished
    assert t2.finished
    assert par._state == AnimationState.FINISHED


def test_parallel_finishes_only_when_all_done():
    t1 = DummyTask()
    t2 = DummyTask()
    par = TaskParallel(t1, t2)
    t1.update(1)
    t1.update(1)
    par.update(1)
    assert par._state == AnimationState.RUNNING
    par.update(1)
    assert par._state == AnimationState.FINISHED


def test_parallel_abort_aborts_all_tasks():
    t1 = DummyTask()
    t2 = DummyTask()
    par = TaskParallel(t1, t2)
    par.abort()
    assert t1.aborted
    assert t2.aborted
    assert par._state == AnimationState.ABORTED


def test_parallel_executes_callbacks():
    t1 = DummyTask()
    par = TaskParallel(t1)
    called = []
    par.schedule(lambda: called.append("update"), ScheduleType.ON_UPDATE)
    par.schedule(lambda: called.append("finish"), ScheduleType.ON_FINISH)
    par.update(1)
    par.update(1)
    assert "update" in called
    assert "finish" in called


def test_parallel_empty_finishes_immediately():
    par = TaskParallel()
    assert par._state == AnimationState.FINISHED


class StartCountingTask(DummyTask):
    def __init__(self):
        super().__init__()
        self.started = False

    def start(self):
        self.started = True
        self._state = AnimationState.RUNNING


def test_parallel_starts_not_started_tasks():
    t = StartCountingTask()
    t._state = AnimationState.NOT_STARTED
    par = TaskParallel(t)
    par.update(1)
    assert t.started
    assert t.updated == 1


def test_parallel_waits_for_all():
    t1 = DummyTask()
    t2 = DummyTask()
    par = TaskParallel(t1, t2)
    t1.update(1)
    t1.update(1)
    par.update(1)
    assert par._state == AnimationState.RUNNING
    par.update(1)
    assert par._state == AnimationState.FINISHED


class InstantTask(DummyTask):
    def update(self, dt):
        self.finish()


def test_parallel_handles_instant_tasks():
    t1 = InstantTask()
    t2 = DummyTask()
    par = TaskParallel(t1, t2)
    par.update(1)
    assert t1.finished
    assert t2.updated == 1


def test_parallel_nested():
    inner = TaskParallel(DummyTask(), DummyTask())
    outer = TaskParallel(inner, DummyTask())
    for _ in range(5):
        outer.update(1)
    assert outer._state == AnimationState.FINISHED


@pytest.mark.parametrize(
    "count",
    [
        pytest.param(1, id="one_task"),
        pytest.param(2, id="two_tasks"),
        pytest.param(5, id="five_tasks"),
        pytest.param(10, id="ten_tasks"),
    ],
)
def test_parallel_many_tasks(count):
    tasks = [DummyTask() for _ in range(count)]
    par = TaskParallel(*tasks)

    for _ in range(20):
        par.update(1)

    assert par._state == AnimationState.FINISHED
    assert all(t.finished for t in tasks)

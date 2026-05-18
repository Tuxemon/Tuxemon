# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import pytest

from tuxemon.animation import (
    AnimationState,
    ScheduleType,
    TaskBase,
    TaskSequence,
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


def test_sequence_runs_tasks_in_order():
    t1 = DummyTask()
    t2 = DummyTask()
    seq = TaskSequence(t1, t2)
    seq.update(1)
    assert t1.updated == 1
    assert t2.updated == 0
    seq.update(1)
    assert t1.finished
    assert t2.updated == 1
    seq.update(1)
    assert t2.finished
    assert seq._state == AnimationState.FINISHED


def test_sequence_finishes_when_all_tasks_done():
    t1 = DummyTask()
    t2 = DummyTask()
    seq = TaskSequence(t1, t2)
    for _ in range(5):
        seq.update(1)
    assert seq._state == AnimationState.FINISHED


def test_sequence_aborts_current_task():
    t1 = DummyTask()
    t2 = DummyTask()
    seq = TaskSequence(t1, t2)
    seq.abort()
    assert t1.aborted
    assert seq._state == AnimationState.ABORTED


def test_sequence_executes_callbacks():
    t1 = DummyTask()
    seq = TaskSequence(t1)
    called = []
    seq.schedule(lambda: called.append("update"), ScheduleType.ON_UPDATE)
    seq.schedule(lambda: called.append("finish"), ScheduleType.ON_FINISH)
    seq.update(1)
    seq.update(1)
    assert "update" in called
    assert "finish" in called


def test_sequence_empty_finishes_immediately():
    seq = TaskSequence()
    assert seq._state == AnimationState.FINISHED


def test_sequence_skips_finished_tasks():
    t1 = DummyTask()
    t1.finish()
    t2 = DummyTask()
    seq = TaskSequence(t1, t2)
    seq.update(1)
    assert t2.updated == 1


class InstantTask(DummyTask):
    def update(self, dt):
        self.finish()


def test_sequence_handles_instant_tasks():
    t1 = InstantTask()
    t2 = DummyTask()
    seq = TaskSequence(t1, t2)
    seq.update(1)
    assert t1.finished
    assert t2.updated == 1


class AbortTask(DummyTask):
    def update(self, dt):
        self.abort()


def test_sequence_child_abort_advances():
    t1 = AbortTask()
    t2 = DummyTask()
    seq = TaskSequence(t1, t2)
    seq.update(1)
    assert t1.aborted
    assert t2.updated == 1


@pytest.mark.parametrize(
    "count",
    [
        pytest.param(1, id="one_task"),
        pytest.param(2, id="two_tasks"),
        pytest.param(5, id="five_tasks"),
        pytest.param(10, id="ten_tasks"),
    ],
)
def test_sequence_multiple_tasks(count):
    tasks = [DummyTask() for _ in range(count)]
    seq = TaskSequence(*tasks)

    for _ in range(20):
        seq.update(1)

    assert seq._state == AnimationState.FINISHED
    assert all(t.finished for t in tasks)

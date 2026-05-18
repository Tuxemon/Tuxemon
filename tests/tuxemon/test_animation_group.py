# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import logging
from unittest.mock import Mock

import pytest

from tuxemon.animation import Animation, ScheduleType, Task
from tuxemon.state.animation_group import AnimationGroup


@pytest.fixture
def group():
    return AnimationGroup()


@pytest.fixture
def fake_group():
    group = AnimationGroup()
    group.task = Mock()
    return group


@pytest.fixture
def dummy_target():
    class Dummy:
        x = 0

    return Dummy()


@pytest.fixture
def dummy_callback():
    return Mock()


def test_animate_adds_animation_to_group(group, dummy_target):
    ani = group.animate(dummy_target, x=0)
    assert isinstance(ani, Animation)
    assert ani in group._group


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({"x": 0}, id="x_only"),
        pytest.param({"duration": 1.0, "x": 5}, id="duration_and_x"),
        pytest.param(
            {"duration": 0.5, "opacity": 1}, id="duration_and_opacity"
        ),
    ],
)
def test_animate_parametrized(group, dummy_target, kwargs):
    ani = group.animate(dummy_target, **kwargs)
    assert ani in group._group


def test_task_creates_task(group, dummy_callback):
    task = group.task(dummy_callback)
    assert isinstance(task, Task)
    assert task in group._group


def test_task_requires_callable(group):
    with pytest.raises(ValueError):
        group.task("not-a-function")


def test_task_schedules_on_finish(group, dummy_callback):
    finish = Mock()
    task = group.task(dummy_callback, on_finish=finish)
    assert ScheduleType.ON_FINISH in task._callbacks


def test_task_invalid_schedule_type_raises(group, dummy_callback):
    with pytest.raises(ValueError):
        group.task(dummy_callback, not_a_real_trigger=lambda: None)


@pytest.mark.parametrize(
    "schedule_type",
    [
        pytest.param("on finish", id="on_finish"),
        pytest.param("on interval", id="on_interval"),
    ],
)
def test_task_parametrized_schedule_types(
    group, dummy_callback, schedule_type
):
    cb = Mock()
    task = group.task(dummy_callback, **{schedule_type: cb})
    assert ScheduleType(schedule_type) in task._callbacks


def test_update_calls_update_on_group(group, dummy_callback):
    task = group.task(dummy_callback)
    task.update = Mock()
    group.update(0.1)
    task.update.assert_called_once()


def test_clear_aborts_tasks(group, dummy_callback):
    task = group.task(dummy_callback)
    task.abort = Mock()
    group.clear()
    task.abort.assert_called_once()
    assert len(group._group) == 0


def test_clear_handles_empty_group(group):
    group.clear()
    assert len(group._group) == 0


def test_remove_of_removes_matching_animations(group, dummy_target):
    ani = group.animate(dummy_target, x=0)
    assert ani in group._group
    group.remove_of(dummy_target)
    assert ani not in group._group


def test_remove_of_does_not_remove_unrelated(group, dummy_target):
    ani1 = group.animate(dummy_target, x=0)

    class Dummy2:
        x = 0

    ani2 = group.animate(Dummy2(), x=0)
    group.remove_of(dummy_target)
    assert ani1 not in group._group
    assert ani2 in group._group


def test_remove_of_no_matches_logs_debug(group, caplog):
    with caplog.at_level(logging.DEBUG):
        group.remove_of(object())
    assert "No animations found" in caplog.text


def test_chain_animations_calls_factories_in_order(fake_group):
    anim1 = Mock()
    anim2 = Mock()
    anim3 = Mock()
    f1 = Mock(return_value=anim1)
    f2 = Mock(return_value=anim2)
    f3 = Mock(return_value=anim3)
    fake_group.chain_animations(f1, f2, f3, start_delay=0)
    scheduled_func = fake_group.task.call_args[0][0]
    scheduled_func()
    anim1.schedule.call_args[0][0]()
    anim2.schedule.call_args[0][0]()
    f1.assert_called_once()
    f2.assert_called_once()
    f3.assert_called_once()
    anim1.schedule.assert_called_once()
    anim2.schedule.assert_called_once()
    anim3.schedule.assert_called_once()
    assert anim1.schedule.call_args.kwargs["when"] == ScheduleType.ON_FINISH
    assert anim2.schedule.call_args.kwargs["when"] == ScheduleType.ON_FINISH
    assert anim3.schedule.call_args.kwargs["when"] == ScheduleType.ON_FINISH


def test_chain_animations_passes_start_delay(fake_group):
    fake_group.chain_animations(lambda: Mock(), start_delay=250)
    fake_group.task.assert_called_once()
    assert fake_group.task.call_args.kwargs["interval"] == 250


def test_chain_animations_only_starts_first(fake_group):
    anim1 = Mock()
    anim2 = Mock()
    f1 = Mock(return_value=anim1)
    f2 = Mock(return_value=anim2)
    fake_group.chain_animations(f1, f2)
    scheduled_func = fake_group.task.call_args[0][0]
    f1.assert_not_called()
    f2.assert_not_called()
    scheduled_func()
    f1.assert_called_once()
    f2.assert_not_called()


def test_chain_animations_schedule_callback_is_callable(fake_group):
    anim = Mock()
    f = Mock(return_value=anim)
    fake_group.chain_animations(f)
    scheduled_func = fake_group.task.call_args[0][0]
    scheduled_func()
    callback = anim.schedule.call_args[0][0]
    assert callable(callback)


def test_chain_animations_no_errors_logged(fake_group, caplog):
    with caplog.at_level(logging.ERROR):
        fake_group.chain_animations(lambda: Mock())
        scheduled_func = fake_group.task.call_args[0][0]
        scheduled_func()
    assert caplog.text == ""


def test_sequence_creates_tasksequence(group):
    t1 = Mock(spec=Task)
    t2 = Mock(spec=Task)
    seq = group.sequence(t1, t2)
    from tuxemon.animation import TaskSequence

    assert isinstance(seq, TaskSequence)
    assert seq in group._group
    assert seq._queue == [t1, t2]


def test_sequence_empty_creates_finished_sequence(group):
    seq = group.sequence()
    from tuxemon.animation import TaskSequence

    assert isinstance(seq, TaskSequence)
    assert seq in group._group
    assert seq._state == seq._state.FINISHED


def test_parallel_creates_taskparallel(group):
    t1 = Mock(spec=Task)
    t2 = Mock(spec=Task)
    para = group.parallel(t1, t2)
    from tuxemon.animation import TaskParallel

    assert isinstance(para, TaskParallel)
    assert para in group._group
    assert para._tasks == [t1, t2]


def test_parallel_empty_creates_finished_parallel(group):
    para = group.parallel()
    from tuxemon.animation import TaskParallel

    assert isinstance(para, TaskParallel)
    assert para in group._group
    assert para._state == para._state.FINISHED


def test_loop_creates_looptask(group):
    t = Mock(spec=Task)
    loop = group.loop(t, times=3)
    from tuxemon.animation import LoopTask

    assert isinstance(loop, LoopTask)
    assert loop in group._group
    assert loop._total_loops == 3


def test_loop_rejects_invalid_times(group):
    t = Mock(spec=Task)
    with pytest.raises(ValueError):
        group.loop(t, times=0)


def test_retry_creates_retrytask(group):
    t = Mock(spec=Task)
    retry = group.retry(t, max_attempts=5)
    from tuxemon.animation import RetryTask

    assert isinstance(retry, RetryTask)
    assert retry in group._group
    assert retry._max_attempts == 5


def test_retry_rejects_invalid_attempts(group):
    t = Mock(spec=Task)
    with pytest.raises(ValueError):
        group.retry(t, max_attempts=0)


def test_conditional_creates_conditionaltask(group):
    t1 = Mock(spec=Task)
    t2 = Mock(spec=Task)
    cond = group.conditional(lambda: True, t1, t2)
    from tuxemon.animation import ConditionalTask

    assert isinstance(cond, ConditionalTask)
    assert cond in group._group
    assert cond._true_task is t1
    assert cond._false_task is t2


def test_conditional_predicate_selects_true_task(group):
    t1 = Mock(spec=Task)
    t2 = Mock(spec=Task)
    cond = group.conditional(lambda: True, t1, t2)
    cond.start()
    assert cond._active_task is t1


def test_conditional_predicate_selects_false_task(group):
    t1 = Mock(spec=Task)
    t2 = Mock(spec=Task)
    cond = group.conditional(lambda: False, t1, t2)
    cond.start()
    assert cond._active_task is t2


def test_race_creates_racetask(group):
    t1 = Mock(spec=Task)
    t2 = Mock(spec=Task)
    race = group.race(t1, t2)
    from tuxemon.animation import RaceTask

    assert isinstance(race, RaceTask)
    assert race in group._group
    assert race._tasks == [t1, t2]


def test_race_warns_on_single_task(group, caplog):
    t = Mock(spec=Task)
    with caplog.at_level(logging.WARNING):
        group.race(t)
    assert "at least two tasks" in caplog.text


def test_delay_creates_delaytask(group):
    delay = group.delay(1.0)
    from tuxemon.animation import DelayTask

    assert isinstance(delay, DelayTask)
    assert delay in group._group
    assert delay._duration == 1.0


def test_delay_rejects_negative_duration(group):
    with pytest.raises(ValueError):
        group.delay(-1.0)


def test_sequence_with_delay_runs_in_order(group):
    t1 = Mock(spec=Task)
    t2 = Mock(spec=Task)
    seq = group.sequence(t1, group.delay(0.1), t2)
    assert seq in group._group


def test_race_with_delay_creates_timeout(group):
    t = Mock(spec=Task)
    race = group.race(t, group.delay(0.1))
    assert race in group._group

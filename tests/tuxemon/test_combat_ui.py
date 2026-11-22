# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.ui.combat_bars import CombatBars


@pytest.fixture
def fake_context():
    ctx = MagicMock()
    ctx.scaling = MagicMock()
    ctx.scaling.scale_int = lambda x: x * 2
    ctx.scaling.scale_tuple = lambda t: tuple(x * 2 for x in t)
    return ctx


@pytest.fixture
def combat_ui(fake_context):
    return CombatBars(fake_context)


@pytest.fixture
def graphics():
    g = MagicMock()
    g.hud.hp_bar_player = True
    g.hud.hp_bar_opponent = True
    g.hud.exp_bar_player = True
    g.hud.hp_bar_width = 70
    g.hud.hp_bar_height = 8
    g.hud.hp_player_top = 18
    g.hud.hp_opponent_top = 12
    g.hud.exp_bar_height = 6
    g.hud.exp_bar_top = 31
    g.hud.bar_right_padding = 8
    return g


def test_init(combat_ui):
    assert combat_ui._hp_bars == {}
    assert combat_ui._exp_bars == {}


@pytest.mark.parametrize(
    "hp_ratio, exp_ratio",
    [
        pytest.param(0.75, 0.5, id="player_with_exp"),
        pytest.param(0.5, 0.0, id="opponent_no_exp"),
    ],
)
def test_draw_bars_hp_and_exp(combat_ui, graphics, hp_ratio, exp_ratio):
    monster = MagicMock()
    monster.hp_ratio = hp_ratio
    monster.experience_progress_percent = exp_ratio

    is_player = exp_ratio > 0

    hud = {monster: MagicMock(player=is_player, image=MagicMock())}

    combat_ui._hp_bars = {monster: MagicMock()}
    combat_ui._exp_bars = {monster: MagicMock()}
    combat_ui.create_rect_for_bar = MagicMock(return_value=MagicMock())

    combat_ui.draw_bars(hud, graphics)

    combat_ui._hp_bars[monster].draw.assert_called_once()

    if is_player:
        combat_ui._exp_bars[monster].draw.assert_called_once()
    else:
        assert not combat_ui._exp_bars[monster].draw.called


def test_create_rect_for_bar(combat_ui, fake_context):
    hud = MagicMock()
    hud.image.get_width.return_value = 100
    rect = combat_ui.create_rect_for_bar(hud, 70, 8, 0, 8)
    assert rect.width == fake_context.scaling.scale_int(70)
    assert rect.height == fake_context.scaling.scale_int(8)
    assert rect.right == 100 - fake_context.scaling.scale_int(8)
    assert rect.top == fake_context.scaling.scale_int(0)


@pytest.mark.parametrize(
    "ratio",
    [
        pytest.param(0.0, id="ratio_0_0"),
        pytest.param(0.4, id="ratio_0_4"),
        pytest.param(0.6, id="ratio_0_6"),
        pytest.param(1.0, id="ratio_1_0"),
    ],
)
def test_get_hp_bar_initializes_with_monster_value(combat_ui, ratio):
    monster = MagicMock()
    monster.hp_ratio = ratio
    bar = combat_ui.get_hp_bar(monster)
    assert bar.value == ratio


@pytest.mark.parametrize(
    "ratio",
    [
        pytest.param(0.0, id="ratio_0_0"),
        pytest.param(0.2, id="ratio_0_2"),
        pytest.param(0.4, id="ratio_0_4"),
        pytest.param(0.9, id="ratio_0_9"),
    ],
)
def test_get_exp_bar_initializes_with_monster_value(combat_ui, ratio):
    monster = MagicMock()
    monster.experience_progress_percent = ratio
    bar = combat_ui.get_exp_bar(monster)
    assert bar.value == ratio


def test_remove_monster_clears_bars(combat_ui):
    monster = MagicMock()
    monster.hp_ratio = 0.5
    monster.experience_progress_percent = 0.3
    combat_ui.get_hp_bar(monster)
    combat_ui.get_exp_bar(monster)
    assert monster in combat_ui._hp_bars
    assert monster in combat_ui._exp_bars
    combat_ui.remove_monster(monster)
    assert monster not in combat_ui._hp_bars
    assert monster not in combat_ui._exp_bars


def test_clear_all_removes_all_bars(combat_ui):
    m1, m2 = MagicMock(), MagicMock()
    m1.hp_ratio, m1.experience_progress_percent = 0.5, 0.2
    m2.hp_ratio, m2.experience_progress_percent = 0.8, 0.7
    combat_ui.get_hp_bar(m1)
    combat_ui.get_exp_bar(m1)
    combat_ui.get_hp_bar(m2)
    combat_ui.get_exp_bar(m2)
    assert combat_ui._hp_bars
    assert combat_ui._exp_bars
    combat_ui.clear_all()
    assert combat_ui._hp_bars == {}
    assert combat_ui._exp_bars == {}


def test_resync_snaps_a_stale_bar_onto_the_model(combat_ui):
    monster = MagicMock()
    monster.experience_progress_percent = 0.2
    bar = combat_ui.get_exp_bar(monster)

    # experience gained with no animation scheduled for it
    monster.experience_progress_percent = 0.75
    combat_ui.resync(bar, monster.experience_progress_percent)

    assert bar.value == 0.75
    assert bar.target_value == 0.75


def test_resync_leaves_a_claimed_bar_for_its_animation(combat_ui):
    monster = MagicMock()
    monster.experience_progress_percent = 0.2
    bar = combat_ui.get_exp_bar(monster)

    # experience gained; the animation that will show it starts later
    monster.experience_progress_percent = 0.75
    combat_ui.claim(bar, monster.experience_progress_percent)
    combat_ui.resync(bar, monster.experience_progress_percent)

    assert bar.value == 0.2
    assert bar.target_value == 0.75


def test_resync_recovers_a_bar_whose_animation_never_landed(combat_ui):
    monster = MagicMock()
    monster.experience_progress_percent = 0.2
    bar = combat_ui.get_exp_bar(monster)

    monster.experience_progress_percent = 0.75
    combat_ui.claim(bar, monster.experience_progress_percent)
    bar.value = 1.0  # animation aborted part-way through a level-up wrap

    # a later gain moves the model on again, so the claim is stale too
    monster.experience_progress_percent = 0.8
    combat_ui.resync(bar, monster.experience_progress_percent)

    assert bar.value == 0.8


def test_draw_bars_resyncs_a_stale_exp_bar(combat_ui, graphics):
    monster = MagicMock()
    monster.hp_ratio = 1.0
    monster.experience_progress_percent = 0.2
    combat_ui.create_rect_for_bar = MagicMock(return_value=MagicMock())

    exp_bar = combat_ui.get_exp_bar(monster)
    exp_bar.draw = MagicMock()
    combat_ui.get_hp_bar(monster).draw = MagicMock()

    monster.experience_progress_percent = 0.6
    combat_ui.draw_bars(
        {monster: MagicMock(player=True, image=MagicMock())}, graphics
    )

    assert exp_bar.value == 0.6


def _sweeps(start, target, levels):
    from tuxemon.states.combat_animations import CombatAnimations

    return CombatAnimations.exp_bar_sweeps(start, target, levels)


def _peak_speed(distance):
    """The fastest moment of a single sweep, in bar-widths per second."""
    from tuxemon.state.animation_transition import AnimationTransition
    from tuxemon.states.combat_animations import EXP_BAR_TRANSITION

    ease = getattr(AnimationTransition, EXP_BAR_TRANSITION)
    ((_, duration, _, _),) = _sweeps(0.0, distance, 0)

    step = 0.001
    return max(
        (ease(p + step) - ease(p)) * distance / (step * duration)
        for p in [i * step for i in range(int(1 / step))]
    )


def test_a_plain_gain_is_a_single_sweep():
    ((value, duration, from_empty, delay),) = _sweeps(0.2, 0.6, 0)
    assert (value, from_empty, delay) == (0.6, False, 0.0)
    assert duration > 0


@pytest.mark.parametrize(
    "distance",
    [
        pytest.param(0.25, id="quarter_bar"),
        pytest.param(0.5, id="half_bar"),
        pytest.param(0.9, id="most_of_the_bar"),
    ],
)
def test_sweep_time_is_proportional_to_the_distance(distance):
    """
    Twice the distance takes twice as long, rather than moving twice as fast.

    This is what holds the ease-out's opening speed steady however much
    experience was gained (see test_the_opening_flick_is_the_same_speed).
    """
    from tuxemon.states.combat_animations import EXP_BAR_SWEEP_TIME

    ((_, duration, _, _),) = _sweeps(0.0, distance, 0)
    assert duration == pytest.approx(distance * EXP_BAR_SWEEP_TIME)


@pytest.mark.parametrize(
    "distance",
    [
        pytest.param(0.25, id="quarter_bar"),
        pytest.param(0.5, id="half_bar"),
        pytest.param(0.9, id="most_of_the_bar"),
    ],
)
def test_the_opening_flick_is_the_same_speed(distance):
    """
    An ease-out is fastest at its start, and that opening speed is what the
    eye has to keep up with. It should not depend on the size of the gain.

    Only gains long enough to escape EXP_BAR_MIN_SWEEP_TIME are compared; a
    sliver of a gain is deliberately given more time than its share, which
    makes it gentler still.
    """
    assert _peak_speed(distance) == pytest.approx(_peak_speed(0.5), rel=0.02)


def test_the_opening_flick_is_slow_enough_to_follow():
    """
    Roughly a bar-width per second. Before this was tuned the bar could cover
    five in the same time, which is what made it impossible to read.
    """
    assert _peak_speed(0.9) < 1.5


def test_the_settle_point_lands_before_the_animation_ends():
    """
    An ease-out creeps long after it looks stopped; anything scheduled to
    follow the bar keys off the settle point instead of the nominal end.
    """
    from tuxemon.states.combat_animations import EXP_BAR_SETTLE

    assert 0.5 < EXP_BAR_SETTLE < 1.0


def test_a_tiny_gain_still_gets_a_visible_sweep():
    from tuxemon.states.combat_animations import EXP_BAR_MIN_SWEEP_TIME

    ((_, duration, _, _),) = _sweeps(0.5, 0.501, 0)
    assert duration == EXP_BAR_MIN_SWEEP_TIME


def test_a_level_up_tops_the_bar_out_then_wraps_round():
    top, rest = _sweeps(0.8, 0.15, 1)

    value, duration, from_empty, delay = top
    assert value == 1.0
    assert not from_empty and delay == 0.0

    value, duration, from_empty, delay = rest
    assert value == 0.15
    assert from_empty  # restarts from empty rather than draining down
    assert delay > 0  # pauses at the top so the wrap is seen


def test_each_level_gained_gets_its_own_sweep():
    sweeps = _sweeps(0.8, 0.3, 3)
    assert [value for value, _, _, _ in sweeps] == [1.0, 1.0, 1.0, 0.3]
    assert all(delay > 0 for _, _, _, delay in sweeps[1:])


def test_a_huge_gain_is_capped_but_keeps_every_sweep():
    """Five levels at full pace would run far too long to sit through."""
    from tuxemon.states.combat_animations import EXP_BAR_MAX_TOTAL_TIME

    sweeps = _sweeps(0.1, 0.4, 5)
    total = sum(duration + delay for _, duration, _, delay in sweeps)

    assert len(sweeps) == 6  # one per level, plus the settling sweep
    assert total == pytest.approx(EXP_BAR_MAX_TOTAL_TIME)


class _FlushHarness:
    """Just enough CombatState to exercise the end-of-combat flush."""

    from tuxemon.states.combat_state import CombatState

    _flush_pending_experience_display = (
        CombatState._flush_pending_experience_display
    )

    def __init__(self, bars):
        self.bars = bars
        self._pending_exp_display = []
        self._pending_levelup_summaries = []
        self.pending_level_ups = {}


def test_combat_ending_early_leaves_the_bar_telling_the_truth(combat_ui):
    """
    The phase machine will not end combat with a message queued, so this
    should never happen -- but if it did, a claimed bar would otherwise sit
    on the old value for an animation that is never going to run.
    """
    monster = MagicMock()
    monster.experience_progress_percent = 0.2
    bar = combat_ui.get_exp_bar(monster)

    monster.experience_progress_percent = 0.75
    combat_ui.claim(bar, monster.experience_progress_percent)
    assert bar.value == 0.2  # holding still, waiting for its animation

    harness = _FlushHarness(combat_ui)
    harness._pending_exp_display.append(monster)
    harness.pending_level_ups[monster] = 1
    harness._flush_pending_experience_display()

    assert bar.value == 0.75
    assert harness._pending_exp_display == []
    assert harness.pending_level_ups == {}

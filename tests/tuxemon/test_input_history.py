# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import random

import pytest

from tuxemon.platform.input_history import (
    ComboHint,
    HistoryEntry,
    InputHistory,
)


class FakeEvent:
    """Minimal PlayerInput stub."""

    def __init__(self, button, pressed=False, released=False):
        self.button = button
        self.pressed = pressed
        self.released = released


class FakeTranslator:
    """Bypasses InputTranslatorMiddleware."""

    def preprocess(self, event):
        return event


class FakeConfig:
    class Controller:
        combo_window_seconds = 0.5

    controller = Controller()


@pytest.fixture
def history(monkeypatch):
    h = InputHistory(FakeConfig())
    monkeypatch.setattr(h, "translator", FakeTranslator())
    return h


@pytest.mark.parametrize(
    "events, expected",
    [
        pytest.param(
            [FakeEvent(1, pressed=True)],
            [1],
            id="single_press",
        ),
        pytest.param(
            [FakeEvent(1, pressed=True), FakeEvent(1, pressed=True)],
            [1],  # duplicate suppressed
            id="duplicate_press_suppressed",
        ),
        pytest.param(
            [FakeEvent(1, pressed=True), FakeEvent(2, pressed=True)],
            [1, 2],
            id="two_distinct_presses",
        ),
    ],
)
def test_record_input_distinct(history, events, expected):
    for e in events:
        history.record_input(e)

    assert [entry.event.button for entry in history.history] == expected


def test_click_tracking(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.record_input(FakeEvent(1, released=True))
    history.record_input(FakeEvent(1, pressed=True))
    history.record_input(FakeEvent(1, released=True))

    assert history.get_button_click_count(1) == 2
    assert history.get_last_button_clicked() == 1


def test_click_tracking_reset(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.record_input(FakeEvent(1, released=True))
    history.reset_click_tracking()

    assert history.get_button_click_count(1) == 0
    assert history.get_last_button_clicked() is None
    assert len(history._buttons_down) == 0


@pytest.mark.parametrize(
    "buttons, expected",
    [
        pytest.param([1, 2], True, id="exact_combo_match"),
        pytest.param([1, 2, 3], False, id="combo_too_long"),
        pytest.param([1, 3], False, id="wrong_second_button"),
    ],
)
def test_is_button_combo(history, buttons, expected):
    history.record_input(FakeEvent(1, pressed=True))
    history.record_input(FakeEvent(2, pressed=True))

    assert history.is_button_combo(buttons) is expected


def test_combo_partial_hint(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.record_input(FakeEvent(2, pressed=True))

    history.is_button_combo([1, 2, 3])
    assert history.current_combo_hint == ComboHint(
        match_length=2, total_combo_length=3
    )


def test_combo_partial_hint_zero(history):
    history.record_input(FakeEvent(2, pressed=True))

    history.is_button_combo([1, 3])
    assert history.current_combo_hint == ComboHint(
        match_length=0, total_combo_length=2
    )


def test_history_aging_removes_old_entries(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.update_history(dt=1.0)

    assert len(history.history) == 0
    assert history.last_history_event is None


def test_history_aging_keeps_recent_entries(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.update_history(dt=0.1)

    assert len(history.history) == 1
    assert history.history[0].age == pytest.approx(0.1)


def test_button_hold_time(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.update(dt=0.3)

    assert history.is_button_held(1, min_hold_time=0.2) is True
    assert history.is_button_held(1, min_hold_time=0.5) is False


def test_clear_history(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.record_input(FakeEvent(2, pressed=True))

    history.clear_history()
    assert len(history.history) == 0


def test_history_entry_structure(history):
    history.record_input(FakeEvent(1, pressed=True))
    entry = history.history[0]

    assert isinstance(entry, HistoryEntry)
    assert entry.event.button == 1
    assert entry.age == 0.0


def test_translator_none_event_is_ignored(history, monkeypatch):
    class NullTranslator:
        def preprocess(self, event):
            return None

    monkeypatch.setattr(history, "translator", NullTranslator())

    history.record_input(FakeEvent(1, pressed=True))
    assert len(history.history) == 0


def test_history_aging_exact_threshold(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.update_history(dt=history.combo_window_seconds)

    assert len(history.history) == 1


def test_history_aging_just_over_threshold(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.update_history(dt=history.combo_window_seconds + 0.0001)

    assert len(history.history) == 0


def test_combo_suffix_match(history):
    history.record_input(FakeEvent(9, pressed=True))
    history.record_input(FakeEvent(1, pressed=True))
    history.record_input(FakeEvent(2, pressed=True))

    assert history.is_button_combo([1, 2]) is True
    assert history.current_combo_hint == ComboHint(2, 2)


@pytest.mark.parametrize(
    "history_buttons, combo, expected_hint",
    [
        pytest.param(
            [1, 2, 1], [1, 2, 1, 3], ComboHint(3, 4), id="overlapping_prefix"
        ),
        pytest.param(
            [1, 2, 1], [1, 2, 2], ComboHint(2, 3), id="partial_overlap"
        ),
        pytest.param(
            [1, 2, 1], [2, 1, 3], ComboHint(2, 3), id="shifted_overlap"
        ),
    ],
)
def test_overlapping_prefixes(history, history_buttons, combo, expected_hint):
    for b in history_buttons:
        history.record_input(FakeEvent(b, pressed=True))

    history.is_button_combo(combo)
    assert history.current_combo_hint == expected_hint


def test_held_timer_resets_on_repress(history):
    history.record_input(FakeEvent(1, pressed=True))
    history.update(dt=0.3)

    history.record_input(FakeEvent(1, released=True))
    history.record_input(FakeEvent(1, pressed=True))

    assert history.get_hold_time(1) == 0.0


def test_click_tracking_invalid_release(history):
    history.record_input(FakeEvent(1, released=True))  # no press first
    assert history.get_button_click_count(1) == 0


def test_history_entry_is_immutable(history):
    history.record_input(FakeEvent(1, pressed=True))
    entry = history.history[0]

    with pytest.raises(AttributeError):
        entry.age = 10


def test_translator_modifies_event(history, monkeypatch):
    class ModifyingTranslator:
        def preprocess(self, event):
            event.button = 99
            return event

    monkeypatch.setattr(history, "translator", ModifyingTranslator())

    history.record_input(FakeEvent(1, pressed=True))
    assert history.history[0].event.button == 99


def test_combo_empty_history(history):
    history.is_button_combo([1, 2, 3])
    assert history.current_combo_hint == ComboHint(0, 3)


def test_combo_empty_list(history):
    history.record_input(FakeEvent(1, pressed=True))

    assert history.is_button_combo([]) is False
    assert history.current_combo_hint == ComboHint(0, 0)


def test_rapid_alternating_presses(history):
    seq = [1, 2, 1, 2, 1]
    for b in seq:
        history.record_input(FakeEvent(b, pressed=True))

    assert [e.event.button for e in history.history] == seq


@pytest.mark.parametrize(
    "history_buttons, combo, expected",
    [
        pytest.param(
            [1, 2, 1, 2], [1, 2, 3], ComboHint(2, 3), id="repeat_prefix"
        ),
        pytest.param(
            [1, 2, 1, 2],
            [1, 2, 1, 3],
            ComboHint(3, 4),
            id="repeat_longer_prefix",
        ),
        pytest.param(
            [1, 2, 1, 2], [2, 1, 2, 3], ComboHint(3, 4), id="repeat_shifted"
        ),
    ],
)
def test_repeated_patterns(history, history_buttons, combo, expected):
    for b in history_buttons:
        history.record_input(FakeEvent(b, pressed=True))

    history.is_button_combo(combo)
    assert history.current_combo_hint == expected


def test_deep_partial_match(history):
    history_buttons = [1, 2, 3]
    combo = [1, 2, 3, 4, 5]

    for b in history_buttons:
        history.record_input(FakeEvent(b, pressed=True))

    history.is_button_combo(combo)
    assert history.current_combo_hint == ComboHint(3, 5)


def test_wrong_order_no_match(history):
    history_buttons = [1, 3, 2]
    combo = [1, 2, 3]

    for b in history_buttons:
        history.record_input(FakeEvent(b, pressed=True))

    history.is_button_combo(combo)
    assert history.current_combo_hint == ComboHint(1, 3)


def test_repeated_first_element(history):
    history_buttons = [1, 1, 1]
    combo = [1, 1, 2]

    for b in history_buttons:
        history.record_input(FakeEvent(b, pressed=True))

    history.is_button_combo(combo)
    assert history.current_combo_hint == ComboHint(1, 3)


@pytest.mark.parametrize(
    "history_buttons, combo, expected",
    [
        pytest.param([1, 2, 1, 2], [1, 2], ComboHint(2, 2), id="branch_exact"),
        pytest.param(
            [1, 2, 1, 2], [1, 2, 1], ComboHint(3, 3), id="branch_partial"
        ),
        pytest.param(
            [1, 2, 1, 2],
            [1, 2, 1, 2, 3],
            ComboHint(4, 5),
            id="branch_extended",
        ),
    ],
)
def test_multi_branch_combos(history, history_buttons, combo, expected):
    for b in history_buttons:
        history.record_input(FakeEvent(b, pressed=True))

    history.is_button_combo(combo)
    assert history.current_combo_hint == expected


def test_fuzz_random_inputs(history):
    random.seed(1234)

    for _ in range(200):
        history.clear_history()
        seq_len = random.randint(0, 10)
        for _ in range(seq_len):
            history.record_input(FakeEvent(random.randint(1, 4), pressed=True))

        combo = [random.randint(1, 4) for _ in range(random.randint(1, 5))]

        history.is_button_combo(combo)
        hint = history.current_combo_hint
        assert 0 <= hint.match_length <= hint.total_combo_length
        assert hint.total_combo_length == len(combo)

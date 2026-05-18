# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock, patch

import pytest

from tuxemon.world.weather import (
    Temperature,
    WeatherTransitionRecord,
    WeatherTransitionRule,
    WeatherTransitionRulesModel,
    Wind,
    WorldWeatherManager,
)


@pytest.fixture
def weather_patch():
    patcher = patch("tuxemon.world.weather.Weather.get")
    mock_weather_class = patcher.start()

    def dummy_weather(slug):
        obj = MagicMock()
        obj.slug = slug
        obj.current_temperature = Temperature("mild")
        obj.current_wind = Wind("calm")
        return obj

    mock_weather_class.side_effect = dummy_weather
    yield
    patcher.stop()


@pytest.fixture
def rules_model():
    rule = WeatherTransitionRule(next_slug="rainy", trigger_chance=1.0)
    return WeatherTransitionRulesModel(transitions={"sunny": [rule]})


def test_initial_weather(weather_patch, rules_model):
    mgr = WorldWeatherManager(initial_slug="sunny", rules_model=rules_model)
    assert mgr.current_slug == "sunny"
    assert mgr.elapsed_time == 0.0


def test_force_transition_records_elapsed(weather_patch, rules_model):
    mgr = WorldWeatherManager(initial_slug="sunny", rules_model=rules_model)
    mgr._elapsed_duration_seconds = 5.0
    mgr.force_transition("rainy")
    history = mgr.get_transition_history()
    assert len(history) == 1
    rec = history[0]
    assert rec.from_slug == "sunny"
    assert rec.to_slug == "rainy"
    assert rec.sim_time == 5.0


def test_advance_turn_triggers_transition(weather_patch, rules_model):
    mgr = WorldWeatherManager(
        initial_slug="sunny", rules_model=rules_model, seed=42
    )
    mgr._elapsed_duration_seconds = 3.0
    mgr.advance_turn()
    history = mgr.get_transition_history()
    assert len(history) == 1
    rec = history[0]
    assert rec.from_slug == "sunny"
    assert rec.to_slug == "rainy"
    assert rec.sim_time == 3.0


def test_no_transition_when_chance_zero(weather_patch):
    zero_rule = WeatherTransitionRule(next_slug="rainy", trigger_chance=0.0)
    rules_model = WeatherTransitionRulesModel(
        transitions={"sunny": [zero_rule]}
    )
    mgr = WorldWeatherManager(
        initial_slug="sunny", rules_model=rules_model, seed=42
    )
    mgr._elapsed_duration_seconds = 5.0
    mgr.advance_turn()
    assert len(mgr.get_transition_history()) == 0


def test_validator_cumulative_chance_exceeds_one():
    bad_rules = [
        WeatherTransitionRule(next_slug="rainy", trigger_chance=0.6),
        WeatherTransitionRule(next_slug="stormy", trigger_chance=0.6),
    ]
    with pytest.raises(ValueError):
        WeatherTransitionRulesModel(transitions={"sunny": bad_rules})


def test_validator_invalid_duration_bounds():
    bad_rule = WeatherTransitionRule(
        next_slug="rainy",
        trigger_chance=1.0,
        min_duration_seconds=10,
        max_duration_seconds=5,
    )
    with pytest.raises(ValueError):
        WeatherTransitionRulesModel(transitions={"sunny": [bad_rule]})


def test_temperature_requirement_blocks_transition(weather_patch):
    rule = WeatherTransitionRule(
        next_slug="rainy",
        trigger_chance=1.0,
        required_temperature=Temperature("hot"),
    )
    rules_model = WeatherTransitionRulesModel(transitions={"sunny": [rule]})
    mgr = WorldWeatherManager(initial_slug="sunny", rules_model=rules_model)
    mgr._elapsed_duration_seconds = 5.0
    mgr.advance_turn()
    assert len(mgr.get_transition_history()) == 0


def test_wind_requirement_blocks_transition(weather_patch):
    rule = WeatherTransitionRule(
        next_slug="rainy",
        trigger_chance=1.0,
        required_wind=Wind("stormy"),
    )
    rules_model = WeatherTransitionRulesModel(transitions={"sunny": [rule]})
    mgr = WorldWeatherManager(initial_slug="sunny", rules_model=rules_model)
    mgr._elapsed_duration_seconds = 5.0
    mgr.advance_turn()
    assert len(mgr.get_transition_history()) == 0


def test_multiple_transitions_accumulate_history(weather_patch, rules_model):
    mgr = WorldWeatherManager(
        initial_slug="sunny", rules_model=rules_model, seed=42
    )
    mgr._elapsed_duration_seconds = 2.0
    mgr.advance_turn()
    mgr._elapsed_duration_seconds = 4.0
    mgr.force_transition("rainy")
    history = mgr.get_transition_history()
    assert len(history) == 2
    assert history[0].from_slug == "sunny"
    assert history[1].from_slug == "rainy"


def test_deterministic_transitions_with_seed(weather_patch):
    rule = WeatherTransitionRule(next_slug="rainy", trigger_chance=1.0)
    rules_model = WeatherTransitionRulesModel(transitions={"sunny": [rule]})
    mgr1 = WorldWeatherManager(
        initial_slug="sunny", rules_model=rules_model, seed=123
    )
    mgr2 = WorldWeatherManager(
        initial_slug="sunny", rules_model=rules_model, seed=123
    )
    mgr1._elapsed_duration_seconds = 2.0
    mgr1.advance_turn()
    mgr2._elapsed_duration_seconds = 2.0
    mgr2.advance_turn()
    h1 = mgr1.get_transition_history()
    h2 = mgr2.get_transition_history()
    assert [(r.from_slug, r.to_slug, r.sim_time) for r in h1] == [
        (r.from_slug, r.to_slug, r.sim_time) for r in h2
    ]


def test_performance_many_updates(weather_patch):
    rules_model = WeatherTransitionRulesModel(
        transitions={
            "sunny": [
                WeatherTransitionRule(next_slug="rainy", trigger_chance=1.0)
            ],
            "rainy": [
                WeatherTransitionRule(next_slug="sunny", trigger_chance=1.0)
            ],
        }
    )
    mgr = WorldWeatherManager(
        initial_slug="sunny", rules_model=rules_model, seed=42
    )
    for i in range(1000):
        mgr._elapsed_duration_seconds = i + 1
        mgr.advance_turn()
    history = mgr.get_transition_history()
    assert len(history) == 1000
    for rec in history:
        assert rec.from_slug is not None
        assert rec.to_slug is not None


def test_weighted_randomness_with_multiple_rules(weather_patch):
    rules = [
        WeatherTransitionRule(next_slug="rainy", trigger_chance=0.7),
        WeatherTransitionRule(next_slug="stormy", trigger_chance=0.3),
    ]
    rules_model = WeatherTransitionRulesModel(transitions={"sunny": rules})
    mgr = WorldWeatherManager(
        initial_slug="sunny", rules_model=rules_model, seed=99
    )
    outcomes = []
    for i in range(100):
        mgr._elapsed_duration_seconds = i + 1
        mgr.advance_turn()
        if mgr.current_slug != "sunny":
            outcomes.append(mgr.current_slug)
            mgr.set_weather("sunny")
    rainy_count = outcomes.count("rainy")
    stormy_count = outcomes.count("stormy")
    assert rainy_count > 0
    assert stormy_count > 0
    assert rainy_count > stormy_count


def test_history_integrity_sequence(weather_patch):
    rules_model = WeatherTransitionRulesModel(
        transitions={
            "sunny": [
                WeatherTransitionRule(next_slug="rainy", trigger_chance=1.0)
            ],
            "rainy": [
                WeatherTransitionRule(next_slug="sunny", trigger_chance=1.0)
            ],
        }
    )
    mgr = WorldWeatherManager(
        initial_slug="sunny", rules_model=rules_model, seed=42
    )
    for i in range(20):
        mgr._elapsed_duration_seconds = i + 1
        mgr.advance_turn()
    history = mgr.get_transition_history()
    assert len(history) > 0
    for i in range(1, len(history)):
        prev = history[i - 1]
        curr = history[i]
        assert prev.to_slug == curr.from_slug, (
            f"History integrity broken at index {i}"
        )


def test_alternating_pattern_in_history(weather_patch):
    rules_model = WeatherTransitionRulesModel(
        transitions={
            "sunny": [
                WeatherTransitionRule(next_slug="rainy", trigger_chance=1.0)
            ],
            "rainy": [
                WeatherTransitionRule(next_slug="sunny", trigger_chance=1.0)
            ],
        }
    )
    mgr = WorldWeatherManager(
        initial_slug="sunny", rules_model=rules_model, seed=42
    )

    for i in range(10):
        mgr._elapsed_duration_seconds = i + 1
        mgr.advance_turn()

    history = mgr.get_transition_history()
    assert len(history) > 0

    expected_sequence = []
    current = "sunny"
    for _ in range(len(history)):
        next_slug = "rainy" if current == "sunny" else "sunny"
        expected_sequence.append((current, next_slug))
        current = next_slug

    actual_sequence = [(rec.from_slug, rec.to_slug) for rec in history]
    assert actual_sequence == expected_sequence


def test_serialization_of_transition_record():
    rec = WeatherTransitionRecord(
        from_slug="sunny", to_slug="rainy", sim_time=5.0
    )
    as_dict = rec.__dict__
    assert "from_slug" in as_dict
    assert "to_slug" in as_dict
    assert "sim_time" in as_dict
    assert "real_time" in as_dict


def test_no_rules_means_weather_stuck(weather_patch):
    rules_model = WeatherTransitionRulesModel(transitions={})
    mgr = WorldWeatherManager(initial_slug="sunny", rules_model=rules_model)
    mgr._elapsed_duration_seconds = 5.0
    mgr.advance_turn()
    assert len(mgr.get_transition_history()) == 0
    assert mgr.current_slug == "sunny"


def test_last_transition_property_updates(weather_patch, rules_model):
    mgr = WorldWeatherManager(initial_slug="sunny", rules_model=rules_model)
    mgr._elapsed_duration_seconds = 3.0
    mgr.advance_turn()
    assert mgr.last_transition is not None
    assert mgr.last_transition.next_slug == "rainy"


def test_real_time_field_is_populated(weather_patch, rules_model):
    mgr = WorldWeatherManager(initial_slug="sunny", rules_model=rules_model)
    mgr._elapsed_duration_seconds = 2.0
    mgr.advance_turn()
    history = mgr.get_transition_history()
    assert len(history) > 0
    rec = history[0]
    assert isinstance(rec.real_time, float)
    assert rec.real_time > 0.0

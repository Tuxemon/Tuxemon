# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from tuxemon.entity.routing import RoutingPolicy, RoutingPolicyRegistry
from tuxemon.platform.const.sizes import KENNEL, LOCKER


def _register(name: str, overrides: dict[str, Any] | None = None) -> None:
    base: dict[str, Any] = {
        "force_to_box": False,
        "kennel_override": None,
        "locker_override": None,
        "max_party_size": None,
        "allow_party_addition": True,
        "auto_release_if_box_full": False,
        "auto_discard_if_box_full": False,
        "overflow_kennel": None,
        "overflow_locker": None,
        "max_box_capacity": None,
        "nickname_rules": {},
        "kennel_name_rules": {},
        "locker_name_rules": {},
    }
    if overrides:
        base.update(overrides)
    RoutingPolicyRegistry._policies[name] = base


@dataclass
class FakeNPCState:
    routing_policy: Any = "default"


@pytest.fixture(autouse=True)
def clean_registry():
    """Isolate each test — clear and repopulate with a known default."""
    RoutingPolicyRegistry._policies = {}
    _register("default")
    yield
    RoutingPolicyRegistry._policies = {}


class TestRegistryHas:
    def test_known_policy_returns_true(self):
        assert RoutingPolicyRegistry.has("default") is True

    def test_unknown_policy_returns_false(self):
        assert RoutingPolicyRegistry.has("nonexistent") is False


class TestRegistryGet:
    def test_returns_routing_policy_instance(self):
        policy = RoutingPolicyRegistry.get("default")
        assert isinstance(policy, RoutingPolicy)

    def test_returned_policy_has_correct_name(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.name == "default"

    def test_unknown_policy_raises_key_error(self):
        with pytest.raises(KeyError, match="nonexistent"):
            RoutingPolicyRegistry.get("nonexistent")


class TestRegistryGetRaw:
    def test_returns_dict(self):
        raw = RoutingPolicyRegistry.get_raw("default")
        assert isinstance(raw, dict)

    def test_missing_key_raises(self):
        with pytest.raises(KeyError):
            RoutingPolicyRegistry.get_raw("missing")


class TestRegistryLazyLoad:
    def test_empty_registry_triggers_load_on_get(self, monkeypatch):
        RoutingPolicyRegistry._policies = {}
        monkeypatch.setattr(
            RoutingPolicyRegistry,
            "load_from_file",
            lambda cls=None: _register("default"),
        )
        assert RoutingPolicyRegistry.has("default")

    def test_empty_registry_triggers_load_on_has(self, monkeypatch):
        RoutingPolicyRegistry._policies = {}
        called = []

        def fake_load(cls=None):
            called.append(True)
            _register("default")

        monkeypatch.setattr(RoutingPolicyRegistry, "load_from_file", fake_load)
        RoutingPolicyRegistry.has("default")
        assert called

    def test_populated_registry_does_not_reload(self, monkeypatch):
        called = []

        def fake_load(cls=None):
            called.append(True)

        monkeypatch.setattr(RoutingPolicyRegistry, "load_from_file", fake_load)
        RoutingPolicyRegistry.get("default")
        assert not called


class TestFromRegistry:
    def test_defaults_are_applied_for_missing_keys(self):
        RoutingPolicyRegistry._policies["sparse"] = {}
        policy = RoutingPolicyRegistry.get("sparse")
        assert policy.force_to_box is False
        assert policy.allow_party_addition is True
        assert policy.auto_release_if_box_full is False
        assert policy.auto_discard_if_box_full is False
        assert policy.nickname_rules == {}
        assert policy.kennel_name_rules == {}
        assert policy.locker_name_rules == {}

    def test_overrides_are_applied(self):
        _register("custom", {"force_to_box": True, "max_party_size": 3})
        policy = RoutingPolicyRegistry.get("custom")
        assert policy.force_to_box is True
        assert policy.max_party_size == 3

    @pytest.mark.parametrize(
        "raw_value, expected",
        [
            pytest.param(1, True, id="int-truthy-becomes-true"),
            pytest.param(0, False, id="int-falsy-becomes-false"),
            pytest.param("yes", True, id="nonempty-string-becomes-true"),
            pytest.param("", False, id="empty-string-becomes-false"),
        ],
    )
    def test_bool_coercion_on_force_to_box(self, raw_value, expected):
        _register("coerce", {"force_to_box": raw_value})
        policy = RoutingPolicyRegistry.get("coerce")
        assert policy.force_to_box is expected

    @pytest.mark.parametrize(
        "raw_value, expected",
        [
            pytest.param(1, True, id="int-1"),
            pytest.param(0, False, id="int-0"),
        ],
    )
    def test_bool_coercion_on_allow_party_addition(self, raw_value, expected):
        _register("coerce", {"allow_party_addition": raw_value})
        policy = RoutingPolicyRegistry.get("coerce")
        assert policy.allow_party_addition is expected

    def test_none_overrides_are_preserved(self):
        _register("nulls", {"kennel_override": None, "locker_override": None})
        policy = RoutingPolicyRegistry.get("nulls")
        assert policy.kennel_override is None
        assert policy.locker_override is None

    def test_string_overrides_are_preserved(self):
        _register(
            "overrides",
            {
                "kennel_override": "my_kennel",
                "locker_override": "my_locker",
            },
        )
        policy = RoutingPolicyRegistry.get("overrides")
        assert policy.kennel_override == "my_kennel"
        assert policy.locker_override == "my_locker"

    def test_nickname_rules_preserved(self):
        _register("nick", {"nickname_rules": {"prefix": "S-", "suffix": "!"}})
        policy = RoutingPolicyRegistry.get("nick")
        assert policy.nickname_rules == {"prefix": "S-", "suffix": "!"}

    def test_max_party_size_negative_one(self):
        _register("unlimited", {"max_party_size": -1})
        policy = RoutingPolicyRegistry.get("unlimited")
        assert policy.max_party_size == -1

    def test_max_box_capacity_preserved(self):
        _register("capped", {"max_box_capacity": 20})
        policy = RoutingPolicyRegistry.get("capped")
        assert policy.max_box_capacity == 20


class TestShouldForceToBox:
    def test_returns_true_when_force_to_box_true(self):
        _register("forced", {"force_to_box": True})
        policy = RoutingPolicyRegistry.get("forced")
        assert policy.should_force_to_box() is True

    def test_returns_false_when_force_to_box_false(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.should_force_to_box() is False


class TestGetKennel:
    def test_returns_kennel_constant_when_no_override(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.get_kennel() == KENNEL

    def test_returns_override_when_set(self):
        _register("k_override", {"kennel_override": "special_box"})
        policy = RoutingPolicyRegistry.get("k_override")
        assert policy.get_kennel() == "special_box"

    def test_returns_kennel_constant_when_override_is_none(self):
        _register("k_none", {"kennel_override": None})
        policy = RoutingPolicyRegistry.get("k_none")
        assert policy.get_kennel() == KENNEL


class TestGetLocker:
    def test_returns_locker_constant_when_no_override(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.get_locker() == LOCKER

    def test_returns_override_when_set(self):
        _register("l_override", {"locker_override": "special_locker"})
        policy = RoutingPolicyRegistry.get("l_override")
        assert policy.get_locker() == "special_locker"

    def test_returns_locker_constant_when_override_is_none(self):
        _register("l_none", {"locker_override": None})
        policy = RoutingPolicyRegistry.get("l_none")
        assert policy.get_locker() == LOCKER


class TestSerialize:
    def test_returns_policy_name(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.serialize() == "default"

    def test_returns_custom_policy_name(self):
        _register("custom_name")
        policy = RoutingPolicyRegistry.get("custom_name")
        assert policy.serialize() == "custom_name"


class TestDeserialize:
    def test_valid_policy_name_is_returned(self):
        state = FakeNPCState(routing_policy="default")
        result = RoutingPolicy.deserialize(state)
        assert result == "default"

    def test_missing_policy_falls_back_to_default(self):
        state = FakeNPCState(routing_policy="nonexistent")
        result = RoutingPolicy.deserialize(state)
        assert result == "default"

    def test_none_routing_policy_falls_back_to_default(self):
        state = FakeNPCState(routing_policy=None)
        result = RoutingPolicy.deserialize(state)
        assert result == "default"

    def test_empty_string_falls_back_to_default(self):
        state = FakeNPCState(routing_policy="")
        result = RoutingPolicy.deserialize(state)
        assert result == "default"

    @pytest.mark.parametrize(
        "bad_value",
        [
            pytest.param(123, id="integer"),
            pytest.param([], id="list"),
            pytest.param({}, id="dict"),
            pytest.param(False, id="bool-false"),
        ],
    )
    def test_non_string_values_fall_back_to_default(self, bad_value):
        state = FakeNPCState(routing_policy=bad_value)
        result = RoutingPolicy.deserialize(state)
        assert result == "default"

    def test_valid_non_default_policy_is_returned(self):
        _register("special")
        state = FakeNPCState(routing_policy="special")
        result = RoutingPolicy.deserialize(state)
        assert result == "special"

    def test_deserialize_logs_warning_for_missing_policy(self, caplog):
        import logging

        state = FakeNPCState(routing_policy="ghost")
        with caplog.at_level(logging.WARNING, logger="tuxemon.entity.routing"):
            RoutingPolicy.deserialize(state)
        assert "ghost" in caplog.text

    def test_deserialize_logs_warning_for_none(self, caplog):
        import logging

        state = FakeNPCState(routing_policy=None)
        with caplog.at_level(logging.WARNING, logger="tuxemon.entity.routing"):
            RoutingPolicy.deserialize(state)
        assert "default" in caplog.text


class TestRoundTrip:
    def test_serialize_then_deserialize_returns_same_name(self):
        _register("round_trip")
        policy = RoutingPolicyRegistry.get("round_trip")
        name = policy.serialize()
        state = FakeNPCState(routing_policy=name)
        result = RoutingPolicy.deserialize(state)
        assert result == policy.name

    @pytest.mark.parametrize(
        "policy_name",
        [
            pytest.param("default", id="default"),
            pytest.param("unlimited", id="unlimited-party"),
        ],
    )
    def test_round_trip_for_known_policies(self, policy_name):
        _register("unlimited", {"max_party_size": -1})
        policy = RoutingPolicyRegistry.get(policy_name)
        state = FakeNPCState(routing_policy=policy.serialize())
        assert RoutingPolicy.deserialize(state) == policy_name


class TestEdgeCases:
    def test_multiple_policies_coexist(self):
        _register("a", {"force_to_box": True})
        _register("b", {"max_party_size": 6})
        assert RoutingPolicyRegistry.get("a").force_to_box is True
        assert RoutingPolicyRegistry.get("b").max_party_size == 6

    def test_get_returns_new_instance_each_call(self):
        p1 = RoutingPolicyRegistry.get("default")
        p2 = RoutingPolicyRegistry.get("default")
        assert p1 is not p2

    def test_mutating_returned_policy_does_not_affect_registry(self):
        policy = RoutingPolicyRegistry.get("default")
        policy.force_to_box = True
        fresh = RoutingPolicyRegistry.get("default")
        assert fresh.force_to_box is False

    def test_nickname_rules_empty_dict_by_default(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.nickname_rules == {}

    def test_overflow_fields_none_by_default(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.overflow_kennel is None
        assert policy.overflow_locker is None

    def test_max_party_size_none_by_default(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.max_party_size is None

    def test_kennel_name_rules_empty_dict_by_default(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.kennel_name_rules == {}

    def test_locker_name_rules_empty_dict_by_default(self):
        policy = RoutingPolicyRegistry.get("default")
        assert policy.locker_name_rules == {}

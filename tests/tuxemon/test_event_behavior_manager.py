# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from unittest.mock import MagicMock

import pytest

from tuxemon.db import (
    Behavior,
    BoundingBox,
    EventObject,
    Operator,
    ParameterizableRule,
    SpatialCondition,
)
from tuxemon.event.eventbehavior import (
    BehaviorManager,
    EventBehavior,
    expand_behavior,
)


@pytest.fixture
def dummy_event():
    return EventObject(
        id=123,
        name="test",
        box=BoundingBox(x=0, y=0, width=1, height=1),
        priority=0,
        timeout=None,
        delay=None,
        conds=[],
        acts=[],
        behavs=[],
    )


@pytest.fixture
def patch_behavior_plugins(monkeypatch):
    def _patch(mapping):
        fake_manager = MagicMock()
        fake_manager.get_class_map.return_value = mapping
        monkeypatch.setattr(
            "tuxemon.event.eventbehavior.PluginManager.from_directory",
            lambda *args, **kwargs: fake_manager,
        )

    return _patch


@pytest.fixture
def behavior_manager(patch_behavior_plugins):
    patch_behavior_plugins({})
    return BehaviorManager(root_path=None)


class DummyBehavior(EventBehavior):
    name = "dummy"

    def expand(self, event, behavior):
        cond = SpatialCondition(
            type="dummy_cond",
            parameters=["x"],
            box=event.box,
            operator=Operator.IS,
            name="dummy_cond",
        )
        act = ParameterizableRule(
            type="dummy_act",
            parameters=["y"],
            name="dummy_act",
        )
        return [cond], [act]


class EmptyBehavior(EventBehavior):
    name = "empty"

    def expand(self, event, behavior):
        return [], []


class ExplodingBehavior(EventBehavior):
    name = "explode"

    def expand(self, event, behavior):
        raise RuntimeError("boom")


class TestBehaviorManager:
    def test_get_behavior_success(self, patch_behavior_plugins):
        patch_behavior_plugins({"dummy": DummyBehavior})
        mgr = BehaviorManager(root_path=None)
        beh = mgr.get_behavior("dummy")
        assert isinstance(beh, DummyBehavior)

    def test_get_behavior_returns_new_instance_each_call(
        self, patch_behavior_plugins
    ):
        patch_behavior_plugins({"dummy": DummyBehavior})
        mgr = BehaviorManager(root_path=None)
        a = mgr.get_behavior("dummy")
        b = mgr.get_behavior("dummy")
        assert a is not b

    def test_get_behavior_missing(self, patch_behavior_plugins, caplog):
        patch_behavior_plugins({})
        mgr = BehaviorManager(root_path=None)
        beh = mgr.get_behavior("unknown")
        assert beh is None
        assert "not implemented" in caplog.text.lower()

    def test_get_behavior_instantiation_error(
        self, patch_behavior_plugins, caplog
    ):
        class BadBehavior(EventBehavior):
            name = "bad"

            def __init__(self):
                raise RuntimeError("boom")

            def expand(self, event, behavior):
                return [], []

        patch_behavior_plugins({"bad": BadBehavior})
        mgr = BehaviorManager(root_path=None)
        beh = mgr.get_behavior("bad")
        assert beh is None
        assert "error instantiating behavior" in caplog.text.lower()

    def test_get_behaviors_returns_all(self, patch_behavior_plugins):
        patch_behavior_plugins(
            {"dummy": DummyBehavior, "empty": EmptyBehavior}
        )
        mgr = BehaviorManager(root_path=None)
        result = mgr.get_behaviors()
        assert set(result) == {DummyBehavior, EmptyBehavior}


class TestExpandBehavior:
    def test_returns_both_conditions_and_actions(
        self, patch_behavior_plugins, dummy_event
    ):
        dummy_event.behavs = [Behavior(type="dummy", args=[], name="b1")]
        patch_behavior_plugins({"dummy": DummyBehavior})
        mgr = BehaviorManager(root_path=None)
        conds, acts = expand_behavior(dummy_event, mgr)
        assert len(conds) == 1
        assert len(acts) == 1
        assert isinstance(conds[0], SpatialCondition)
        assert isinstance(acts[0], ParameterizableRule)
        assert conds[0].type == "dummy_cond"
        assert acts[0].type == "dummy_act"

    def test_conditions_and_actions_come_from_same_expand_call(
        self, patch_behavior_plugins, dummy_event
    ):
        call_count = {"n": 0}

        class CountingBehavior(EventBehavior):
            name = "counting"

            def expand(self, event, behavior):
                call_count["n"] += 1
                cond = SpatialCondition(
                    type="c",
                    parameters=[],
                    box=event.box,
                    operator=Operator.IS,
                    name="c",
                )
                act = ParameterizableRule(type="a", parameters=[], name="a")
                return [cond], [act]

        dummy_event.behavs = [Behavior(type="counting", args=[], name="b1")]
        patch_behavior_plugins({"counting": CountingBehavior})
        mgr = BehaviorManager(root_path=None)
        expand_behavior(dummy_event, mgr)
        assert call_count["n"] == 1, (
            f"expand() was called {call_count['n']} times — expected exactly 1"
        )

    def test_no_behavs_returns_empty(
        self, patch_behavior_plugins, dummy_event
    ):
        patch_behavior_plugins({})
        mgr = BehaviorManager(root_path=None)
        conds, acts = expand_behavior(dummy_event, mgr)
        assert conds == []
        assert acts == []

    def test_skips_missing_plugin(self, patch_behavior_plugins, dummy_event):
        dummy_event.behavs = [Behavior(type="missing", args=[], name="b1")]
        patch_behavior_plugins({})
        mgr = BehaviorManager(root_path=None)
        conds, acts = expand_behavior(dummy_event, mgr)
        assert conds == []
        assert acts == []

    def test_multiple_behaviors_accumulated(
        self, patch_behavior_plugins, dummy_event
    ):
        dummy_event.behavs = [
            Behavior(type="dummy", args=[], name="b1"),
            Behavior(type="dummy", args=[], name="b2"),
        ]
        patch_behavior_plugins({"dummy": DummyBehavior})
        mgr = BehaviorManager(root_path=None)
        conds, acts = expand_behavior(dummy_event, mgr)
        assert len(conds) == 2
        assert len(acts) == 2

    def test_empty_behavior_contributes_nothing(
        self, patch_behavior_plugins, dummy_event
    ):
        dummy_event.behavs = [Behavior(type="empty", args=[], name="b1")]
        patch_behavior_plugins({"empty": EmptyBehavior})
        mgr = BehaviorManager(root_path=None)
        conds, acts = expand_behavior(dummy_event, mgr)
        assert conds == []
        assert acts == []

    def test_exploding_behavior_skipped_entirely(
        self, patch_behavior_plugins, dummy_event, caplog
    ):
        dummy_event.behavs = [Behavior(type="explode", args=[], name="b1")]
        patch_behavior_plugins({"explode": ExplodingBehavior})
        mgr = BehaviorManager(root_path=None)
        conds, acts = expand_behavior(dummy_event, mgr)
        assert conds == []
        assert acts == []
        assert "failed to expand" in caplog.text.lower()

    def test_exploding_behavior_does_not_affect_others(
        self, patch_behavior_plugins, dummy_event, caplog
    ):
        dummy_event.behavs = [
            Behavior(type="explode", args=[], name="b1"),
            Behavior(type="dummy", args=[], name="b2"),
        ]
        patch_behavior_plugins(
            {"explode": ExplodingBehavior, "dummy": DummyBehavior}
        )
        mgr = BehaviorManager(root_path=None)
        conds, acts = expand_behavior(dummy_event, mgr)
        assert len(conds) == 1
        assert len(acts) == 1
        assert conds[0].type == "dummy_cond"
        assert acts[0].type == "dummy_act"

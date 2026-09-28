# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import sys

from tuxemon.database.runtime import db
from tuxemon.startup_state_machine import (
    StartupStateMachine,
)


class DummyClient:
    def __init__(self):
        self.states = []
        self.state_manager = object()

    def push_state(self, name, **kwargs):
        self.states.append(("push", name, kwargs))

    def pop_state(self):
        self.states.append(("pop", None, {}))


class DummyConfig:
    def __init__(self):
        self.skip_titlescreen = False
        self.splash = True
        self.mods = []


class DummyMeta:
    def __init__(self, startup_rules=None):
        self.startup_rules = startup_rules or []


def test_engine_rules_execute_in_order(monkeypatch):
    client = DummyClient()
    config = DummyConfig()
    load_slot = None
    config.mods = []
    machine = StartupStateMachine(client, config, load_slot)
    machine.run()
    pushed = [s for s in client.states if s[0] == "push"]
    assert pushed[0][1] == "BackgroundState"
    assert pushed[1][1] == "IntroState"
    assert pushed[2][1] == "SplashState"
    assert pushed[3][1] == "FadeInTransition"


def test_mod_defined_rules(monkeypatch, tmp_path):
    mod_dir = tmp_path / "tuxemon"
    mod_dir.mkdir()
    (mod_dir / "__init__.py").write_text("")
    (mod_dir / "rules.py").write_text(
        "from tuxemon.startup_rules import StartupRule\n"
        "class CustomRule(StartupRule):\n"
        "    def __init__(self, client, config, load_slot):\n"
        "        self.client = client\n"
        "    def should_apply(self):\n"
        "        return True\n"
        "    def apply(self):\n"
        "        self.client.push_state('CustomState')\n"
    )
    monkeypatch.delitem(sys.modules, "tuxemon", raising=False)
    monkeypatch.delitem(sys.modules, "tuxemon.rules", raising=False)
    sys.path.insert(0, str(tmp_path))
    meta = DummyMeta(startup_rules=["tuxemon.rules.CustomRule"])
    monkeypatch.setattr(db.mod_metadata, "get_mod_metadata", lambda name: meta)
    config = DummyConfig()
    config.mods = ["tuxemon"]
    client = DummyClient()
    machine = StartupStateMachine(client, config, None)
    machine.run()
    assert ("push", "CustomState", {}) in client.states
    sys.path.remove(str(tmp_path))


def test_intro_skipped_when_titlescreen_disabled():
    client = DummyClient()
    config = DummyConfig()
    config.skip_titlescreen = True
    config.mods = []
    machine = StartupStateMachine(client, config, None)
    machine.run()
    pushed = [s for s in client.states if s[0] == "push"]
    names = [p[1] for p in pushed]
    assert "IntroState" not in names
    assert "BackgroundState" in names


def test_splash_skipped_when_disabled():
    client = DummyClient()
    config = DummyConfig()
    config.splash = False
    machine = StartupStateMachine(client, config, None)
    machine.run()
    pushed = [s for s in client.states if s[0] == "push"]
    names = [p[1] for p in pushed]
    assert "SplashState" not in names
    assert "FadeInTransition" not in names


def test_load_slot_prevents_other_rules():
    client = DummyClient()
    config = DummyConfig()
    load_slot = 3
    machine = StartupStateMachine(client, config, load_slot)
    machine.run()
    pushed = [s for s in client.states if s[0] == "push"]
    names = [p[1] for p in pushed]
    assert "LoadMenuState" in names
    assert "SplashState" not in names
    assert "FadeInTransition" not in names


def test_mods_choice_when_multiple_mods(monkeypatch):
    client = DummyClient()
    config = DummyConfig()
    config.skip_titlescreen = True
    config.mods = ["mod1", "mod2"]
    monkeypatch.setattr(
        db.mod_metadata,
        "get_mod_metadata",
        lambda name: DummyMeta(startup_rules=[]),
    )
    machine = StartupStateMachine(client, config, None)
    machine.run()
    pushed = [s for s in client.states if s[0] == "push"]
    names = [p[1] for p in pushed]
    assert "ModsChoice" in names


def test_single_mod_launch(monkeypatch):
    client = DummyClient()
    config = DummyConfig()
    config.skip_titlescreen = True
    config.mods = ["mod1"]
    monkeypatch.setattr(
        db.mod_metadata,
        "get_mod_metadata",
        lambda name: DummyMeta(startup_rules=[]),
    )
    calls = {}

    class FakeLauncher:
        def __init__(self, client):
            pass

        def launch(self, session, meta):
            calls["launched"] = True

    monkeypatch.setattr(
        "tuxemon.startup_state_machine.GameLauncher", FakeLauncher
    )
    machine = StartupStateMachine(client, config, None)
    machine.run()
    assert calls.get("launched") is True

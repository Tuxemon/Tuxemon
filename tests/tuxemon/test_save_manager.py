# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path

import pytest
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.save_system.save_manager import SaveManager


@pytest.fixture
def fake_save_path(monkeypatch, tmp_path):
    def _fake_get_save_path(slot: int) -> str:
        return str(tmp_path / f"slot{slot}.save")

    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.get_save_path", _fake_get_save_path
    )
    return tmp_path


@pytest.fixture
def fake_session():
    class FakeSession:
        def __init__(self):
            self.calls = []

        def save_state(self, index, slot):
            self.calls.append((index, slot))

    return FakeSession()


@pytest.mark.parametrize(
    "slot, create_file, expected",
    [
        pytest.param(1, True, True, id="file_exists"),
        pytest.param(2, False, False, id="file_missing"),
    ],
)
def test_exists(fake_save_path, slot, create_file, expected):
    path = fake_save_path / f"slot{slot}.save"
    if create_file:
        path.write_text("dummy")

    assert SaveManager.exists(slot) is expected


@pytest.mark.parametrize(
    "content, expected_type",
    [
        pytest.param("{}", dict, id="valid_json"),
        pytest.param("", type(None), id="empty_file_returns_none"),
    ],
)
def test_load(monkeypatch, fake_save_path, content, expected_type):
    def fake_load(path):
        if not content:
            return None
        return {"data": True}

    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.save.load", fake_load
    )

    path = fake_save_path / "slot1.save"
    path.write_text(content)

    result = SaveManager.load(1)
    assert isinstance(result, expected_type)


@pytest.mark.parametrize(
    "create_file, expected",
    [
        pytest.param(True, True, id="delete_existing"),
        pytest.param(False, False, id="delete_missing"),
    ],
)
def test_delete(fake_save_path, create_file, expected):
    slot = 1
    path = fake_save_path / "slot1.save"

    if create_file:
        path.write_text("dummy")

    result = SaveManager.delete(slot)
    assert result is expected
    assert path.exists() is False


def test_save_calls_session_save_state(fake_session, fake_save_path):
    slot = 3
    SaveManager.save(fake_session, slot)

    assert fake_session.calls == [(slot, slot)]


def test_delete_oserror(monkeypatch, fake_save_path):
    slot = 1
    path = fake_save_path / "slot1.save"
    path.write_text("dummy")

    def fake_unlink():
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "unlink", lambda self: fake_unlink())

    result = SaveManager.delete(slot)
    assert result is False


def test_save_raises(monkeypatch, fake_session, fake_save_path):
    def fake_save_state(index, slot):
        raise RuntimeError("boom")

    monkeypatch.setattr(fake_session, "save_state", fake_save_state)

    with pytest.raises(RuntimeError):
        SaveManager.save(fake_session, 1)


def test_exists_mutation(monkeypatch, fake_save_path):
    monkeypatch.setattr(Path, "exists", lambda self: True)
    assert SaveManager.exists(1) is True


def test_load_mutation(monkeypatch, fake_save_path):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.save.load", lambda path: "not-a-save"
    )

    path = fake_save_path / "slot1.save"
    path.write_text("dummy")

    result = SaveManager.load(1)
    assert result == "not-a-save"


def test_delete_mutation(monkeypatch, fake_save_path):
    slot = 1
    path = fake_save_path / "slot1.save"
    path.write_text("dummy")

    monkeypatch.setattr(Path, "unlink", lambda self: None)

    result = SaveManager.delete(slot)
    assert result is True


def test_save_mutation(monkeypatch, fake_session, fake_save_path):
    def fake_save_state(index, slot):
        fake_session.calls.append(("wrong", "wrong"))

    monkeypatch.setattr(fake_session, "save_state", fake_save_state)

    SaveManager.save(fake_session, 3)

    assert fake_session.calls == [("wrong", "wrong")]


def test_all_slots(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.ui_to_save_index",
        lambda i: i + 10,
    )
    assert SaveManager.all_slots(3) == [10, 11, 12]


def test_slot_from_ui(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.ui_to_save_index",
        lambda i: i * 2,
    )
    assert SaveManager.slot_from_ui(4) == 8


def test_render_empty(monkeypatch):
    called = {}

    def fake_render(rect, scaling, font):
        called["ok"] = True
        return "surface"

    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.render_empty_slot",
        fake_render,
    )

    result = SaveManager.render_empty("rect", "scaling", "font")
    assert result == "surface"
    assert called["ok"] is True


def test_render_slot(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.SaveManager.load",
        lambda slot: {"dummy": True},
    )
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.render_thumbnail",
        lambda data, rect: Surface((10, 10)),
    )
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.render_slot_text",
        lambda *args, **kwargs: None,
    )

    rect = Rect(0, 0, 200, 100)
    result = SaveManager.render_slot(rect, 1, "scaling", "font")

    assert isinstance(result, Surface)


def test_render_slot_missing_data(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.SaveManager.load",
        lambda slot: None,
    )

    rect = Rect(0, 0, 200, 100)

    with pytest.raises(RuntimeError):
        SaveManager.render_slot(rect, 1, "scaling", "font")


def test_delete_logs_warning(monkeypatch, caplog):
    monkeypatch.setattr(Path, "exists", lambda self: False)

    caplog.set_level("WARNING", logger="tuxemon.save_system.save_manager")

    SaveManager.delete(1)
    assert "does not exist" in caplog.text

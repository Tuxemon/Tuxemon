# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from pathlib import Path

import pytest
from pygame.rect import Rect
from pygame.surface import Surface

from tuxemon.save_system.save_manager import SaveManager
from tuxemon.save_system.save_slots import AUTOSAVE_SLOT


@pytest.fixture
def fake_save_path(monkeypatch, tmp_path):
    def _fake_get_save_path(slot: int) -> str:
        return str(tmp_path / f"slot{slot}.save")

    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.get_save_path",
        _fake_get_save_path,
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
        pytest.param(1, True, True, id="exists-file"),
        pytest.param(2, False, False, id="exists-missing"),
    ],
)
def test_exists(fake_save_path, slot, create_file, expected):
    path = fake_save_path / f"slot{slot}.save"
    if create_file:
        path.write_text("x")
    assert SaveManager.exists(slot) is expected


@pytest.mark.parametrize(
    "content, expected_type",
    [
        pytest.param("{}", dict, id="load-valid"),
        pytest.param("", type(None), id="load-empty"),
    ],
)
def test_load(monkeypatch, fake_save_path, content, expected_type):
    def fake_load(path):
        if not content:
            return None
        return {"ok": True}

    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.save.load",
        fake_load,
    )
    path = fake_save_path / "slot1.save"
    path.write_text(content)
    result = SaveManager.load(1)
    assert isinstance(result, expected_type)


@pytest.mark.parametrize(
    "create_file, expected",
    [
        pytest.param(True, True, id="delete-existing"),
        pytest.param(False, False, id="delete-missing"),
    ],
)
def test_delete(fake_save_path, create_file, expected):
    slot = 1
    path = fake_save_path / "slot1.save"
    if create_file:
        path.write_text("x")
    result = SaveManager.delete(slot)
    assert result is expected
    assert not path.exists()


def test_save_calls_session_save_state(fake_session, fake_save_path):
    SaveManager.save(fake_session, 3)
    assert fake_session.calls == [(3, 3)]


def test_delete_oserror(monkeypatch, fake_save_path):
    slot = 1
    path = fake_save_path / "slot1.save"
    path.write_text("x")

    def fake_unlink():
        raise OSError("denied")

    monkeypatch.setattr(Path, "unlink", lambda self: fake_unlink())
    assert SaveManager.delete(slot) is False


def test_save_raises(monkeypatch, fake_session, fake_save_path):
    def fake_save_state(index, slot):
        raise RuntimeError("boom")

    monkeypatch.setattr(fake_session, "save_state", fake_save_state)
    with pytest.raises(RuntimeError):
        SaveManager.save(fake_session, 1)


def test_exists_mutation(monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda self: True)
    assert SaveManager.exists(1) is True


def test_load_mutation(monkeypatch, fake_save_path):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.save.load",
        lambda path: "x",
    )
    path = fake_save_path / "slot1.save"
    path.write_text("x")
    assert SaveManager.load(1) == "x"


def test_delete_mutation(monkeypatch, fake_save_path):
    slot = 1
    path = fake_save_path / "slot1.save"
    path.write_text("x")
    monkeypatch.setattr(Path, "unlink", lambda self: None)
    assert SaveManager.delete(slot) is True


def test_save_mutation(monkeypatch, fake_session, fake_save_path):
    def fake_save_state(index, slot):
        fake_session.calls.append(("bad", "bad"))

    monkeypatch.setattr(fake_session, "save_state", fake_save_state)
    SaveManager.save(fake_session, 3)
    assert fake_session.calls == [("bad", "bad")]


def test_all_slots_offset(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.ui_to_save_index",
        lambda i: i + 10,
    )
    assert SaveManager.all_slots(3) == [10, 11, 12]


def test_slot_from_ui_offset(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.ui_to_save_index",
        lambda i: i * 2,
    )
    assert SaveManager.slot_from_ui(4) == 8


def test_render_empty(monkeypatch):
    called = {}

    def fake_render(rect, scaling, font, slot):
        called["ok"] = True
        return "surface"

    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.render_empty_slot",
        fake_render,
    )
    result = SaveManager.render_empty("rect", 1, "scaling", "font")
    assert result == "surface"
    assert called["ok"] is True


def test_render_slot(monkeypatch):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.SaveManager.load",
        lambda slot: {"x": True},
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
    assert isinstance(
        SaveManager.render_slot(rect, 1, "scaling", "font"),
        Surface,
    )


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


@pytest.mark.parametrize(
    "exists, expected",
    [
        pytest.param(True, True, id="autosave-exists"),
        pytest.param(False, False, id="autosave-missing"),
    ],
)
def test_has_autosave(monkeypatch, exists, expected):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.SaveManager.exists",
        lambda slot: exists if slot == AUTOSAVE_SLOT else False,
    )
    assert SaveManager.has_autosave() is expected


@pytest.mark.parametrize(
    "max_slots, include_autosave, expected",
    [
        pytest.param(3, False, [1, 2, 3], id="slots-no-autosave"),
        pytest.param(3, True, [0, 1, 2, 3], id="slots-with-autosave"),
    ],
)
def test_all_slots_autosave(
    monkeypatch, max_slots, include_autosave, expected
):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.ui_to_save_index",
        lambda i: i + 1,
    )
    assert SaveManager.all_slots(max_slots, include_autosave) == expected


@pytest.mark.parametrize(
    "ui_index, includes_autosave, expected",
    [
        pytest.param(0, False, 1, id="ui0-no-autosave"),
        pytest.param(1, False, 2, id="ui1-no-autosave"),
        pytest.param(0, True, 0, id="ui0-autosave"),
        pytest.param(1, True, 1, id="ui1-autosave"),
    ],
)
def test_slot_from_ui(monkeypatch, ui_index, includes_autosave, expected):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.ui_to_save_index",
        lambda i: i + 1,
    )
    assert SaveManager.slot_from_ui(ui_index, includes_autosave) == expected


@pytest.mark.parametrize(
    "slot, expected_label",
    [
        pytest.param(0, "menu_autosave", id="label-autosave"),
        pytest.param(2, "slot", id="label-normal"),
    ],
)
def test_render_slot_label(monkeypatch, slot, expected_label):
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.SaveManager.load",
        lambda s: {"x": True},
    )
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.render_thumbnail",
        lambda data, rect: Surface((10, 10)),
    )
    captured = {}

    def fake_render_slot_text(surface, rect, label, save_data, scaling, font):
        captured["label"] = label

    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.render_slot_text",
        fake_render_slot_text,
    )
    monkeypatch.setattr(
        "tuxemon.save_system.save_manager.T.translate",
        lambda key: key,
    )
    rect = Rect(0, 0, 200, 100)
    SaveManager.render_slot(rect, slot, "scaling", "font")
    assert expected_label in captured["label"]

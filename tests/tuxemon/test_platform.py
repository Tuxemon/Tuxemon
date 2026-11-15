# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
import sys
import types
from pathlib import Path

from tuxemon.platform import ASSET_ROOT, DummyMixer, Platform


def fake_module(name, **attrs):
    module = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(module, k, v)
    return module


def test_detect_android(monkeypatch):
    android = fake_module("android", context=None)
    monkeypatch.setitem(sys.modules, "android", android)

    p = Platform()
    p._detect_android()

    assert p.android is android


def test_detect_android_missing(monkeypatch):
    monkeypatch.delitem(sys.modules, "android", raising=False)

    p = Platform()
    p._detect_android()

    assert p.android is None


def test_android_mixer(monkeypatch):
    android = fake_module("android", context=None)
    android_mixer = fake_module("android.mixer", music=None)

    monkeypatch.setitem(sys.modules, "android", android)
    monkeypatch.setitem(sys.modules, "android.mixer", android_mixer)

    p = Platform()
    p._detect_android()
    p._init_mixer()

    assert p.mixer is android_mixer
    assert not p._pygame_mixer_in_use


def test_android_mixer_missing(monkeypatch):
    android = fake_module("android", context=None)
    fake_pygame = fake_module("pygame")
    fake_pygame_mixer = fake_module("pygame.mixer", music=None)

    monkeypatch.setitem(sys.modules, "android", android)
    monkeypatch.delitem(sys.modules, "android.mixer", raising=False)

    fake_pygame.mixer = fake_pygame_mixer
    monkeypatch.setitem(sys.modules, "pygame", fake_pygame)
    monkeypatch.setitem(sys.modules, "pygame.mixer", fake_pygame_mixer)

    p = Platform()
    p._detect_android()
    p._init_mixer()

    assert p.mixer is fake_pygame_mixer
    assert p._pygame_mixer_in_use


def test_pygame_mixer(monkeypatch):
    fake_pygame = fake_module("pygame")
    fake_pygame_mixer = fake_module("pygame.mixer", music=None)

    fake_pygame.mixer = fake_pygame_mixer

    monkeypatch.setitem(sys.modules, "pygame", fake_pygame)
    monkeypatch.setitem(sys.modules, "pygame.mixer", fake_pygame_mixer)

    p = Platform()
    p._detect_android()
    p._init_mixer()

    assert p.mixer is fake_pygame_mixer
    assert p._pygame_mixer_in_use


def test_no_mixers(monkeypatch):
    monkeypatch.delitem(sys.modules, "android", raising=False)

    fake_pygame = fake_module("pygame")
    fake_pygame.mixer = None

    monkeypatch.setitem(sys.modules, "pygame", fake_pygame)
    monkeypatch.delitem(sys.modules, "pygame.mixer", raising=False)

    p = Platform()
    p._detect_android()
    p._init_mixer()

    assert isinstance(p.mixer, DummyMixer)


def test_user_storage_desktop():
    p = Platform()
    p.android = None

    user_dir = p.user_storage.user_dir()
    assert user_dir.name == ".tuxemon"


def test_system_storage_desktop():
    p = Platform()
    p.android = None

    dirs = p.system_storage.system_dirs()
    paths = [h.path for h in dirs if h.path is not None]
    assert any(str(p).endswith("tuxemon") for p in paths)


def test_lazy_storage(monkeypatch):
    p = Platform()
    p.android = None
    storage1 = p.system_storage
    assert storage1.android is None

    fake_android = fake_module("android", context=None)
    p.android = fake_android

    storage2 = p.system_storage
    assert storage2 is storage1
    assert storage2.android is None


def test_system_storage_android(monkeypatch, tmp_path):
    obb_path = tmp_path / "obb"
    obb_path.mkdir()

    ctx = fake_module(
        "ctx",
        getObbDir=lambda: fake_module("obb", getPath=lambda: str(obb_path)),
        getAssets=lambda: object(),
        getExternalFilesDir=lambda arg: fake_module(
            "efd", getPath=lambda: "/tmp/ext"
        ),
    )
    android = fake_module("android", context=ctx)

    p = Platform()
    p.android = android

    dirs = p.system_storage.system_dirs()
    assert any(h.asset == ASSET_ROOT for h in dirs)
    assert any(h.path == obb_path for h in dirs if h.path is not None)


def test_user_storage_android(monkeypatch):
    ctx = fake_module(
        "ctx",
        getExternalFilesDir=lambda arg: fake_module(
            "efd", getPath=lambda: "/tmp/ext"
        ),
    )
    android = fake_module("android", context=ctx)

    p = Platform()
    p.android = android

    assert p.user_storage.user_dir() == Path("/tmp/ext")


def test_platform_error_on_invalid_android(monkeypatch):
    bad_android = fake_module("android")
    monkeypatch.setitem(sys.modules, "android", bad_android)

    p = Platform()
    p._detect_android()

    assert p.android is None

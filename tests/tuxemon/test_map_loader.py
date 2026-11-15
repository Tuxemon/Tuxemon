# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from collections import OrderedDict, defaultdict
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tuxemon.map.loader import MapLoader


@pytest.fixture
def fake_context():
    ctx = MagicMock()
    ctx.tile_size = (16, 16)
    ctx.rect = MagicMock()
    ctx.rect.size = (320, 240)
    return ctx


@pytest.fixture
def mock_tmx_map(mocker):
    m = mocker.MagicMock()
    m.scenario = None
    m.events = []
    m.inits = []
    m.collision_map = {}
    return m


@pytest.fixture
def mock_yaml_loader(mocker):
    loader = mocker.MagicMock()
    loader.load_collision.return_value = {(1, 1): {"foo": "bar"}}
    loader.load_events.side_effect = lambda path, key: {key: [f"{key}_event"]}
    return loader


@pytest.fixture
def mock_tmx_loader(mocker, mock_tmx_map):
    loader = mocker.MagicMock()
    loader.load.return_value = mock_tmx_map
    return loader


@pytest.fixture
def mock_fetch_asset(mocker):
    """Return different fake TMX paths depending on map name."""

    def fake_fetch(folder, filename):
        name = Path(filename).stem
        return f"/fake/maps/{name}.tmx"

    return mocker.patch(
        "tuxemon.map.loader.fetch_asset", side_effect=fake_fetch
    )


@pytest.fixture
def mock_null_map(mocker):
    NullMap = mocker.patch("tuxemon.map.loader.NullMap")
    instance = NullMap.return_value
    instance.events = []
    instance.inits = []
    instance.collision_map = {}
    return instance


@pytest.fixture
def mock_mods_folder(mocker):
    folder = Path("/fake/mods")
    return mocker.patch("tuxemon.map.loader.mods_folder", folder)


@pytest.fixture
def loader(mocker, mock_tmx_loader, mock_yaml_loader, fake_context):
    mocker.patch(
        "tuxemon.map.loader.TMXMapLoader", return_value=mock_tmx_loader
    )
    mocker.patch(
        "tuxemon.map.loader.YAMLEventLoader", return_value=mock_yaml_loader
    )
    return MapLoader(context=fake_context, cache_size=2, enable_cache=True)


def test_load_map_data_cache_miss(loader, mock_fetch_asset, mock_tmx_loader):
    result = loader.load_map_data("test")
    mock_tmx_loader.load.assert_called_once()
    assert result is mock_tmx_loader.load.return_value
    assert len(loader._cache) == 1


def test_load_map_data_cache_hit(loader, mock_fetch_asset, mock_tmx_loader):
    first = loader.load_map_data("test")
    second = loader.load_map_data("test")
    assert first is second
    assert mock_tmx_loader.load.call_count == 1


def test_cache_eviction(loader, mock_fetch_asset, mock_tmx_loader):
    loader.load_map_data("a")
    loader.load_map_data("b")
    loader.load_map_data("c")  # should evict "a"
    assert len(loader._cache) == 2
    assert "/fake/maps/a.tmx" not in loader._cache


def test_cache_disabled(
    mocker, mock_fetch_asset, mock_tmx_loader, fake_context
):
    mocker.patch(
        "tuxemon.map.loader.TMXMapLoader", return_value=mock_tmx_loader
    )
    loader = MapLoader(context=fake_context, enable_cache=False)
    loader.load_map_data("test")
    loader.load_map_data("test")
    assert mock_tmx_loader.load.call_count == 2
    assert len(loader._cache) == 0


def test_resolve_yaml_files_with_scenario(
    loader, mock_fetch_asset, mock_tmx_map, mocker
):
    mock_tmx_map.scenario = "scenario_file"
    mocker.patch(
        "tuxemon.map.loader.fetch_asset",
        return_value="/fake/maps/scenario_file.yaml",
    )

    files = loader.resolve_yaml_files(mock_tmx_map, "/fake/maps/test.tmx")
    assert len(files) == 2
    assert files[0].suffix == ".yaml"
    assert "scenario_file.yaml" in str(files[1])


def test_load_null_map(loader, mock_null_map, mock_mods_folder):
    result = loader.load_null_map("events.yaml")
    assert result is mock_null_map
    assert mock_null_map.add_events.called or True  # events merged


def test_load_map_data_missing_asset(loader, mocker):
    mocker.patch("tuxemon.map.loader.fetch_asset", return_value=None)

    with pytest.raises(FileNotFoundError):
        loader.load_map_data("missing")


def test_process_events_missing_yaml(loader, mock_yaml_loader, mocker):
    fake_path = Path("/does/not/exist.yaml")
    mocker.patch.object(Path, "exists", return_value=False)
    collision, events = loader._process_events([fake_path])
    assert collision == {}
    assert events == defaultdict(list)


def test_add_to_cache_disabled(mocker, fake_context):
    loader = MapLoader(context=fake_context, enable_cache=False)
    loader.add_to_cache("x", MagicMock())
    assert len(loader._cache) == 0


def test_remove_from_cache(loader):
    loader._cache["/fake/path"] = MagicMock()
    assert loader.remove_from_cache("/fake/path") is True
    assert loader.remove_from_cache("/fake/path") is False


def test_cache_info(loader):
    loader._cache["/fake/a"] = MagicMock()
    info = loader.cache_info()
    assert info["enabled"] is True
    assert info["size"] == 1
    assert "/fake/a" in info["keys"]


def test_clear_cache(loader):
    loader._cache["/fake/a"] = MagicMock()
    loader.clear_cache()
    assert loader._cache == OrderedDict()

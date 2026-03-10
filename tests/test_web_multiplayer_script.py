from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "run_web_multiplayer", Path("scripts/run_web_multiplayer.py")
)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_headless_command_contains_expected_flags() -> None:
    cmd = module.headless_command("python", 45555)
    assert cmd == [
        "python",
        "run_tuxemon.py",
        "--headless",
        "--host-server",
        "--server-port",
        "45555",
    ]


def test_ensure_web_build_requires_index(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        module.ensure_web_build(tmp_path)


def test_ensure_web_build_passes_with_index(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html></html>")
    module.ensure_web_build(tmp_path)

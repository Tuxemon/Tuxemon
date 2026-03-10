"""Compatibility helpers for runtimes where pygame submodules are not real packages.

Some wasm pygame runtimes expose most APIs on the top-level `pygame` module,
while imports like `from pygame.rect import Rect` fail. This helper installs
lightweight `sys.modules` aliases for commonly used pygame submodules.
"""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any


def _make_module(name: str, exports: dict[str, Any]) -> ModuleType:
    module = ModuleType(name)
    for key, value in exports.items():
        setattr(module, key, value)
    return module


def install_pygame_submodule_aliases(pygame: Any) -> None:
    """Install synthetic pygame submodules when they are missing."""
    mapping: dict[str, dict[str, Any]] = {
        "pygame.rect": {
            "Rect": getattr(pygame, "Rect", None),
            "FRect": getattr(pygame, "FRect", None),
        },
        "pygame.surface": {
            "Surface": getattr(pygame, "Surface", None),
        },
        "pygame.font": {
            "Font": getattr(pygame, "Font", None),
            "get_default_font": getattr(pygame, "get_default_font", None),
        },
        "pygame.color": {
            "Color": getattr(pygame, "Color", None),
        },
        "pygame.event": {
            "Event": getattr(pygame, "Event", None),
        },
        "pygame.transform": {
            "scale": getattr(getattr(pygame, "transform", None), "scale", None),
            "smoothscale": getattr(
                getattr(pygame, "transform", None), "smoothscale", None
            ),
            "rotate": getattr(getattr(pygame, "transform", None), "rotate", None),
            "rotozoom": getattr(
                getattr(pygame, "transform", None), "rotozoom", None
            ),
            "flip": getattr(getattr(pygame, "transform", None), "flip", None),
        },
        "pygame.image": {
            "load": getattr(getattr(pygame, "image", None), "load", None),
            "frombuffer": getattr(getattr(pygame, "image", None), "frombuffer", None),
            "tobytes": getattr(getattr(pygame, "image", None), "tobytes", None),
        },
        "pygame.draw": {
            "line": getattr(getattr(pygame, "draw", None), "line", None),
            "rect": getattr(getattr(pygame, "draw", None), "rect", None),
            "circle": getattr(getattr(pygame, "draw", None), "circle", None),
        },
        "pygame.joystick": {
            "Joystick": getattr(getattr(pygame, "joystick", None), "Joystick", None),
            "JoystickType": getattr(
                getattr(pygame, "joystick", None), "JoystickType", None
            ),
            "get_count": getattr(
                getattr(pygame, "joystick", None), "get_count", None
            ),
            "init": getattr(getattr(pygame, "joystick", None), "init", None),
        },
        "pygame.sprite": {
            "Sprite": getattr(getattr(pygame, "sprite", None), "Sprite", None),
            "DirtySprite": getattr(
                getattr(pygame, "sprite", None), "DirtySprite", None
            ),
            "Group": getattr(getattr(pygame, "sprite", None), "Group", None),
            "LayeredUpdates": getattr(
                getattr(pygame, "sprite", None), "LayeredUpdates", None
            ),
        },
        "pygame.gfxdraw": {
            "box": getattr(getattr(pygame, "gfxdraw", None), "box", None),
        },
    }

    for module_name, exports in mapping.items():
        if module_name in sys.modules:
            continue
        cleaned = {k: v for k, v in exports.items() if v is not None}
        if cleaned:
            sys.modules[module_name] = _make_module(module_name, cleaned)

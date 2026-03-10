"""Compatibility helpers for runtimes where pygame submodules are not real packages."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any


class _DummyRect:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


def _make_module(name: str, exports: dict[str, Any]) -> ModuleType:
    module = ModuleType(name)
    for key, value in exports.items():
        setattr(module, key, value)
    return module


def _resolve(pygame: Any, *paths: str) -> Any:
    for path in paths:
        current = pygame
        ok = True
        for part in path.split('.'):
            if not hasattr(current, part):
                ok = False
                break
            current = getattr(current, part)
        if ok and current is not None:
            return current
    return None


def install_pygame_submodule_aliases(pygame: Any) -> None:
    """Install synthetic pygame submodules when they are missing."""
    mapping: dict[str, dict[str, Any]] = {
        "pygame.rect": {
            "Rect": _resolve(pygame, "Rect", "rect.Rect") or _DummyRect,
            "FRect": _resolve(pygame, "FRect", "rect.FRect") or _DummyRect,
        },
        "pygame.surface": {
            "Surface": _resolve(pygame, "Surface", "surface.Surface"),
        },
        "pygame.font": {
            "Font": _resolve(pygame, "Font", "font.Font"),
            "get_default_font": _resolve(
                pygame, "get_default_font", "font.get_default_font"
            ),
        },
        "pygame.color": {
            "Color": _resolve(pygame, "Color", "color.Color"),
        },
        "pygame.event": {
            "Event": _resolve(pygame, "Event", "event.Event"),
        },
        "pygame.transform": {
            "scale": _resolve(pygame, "transform.scale"),
            "smoothscale": _resolve(pygame, "transform.smoothscale"),
            "rotate": _resolve(pygame, "transform.rotate"),
            "rotozoom": _resolve(pygame, "transform.rotozoom"),
            "flip": _resolve(pygame, "transform.flip"),
        },
        "pygame.image": {
            "load": _resolve(pygame, "image.load"),
            "frombuffer": _resolve(pygame, "image.frombuffer"),
            "tobytes": _resolve(pygame, "image.tobytes"),
        },
        "pygame.draw": {
            "line": _resolve(pygame, "draw.line"),
            "rect": _resolve(pygame, "draw.rect"),
            "circle": _resolve(pygame, "draw.circle"),
        },
        "pygame.joystick": {
            "Joystick": _resolve(pygame, "joystick.Joystick"),
            "JoystickType": _resolve(pygame, "joystick.JoystickType"),
            "get_count": _resolve(pygame, "joystick.get_count"),
            "init": _resolve(pygame, "joystick.init"),
        },
        "pygame.sprite": {
            "Sprite": _resolve(pygame, "sprite.Sprite"),
            "DirtySprite": _resolve(pygame, "sprite.DirtySprite"),
            "Group": _resolve(pygame, "sprite.Group"),
            "LayeredUpdates": _resolve(pygame, "sprite.LayeredUpdates"),
        },
        "pygame.gfxdraw": {
            "box": _resolve(pygame, "gfxdraw.box"),
        },
    }

    for module_name, exports in mapping.items():
        if module_name in sys.modules:
            continue
        cleaned = {k: v for k, v in exports.items() if v is not None}
        if module_name == "pygame.rect" and not cleaned:
            cleaned = {"Rect": _DummyRect, "FRect": _DummyRect}
        if cleaned:
            sys.modules[module_name] = _make_module(module_name, cleaned)

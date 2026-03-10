# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from tuxemon.compat.rect import ReadOnlyRect

Rect: type[ReadOnlyRect]

try:
    import pygame

    Rect = getattr(pygame, "Rect", None)
    if Rect is None:
        from tuxemon.compat.rect import Rect
except Exception:
    from tuxemon.compat.rect import Rect

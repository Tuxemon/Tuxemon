# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from tuxemon.compat.rect import ReadOnlyRect

__all__ = ["Rect", "ReadOnlyRect"]

try:
    from pygame.rect import Rect
except ImportError:
    from tuxemon.compat.rect import Rect

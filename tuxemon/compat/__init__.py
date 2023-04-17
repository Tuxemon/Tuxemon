# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from typing import Type

from tuxemon.compat.rect import ReadOnlyRect

Rect: Type[ReadOnlyRect]

try:
    from pygame.rect import Rect
except ImportError:
    from tuxemon.compat.rect import Rect

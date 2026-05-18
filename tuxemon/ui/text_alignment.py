# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from enum import Enum


class DialogPosition(Enum):
    BOTTOM = "bottom"
    TOP = "top"
    CENTER = "center"
    TOPLEFT = "topleft"
    TOPRIGHT = "topright"
    BOTTOMLEFT = "bottomleft"
    BOTTOMRIGHT = "bottomright"
    RIGHT = "right"
    LEFT = "left"
    AT_TARGET = "at_target"


class VerticalAlignment(Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class HorizontalAlignment(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"

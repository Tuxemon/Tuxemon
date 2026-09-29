# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from math import cos, pi, sin, sqrt

logger = logging.getLogger(__name__)


class AnimationTransition:
    """
    Collection of animation functions to be used with the Animation object.

    Easing Functions ported to Kivy from the Clutter Project
    http://www.clutter-project.org/docs/clutter/stable/ClutterAlpha.html

    The `progress` parameter in each animation function is in the range 0-1.
    """

    @staticmethod
    def linear(progress: float) -> float:
        return progress

    @staticmethod
    def in_quad(progress: float) -> float:
        return progress * progress

    @staticmethod
    def out_quad(progress: float) -> float:
        return -1.0 * progress * (progress - 2.0)

    @staticmethod
    def in_out_quad(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p
        p -= 1.0
        return -0.5 * (p * (p - 2.0) - 1.0)

    @staticmethod
    def in_cubic(progress: float) -> float:
        return progress * progress * progress

    @staticmethod
    def out_cubic(progress: float) -> float:
        p = progress - 1.0
        return p * p * p + 1.0

    @staticmethod
    def in_out_cubic(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p
        p -= 2
        return 0.5 * (p * p * p + 2.0)

    @staticmethod
    def in_quart(progress: float) -> float:
        return progress * progress * progress * progress

    @staticmethod
    def out_quart(progress: float) -> float:
        p = progress - 1.0
        return -1.0 * (p * p * p * p - 1.0)

    @staticmethod
    def in_out_quart(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p
        p -= 2
        return -0.5 * (p * p * p * p - 2.0)

    @staticmethod
    def in_quint(progress: float) -> float:
        return progress * progress * progress * progress * progress

    @staticmethod
    def out_quint(progress: float) -> float:
        p = progress - 1.0
        return p * p * p * p * p + 1.0

    @staticmethod
    def in_out_quint(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p * p
        p -= 2.0
        return 0.5 * (p * p * p * p * p + 2.0)

    @staticmethod
    def in_sine(progress: float) -> float:
        return -1.0 * cos(progress * (pi / 2.0)) + 1.0

    @staticmethod
    def out_sine(progress: float) -> float:
        return sin(progress * (pi / 2.0))

    @staticmethod
    def in_out_sine(progress: float) -> float:
        return -0.5 * (cos(pi * progress) - 1.0)

    @staticmethod
    def in_expo(progress: float) -> float:
        if progress == 0:
            return 0.0
        value = pow(2, 10 * (progress - 1.0))
        return float(value)

    @staticmethod
    def out_expo(progress: float) -> float:
        if progress == 1.0:
            return 1.0
        value = -pow(2, -10 * progress) + 1.0
        return float(value)

    @staticmethod
    def in_out_expo(progress: float) -> float:
        if progress == 0:
            return 0.0
        if progress == 1.0:
            return 1.0
        p = progress * 2
        if p < 1:
            value = 0.5 * pow(2, 10 * (p - 1.0))
            return float(value)
        p -= 1.0
        value = 0.5 * (-pow(2, -10 * p) + 2.0)
        return float(value)

    @staticmethod
    def in_circ(progress: float) -> float:
        return -1.0 * (sqrt(1.0 - progress * progress) - 1.0)

    @staticmethod
    def out_circ(progress: float) -> float:
        p = progress - 1.0
        return sqrt(1.0 - p * p)

    @staticmethod
    def in_out_circ(progress: float) -> float:
        p = progress * 2
        if p < 1:
            return -0.5 * (sqrt(1.0 - p * p) - 1.0)
        p -= 2.0
        return 0.5 * (sqrt(1.0 - p * p) + 1.0)

    @staticmethod
    def in_elastic(progress: float) -> float:
        p = 0.3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        q -= 1.0
        value = -(pow(2, 10 * q) * sin((q - s) * (2 * pi) / p))
        return float(value)

    @staticmethod
    def out_elastic(progress: float) -> float:
        p = 0.3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        value = pow(2, -10 * q) * sin((q - s) * (2 * pi) / p) + 1.0
        return float(value)

    @staticmethod
    def in_out_elastic(progress: float) -> float:
        p = 0.3 * 1.5
        s = p / 4.0
        q = progress * 2
        if q == 2:
            return 1.0
        if q < 1:
            q -= 1.0
            value = -0.5 * (pow(2, 10 * q) * sin((q - s) * (2.0 * pi) / p))
            return float(value)
        else:
            q -= 1.0
            value = pow(2, -10 * q) * sin((q - s) * (2.0 * pi) / p) * 0.5 + 1.0
            return float(value)

    @staticmethod
    def in_back(progress: float) -> float:
        return progress * progress * ((1.70158 + 1.0) * progress - 1.70158)

    @staticmethod
    def out_back(progress: float) -> float:
        p = progress - 1.0
        return p * p * ((1.70158 + 1) * p + 1.70158) + 1.0

    @staticmethod
    def in_out_back(progress: float) -> float:
        p = progress * 2.0
        s = 1.70158 * 1.525
        if p < 1:
            return 0.5 * (p * p * ((s + 1.0) * p - s))
        p -= 2.0
        return 0.5 * (p * p * ((s + 1.0) * p + s) + 2.0)

    @staticmethod
    def _out_bounce_internal(t: float, d: float) -> float:
        p = t / d
        if p < (1.0 / 2.75):
            return 7.5625 * p * p
        elif p < (2.0 / 2.75):
            p -= 1.5 / 2.75
            return 7.5625 * p * p + 0.75
        elif p < (2.5 / 2.75):
            p -= 2.25 / 2.75
            return 7.5625 * p * p + 0.9375
        else:
            p -= 2.625 / 2.75
            return 7.5625 * p * p + 0.984375

    @staticmethod
    def _in_bounce_internal(t: float, d: float) -> float:
        return 1.0 - AnimationTransition._out_bounce_internal(d - t, d)

    @staticmethod
    def in_bounce(progress: float) -> float:
        return AnimationTransition._in_bounce_internal(progress, 1.0)

    @staticmethod
    def out_bounce(progress: float) -> float:
        return AnimationTransition._out_bounce_internal(progress, 1.0)

    @staticmethod
    def in_out_bounce(progress: float) -> float:
        p = progress * 2.0
        if p < 1.0:
            return AnimationTransition._in_bounce_internal(p, 1.0) * 0.5
        return (
            AnimationTransition._out_bounce_internal(p - 1.0, 1.0) * 0.5 + 0.5
        )

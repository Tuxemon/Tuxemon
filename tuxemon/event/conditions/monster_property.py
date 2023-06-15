# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

from tuxemon.db import ElementType
from tuxemon.event import MapCondition
from tuxemon.event.eventcondition import EventCondition
from tuxemon.session import Session


class MonsterPropertyCondition(EventCondition):
    """
    Check to see if a monster in the party has one of
    the following property.

    Script usage:
        .. code-block::

            is monster_property <property>,<value>

    Script parameters:
        property: Property of the monster to check (e.g. "level").
        Valid values are:
                - slug (slug, rockitten)
                - level (level, 8)
                - level_reached (level_reached, 8)
                - stage (stage, standalone)
                - shape (shape, piscine)
                - taste_cold (taste_cold, mild)
                - taste_warm (taste_warm, peppy)
                - type (type, fire)
                - gender (gender, female)
                - tech (tech, ram)
        value: Value to compare the property with.

    """

    name = "monster_property"

    def test(self, session: Session, condition: MapCondition) -> bool:
        """
        Check to see if a monster in the party has one of
        the following property.

        Parameters:
            session: The session object
            condition: The map condition object.

        Returns:
            Whether the monster property is verified.

        """
        prop = condition.parameters[0]
        val = condition.parameters[1]
        player = session.player
        for mon in player.monsters:
            # monster slug
            if prop == "slug":
                if mon.slug == val:
                    return True
            # monster level
            elif prop == "level":
                if str(mon.level) == val:
                    return True
            # monster level_reached
            elif prop == "level_reached":
                if str(mon.level) >= val:
                    return True
            # monster stage (eg. standalone, basic, etc.)
            elif prop == "stage":
                if mon.stage == val:
                    return True
            # monster shape (eg. piscine, brute, etc.)
            elif prop == "shape":
                if mon.shape == val:
                    return True
            # monster taste_cold (eg. mild, etc.)
            elif prop == "taste_cold":
                if mon.taste_cold == val:
                    return True
            # monster taste_warm (eg peppy, etc.)
            elif prop == "taste_warm":
                if mon.taste_warm == val:
                    return True
            # monster type (eg. earth, fire, etc)
            elif prop == "type":
                ele = ElementType(val)
                if mon.has_type(ele):
                    return True
            # monster gender (eg. male, female or neuter)
            elif prop == "gender":
                if mon.gender == val:
                    return True
            # monster tech (eg. ram, blossom, etc.)
            elif prop == "tech":
                if player.has_tech(val):
                    return True
            else:
                raise ValueError(f"{prop} isn't among the valid values.")
        return False

#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# core.main Sets up the states and main game loop.
#
"""The main function is defined here. It simply creates an instance of
tools.Control and adds the game states to its dictionary using
tools.setup_states.  This allows us to seamlessly switch between
different states of the game such as combat, the overworld, etc.
"""

from . import prepare, tools
from .states import start, world, combat, pc, serverheadless

def main():
    """Add all available states to our scene manager (tools.Control)
    and start the game.

    Currently available states are: "START", "WORLD", "COMBAT", and "PC".

    :param None:
    
    :rtype: None
    :returns: None

    """

    prepare.init()
    run_it = tools.Control(prepare.ORIGINAL_CAPTION)
    run_it.player1 = prepare.player1
    state_dict = {"START": start.StartScreen(run_it),
                  "WORLD": world.World(run_it),
                  "COMBAT": combat.Combat(run_it),
                  "PC": pc.PC(run_it)}
    run_it.setup_states(state_dict, "START")
    run_it.main()

def headless():
    """Sets up out headless server (tools.HeadlessControl)
    and start the game.

    :param None:
    
    :rtype: None
    :returns: None

    """
    prepare.init()
    run_it = tools.HeadlessControl()
    state_dict = {"WORLD": serverheadless.Headless(run_it)}
    run_it.setup_states(state_dict, "WORLD")
    run_it.main()

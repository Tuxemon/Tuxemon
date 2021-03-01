#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>,
#                         Leif Theden <leif.theden@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


class EventQueueHandler:
    """ Event QueueHandler for different platforms

    * Only one per game
    * Sole manager of platform events of type
    """

    def release_controls(self):
        """ Send virtual input events which release held buttons/axis

        After this frame, held/triggered inputs will return to previous state

        :return:
        """
        for key, value in self._inputs.items():
            for inp in value:
                yield from inp.virtual_stop_events()

    def process_events(self):
        raise NotImplementedError


class InputHandler:
    """ Enables basic input device with discrete inputs
    """
    event_type = None
    default_input_map = None

    def __init__(self, event_map=None):
        if event_map is None:
            assert self.default_input_map
            event_map = self.default_input_map.copy()
        self.buttons = dict()
        self.event_map = event_map
        for button in event_map.values():
            self.buttons[button] = PlayerInput(button)

    def process_event(self, pg_event):
        raise NotImplementedError

    def virtual_stop_events(self):
        """ Send virtual input events simulating released buttons/axis

        This is used to force a state to release inputs without changing input state

        :return:
        """
        for button, inp in self.buttons.items():
            if inp.held:
                yield PlayerInput(inp.button, 0, 0)

    def get_events(self):
        for inp in self.buttons.values():
            if inp.held:
                yield inp
                inp.hold_time += 1
            elif inp.triggered:
                yield inp
                inp.triggered = False

    def press(self, button, value=1):
        inp = self.buttons[button]
        inp.value = value
        if not inp.hold_time:
            inp.hold_time = 1

    def release(self, button):
        inp = self.buttons[button]
        inp.value = 0
        inp.hold_time = 0
        inp.triggered = True


class PlayerInput:
    __slots__ = ("button", "value", "hold_time", "triggered")
    
    def __init__(self, button, value=0, hold_time=0):
        """ Represents a single player input

        Each instance represents the state of a single input:
        * have float value 0-1
        * are "pressed" when value is above 0, for exactly one frame
        * are "held" when "pressed" for longer than zero frames

        Do not manipulate these values
        Once created, these objects will not be destroyed
        Input managers will set values on these objects
        These objects are reused between frames, do not hold references to them

        :type button: int
        :type value: float
        :type hold_time: int
        """
        self.button = button
        self.value = value
        self.hold_time = hold_time
        self.triggered = False

    def __str__(self):
        return "<PlayerInput: {} {} {} {} {}>".format(self.button, self.value, self.pressed, self.held, self.hold_time)

    @property
    def pressed(self):
        """ This is edge triggered, meaning it will only be true once!

        :rtype: bool
        """
        return bool(self.value) and self.hold_time == 1

    @property
    def held(self):
        """ This will be true as long as button is held down

        :rtype: bool
        """
        return bool(self.value)

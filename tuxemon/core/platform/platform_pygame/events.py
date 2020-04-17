from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import defaultdict

import pygame as pg

from tuxemon.core import prepare
from tuxemon.core.platform.const import buttons, events
from tuxemon.core.platform.events import InputHandler, PlayerInput, EventQueueHandler
from tuxemon.core.session import local_session


class PygameEventQueueHandler(EventQueueHandler):
    """ Handle all events from the pygame event queue
    """

    def __init__(self):
        # TODO: move this config to the config file
        self._inputs = defaultdict(list)  # type Dict[int, List[InputHandler]]
        self._inputs[0].append(PygameKeyboardInput(prepare.CONFIG.keyboard_button_map))
        self._inputs[0].append(PygameGamepadInput(prepare.CONFIG.gamepad_button_map, prepare.CONFIG.gamepad_deadzone))
        if prepare.CONFIG.hide_mouse is False:
            self._inputs[0].append(PygameMouseInput())

    def process_events(self):
        """ Process all pygame events

        * Should never return pygame-unique events
        * All events returned should be Tuxemon game specific
        * This must be the only function to get events from the pygame event queue

        :returns: Iterator of game events
        """
        for pg_event in pg.event.get():
            for player, inputs in self._inputs.items():
                for player_input in inputs:
                    player_input.process_event(pg_event)

            if pg_event.type == pg.QUIT:
                local_session.client.exit = True

        for player, inputs in self._inputs.items():
            for player_input in inputs:
                for game_event in player_input.get_events():
                    yield game_event


class PygameEventHandler(InputHandler):
    def process_event(self, pg_event):
        """

        :rtype:  bool
        """
        return False


class PygameGamepadInput(PygameEventHandler):
    """
    NOTE: Due to implementation, you may receive "released" inputs for
    buttons/directions/axis even if they are released already.  Pressed
    or held inputs will never be duplicated and are always "correct".
    """
    event_type = PlayerInput
    # Xbox 360 Controller buttons:
    # A = 0    Start = 7    D-Up = 13
    # B = 1    Back = 6     D-Down = 14
    # X = 2                 D-Left = 11
    # Y = 3                 D-Right = 12
    #
    default_input_map = {
        0: buttons.A,
        1: buttons.B,
        6: buttons.BACK,
        11: buttons.LEFT,
        12: buttons.RIGHT,
        13: buttons.UP,
        14: buttons.DOWN,
        7: buttons.START,
    }

    def __init__(self, event_map=None, deadzone=.25):
        super(PygameGamepadInput, self).__init__(event_map)
        self.deadzone = deadzone

    def process_event(self, pg_event):
        self.check_button(pg_event)
        self.check_hat(pg_event)
        self.check_axis(pg_event)

    def check_button(self, pg_event):
        try:
            button = self.event_map[pg_event.button]
            if pg_event.type == pg.JOYBUTTONDOWN:
                self.press(button)
            elif pg_event.type == pg.JOYBUTTONUP:
                self.release(button)
        except (KeyError, AttributeError):
            pass

    def check_hat(self, pg_event):
        if pg_event.type == pg.JOYHATMOTION:
            x, y = pg_event.value
            if x == -1:
                self.press(buttons.LEFT, value=x * -1)
            elif x == 0:
                self.release(buttons.LEFT)
                self.release(buttons.RIGHT)
            elif x == 1:
                self.press(buttons.RIGHT)

            if y == -1:
                self.press(buttons.DOWN, value=y * -1)
            elif y == 0:
                self.release(buttons.DOWN)
                self.release(buttons.UP)
            elif y == 1:
                self.press(buttons.UP)

    def check_axis(self, pg_event):
        if pg_event.type == pg.JOYAXISMOTION:
            value = pg_event.value

            if pg_event.axis == 0:
                if abs(value) >= self.deadzone:
                    if value < 0:
                        self.press(buttons.LEFT, value * -1)
                    else:
                        self.press(buttons.RIGHT, value)
                else:
                    self.release(buttons.LEFT)
                    self.release(buttons.RIGHT)

            elif pg_event.axis == 1:
                if abs(value) >= self.deadzone:
                    if value < 0:
                        self.press(buttons.UP, value * -1)
                    else:
                        self.press(buttons.DOWN, value)
                else:
                    self.release(buttons.UP)
                    self.release(buttons.DOWN)


class PygameKeyboardInput(PygameEventHandler):
    default_input_map = {
        pg.K_UP: buttons.UP,
        pg.K_DOWN: buttons.DOWN,
        pg.K_LEFT: buttons.LEFT,
        pg.K_RIGHT: buttons.RIGHT,
        pg.K_RETURN: buttons.A,
        pg.K_RSHIFT: buttons.B,
        pg.K_LSHIFT: buttons.B,
        pg.K_ESCAPE: buttons.BACK,
        pg.K_BACKSPACE: events.BACKSPACE,
        None: events.UNICODE,
    }

    def process_event(self, pg_event):
        """ Translate a pg event to an internal game event

        :type pg_event: pg.event.Event
        """
        pressed = pg_event.type == pg.KEYDOWN
        released = pg_event.type == pg.KEYUP

        if pressed or released:
            # try to get game-specific action for the key
            try:
                button = self.event_map[pg_event.key]
            except KeyError:
                pass
            else:
                if pressed:
                    self.press(button)
                else:
                    self.release(button)
                return

            # just get unicode value
            try:
                if pressed:
                    self.release(events.UNICODE)
                    self.press(events.UNICODE, pg_event.unicode)
                else:
                    self.release(events.UNICODE)
            except AttributeError:
                pass


class PygameTouchOverlayInput(PygameEventHandler):
    def get_overlay_event(self, event):
        """ Process all events from the controller overlay and pass them down to
        current State. All controller overlay events are converted to keyboard
        events for compatibility. This is primarily used for the mobile version
        of Tuxemon.

        :type event: pg.event.Event
        """
        pressed = event.type == pg.MOUSEBUTTONDOWN
        released = event.type == pg.MOUSEBUTTONUP

        if (pressed or released) and event.button == 1:
            mouse_pos = self.mouse_pos
            dpad_rect = self.controller.dpad["rect"]

            if dpad_rect["up"].collidepoint(mouse_pos):
                yield PlayerInput(buttons.UP)
            if dpad_rect["down"].collidepoint(mouse_pos):
                yield PlayerInput(buttons.DOWN)
            if dpad_rect["left"].collidepoint(mouse_pos):
                yield PlayerInput(buttons.LEFT)
            if dpad_rect["right"].collidepoint(mouse_pos):
                yield PlayerInput(buttons.RIGHT)
            if self.controller.a_button["rect"].collidepoint(mouse_pos):
                yield PlayerInput(buttons.A)
            if self.controller.b_button["rect"].collidepoint(mouse_pos):
                yield PlayerInput(buttons.B)


class PygameMouseInput(PygameEventHandler):
    default_input_map = {
        pg.MOUSEBUTTONDOWN: buttons.MOUSELEFT,
        pg.MOUSEBUTTONUP: buttons.MOUSELEFT,
    }

    def process_event(self, pg_event):
        if pg_event.type == pg.MOUSEBUTTONDOWN:
            self.press(buttons.MOUSELEFT, pg_event.pos)
        elif pg_event.type == pg.MOUSEBUTTONUP:
            self.release(buttons.MOUSELEFT)

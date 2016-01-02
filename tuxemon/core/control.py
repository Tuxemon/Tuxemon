from __future__ import absolute_import
import time

import pygame as pg

from . import prepare
from . import tools
from .components import ai
from .components import cli
from .components import controller
from .components import db
from .components import event
from .components import item
from .components import map as maps
from .components import monster
from .components import networking
from .components import player
from .components import pyganim
from .components import rumble
#from .components.combat import CombatEngine, CombatRouter
from .state import StateManager
from .tools import android, logger


class Control(StateManager):
    """Control class for entire project. Contains the game loop, and contains
    the event_loop which passes events to States as needed.

    :param caption: The window caption to use for the game itself.

    :type caption: String

    :rtype: None
    :returns: None

    """

    def __init__(self, caption):
        # INFO: no need to call superclass for now
        self.screen = pg.display.get_surface()
        self.caption = caption
        self.done = False
        self.clock = pg.time.Clock()
        self.fps = 60.0
        self.show_fps = True
        self.current_time = 0.0
        self.keys = pg.key.get_pressed()
        self.key_events = []
        self.ishost = False
        self.isclient = False

        # TODO: move out to state manager
        self.package = "core.states"
        self.state_dict = dict()
        self.state_stack = list()
        self._current_state_requires_resume = True

        # Set up our networking for multiplayer.
        self.server = networking.TuxemonServer(self)
        self.client = networking.TuxemonClient(self)

        # Set up our combat engine and router.
#        self.combat_engine = CombatEngine(self)
#        self.combat_router = CombatRouter(self, self.combat_engine)

        # Set up our game's configuration from the prepare module.
        self.config = prepare.CONFIG

        # Set up our game's event engine which executes actions based on
        # conditions defined in map files.
        self.event_engine = event.EventEngine()
        self.event_conditions = {}
        self.event_actions = {}
        self.event_persist = {}

        # Set up a variable that will keep track of currently playing music.
        self.current_music = {"status": "stopped", "song": None}

        # Keep track of animations that we will play.
        self.animations = {}

        # Create these Pygame event objects to simulate KEYDOWN and KEYUP
        # events for all the directional keys
        self.keyboard_events = {}
        self.keyboard_events["KEYDOWN"] = {}
        self.keyboard_events["KEYDOWN"]["up"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 111, 'key': 273, 'unicode': u'', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["down"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 116, 'key': 274, 'unicode': u'', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["left"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 113, 'key': 276, 'unicode': u'', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["right"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 114, 'key': 275, 'unicode': u'', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["enter"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 36, 'key': 13, 'unicode': u'\r', 'mod': 4096})
        self.keyboard_events["KEYDOWN"]["escape"] = pg.event.Event(
            pg.KEYDOWN,
            {'scancode': 9, 'key': 27, 'unicode': u'\x1b', 'mod': 4096})
        self.keyboard_events["KEYUP"] = {}
        self.keyboard_events["KEYUP"]["up"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 111, 'key': 273, 'mod': 4096})
        self.keyboard_events["KEYUP"]["down"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 116, 'key': 274, 'mod': 4096})
        self.keyboard_events["KEYUP"]["left"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 113, 'key': 276, 'mod': 4096})
        self.keyboard_events["KEYUP"]["right"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 114, 'key': 275, 'mod': 4096})
        self.keyboard_events["KEYUP"]["enter"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 36, 'key': 13, 'mod': 4096})
        self.keyboard_events["KEYUP"]["escape"] = pg.event.Event(
            pg.KEYUP,
            {'scancode': 9, 'key': 27, 'mod': 4096})

        # Set up the command line. This provides a full python shell for
        # troubleshooting. You can view and manipulate any variables in
        # the game.
        self.exit = False   # Allow exit from the CLI
        if self.config.cli:
            self.cli = cli.CommandLine(self)

        # Controller overlay
        if self.config.controller_overlay == "1":
            self.controller = controller.Controller(self)
            self.controller.load()

            # Keep track of what buttons have been pressed when the overlay
            # controller is enabled.
            self.overlay_pressed = {
                "up": False,
                "down": False,
                "left": False,
                "right": False,
                "a": False,
                "b": False
            }

        # Set up our networked controller if enabled.
        if self.config.net_controller_enabled == "1":
            self.controller_server = networking.ControllerServer(self)

        # Set up rumble support for gamepads
        self.rumble_manager = rumble.RumbleManager()
        self.rumble = self.rumble_manager.rumbler

    def update(self, dt):
        """Checks if a state is done or has called for a game quit.
        State is flipped if neccessary and State.update is called. This
        also calls the currently active state's "update" function each
        frame.

        The screen will be drawn here as well.

        :param dt: Time delta - Amount of time passed since last frame.

        :type dt: Float

        :rtype: None
        :returns: None

        **Example:**

        >>> dt
        0.031

        """
        self.current_time = pg.time.get_ticks()
        current_state = self.current_state  # deref here is required in cases where state changes during update

        if self._current_state_requires_resume:
            self._current_state_requires_resume = False
            current_state.resume()

        current_state.update(dt)
        current_state.draw(self.screen)

        if self.config.controller_overlay == "1":
            self.controller.draw(self)

    def event_loop(self):
        """Process all events and pass them down to current State.  The F5 key
        globally turns on/off the display of FPS in the caption

        :param None:

        :rtype: None
        :returns: None

        """
        # Loop through our pygame events and pass them to the current state.
        self.key_events = []
        self.keys = list(pg.key.get_pressed())
        for event in pg.event.get():
            self.key_events.append(event)
            if event.type == pg.QUIT:
                self.done = True
                self.exit = True

            elif event.type == pg.KEYDOWN:
                self.toggle_show_fps(event.key)

            # Loop through our controller overlay events and pass them to the current state.
            if self.config.controller_overlay == "1":
                self.mouse_pos = pg.mouse.get_pos()
                contr_events = self.controller_event_loop(event)
                if contr_events:
                    for contr_event in contr_events:
                        self.key_events.append(contr_event)
                        self.current_state.get_event(contr_event)

            # Loop through our joystick events and pass them to the current state.
            joy_events = self.joystick_event_loop(event)
            if joy_events:
                for joy_event in joy_events:
                    self.key_events.append(joy_event)
                    self.current_state.get_event(joy_event)

            self.current_state.get_event(event)

        # Remove the remaining events after they have been processed
        pg.event.pump()

    def controller_event_loop(self, event):
        """Process all events from the controller overlay and pass them down to
        current State. All controller overlay events are converted to keyboard
        events for compatibility. This is primarily used for the mobile version
        of Tuxemon.

        :param event: A Pygame event object from pg.event.get()
        :type event: pygame.event.Event

        :rtype: None
        :returns: None

        """
        events = []
        if (event.type == pg.MOUSEBUTTONDOWN
            and event.button == 1):

            if self.controller.dpad["rect"]["up"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["up"])
                self.keys[pg.K_UP] = 1
                self.overlay_pressed["up"] = True
            if self.controller.dpad["rect"]["down"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["down"])
                self.keys[pg.K_DOWN] = 1
                self.overlay_pressed["down"] = True
            if self.controller.dpad["rect"]["left"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["left"])
                self.keys[pg.K_LEFT] = 1
                self.overlay_pressed["left"] = True
            if self.controller.dpad["rect"]["right"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["right"])
                self.keys[pg.K_RIGHT] = 1
                self.overlay_pressed["right"] = True
            if self.controller.a_button["rect"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["enter"])
                self.keys[pg.K_RETURN] = 1
                self.overlay_pressed["a"] = True
            if self.controller.b_button["rect"].collidepoint(self.mouse_pos):
                events.append(
                    self.keyboard_events["KEYDOWN"]["escape"])
                self.keys[pg.K_ESCAPE] = 1
                self.overlay_pressed["b"] = True

        if (event.type == pg.MOUSEBUTTONUP) and (event.button == 1):
            if self.overlay_pressed["up"]:
                events.append(self.keyboard_events["KEYUP"]["up"])
                self.overlay_pressed["up"] = False
            if self.overlay_pressed["down"]:
                events.append(self.keyboard_events["KEYUP"]["down"])
                self.overlay_pressed["down"] = False
            if self.overlay_pressed["left"]:
                events.append(self.keyboard_events["KEYUP"]["left"])
                self.overlay_pressed["left"] = False
            if self.overlay_pressed["right"]:
                events.append(self.keyboard_events["KEYUP"]["right"])
                self.overlay_pressed["right"] = False
            if self.overlay_pressed["a"]:
                events.append(self.keyboard_events["KEYUP"]["enter"])
                self.overlay_pressed["a"] = False
                self.keys[pg.K_RETURN] = 0
            if self.overlay_pressed["b"]:
                events.append(self.keyboard_events["KEYUP"]["escape"])
                self.overlay_pressed["b"] = False

        return events

    def joystick_event_loop(self, event):
        """Process all events from a joystick and pass them down to
        current State. All joystick events are converted to keyboard
        events for compatibility.

        :param event: A Pygame event object from pg.event.get()
        :type event: pygame.event.Event

        :rtype: None
        :returns: None

        """

        # Handle joystick events if we detected one
        events = []
        if len(prepare.JOYSTICKS) > 0:

            # Xbox 360 Controller buttons:
            # A = 0    Start = 7    D-Up = 13
            # B = 1    Back = 6     D-Down = 14
            # X = 2                 D-Left = 11
            # Y = 3                 D-Right = 12
            #
            if event.type == pg.JOYBUTTONDOWN:
                if event.button == 0:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["enter"])
                    self.keys[pg.K_RETURN] = 1
                if (event.button == 1
                    or event.button == 7 or event.button == 6):
                    events.append(
                        self.keyboard_events["KEYDOWN"]["escape"])
                    self.keys[pg.K_ESCAPE] = 1

                if event.button == 13:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["up"])
                    self.keys[pg.K_UP] = 1
                if event.button == 14:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["down"])
                    self.keys[pg.K_DOWN] = 1
                if event.button == 11:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["left"])
                    self.keys[pg.K_LEFT] = 1
                if event.button == 12:
                    events.append(
                        self.keyboard_events["KEYDOWN"]["right"])
                    self.keys[pg.K_RIGHT] = 1

            elif event.type == pg.JOYBUTTONUP:
                if event.button == 0:
                    events.append(
                        self.keyboard_events["KEYUP"]["enter"])
                if (event.button == 1
                    or event.button == 7 or event.button == 6):
                    events.append(
                        self.keyboard_events["KEYUP"]["escape"])

                if event.button == 13:
                    events.append(self.keyboard_events["KEYUP"]["up"])
                if event.button == 14:
                    events.append(
                        self.keyboard_events["KEYUP"]["down"])
                if event.button == 11:
                    events.append(
                        self.keyboard_events["KEYUP"]["left"])
                if event.button == 12:
                    events.append(
                        self.keyboard_events["KEYUP"]["right"])

            # Handle left joystick movement as well.
            # Axis 1 - up = negative, down = positive
            # Axis 0 - left = negative, right = positive
            if event.type == pg.JOYAXISMOTION and False:    # Disabled until input manager is implemented

                # Handle the left/right axis
                if event.axis == 0:
                    if event.value >= 0.5:
                        events.append(
                            self.keyboard_events["KEYDOWN"]["right"])
                        self.keys[pg.K_RIGHT] = 1
                    elif event.value <= -0.5:
                        events.append(
                            self.keyboard_events["KEYDOWN"]["left"])
                        self.keys[pg.K_LEFT] = 1
                    else:
                        events.append(
                            self.keyboard_events["KEYUP"]["left"])
                        events.append(
                            self.keyboard_events["KEYUP"]["right"])

                # Handle the up/down axis
                if event.axis == 1:
                    if event.value >= 0.5:
                        events.append(
                            self.keyboard_events["KEYDOWN"]["down"])
                        self.keys[pg.K_DOWN] = 1
                    elif event.value <= -0.5:
                        events.append(
                            self.keyboard_events["KEYDOWN"]["up"])
                        self.keys[pg.K_LEFT] = 1
                    else:
                        events.append(
                            self.keyboard_events["KEYUP"]["up"])
                        events.append(
                            self.keyboard_events["KEYUP"]["down"])

        return events

    def toggle_show_fps(self, key):
        """Press f5 to turn on/off displaying the framerate in the caption.

        :param key: A pygame key event from pygame.event.get()

        :type key: PyGame Event

        :rtype: None
        :returns: None

        """
        if key == pg.K_F5:
            self.show_fps = not self.show_fps
            if not self.show_fps:
                pg.display.set_caption(self.caption)

    def main(self):
        """Initiates the main game loop. Since we are using Asteria networking
        to handle network events, we pass this core.control.Control instance to
        networking which in turn executes the "main_loop" method every frame.
        This leaves the networking component responsible for the main loop.

        :param None:

        :rtype: None
        :returns: None

        """
        while not self.exit:
            self.main_loop()

    def main_loop(self):
        """Main loop for entire game. This method gets execute every frame
        by Asteria Networking's "listen()" function. Every frame we get the
        amount of time that has passed each frame, check game conditions,
        and draw the game to the screen.

        :param None:

        :rtype: None
        :returns: None

        """
        # Android-specific check for pause
        if android:
            if android.check_pause():
                android.wait_for_resume()

        # Get the amount of time that has passed since the last frame.
        time_delta = self.clock.tick(self.fps) / 1000.0
        self.time_passed_seconds = time_delta

        # Update our networking.
        if self.controller_server:
            self.controller_server.update()

        if self.client.listening:
            self.client.update(time_delta)
            self.add_clients_to_map(self.client.client.registry)

        if self.server.listening:
            self.server.update()

        # Run our event engine which will check to see if game conditions.
        # are met and run an action associated with that condition.
        self.event_loop()
#        self.combat_router.update()

        # Run our event engine which will check to see if game conditions
        # are met and run an action associated with that condition.
        self.event_data = {}
        self.event_engine.check_conditions(self, time_delta)
        logger.debug("Event Data:" + str(self.event_data))

        # Draw and update our display
        self.update(time_delta)
        pg.display.update()

        if self.show_fps:
            fps = self.clock.get_fps()
            with_fps = "{} - {:.2f} FPS".format(self.caption, fps)
            pg.display.set_caption(with_fps)
        if self.exit:
            self.done = True

    def get_menu_event(self, menu, event):
        """Run this function to process pygame basic menu events (such as keypresses/mouse clicks -
        up, down, enter, escape).

        :param menu: -- The active menu.
        :param event: -- A single pygame event from pygame.event.get()

        :type menu: core.components.menu.Menu()
        :type events: List

        :rtype: None
        :returns: None

        """
        # use the default sound if a custom sound is nt specified.
        try:
            if menu.menu_select_sound:
                pass
        except AttributeError:
            menu.menu_select_sound = pg.mixer.Sound(
                prepare.BASEDIR + "resources/sounds/interface/50561__broumbroum__sf3-sfx-menu-select.ogg")

        if len(menu.menu_items) > 0:
            menu.line_spacing = (menu.size_y / len(menu.menu_items)) - menu.font_size

        if event.type == pg.KEYUP and event.key == pg.K_ESCAPE and not menu.previous_menu:
            menu.menu_select_sound.play()
            self.pop_state()

        if event.type == pg.KEYUP and event.key == pg.K_ESCAPE and menu.previous_menu:
            menu.menu_select_sound.play()
            menu.interactable = False
            menu.visible = False
            if menu.previous_menu:
                menu.previous_menu.interactable = True
                menu.previous_menu.visible = True

        if event.type == pg.KEYUP and event.key == pg.K_DOWN:
            menu.menu_select_sound.play()
            menu.selected_menu_item += 1
            if menu.selected_menu_item > len(menu.menu_items) - 1:
                menu.selected_menu_item = 0

        if event.type == pg.KEYUP and event.key == pg.K_UP:
            menu.menu_select_sound.play()
            menu.selected_menu_item -= 1
            if menu.selected_menu_item < 0:
                menu.selected_menu_item = len(menu.menu_items) - 1

        if event.type == pg.KEYUP and event.key == pg.K_RETURN:
            menu.menu_select_sound.play()
            menu.get_event(event)

    def scale_new_player(self, sprite):
        """Scales a new player to the screen.

        :param sprite: Player sprite from the server registry.

        :type sprite: -- Player or Npc object from core.components.player

        :rtype: None
        :returns: None

        """
        SCALE = prepare.SCALE
        TILE_SIZE = prepare.TILE_SIZE
        SCREEN_SIZE = prepare.TILE_SIZE

        for key, animation in sprite.sprite.items():
            animation.scale(
                tuple(i * SCALE for i in animation.getMaxSize()))

        for key, image in sprite.standing.items():
            sprite.standing[key] = pg.transform.scale(
                image, (image.get_width() * SCALE,
                        image.get_height() * SCALE))

        # Set the player's width and height based on the size of our scaled
        # sprite.
        sprite.playerWidth, sprite.playerHeight = \
            sprite.standing["front"].get_size()
        sprite.playerWidth = TILE_SIZE[0]
        sprite.playerHeight = TILE_SIZE[1]
        sprite.tile_size = TILE_SIZE

        # Put the player right in the middle of our screen.
        sprite.position = [
            (SCREEN_SIZE[0] / 2) - (sprite.playerWidth / 2),
            (SCREEN_SIZE[1] / 2) - (sprite.playerHeight / 2)]

        # Set the player's collision rectangle
        sprite.rect = pg.Rect(
            sprite.position[0],
            sprite.position[1],
            TILE_SIZE[0],
            TILE_SIZE[1])

        # Set the walking and running pixels per second based on the scale
        sprite.walkrate *= SCALE
        sprite.runrate *= SCALE

    def add_clients_to_map(self, registry):
        """Checks to see if clients are supposed to be displayed on the current map. If
        they are on the same map as the host then it will add them to the npc's list.
        If they are still being displayed and have left the map it will remove them from
        the map.

        :param registry: Locally hosted Neteria client/server registry.

        :type registry: Dictionary

        :rtype: None
        :returns: None

        """
        world = self.get_state_name("world")
        if not world:
            return

        world.npcs = []
        world.npcs_off_map = []
        for client in registry:
            if "sprite" in registry[client]:
                sprite = registry[client]["sprite"]
                client_map = registry[client]["map_name"]
                current_map = self.get_map_name()

                # Add the player to the screen if they are on the same map.
                if client_map == current_map:
                    if not sprite in world.npcs:
                        world.npcs.append(sprite)
                    if sprite in world.npcs_off_map:
                        world.npcs_off_map.remove(sprite)

                # Remove player from the map if they have changed maps.
                elif client_map != current_map:
                    if not sprite in world.npcs_off_map:
                        world.npcs_off_map.append(sprite)
                    if sprite in world.npcs:
                        world.npcs.remove(sprite)

    def get_map_name(self):
        """Gets the map of the player.

        :param: None

        :rtype: String
        :returns: map_name

        """
        world = self.get_state_name("world")
        if not world:
            return

        map_path = world.current_map.filename
        map_name = str(map_path.replace(prepare.BASEDIR, ""))
        map_name = str(map_name.replace("resources/maps/", ""))
        return map_name

    def get_state_name(self, name):
        for state in self.state_stack:
            if state.__module__ == "core.states." + name:
                return state
        return None

class PygameControl(Control):
    pass


class HeadlessControl(StateManager):
    """Control class for headless server. Contains the game loop, and contains
    the event_loop which passes events to States as needed.

    :param: None
    :rtype: None
    :returns: None

    """

    def __init__(self):
        self.done = False

        self.clock = time.clock()
        self.fps = 60.0
        self.current_time = 0.0

        # TODO: move out to state manager
        self.package = "core.states"
        self.state_dict = dict()
        self.state_stack = list()

        self.server = networking.TuxemonServer(self)
        # self.server_thread = threading.Thread(target=self.server)
        # self.server_thread.start()
        self.server.server.listen()

        #Set up our game's configuration from the prepare module.
        self.config = prepare.HEADLESSCONFIG

        # Set up the command line. This provides a full python shell for
        # troubleshooting. You can view and manipulate any variables in
        # the game.
        self.exit = False   # Allow exit from the CLI
        if self.config.cli:
            self.cli = cli.CommandLine(self)

    def main_loop(self):
        """Main loop for entire game. This method gets execute every frame
        by Asteria Networking's "listen()" function. Every frame we get the
        amount of time that has passed each frame, check game conditions,
        and draw the game to the screen.

        :param None:

        :rtype: None
        :returns: None

        """
        # Get the amount of time that has passed since the last frame.
        # self.time_passed_seconds = time.clock() - self.clock
        # self.server.update()

        if self.exit:
            self.done = True

    def main(self):
        """Initiates the main game loop. Since we are using Asteria networking
        to handle network events, we pass this core.control.Control instance to
        networking which in turn executes the "main_loop" method every frame.
        This leaves the networking component responsible for the main loop.
        :param None:
        :rtype: None
        :returns: None
        """
        while not self.exit:
            self.main_loop()

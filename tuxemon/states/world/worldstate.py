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
# Leif Theden <leif.theden@gmail.com>
#
# states.world Handles the world map and player movement.
#
#

import logging
from functools import partial

import tuxemon
from tuxemon import prepare, state, networking
from tuxemon import rumble
from tuxemon.map import direction_map
from tuxemon.map_view import MapView
from tuxemon.platform.const import buttons, events, intentions
from tuxemon.platform.events import PlayerInput
from tuxemon.session import local_session

logger = logging.getLogger(__name__)


class WorldState(state.State):
    """The state responsible for the world movement and interaction"""

    keymap = {
        buttons.UP: intentions.UP,
        buttons.DOWN: intentions.DOWN,
        buttons.LEFT: intentions.LEFT,
        buttons.RIGHT: intentions.RIGHT,
        buttons.A: intentions.INTERACT,
        buttons.B: intentions.RUN,
        buttons.START: intentions.WORLD_MENU,
        buttons.BACK: intentions.WORLD_MENU,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = local_session.client
        self.wants_to_move_player = None
        self.current_music = {"status": "stopped", "song": None, "previoussong": None}
        self.rumble_manager = rumble.RumbleManager()
        self.rumble = self.rumble_manager.rumbler
        self.player_npc = None
        self.view = None
        self.session = None

    def startup(self, *args, **kwargs):
        session = kwargs["session"]
        self.session = session
        self.player_npc = None  # type: tuxemon.npc.NPC
        self.wants_to_move_player = None
        self.view = MapView(self.session.world)
        self.player_npc = session.player
        self.set_player_npc(self.player_npc)

    def set_player_npc(self, entity):
        """Set the npc which is controlled and set camera to follow them"""
        self.player_npc = entity
        self.view.follow(entity)

    def stop_player(self):
        """Reset controls and stop player movement at once.  Do not lock controls

        If player was in a movement when stopped, the player will be moved to end.
        """
        self.wants_to_move_player = None
        self.client.release_controls()
        if self.player_npc is not None:
            self.player_npc.cancel_movement()

    def stop_and_reset_player(self):
        """Reset controls, stop player and abort movement.  Do not lock controls.

        Movement is aborted here, so the player will not complete movement
        to a tile.  It will be reset to the tile where movement started.

        Use if you don't want to trigger another tile event.
        """
        self.wants_to_move_player = None
        self.client.release_controls()
        if self.player_npc is not None:
            self.player_npc.abort_movement()

    def move_player(self, direction: str):
        """Move player in a direction.  Changes facing."""
        # TODO: clean up the event engines so this call is not so horrible
        do = partial(self.session.world.eventengine.start_action, self.session)
        print("move")
        do("player_face", [direction])
        do("npc_move_tile", ("player", direction))

    def pause(self):
        """Called before another state gets focus"""
        # self.lock_controls()
        self.stop_player()

    def resume(self):
        """Called after returning focus to this state"""
        # self.unlock_controls()
        pass

    def draw(self, surface):
        """Draw the game world to the screen"""
        self.view.draw(surface)

    def process_event(self, event):
        """Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        :type event: input.PlayerInput
        :rtype: Optional[input.PlayerInput]
        """
        # map may not have a player registered
        if self.player_npc is None:
            return

        event = self.translate_input_event(event)

        # has the player pressed the action key?
        # if event.pressed and event.button == buttons.A:
        #     for map_event in self.world.interacts:
        #         self.process_map_event(map_event)
        #

        if event.button == intentions.WORLD_MENU:
            pass

        locked_controls = self.player_npc.game_variables.get("CONTROLS_LOCKED")
        if not locked_controls:
            if event.button == intentions.RUN:
                if event.held:
                    self.player_npc.moverate = self.client.config.player_runrate
                else:
                    self.player_npc.moverate = self.client.config.player_walkrate
            direction = direction_map.get(event.button)
            if direction is not None:
                if event.held:
                    self.wants_to_move_player = direction
                    self.move_player(direction)
                    return
                elif not event.pressed:
                    if direction == self.wants_to_move_player:
                        self.stop_player()
                        return

        if prepare.DEV_TOOLS:
            if event.pressed and event.button == intentions.NOCLIP:
                self.player_npc.ignore_collisions = (
                    not self.player_npc.ignore_collisions
                )
                return

        # if we made it this far, return the event for others to use
        return event

    def translate_input_event(self, event):
        """Translate a key to a game input

        :type event: tuxemon.input.events.PlayerInput
        :rtype: tuxemon.input.events.PlayerInput
        """
        try:
            return PlayerInput(self.keymap[event.button], event.value, event.hold_time)
        except KeyError:
            pass

        if event.button == events.UNICODE:
            if event.value == "n":
                return PlayerInput(intentions.NOCLIP, event.value, event.hold_time)

        return event

    # boneyard

    def handle_interaction(self, event_data, registry):
        """Presents options window when another player has interacted with this player."""
        target = registry[event_data["target"]]["sprite"]
        target_name = str(target.name)
        networking.update_client(target, event_data["char_dict"], self.game)
        if event_data["interaction"] == "DUEL":
            if not event_data["response"]:
                self.interaction_menu.visible = True
                self.interaction_menu.interactable = True
                self.interaction_menu.player = target
                self.interaction_menu.interaction = "DUEL"
                self.interaction_menu.menu_items = [
                    target_name + " would like to Duel!",
                    "Accept",
                    "Decline",
                ]
            else:
                if self.wants_duel:
                    if event_data["response"] == "Accept":
                        world = self.game.current_statimape
                        pd = world.player1.__dict__
                        event_data = {
                            "type": "CLIENT_INTERACTION",
                            "interaction": "START_DUEL",
                            "target": [event_data["target"]],
                            "response": None,
                            "char_dict": {
                                "monsters": pd["monsters"],
                                "inventory": pd["inventory"],
                            },
                        }
                        self.game.server.notify_client_interaction(cuuid, event_data)

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
# core.states.start Handles the splash screen and start menu.
#
#

import logging

from tuxemon.core import audio
from tuxemon.core import prepare
from tuxemon.core import state

logger = logging.getLogger(__name__)


class SplashState(state.State):
    """ The state responsible for the splash screen
    """
    default_duration = 3

    def fade_out(self):
        self.fading_out = True
        self.client.push_state("FadeOutTransition", caller=self)

    def startup(self, **kwargs):
        # this task will skip the splash screen after some time
        self.task(self.fade_out, self.default_duration)

        # used to ignore keypresses after fadeout has started
        self.fading_out = False

        width, height = prepare.SCREEN_SIZE
        splash_border = prepare.SCREEN_SIZE[0] / 20  # The space between the edge of the screen

        # Set up the splash screen logos
        logo = self.load_sprite("gfx/ui/intro/pygame_logo.png")
        logo.rect.topleft = splash_border, height - splash_border - logo.rect.height

        # Set up the splash screen logos
        cc = self.load_sprite("gfx/ui/intro/creative_commons.png")
        cc.rect.topleft = width - splash_border - cc.rect.width, height - splash_border - cc.rect.height

        self.ding = audio.load_sound("sound_ding")
        self.ding.play()

    def process_event(self, event):
        """ Handles player input events. This function is only called when the
        player provides input such as pressing a key or clicking the mouse.

        Since this is part of a chain of event handlers, the return value
        from this method becomes input for the next one.  Returning None
        signifies that this method has dealt with an event and wants it
        exclusively.  Return the event and others can use it as well.

        You should return None if you have handled input here.

        :type event: tuxemon.core.input.PlayerInput
        :rtype: Optional[core.input.PlayerInput]
        """
        # Skip the splash screen if a key is pressed.
        if event.pressed and not self.fading_out:
            self.animations.empty()
            self.fade_out()

    def draw(self, surface):
        """Draws the start screen to the screen.

        :param surface:
        :param Surface: Surface to draw to

        :type Surface: pygame.Surface

        :rtype: None
        :returns: None

        """
        surface.fill((15, 15, 15))
        self.sprites.draw(surface)

from __future__ import division

import logging

import pygame

from core import prepare
from core.state import State

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("{} successfully imported".format(__name__))


class FlashTransition(State):
    """ The state responsible for the battle transitions.
    """
    force_draw = True

    def startup(self, **kwargs):
        logger.info("Initializing battle transition")
        self.flash_time = 0.2  # Time in seconds between flashes
        self.flash_state = "up"
        self.transition_alpha = 0
        self.max_flash_count = 7
        self.flash_count = 0
        self.game.rumble.rumble(-1, length=1.5)

    def resume(self):
        self.transition_surface = pygame.Surface(prepare.SCREEN_SIZE)
        self.transition_surface.fill((255, 255, 255))

    def update(self, time_delta):
        """ Update function for state.

        :param time_delta: Time since last update in seconds
        :type time_delta: Float
        :rtype: None
        :returns: None
        """
        logger.info("Battle transition!")

        # self.battle_transition_alpha
        if self.flash_state == "up":
            self.transition_alpha += 255 * (time_delta / self.flash_time)

        elif self.flash_state == "down":
            self.transition_alpha -= 255 * (time_delta / self.flash_time)

        if self.transition_alpha >= 255:
            self.flash_state = "down"
            self.flash_count += 1

        elif self.transition_alpha <= 0:
            self.flash_state = "up"
            self.flash_count += 1

        # If we've hit our max number of flashes, stop the battle
        # transition animation.
        if self.flash_count > self.max_flash_count:
            logger.info("Flashed " + str(self.flash_count) + " times. Stopping transition.")
            self.game.pop_state()

    def draw(self, surface):
        """Draws the start screen to the screen.
        :param surface:
        :param surface: Surface to draw to
        :type surface: pygame.Surface

        :returns: None
        """
        # Set the alpha of the screen and fill the screen with white at
        # that alpha level.
        self.transition_surface.set_alpha(self.transition_alpha)
        surface.blit(self.transition_surface, (0, 0))

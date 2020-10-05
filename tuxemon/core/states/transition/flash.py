import logging

import pygame

from tuxemon.core import prepare
from tuxemon.core.state import State

logger = logging.getLogger(__name__)


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
        self.client.rumble.rumble(-1, length=1.5)

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
            self.client.pop_state()

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
        # prevent other states from getting input
        return None

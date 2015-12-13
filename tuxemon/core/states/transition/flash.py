import logging
import pygame

from core import prepare
from core.state import State

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("{} successfully imported".format(__name__))


class FLASH_TRANSITION(State):
    """ The state responsible for the battle transitions.
    """

    def startup(self, params=None):
        self.flash_time = 0.2  # Time in seconds between flashes
        self.flash_state = "up"
        self.transition_alpha = 0
        self.max_flash_count = 7
        self.flash_count = 0
        logger.info("Initializing battle transition")
        self.game.rumble.rumble(-1, length=1.5)

    def resume(self):
        self.original_surface = self.game.screen.copy()
        self.transition_surface = pygame.Surface(prepare.SCREEN_SIZE)
        self.transition_surface.fill((255, 255, 255))

    def update(self, screen, keys, current_time, time_delta):
        """Update function for state.

        :param surface: The pygame.Surface of the screen to draw to.
        :param keys: List of keys from pygame.event.get().
        :param current_time: The amount of time that has passed.

        :type surface: pygame.Surface
        :type keys: Tuple
        :type current_time: Integer

        :rtype: None
        :returns: None
        """
        logger.info("Battle transition!")

        # self.battle_transition_alpha
        if self.flash_state == "up":
            self.transition_alpha += (
                255 * ((time_delta) / self.flash_time))

        elif self.flash_state == "down":
            self.transition_alpha -= (
                255 * ((time_delta) / self.flash_time))

        if self.transition_alpha >= 255:
            self.flash_state = "down"
            self.flash_count += 1

        elif self.transition_alpha <= 0:
            self.flash_state = "up"
            self.flash_count += 1

        self.draw(self.game.screen)

        # If we've hit our max number of flashes, stop the battle
        # transition animation.
        if self.flash_count > self.max_flash_count:
            logger.info("Flashed " + str(self.flash_count) +
                " times. Stopping transition.")
            self.game.pop_state()

    def draw(self, surface):
        """Draws the start screen to the screen.
        :param surface: Surface to draw to
        :type surface: pygame.Surface

        :return: None
        """
        # Blit the original surface to the screen.
        surface.blit(self.original_surface, (0, 0))

        # Set the alpha of the screen and fill the screen with white at
        # that alpha level.
        self.transition_surface.set_alpha(self.transition_alpha)
        surface.blit(self.transition_surface, (0, 0))
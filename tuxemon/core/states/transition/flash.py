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
        self.combat_params = params

        self.original_surface = self.game.screen.copy()
        self.transition_surface = pygame.Surface(prepare.SCREEN_SIZE)
        self.transition_surface.fill((255, 255, 255))
        self.flash_time = 0.2  # Time in seconds between flashes
        self.battle_flash_state = "up"
        self.battle_transition_alpha = 0

        self.max_battle_flash_count = 7
        self.battle_flash_count = 0

        logger.info("Initializing battle transition")
        self.game.rumble.rumble(-1, length=1.5)

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

        **Examples:**

        >>> surface
        <Surface(1280x720x32 SW)>
        >>> keys
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ...
        >>> current_time
        435

        """
        logger.info("Battle transition!")

        # self.battle_transition_alpha
        if self.battle_flash_state == "up":
            self.battle_transition_alpha += (
                255 * ((time_delta) / self.flash_time))

        elif self.battle_flash_state == "down":
            self.battle_transition_alpha -= (
                255 * ((time_delta) / self.flash_time))

        if self.battle_transition_alpha >= 255:
            self.battle_flash_state = "down"
            self.battle_flash_count += 1

        elif self.battle_transition_alpha <= 0:
            self.battle_flash_state = "up"
            self.battle_flash_count += 1

        # If we've hit our max number of flashes, stop the battle
        # transition animation.
        if self.battle_flash_count > self.max_battle_flash_count:
            logger.info("Flashed " + str(self.battle_flash_count) +
                " times. Stopping transition.")
            self.game.pop_state()
            self.game.push_state("COMBAT", params=self.combat_params)

        self.draw()

    def draw(self):
        """Draws the start screen to the screen.

        :param None:
        :type None:

        :rtype: None
        :returns: None

        """
        # Blit the original surface to the screen.
        self.game.screen.blit(self.original_surface, (0, 0))

        # Set the alpha of the screen and fill the screen with white at
        # that alpha level.
        self.transition_surface.set_alpha(self.battle_transition_alpha)
        self.game.screen.blit(self.transition_surface, (0, 0))
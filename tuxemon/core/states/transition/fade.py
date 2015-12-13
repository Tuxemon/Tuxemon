import logging
import pygame
from animation import Animation, Task
from abc import ABCMeta, abstractmethod

from core.state import State

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)
logger.debug("{} successfully imported".format(__name__))


class FadeTransitionBase(State):
    """ The state responsible for the battle transitions.
    """
    __metaclass__ = ABCMeta

    state_duration = 2.5
    fade_duration = 2
    color = (0, 0, 0)

    def startup(self, params=None):
        logger.info("Initializing fade transition")
        if params:
            self.state_duration = params.get('state_duration', self.state_duration)
            self.fade_duration = params.get('fade_duration', self.fade_duration)

    def resume(self):
        self.animations = pygame.sprite.Group()
        size = self.game.screen.get_size()
        self.original_surface = self.game.screen.copy()
        self.transition_surface = pygame.Surface(size)
        self.transition_surface.fill(self.color)
        self.create_fade_animation()

    @abstractmethod
    def create_fade_animation(self):
        pass

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
        self.animations.update(time_delta)
        self.draw(self.game.screen)

    def draw(self, surface):
        # Blit the original surface to the screen.
        surface.blit(self.original_surface, (0, 0))

        # Cover the screen with our faded surface
        surface.blit(self.transition_surface, (0, 0))


class FADE_OUT_TRANSITION(FadeTransitionBase):
    def create_fade_animation(self):
        task = Task(self.game.pop_state, self.state_duration)
        ani = Animation(set_alpha=255, initial=0, duration=self.fade_duration)
        ani.start(self.transition_surface)
        self.animations.add(ani, task)


class FADE_IN_TRANSITION(FadeTransitionBase):
    def create_fade_animation(self):
        task = Task(self.game.pop_state, self.state_duration)
        ani = Animation(set_alpha=0, initial=255, duration=self.fade_duration)
        ani.start(self.transition_surface)
        self.animations.add(ani, task)

import logging
import pygame
from abc import abstractmethod

from core.components.animation import Animation, Task
from core.state import State


logger = logging.getLogger(__name__)
logger.debug("{} successfully imported".format(__name__))


class FadeTransitionBase(State):
    """ The state responsible for the battle transitions.
    """
    state_duration = 2.5
    fade_duration = 2
    color = (0, 0, 0)

    def startup(self, params=None):
        logger.info("Initializing fade transition")
        if params:
            self.state_duration = params.get("state_duration", self.state_duration)
            self.fade_duration = params.get("fade_duration", self.fade_duration)

    def resume(self):
        self.animations = pygame.sprite.Group()
        size = self.game.screen.get_size()
        self.original_surface = self.game.screen.copy()
        self.transition_surface = pygame.Surface(size)
        self.transition_surface.fill(self.color)
        self.animations.add(Task(self.game.pop_state, self.state_duration))
        self.create_fade_animation()

    @abstractmethod
    def create_fade_animation(self):
        pass

    def update(self, time_delta):
        self.animations.update(time_delta)

    def draw(self, surface):
        # Blit the original surface to the screen.
        surface.blit(self.original_surface, (0, 0))

        # Cover the screen with our faded surface
        surface.blit(self.transition_surface, (0, 0))


class FADE_OUT_TRANSITION(FadeTransitionBase):
    def create_fade_animation(self):
        ani = Animation(set_alpha=255, initial=0, duration=self.fade_duration)
        ani.start(self.transition_surface)
        self.animations.add(ani)


class FADE_IN_TRANSITION(FadeTransitionBase):
    def create_fade_animation(self):
        ani = Animation(set_alpha=0, initial=255, duration=self.fade_duration)
        ani.start(self.transition_surface)
        self.animations.add(ani)

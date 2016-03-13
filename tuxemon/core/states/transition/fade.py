import logging
from abc import abstractmethod

import pygame

from core.state import State

logger = logging.getLogger(__name__)
logger.debug("{} successfully imported".format(__name__))


class FadeTransitionBase(State):
    """ The state responsible for the battle transitions.
    """
    force_draw = True
    state_duration = 1
    fade_duration = 1.5
    color = (0, 0, 0)

    def startup(self, **kwargs):
        logger.info("Initializing fade transition")
        self.state_duration = kwargs.get("state_duration", self.state_duration)
        self.fade_duration = kwargs.get("fade_duration", self.fade_duration)
        self.caller = kwargs.get("caller")

    def resume(self):
        size = self.game.screen.get_size()
        self.transition_surface = pygame.Surface(size)
        self.transition_surface.fill(self.color)
        self.task(self.game.pop_state, self.state_duration)
        self.create_fade_animation()

    def process_event(self, event):
        pass

    def update(self, time_delta):
        self.animations.update(time_delta)

    @abstractmethod
    def create_fade_animation(self):
        pass

    def draw(self, surface):
        # Cover the screen with our faded surface
        surface.blit(self.transition_surface, (0, 0))


class FadeOutTransition(FadeTransitionBase):
    def create_fade_animation(self):
        self.animate(self.transition_surface, set_alpha=255, initial=0, duration=self.fade_duration)

    def shutdown(self):
        self.game.pop_state(self.caller)


class FadeInTransition(FadeTransitionBase):
    def create_fade_animation(self):
        self.animate(self.transition_surface, set_alpha=0, initial=255, duration=self.fade_duration)

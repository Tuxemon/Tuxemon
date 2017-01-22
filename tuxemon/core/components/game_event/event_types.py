import pygame
import sys

INPUT_EVENT = pygame.USEREVENT + 0

# Populate a list of all user defined event types.
USER_EVENTS = []
for event in sys.modules[__name__].__dict__.keys():
    if event.endswith("EVENT"):
        USER_EVENTS.append(getattr(sys.modules[__name__], event))

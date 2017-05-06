from __future__ import absolute_import
from __future__ import print_function

import pygame

from .event_types import *

def _add_event(event):
    """Adds an event to the pygame event queue.

    :param event: The pygame event to add.
    :type event: pygame.event.Event

    :rtype: None
    :returns: None

    """
    pygame.event.post(event)

def input_event(text):
    """Adds an input event to the event queue. Used for passing input from the input
    state to other states such as the monster menu, etc.

    :param text: The text from the input state.
    :type text: str

    :rtype: pygame.event.Event
    :returns: The pygame event added to the event queue.

    """
    event = pygame.event.Event(GAME_EVENT, event_type=INPUT_EVENT, text=text)
    _add_event(event)

    return event

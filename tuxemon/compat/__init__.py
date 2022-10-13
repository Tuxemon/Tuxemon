from typing import Type

from tuxemon.compat.rect import ReadOnlyRect

Rect: Type[ReadOnlyRect]

try:
    from pygame.rect import Rect
except ImportError:
    from tuxemon.compat.rect import Rect

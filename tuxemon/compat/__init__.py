from tuxemon.compat.rect import ReadOnlyRect
from typing import Type

Rect: Type[ReadOnlyRect]

try:
    from pygame.rect import Rect
except ImportError:
    from tuxemon.compat.rect import Rect

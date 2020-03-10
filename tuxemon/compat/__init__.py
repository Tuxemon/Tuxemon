try:
    from pygame.sprite import Rect
except ImportError:
    from tuxemon.compat.rect import Rect

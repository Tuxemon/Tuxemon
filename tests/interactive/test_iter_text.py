import pygame
import this
from tuxemon.core.components.ui import draw

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    clock = pygame.time.Clock()
    font = pygame.font.Font(pygame.font.get_default_font(), 20)
    fg = 255, 245, 64
    bg = 35, 35, 35
    text = "".join([this.d.get(c, c) for c in this.s])
    running = True

    while running:
        for dirty, rect, surface in draw.iter_render_text(text, font, fg, bg, screen.get_rect()):
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False

            if not running:
                break

            screen.fill(bg, dirty)
            screen.blit(surface, rect)
            pygame.display.flip()
            clock.tick(60)

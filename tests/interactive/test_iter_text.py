from tuxemon.core.components.ui import draw

if __name__ == "__main__":
    import pygame

    pygame.init()
    pygame.display.set_mode((640, 480))
    clock = pygame.time.Clock()
    font = pygame.font.Font(pygame.font.get_default_font(), 20)
    fg = 255, 245, 64
    bg = 35, 35, 35

    import this

    text = "".join([this.d.get(c, c) for c in this.s])

    while 1:
        screen = pygame.display.get_surface()
        for dirty, rect, surface in draw.iter_render_text(text, font, fg, screen.get_rect()):
            screen.fill(bg, dirty)
            screen.blit(surface, rect)
            pygame.event.pump()
            pygame.display.flip()
            clock.tick(60)

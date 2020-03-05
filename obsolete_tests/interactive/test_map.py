"""
from map.py
"""

# If the module is being run as a standalone program, run an example
if __name__ == "__main__":

    from . import config

    # set up pygame
    pygame.init()

    # read the configuration file
    config = config.Config()

    # The game resolution
    resolution = config.resolution

    # set up the window with epic name
    screen = pygame.display.set_mode(resolution, config.fullscreen, 32)
    pygame.display.set_caption('Tuxemon Map')

    # Native resolution is similar to the old gameboy resolution. This is used for scaling.
    native_resolution = [240, 160]

    # If scaling is enabled, scale the tiles based on the resolution
    if config.scaling == "1":
        scale = int((resolution[0] / native_resolution[0]))

    # Fill _background
    background = pygame.Surface(screen.get_size())
    background = background.convert()

    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()

    tile_size = [80, 80]    # 1 tile = 16 pixels
    testmap = Map()
    #testmap.loadfile("resources/maps/test.map", tile_size)
    testmap.loadfile("resources/maps/test_pathfinding.map", tile_size)

    # Event loop THIS IS WHAT SHIT IS DOING RIGHT NOW BRAH
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            # Exit the game if you press ESC
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()

        screen.blit(background, (0, 0))
        pygame.display.flip()

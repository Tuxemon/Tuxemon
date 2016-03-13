"""
from combat.py
"""

if __name__ == "__main__":

    print("Runs as standalone")

    from core.components import config


    class Game(object):

        def __init__(self):
            # set up pygame
            pygame.init()
            # read the configuration file
            self.config = config.Config()
            # The game resolution
            self.resolution = self.config.resolution
            # set up the window
            self.screen = pygame.display.set_mode(self.resolution, self.config.fullscreen, 32)
            pygame.display.set_caption('Tuxemon Combat System')
            # Create a clock object that will keep track of how much time has passed since the last frame
            self.clock = pygame.time.Clock()
            # Set the font for the FPS and other shit
            self.font = pygame.font.Font(prepare.BASEDIR + "resources/font/PressStart2P.ttf", 14)

            # Native resolution is similar to the old gameboy resolution. This is used for scaling.
            self.native_resolution = [240, 160]

            # If scaling is enabled, set the scaling based on resolution
            if self.config.scaling == "1":
                self.scale = int((self.resolution[0] / self.native_resolution[0]))
            else:
                self.scale = 1

            self.combat = COMBAT(self)

            while True:
                self.clock.tick()
                self.events = pygame.event.get()

                for event in self.events:
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    # Exit the game if you press ESC
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                self.combat.draw()
                self.combat.handle_events(self)

                # Calculate the FPS and print it onscreen for debugging purposes
                fps = self.font.draw("FPS: " + str(self.clock.get_fps()), 1, (240, 240, 240))
                self.screen.blit(fps, (10, 10))

                pygame.display.flip()


    Game()

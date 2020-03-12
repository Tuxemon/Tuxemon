class Session(object):
    """

    Contains Control, World, and Player

    """
    def __init__(self, control, world, player):
        self.control = control
        self.world = world
        self.player = player


# will be filled in later when game starts
local_session = Session(None, None, None)

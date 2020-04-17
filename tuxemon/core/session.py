class Session(object):
    """

    Contains Client, World, and Player

    Eventually this will be extended to support network sessions

    """
    def __init__(self, client, world, player):
        """
        :param tuxemon.core.client.Client client: Game session
        :param tuxemon.core.world.World world: Game world
        :param tuxemon.core.npc.NPC player: Player NPC object
        """
        self.client = client
        self.world = world
        self.player = player


# will be filled in later when game starts
local_session = Session(None, None, None)

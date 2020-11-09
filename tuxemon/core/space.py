class Space:
    """
    Manage entities that move in physical environment
    """
    def pos_update(self):
        """ WIP.  Required to be called after position changes

        :return:
        """
        self.tile_pos = proj(self.position3)
        self.network_notify_location_change()

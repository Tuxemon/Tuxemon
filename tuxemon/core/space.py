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


class Body:
    # === PHYSICS START ================================================================
    def stop_moving(self):
        """ Completely stop all movement

        :return: None
        """
        self.velocity3.x = 0
        self.velocity3.y = 0
        self.velocity3.z = 0

    def pos_update(self):
        """ WIP.  Required to be called after position changes

        :return:
        """
        self.tile_pos = proj(self.position3)

    def update_physics(self, td):
        """ Move the entity according to the movement vector

        :param td:
        :return:
        """
        self.position3 += self.velocity3 * td
        self.pos_update()

    def set_position(self, pos):
        """ Set the entity's position in the game world

        :param pos:
        :return:
        """
        self.position3.x = pos[0]
        self.position3.y = pos[1]
        self.pos_update()

    # === PHYSICS END ==================================================================

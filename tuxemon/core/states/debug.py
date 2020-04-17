"""

WIP make a state that is responsible for printing/displaying debug info

"""
# TODO: move to its own state
# def draw_event_debug(self):
#     """ Very simple overlay of event data.  Needs some love.
#
#     :return:
#     """
#     y = 20
#     x = 4
#
#     yy = y
#     xx = x
#
#     font = pg.font.Font(pg.font.get_default_font(), 15)
#     for event in self.event_engine.partial_events:
#         w = 0
#         for valid, item in event:
#             p = ' '.join(item.parameters)
#             text = "{} {}: {}".format(item.operator, item.type, p)
#             if valid:
#                 color = (0, 255, 0)
#             else:
#                 color = (255, 0, 0)
#             image = font.render(text, 1, color)
#             self.screen.blit(image, (xx, yy))
#             ww, hh = image.get_size()
#             yy += hh
#             w = max(w, ww)
#
#         xx += w + 20
#
#         if xx > 1000:
#             xx = x
#             y += 200
#
#         yy = y
def debug_drawing(self, surface):
    surface.lock()

    # draw events
    for event in self.game.events:
        topleft = self.get_pos_from_tilepos((event.x, event.y))
        size = self.project((event.w, event.h))
        rect = topleft, size
        box(surface, rect, (0, 255, 0, 128))

    # We need to iterate over all collidable objects.  So, let's start
    # with the walls/collision boxes.
    box_iter = itertools.imap(self._collision_box_to_pgrect, self.collision_map)

    # Next, deal with solid NPCs.
    npc_iter = itertools.imap(self._npc_to_pgrect, self.npcs.values())

    # draw noc and wall collision tiles
    red = (255, 0, 0, 128)
    for item in itertools.chain(box_iter, npc_iter):
        box(surface, item, red)

    # draw center lines to verify camera is correct
    w, h = surface.get_size()
    cx, cy = w // 2, h // 2
    pygame.draw.line(surface, (255, 50, 50), (cx, 0), (cx, h))
    pygame.draw.line(surface, (255, 50, 50), (0, cy), (w, cy))

    surface.unlock()

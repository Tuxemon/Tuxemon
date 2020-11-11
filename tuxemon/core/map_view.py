"""

Anything that is rendered to the screen is handled here.
Any visual representation of a game object should be handled here.

"""
import os

import pyscroll

from tuxemon.compat import Rect
from tuxemon.core import prepare, pyganim
from tuxemon.core.graphics import load_and_scale
from tuxemon.core.map import facing
from tuxemon.core.prepare import CONFIG
from tuxemon.core.tools import nearest

# reference direction and movement states to animation names
animation_mapping = {
    True: {
        'up': 'back_walk',
        'down': 'front_walk',
        'left': 'left_walk',
        'right': 'right_walk'},
    False: {
        'up': 'back',
        'down': 'front',
        'left': 'left',
        'right': 'right'}
}


class MapSprite(object):
    """ WIP.  View of an NPC on the map

    This is largely existing code from the NPC class
    """

    def __init__(self, sprite_name):
        self.sprite_name = sprite_name
        self.standing = dict()
        self.sprite = dict()
        self.moveConductor = pyganim.PygConductor()

    def load_sprites(self):
        """ Load sprite graphics

        :return:
        """
        # Get all of the standing animation images
        self.standing = {}
        for standing_type in facing:
            filename = "{}_{}.png".format(self.sprite_name, standing_type)
            path = os.path.join("sprites", filename)
            self.standing[standing_type] = load_and_scale(path)

        # avoid cutoff frames when steps don't line up with tile movement
        frames = 3
        frame_duration = (1000 / CONFIG.player_walkrate) / frames / 1000 * 2

        # Load all of the player's sprite animations
        anim_types = ['front_walk', 'back_walk', 'left_walk', 'right_walk']
        for anim_type in anim_types:
            images = [
                'sprites/%s_%s.%s.png' % (
                    self.sprite_name,
                    anim_type,
                    str(num).rjust(3, str('0'))
                )
                for num in range(4)
            ]

            frames = []
            for image in images:
                surface = load_and_scale(image)
                frames.append((surface, frame_duration))

            self.sprite[anim_type] = pyganim.PygAnimation(frames, loop=True)

        # Have the animation objects managed by a conductor.
        # With the conductor, we can call play() and stop() on all the animation objects
        # at the same time, so that way they'll always be in sync with each other.
        self.moveConductor.add(self.sprite)

    def get_current_npc_surface(self, npc, layer):
        """ Get the surfaces and layers for the sprite

        :param NPC npc: the npc object
        :param int layer: The layer to draw the sprite on.
        :return:
        """

        def get_frame(d, ani):
            frame = d[ani]
            try:
                surface = frame.getCurrentFrame()
                frame.rate = npc.moverate / CONFIG.player_walkrate
                return surface
            except AttributeError:
                return frame

        frame_dict = self.sprite if npc.moving else self.standing
        state = animation_mapping[npc.moving][npc.facing]
        return [(get_frame(frame_dict, state), npc.tile_pos, layer)]


class SpriteCache(object):
    """ Cache seen sprites.  Currently memory is never freed.

    """

    def __init__(self):
        self.sprites = dict()

    def get(self, slug):
        try:
            return self.sprites[slug]
        except KeyError:
            sprite = MapSprite(slug)
            sprite.load_sprites()
            self.sprites[slug] = sprite
            return sprite


class MapView(object):
    """ Render a map, npcs, etc

    use `follow()` to keep the camera on a game object/npc

    """

    def __init__(self, world):
        """ Constructor

        :param World world: World to draw
        """
        self.world = world
        self.map_animations = dict()
        self.tracked_entity = None
        self.renderer = None
        self.sprite_layer = 0
        self.tilewidth = None
        self.tileheight = None
        self.sprites = SpriteCache()
        self._current_map = None

        # TODO: Transitions should be changed to states and not coded in here
        self.transition_alpha = 0
        self.transition_surface = None
        self.in_transition = False

    def follow(self, entity):
        self.tracked_entity = entity

    def draw(self, surface, rect=None):
        """ Draw the view

        :param Surface surface: Target surface
        :param Rect rect: Area to draw to
        """
        if rect is None:
            rect = surface.get_rect()

        # TODO: make more robust to handle no tracking, and tracking other npcs
        if self.tracked_entity is not None:
            gamemap = self.world.get_map_for_entity(self.tracked_entity)
            if gamemap != self._current_map:
                self.renderer = None
            if self.renderer is None:
                filename = prepare.fetch("maps", gamemap.name)
                size = rect.size if rect else prepare.SCREEN_SIZE
                self.renderer = self.initialize_map_renderer(size, filename)

            # get tracked npc coords to center map
            cx, cy = nearest(self.project(self.tracked_entity.tile_pos))
            cx += self.tilewidth // 2
            cy += self.tileheight // 2
            self.renderer.center((cx, cy))

        # if we are not tacking an npc, we may not have a renderer
        if self.renderer is None:
            return

        # get map_animations
        for anim_data in self.map_animations.values():
            anim = anim_data['animation']
            if not anim.isFinished() and anim.visibility:
                frame = (anim.getCurrentFrame(), anim_data["position"], anim_data['layer'])
                world_surfaces.append(frame)

        screen_surfaces = list()
        world_surfaces = self.get_world_surfaces(gamemap)

        assert self.renderer
        assert self.tracked_entity
        assert world_surfaces

        for frame in world_surfaces:
            s, c, l = frame

            # project to pixel/screen coords
            c = self.get_pos_from_tilepos(c)

            # TODO: better handling of tall sprites
            h = s.get_height()
            if h > self.tileheight:
                # offset for center and image height
                c = nearest((c[0], c[1] - h // 2))
            c = c[0] + rect.left, c[1] + rect.top

            # TODO: filter the off-screen sprites so they are not drawn
            screen_surfaces.append((s, c, l))

        # draw the map and sprites
        self.renderer.draw(surface, rect, screen_surfaces)

    def get_world_surfaces(self, gamemap):
        """

        :param gamemap:
        :return:
        """
        world_surfaces = list()
        for npc in self.world.get_entities_on_map(gamemap.name):
            sprite = self.sprites.get(npc.sprite_name)
            surfaces = sprite.get_current_npc_surface(npc, self.sprite_layer)
            world_surfaces.extend(surfaces)
        return world_surfaces

    def initialize_map_renderer(self, size, map_name):
        """ Initialize the renderer for the map and sprites

        :param Tuple[int, int] size: size of rendered area on the screen
        :param str map_name:
        """
        map_object = self.world.get_map(map_name)
        visual_data = pyscroll.data.TiledMapData(map_object.data)
        self.sprite_layer = int(map_object.data.properties.get("sprite_layer", 2))
        self.tilewidth, self.tileheight = prepare.TILE_SIZE
        self.map_animations = dict()
        return pyscroll.BufferedRenderer(
            visual_data, size, clamp_camera=map_object.clamped, tall_sprites=2
        )

    def fade_and_teleport(self, duration=2):
        """ Fade out, teleport, fade in

        :return:
        """

        def cleanup():
            self.in_transition = False

        def fade_in():
            self.trigger_fade_in(duration)
            self.task(cleanup, duration)

        # cancel any fades that may be going on
        self.remove_animations_of(self)
        self.remove_animations_of(cleanup)
        self.stop_player()
        self.in_transition = True
        self.trigger_fade_out(duration)
        task = self.task(self.handle_delayed_teleport, duration)
        task.chain(fade_in, duration + .5)

    def trigger_fade_in(self, duration=2):
        """ World state has own fade code b/c moving maps doesn't change state

        :returns: None
        """
        self.set_transition_surface()
        self.animate(self, transition_alpha=0, initial=255, duration=duration, round_values=True)
        self.task(self.unlock_controls, duration - .5)

    def trigger_fade_out(self, duration=2):
        """ World state has own fade code b/c moving maps doesn't change state

        * will cause player to teleport if set somewhere else

        :returns: None
        """
        self.set_transition_surface()
        self.animate(self, transition_alpha=255, initial=0, duration=duration, round_values=True)
        self.stop_player()
        self.lock_controls()

    def set_transition_surface(self, color=(0, 0, 0)):
        self.transition_surface = pygame.Surface(self.client.screen.get_size())
        self.transition_surface.fill(color)

    def fullscreen_animations(self, surface):
        """Handles fullscreen animations such as transitions, cutscenes, etc.

        :param surface: Surface to draw onto

        :rtype: None
        :returns: None

        """
        if self.in_transition:
            self.transition_surface.set_alpha(self.transition_alpha)
            surface.blit(self.transition_surface, (0, 0))

    def get_pos_from_tilepos(self, tile_position):
        """ Return the screen pixel coordinate based on tile position

        :param List tile_position: An [x, y] tile position.
        :rtype: Tuple[int, int]
        """
        cx, cy = self.renderer.get_center_offset()
        px, py = self.project(tile_position)
        x = px + cx
        y = py + cy
        return x, y

    def project(self, position):
        return position[0] * self.tilewidth, position[1] * self.tileheight

    def _collision_box_to_pgrect(self, box):
        """Return a Rect (in screen-coords) version of a collision box (in world-coords).
        """
        x, y = self.get_pos_from_tilepos(box)
        return Rect(x, y, self.tilewidth, self.tileheight)

    def _npc_to_pgrect(self, npc):
        """ Return a Rect (in screen-coords) version of an NPC's bounding box.
        """
        x, y = self.get_pos_from_tilepos(npc.tile_pos)
        return Rect(x, y, self.tilewidth, self.tileheight)

"""

Anything that is rendered to the screen is handled here.
Any visual representation of a game object should be handled here.

"""
import os
from typing import List, Tuple

import pygame
import pyscroll

import tuxemon.npc
from tuxemon import prepare, pyganim
from tuxemon.compat import Rect
from tuxemon.graphics import load_and_scale
from tuxemon.map import facing
from tuxemon.prepare import CONFIG
from tuxemon.tools import nearest

# reference direction and movement states to animation names
animation_mapping = {
    True: {
        "up": "back_walk",
        "down": "front_walk",
        "left": "left_walk",
        "right": "right_walk",
    },
    False: {"up": "back", "down": "front", "left": "left", "right": "right"},
}


class MapSprite:
    """
    Graphic representation of game objects

    MapSprites contain PyGanim aminations, directions, and static images
    MapSprites can be reused for other game entities if they look the same
    MapSprites currently just handle NPC objects
    Game entities should not represent themselves
    More game objects should be represented by MapSprites overtime
    MapSprites are related to, but not the same same pygame Sprites

    """

    def __init__(self, sprite_name: str):
        self.sprite_name = sprite_name
        self.standing = dict()
        self.sprite = dict()
        self.moveConductor = pyganim.PygConductor()
        self.last_animation_state = None

    def load_sprites(self):
        """
        Load sprite graphics

        """
        # Get all of the standing animation images
        self.standing = {}
        for standing_type in facing:
            filename = f"{self.sprite_name}_{standing_type}.png"
            path = os.path.join("sprites", filename)
            self.standing[standing_type] = load_and_scale(path)

        # avoid cutoff frames when steps don't line up with tile movement
        frames = 3
        frame_duration = (1000 / CONFIG.player_walkrate) / frames / 1000 * 2

        # Load all of the player's sprite animations
        anim_types = ["front_walk", "back_walk", "left_walk", "right_walk"]
        for anim_type in anim_types:
            images = [
                "sprites/{}_{}.{}.png".format(self.sprite_name, anim_type, str(num).rjust(3, "0")) for num in range(4)
            ]

            frames = []
            for image in images:
                surface = load_and_scale(image)
                frames.append((surface, frame_duration))

            self.sprite[anim_type] = pyganim.PygAnimation(frames, loop=True)

        self.moveConductor.add(self.sprite)

    def get_current_npc_surface(
            self,
            npc: tuxemon.npc.NPC,
            layer: int
    ) -> List[pygame.surface.Surface]:
        """
        Get the surfaces and layers for the sprite

        Parameters:
            npc: The npc object.
            layer: The layer to draw the sprite on.

        """
        def get_frame(d, ani):
            frame = d[ani]
            try:
                surface = frame.getCurrentFrame()
                frame.rate = npc.moverate / CONFIG.player_walkrate
                return surface
            except AttributeError:
                return frame

        if self.last_animation_state != npc.animation:
            self.last_animation_state = npc.animation
            if npc.animation == "idle":
                self.moveConductor.stop()
            else:
                self.moveConductor.play()

        frame_dict = self.sprite if npc.moving else self.standing
        state = animation_mapping[npc.moving][npc.facing]
        return [(get_frame(frame_dict, state), npc.tile_pos, layer)]


class SpriteCache:
    """
    Cache seen sprites.

    Currently memory is never freed.

    """
    def __init__(self):
        self.sprites = dict()

    def get(self, slug: str) -> MapSprite:
        """
        Return MapSprite for the slug

        """
        try:
            return self.sprites[slug]
        except KeyError:
            sprite = MapSprite(slug)
            sprite.load_sprites()
            self.sprites[slug] = sprite
            return sprite


class MapView:
    """
    Render a map, npcs, etc

    use `follow()` to keep the camera on a game object/npc

    """
    def __init__(self, world: tuxemon.world.World):
        """
        Constructor

        Parameters:
            world: World to draw.

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

        self.transition_alpha = 0
        self.transition_surface = None
        self.in_transition = False

    def follow(self, entity):
        self.tracked_entity = entity

    def draw(self, surface, rect=None):
        """Draw the view

        :param Surface surface: Target surface
        :param Rect rect: Area to draw to
        """
        if rect is None:
            rect = surface.get_rect()

        # TODO: make less awkward
        if self.tracked_entity is not None:
            gamemap = self.world.get_map_for_entity(self.tracked_entity)
            if gamemap != self._current_map:
                self.renderer = None
            if self.renderer is None:
                filename = prepare.fetch("maps", gamemap.name)
                self.renderer = self.initialize_map_renderer(rect.size, filename)
                self._current_map = gamemap

        if self.renderer:
            self.center_on_entity(self.tracked_entity)
            world_surfaces = self.get_world_surfaces(gamemap)
            screen_surfaces = self.project_world_surfaces(rect, world_surfaces)
            self.renderer.draw(surface, rect, screen_surfaces)

    def center_on_entity(self, entity):
        # get tracked npc coords to center map
        cx, cy = nearest(self.project(entity.tile_pos))
        cx += self.tilewidth // 2
        cy += self.tileheight // 2
        self.renderer.center((cx, cy))

    def get_world_surfaces(self, gamemap):
        """Return list of surfaces in world coordinates

        each item is (surface, tile_position, layer)
        tile position is (x, y), where each is a float

        :param gamemap:
        :return:
        """
        world_surfaces = list()
        # npcs and other entities
        for npc in self.world.get_entities_on_map(gamemap.name):
            sprite = self.sprites.get(npc.sprite_name)
            surfaces = sprite.get_current_npc_surface(npc, self.sprite_layer)
            world_surfaces.extend(surfaces)
        # "map animations"
        for anim_data in self.map_animations.values():
            anim = anim_data["animation"]
            if not anim.isFinished() and anim.visibility:
                frame = (
                    anim.getCurrentFrame(),
                    anim_data["position"],
                    anim_data["layer"],
                )
                world_surfaces.append(frame)
        return world_surfaces

    def project_world_surfaces(self, screen_rect, world_surfaces):
        screen_surfaces = list()
        left = screen_rect.left
        top = screen_rect.top
        for frame in world_surfaces:
            s, c, l = frame
            c = self.get_pos_from_tilepos(c)
            # TODO: better handling of tall sprites
            h = s.get_height()
            if h > self.tileheight:
                # offset for center and image height
                c = nearest((c[0], c[1] - h // 2))
            c = c[0] + left, c[1] + top
            # TODO: filter the off-screen sprites so they are not drawn
            screen_surfaces.append((s, c, l))
        return screen_surfaces

    def initialize_map_renderer(self, size, map_name):
        """Initialize the renderer for the map and sprites

        :param Tuple[int, int] size: size of rendered area on the screen
        :param str map_name:
        """
        map_object = self.world.get_map(map_name)
        visual_data = pyscroll.data.TiledMapData(map_object.data)
        self.sprite_layer = int(map_object.data.properties.get("sprite_layer", 2))
        self.tilewidth, self.tileheight = prepare.TILE_SIZE
        self.map_animations = dict()
        return pyscroll.BufferedRenderer(visual_data, size, clamp_camera=map_object.clamped, tall_sprites=2)

    def load_map(self, path: str) -> TuxemonMap:
        """
        Returns map data as a dictionary to be used for map changing.

        Parameters:
            path: Path of the map to load.

        Returns:
            Loaded map.

        """
        txmn_map = TMXMapLoader().load(path)
        yaml_path = path[:-4] + ".yaml"
        # TODO: merge the events from both sources
        if os.path.exists(yaml_path):
            new_events = list(txmn_map.events)
            new_events.extend(YAMLEventLoader().load_events(yaml_path))
            txmn_map.events = new_events
        return txmn_map

    def fade_and_teleport(self, duration=2):
        """Fade out, teleport, fade in

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
        task.chain(fade_in, duration + 0.5)

    def trigger_fade_in(self, duration=2):
        """World state has own fade code b/c moving maps doesn't change state

        :returns: None
        """
        self.set_transition_surface()
        self.animate(self, transition_alpha=0, initial=255, duration=duration, round_values=True)
        self.task(self.unlock_controls, duration - 0.5)

    def trigger_fade_out(self, duration=2):
        """World state has own fade code b/c moving maps doesn't change state

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

    def get_pos_from_tilepos(
            self,
            tile_position: Tuple[int, int],
    ) -> Tuple[int, int]:
        """
        Returns the map pixel coordinate based on tile position.

        Parameters:
            tile_position: An [x, y] tile position.

        Returns:
            The pixel coordinates to draw at the given tile position.

        """
        cx, cy = self.renderer.get_center_offset()
        px, py = self.project(tile_position)
        x = px + cx
        y = py + cy
        return x, y

    def project(self, tile_position: Tuple[int, int]) -> Tuple[int, int]:
        """
        Return pixel position of tile position

        Parameters:
            tile_position: A (x, y) tile position.

        """
        return (
            tile_position[0] * self.tilewidth,
            tile_position[1] * self.tileheight,
        )

    def _collision_box_to_pgrect(
            self,
            tile_position: Tuple[int, int],
    ) -> pygame.rect.Rect:
        """
        Return a Rect (in screen-coords) version of a collision box (in world-coords)

        Parameters:
            tile_position: A (x, y) tile position.

        """
        x, y = self.get_pos_from_tilepos(tile_position)
        return Rect(x, y, self.tilewidth, self.tileheight)

    def _npc_to_pgrect(self, npc) -> pygame.rect.Rect:
        """
        Return a Rect (in screen-coords) version of an NPC's bounding box

        Parameters:
            npc: NPC to get rect from.

        """
        x, y = self.get_pos_from_tilepos(npc.tile_pos)
        return Rect(x, y, self.tilewidth, self.tileheight)

    ####################################################
    #                Debug Drawing                     #
    ####################################################
    def debug_drawing(self, surface: pygame.surface.Surface) -> None:
        from pygame.gfxdraw import box

        surface.lock()

        # draw events
        for event in self.client.events:
            topleft = self.get_pos_from_tilepos((event.x, event.y))
            size = self.project((event.w, event.h))
            rect = topleft, size
            box(surface, rect, (0, 255, 0, 128))

        # We need to iterate over all collidable objects.  So, let's start
        # with the walls/collision boxes.
        box_iter = map(self._collision_box_to_pgrect, self.collision_map)

        # Next, deal with solid NPCs.
        npc_iter = map(self._npc_to_pgrect, self.npcs.values())

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

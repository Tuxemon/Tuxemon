"""

Create mapping between tilesets for migrations

duct tape.

* Run with a source tileset, destination, and the output filename.
* The current tile to map *from* is a highlighted with a red box
* Click the matching time on the destination side, the cursor will advance
* Use the arrow arrows to move the cursor
* File is saved after each click
* The mapping can be verified visually

Example:

python scripts/make_map_migration.py mods/tuxemon/gfx/tilesets/My_tuxemon_sheet.png mods/tuxemon/gfx/tilesets/core_outdoor.png txmn-core.yaml

"""
import click
import pygame
import pygame.gfxdraw
import yaml


tilewidth = 16
tileheight = 16
preview_scale_factor = 15
screen_width = 1920
screen_height = 1080
hover_color = 64, 128, 200, 128
current_tile_color = 255, 64, 64, 200


def get_hover_rect(rect, pos):
    if rect.collidepoint(pos):
        x = ((pos[0] - rect.left) // tilewidth) * tilewidth
        y = ((pos[1] - rect.top) // tileheight) * tileheight
        surf_rect = x, y, tilewidth, tileheight
        screen_rect = (x + rect.left, y + rect.top, tilewidth, tileheight)
        return pygame.Rect(screen_rect), pygame.Rect(surf_rect)


def get_tile_by_index(rect, index):
    y, x = divmod(index * tilewidth, rect.width)
    y *= tileheight
    screen_rect = x + rect.left, y + rect.top, tilewidth, tileheight
    surf_rect = x, y, tilewidth, tileheight
    return pygame.Rect(screen_rect), pygame.Rect(surf_rect)


def main(src_filepath, dst_filepath, output_filepath):
    src = pygame.image.load(src_filepath)
    dst = pygame.image.load(dst_filepath)
    dst_rect = dst.get_rect()
    dst_rect.right = screen_width
    src_rect = src.get_rect()
    src_rect.left = screen_width // 2
    tiles_per_row = src_rect.width // tilewidth
    total_tiles = (tiles_per_row * (src_rect.height // tileheight)) - 1
    preview_tile_size = tilewidth * preview_scale_factor, tileheight * preview_scale_factor
    screen = pygame.display.set_mode((screen_width, screen_height))
    hover = None
    running = True
    src_index = 0

    try:
        with open(output_filepath, "r") as fp:
            mapping = yaml.load(fp, yaml.SafeLoader)
    except FileNotFoundError:
        mapping = dict()

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.MOUSEMOTION:
                for source, rect in [(dst, dst_rect), (src, src_rect)]:
                    hover_ = get_hover_rect(rect, e.pos)
                    if hover_:
                        screen_rect, surf_rect = hover_
                        hover = source, screen_rect, surf_rect
                        break
                else:
                    hover = None

            if e.type == pygame.MOUSEBUTTONDOWN:
                if hover:
                    source, screen_rect, surf_rect = hover
                    y = (surf_rect[1] // tileheight) * (dst_rect.width // tilewidth)
                    dst_index = (surf_rect[0] // tilewidth) + y
                    with open(output_filepath, "w") as fp:
                        yaml.dump(mapping, fp, yaml.SafeDumper)
                    mapping[src_index] = dst_index
                    src_index = min(total_tiles, src_index + 1)

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT:
                    src_index = max(0, src_index - 1)
                elif e.key == pygame.K_RIGHT:
                    src_index = min(total_tiles, src_index + 1)
                elif e.key == pygame.K_UP:
                    src_index = max(0, src_index - tiles_per_row)
                elif e.key == pygame.K_DOWN:
                    src_index = min(total_tiles, src_index + tiles_per_row)
                dst_index = mapping.get(src_index)
                if dst_index is None:
                    hover = None
                else:
                    screen_rect, surf_rect = get_tile_by_index(dst_rect, dst_index)
                    hover = dst, screen_rect, surf_rect

        screen.fill(0)
        screen.blit(dst, dst_rect)
        screen.blit(src, src_rect)

        screen_rect, surf_rect = get_tile_by_index(src_rect, src_index)
        surf = src.subsurface(surf_rect)
        surf = pygame.transform.scale(surf, preview_tile_size)
        screen.blit(surf, (0, 0))
        pygame.gfxdraw.rectangle(screen, screen_rect, current_tile_color)

        if mapping:
            for i0, i1 in mapping.items():
                screen_rect0, surf_rect0 = get_tile_by_index(src_rect, i0)
                screen_rect1, surf_rect1 = get_tile_by_index(dst_rect, i1)
                screen_rect0.x = surf_rect0.x + (tilewidth * (preview_scale_factor + 4))
                surf = dst.subsurface(surf_rect1)
                screen.blit(surf, screen_rect0)

        if hover is not None:
            source, screen_rect, surf_rect = hover
            if source == dst:
                surf = dst.subsurface(surf_rect)
                surf = pygame.transform.scale(surf, preview_tile_size)
                screen.blit(surf, (0, tileheight * (preview_scale_factor + 2)))
            pygame.gfxdraw.box(screen, screen_rect, hover_color)

        pygame.display.flip()


@click.command()
@click.argument("source")
@click.argument("destination")
@click.argument("output")
def click_shim(source, destination, output):
    main(source, destination, output)


if __name__ == "__main__":
    click_shim()

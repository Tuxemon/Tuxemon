"""

Compare all tiles in all tilesets and try to remove extra tiles.

The concept is to consolidate tilesets.

There is a hardcoded list of priority for tilesets, be sure to update it.  This will
determine which tileset keeps the tile.

prereqs: PIL numpy

"""
import dataclasses
import logging
from collections import defaultdict
from itertools import combinations

import click
import imagehash
import numpy
import pygame
import pytmx
from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageFont
from PIL.ImageFont import TransposedFont
from imagehash import ImageHash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

tileset_priority = ["core_outdoor"]


@dataclasses.dataclass
class TileImageToken:
    image: Image
    hash: ImageHash
    bytes: str
    gid: int
    rgb: Image
    local_id: int
    flags: pytmx.TileFlags
    tileset: pytmx.TiledTileset

    def __repr__(self):
        return f"<TileImageToken {self.tileset}: {self.local_id}::{self.gid}>"


def image_hash_loader(filename, colorkey, **kwargs):
    image = Image.open(filename)
    ts = kwargs.get("tileset")

    def load_image(rect=None, flags=None):
        if rect:
            try:
                rectP = pygame.Rect(rect)
                left = rectP.x
                top = rectP.y
                right = rectP.x + rectP.width
                bottom = rectP.y + rectP.height
                tile = image.crop((left, top, right, bottom))
                tile = tile.copy()

            except SystemError:
                logger.error('Tile bounds outside bounds of tileset image')
                raise
        else:
            tile = image.copy()

        if flags:
            if any((flags.flipped_horizontally, flags.flipped_vertically, flags.flipped_diagonally)):
                raise Exception("Cannot process transformed tiles")

        # get byte string and hash
        comp = tile.convert("RGB")
        pixels = numpy.asarray(comp)
        bit_string = ''.join(str(b) for b in 1 * pixels.flatten())
        diff = pixels[:, 1:] > pixels[:, :-1]
        hash = ImageHash(diff)

        return TileImageToken(
            image=tile,
            bytes=bit_string,
            hash=hash,
            flags=flags,
            rgb=comp,
            gid=0,
            local_id=0,
            tileset=ts
        )

    return load_image


def process_tmxmap(filename):
    """

    kinda a hack.  pytmx cannot save map changes so we accumulate the changes, then
    rewrite the xml with the required changes.

    not written to be fast
    tile rotations not supported...yet

    """
    data = pytmx.TiledMap(filename, image_loader=image_hash_loader, load_all=True)

    # update gid/local_gid
    all_tokens = list()
    for i, token in enumerate(data.images):
        if token:
            gid = data.tiledgidmap[i]
            token.gid = gid
            token.local_id = gid - token.tileset.firstgid
            all_tokens.append(token)

    draw_guide(all_tokens)



def draw_guide(all_tokens):

    # classify loose fit
    similar = buckit(all_tokens, "hash")

    y = 0
    output = Image.new("RGBA", (8096, 12800))
    draw = ImageDraw.Draw(output)
    font = ImageFont.load_default()
    # font = TransposedFont(ImageFont.load_default(), 45)

    tile_width = 16
    tile_height = 16
    scale = 2
    spacing_x = 0
    spacing_y = 2

    for similar_tiles in similar:
        variations = [group[0] for group in buckit(similar_tiles, "bytes")]
        if len(variations) > 1:

            # show them all together for context
            x = 0
            for tile in variations:
                scaled = ImageOps.scale(tile.image, scale, Image.NEAREST)
                output.paste(scaled, (x, y))
                draw.text((x+ 8, y), tile.tileset.name, font=font)
                x += scaled.width + spacing_x

            draw.line((x + 8, y, x + 8, y + 16), fill=(0, 0, 0, 255))

            # show them with differences
            x += tile_width
            for tile0, tile1 in combinations(variations, 2):
                diff = ImageChops.difference(tile0.image, tile1.image)
                diff = diff.convert("RGB")
                diff = ImageOps.autocontrast(diff)
                # diff = ImageOps.invert(diff)
                # diff = diff.convert("L")

                # tile 1
                scaled = ImageOps.scale(tile0.image, scale, Image.NEAREST)
                output.paste(scaled, (x, y))
                draw.text((x + 8, y), tile0.tileset.name, font=font)
                x += scaled.width

                # tile 2
                scaled = ImageOps.scale(tile1.image, scale, Image.NEAREST)
                output.paste(scaled, (x, y))
                draw.text((x+ 8 , y), tile1.tileset.name, font=font)
                x += scaled.width

                # difference
                scaled = ImageOps.scale(diff, scale, Image.NEAREST)
                output.paste(scaled, (x, y))
                x += scaled.width

                # draw.line((x + 56, y, x + 56, y + 16), fill=(0, 0, 0, 255))
                x += 64

            y += (tile_height * scale) + spacing_y

    output.save("dupes.png")


def buckit(tokens, cmp):
    scratch = defaultdict(list)
    for token in tokens:
        key = getattr(token, cmp)
        scratch[key].append(token)
    return scratch.values()


@click.command()
@click.argument("filenames", nargs=-1)
def click_shim(filenames):
    for filename in filenames:
        process_tmxmap(filename)


if __name__ == "__main__":
    click_shim()

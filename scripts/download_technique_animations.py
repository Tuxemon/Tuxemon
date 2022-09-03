"""
Download wiki .gifs and save as single frame png files

1. Run
2. Inspect
3. Copy

If the file names have changed from the wiki, the technique
json files will need to be updated as well.
"""
from urllib.parse import urljoin
import os.path

import requests
from PIL import Image
from lxml import etree, html

FRAME_SIZE = 64
WIKI_URL = "https://wiki.tuxemon.org"

# TODO: Not needed anymore?
# WIKI_ANIMATIONS_URL = "f{WIKI_URL}/index.php?title=Category:Technique_Animation"

# animation CREDITS entry format
# * ["Tentacles Water"](https://wiki.tuxemon.org/File:Tentacles_water.gif) By daneeklu, adapted by Sanglorian for 64x64pxThunderstrike | https://wiki.tuxemon.org/File:Thunderstrike.gif | Unknown
# * ["Bite Zombie"](https://wiki.tuxemon.org/File:Bite_zombie.gif) is by https://opengameart.org/content/bite
# * ["12 Hits For Sepearation"](https://wiki.tuxemon.org/File:12_hits_for_separation.gif) CC BY on OGA This work, made by Viktor Hahn (Viktor.Hahn@web.de), is licensed under the Creative Commons Attribution 4.0 International License. http://creativecommons.org/licenses/by/4.0/

# Scraping JS-generated web content with selenium, beautiful soup and phantom js
# https://stackoverflow.com/a/36289608




# TODO: Is the return here needed or should be boolean to indicate success/fail?
def download_bytes(url: str, filename: str) -> str:
    """Downloads a stream of bytes from a given URL to a file defined by 'filename'."""
    req = requests.get(url)
    with open(filename, "wb") as fp:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                fp.write(chunk)
    return filename


def process_filename(filename: str) -> str:
    """Extract base filename from an animation file path."""
    cleaned_filename = os.path.splitext(filename)[0]
    cleaned_filename = cleaned_filename.strip("0123456789_")
    cleaned_filename = cleaned_filename.lower()
    return cleaned_filename


def gif_to_frames(filename: str) -> None:
    """Extract individual animation frames as PNG from a GIF."""
    with Image.open(filename) as image:
        if not image.is_animated:
            print(f"{filename} is not animated, skipped")
            return
        if not image.width == image.height == FRAME_SIZE:
            print(f"{filename} is not {FRAME_SIZE}x{FRAME_SIZE}, skipped")
            return
        base_name = process_filename(filename)
        for frame in range(0, image.n_frames):
            frame_filename = f"{base_name}{frame:02}.png"
            print(f"saving {filename}:{frame_filename} {frame}/{image.n_frames - 1}")
            image.seek(frame)
            image.save(frame_filename, optimize=True)


# TODO: Is passing the Wiki URL needed?
def download_technique_animations(wiki_url: str) -> None:
    """Download technique animation frames from the Tuxemon Wiki."""
    print(f"Getting animations and metadata from URL: {wiki_url}")
    animations_url = f"{wiki_url}/index.php?title=Category:Technique_Animation"

    # Animation GIF path
    source = requests.get(animations_url)
    tree = html.fromstring(source.content)

    elements = tree.xpath("//li[@class='gallerybox']//a[@class='image']")
    for index, element in enumerate(elements, start=1):
        # Download animation GIF and convert to frame PNGs
        # TODO: Store frames in correct location and gif only in temporary path?
        gif_url = urljoin(animations_url, element[0].get("src"))
        filename = gif_url.split('/')[-1]
        print(f"{index}/{len(elements)} downloading {filename}")
        download_bytes(gif_url, filename)
        gif_to_frames(filename)

        # Download credits
        gif_sub_url = urljoin(wiki_url, element.get("href"))


if __name__ == "__main__":
    download_technique_animations(WIKI_URL)

    pass
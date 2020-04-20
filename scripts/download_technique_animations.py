"""
Download wiki .gifs and save as single frame png files

1. Run
2. Inspect
3. Copy

If the file names have changed from the wiki, the technique
json files will need to be updated as well.
"""
from urllib.parse import urljoin

import requests
from PIL import Image
from lxml import html


def download(url, filename):
    req = requests.get(url)
    with open(filename, "wb") as fp:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                fp.write(chunk)
    return filename


def process_filename(filename):
    filename = filename[:-4]
    filename = filename.strip("0123456789_")
    filename = filename.lower()
    return filename


def process_gif(filename):
    image = Image.open(filename)
    if not image.is_animated:
        print("...not animated, skipped")
        return
    if not image.width == image.height == 64:
        print("...is not 64x64, skipped")
        return
    base_name = process_filename(filename)
    for frame in range(0, image.n_frames):
        frame_filename = f"{base_name}{frame:02}.png"
        print(f"saving {filename}:{frame_filename} {frame}/{image.n_frames - 1}")
        image.seek(frame)
        image.save(frame_filename, optimize=True)


def download_technique_animations(wiki_url):
    print("getting page source...")
    source = requests.get(wiki_url)
    tree = html.fromstring(source.content)
    elements = tree.xpath("//li[@class='gallerybox']//img")

    for index, element in enumerate(elements, start=1):
        url = urljoin(wiki_url, element.get("src"))
        filename = url.split('/')[-1]
        print(f"{index}/{len(elements)} downloading {filename}")
        download(url, filename)
        process_gif(filename)


if __name__ == "__main__":
    wiki_url = "https://wiki.tuxemon.org/index.php?title=Category:Technique_Animation"
    download_technique_animations(wiki_url)

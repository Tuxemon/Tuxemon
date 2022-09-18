"""
Download wiki .gifs and save as single frame png files

1. Run
2. Inspect
3. Copy

If the file names have changed from the wiki, the technique
json files will need to be updated as well.
"""
import os.path
import pathlib
import tempfile
from urllib.parse import urljoin

import requests
from lxml import html
from PIL import Image

WIKI_URL = "https://wiki.tuxemon.org"

TUXEMON_ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
ANIMATION_DIR = TUXEMON_ROOT_DIR.joinpath(
    pathlib.Path("mods/tuxemon/animations/technique")
)
CREDITS_TEMPLATE = """* ["{animation_name}"]({animation_url})
{credits_text}"""
CREDITS_FILENAME = "TECHNIQUE_ANIMATION_CREDITS.md"

print("Tuxemon project root dir:", TUXEMON_ROOT_DIR)
print("Technique animation dir:", ANIMATION_DIR)


def download_bytes(url: str, filepath: str) -> bool:
    """
    Downloads a stream of bytes from a given URL to a file path.
    
    Returns:
        True on successful byte stream download, False otherwise
    """
    if os.path.isfile(filepath):
        filename = os.path.basename(filepath)
        print(f"Aborting download! Animation GIF file already exists: {filename}")
        return False

    req = requests.get(url)
    with open(filepath, "wb") as fp:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                fp.write(chunk)
    return True


def process_filename(filepath: str) -> str:
    """Extract base filename from an animation file path."""
    cleaned_filename = os.path.splitext(os.path.basename(filepath))[0]
    cleaned_filename = cleaned_filename.lower()
    return cleaned_filename


def process_animation_name(filename: str) -> str:
    """Convert filename of format 'file_name' to a capitalized 'File Name' animation name/title."""
    animation_name = " ".join(
        [name_part.capitalize() for name_part in filename.split("_")]
    )
    return animation_name


def download_animation_credits(gif_page_url: str) -> str:
    """Extract credits text from a GIF animation subpage, from the 'Comments' section."""
    gif_filename = gif_page_url.split("File:")[-1]
    animation_name = process_animation_name(process_filename(gif_filename))

    gifpage_source = requests.get(gif_page_url)
    gifpage_tree = html.fromstring(gifpage_source.content)
    credits_blocks = gifpage_tree.xpath("//div[@class='mw-content-ltr']/div/p")
    
    credits_text = ""
    for credits_row in credits_blocks:
        credits_text += credits_row.text.strip() if credits_row.text else ""

        # Sometimes the credits text has an extra license URL, a link to the original project
        # or is placed after a <br> block
        for credits_line in credits_row:
            if credits_line.tag == "a":
                credits_text += f" [source link]({credits_line.get('href')})"
            elif credits_line.tag == "br" and not credits_row.text:
                credits_text += credits_line.tail.strip()

    credits_text = credits_text or "Unknown animation source/author"
    credits_record = CREDITS_TEMPLATE.format(
        animation_name=animation_name,
        animation_url=gif_page_url,
        credits_text=credits_text,
    )
    return credits_record


def gif_to_frames(filepath: str) -> None:
    """Extract individual animation frames as PNG from a GIF."""
    with Image.open(filepath) as image:
        if not image.is_animated:
            print(f"{filepath} is not animated, skipped")
            return

        base_name = process_filename(filepath)
        animation_name = process_animation_name(base_name)
        for frame in range(0, image.n_frames):
            frame_filename = os.path.join(
                ANIMATION_DIR, f"{base_name}_{frame:02}.png"
            )
            print(
                f"Generating animation frames for '{animation_name}': {frame_filename} - {frame}/{image.n_frames - 1}"
            )
            image.seek(frame)
            image.save(frame_filename, optimize=True)


# TODO: Is passing the Wiki URL needed?
def download_technique_animations(wiki_url: str) -> None:
    """Download technique animation frames from the Tuxemon Wiki."""
    print(f"Getting animations and metadata from URL: {wiki_url}")

    # Animation GIF path
    animations_url = f"{wiki_url}/index.php?title=Category:Used_Technique_Animation"
    anim_source = requests.get(animations_url)
    anim_tree = html.fromstring(anim_source.content)

    with tempfile.TemporaryDirectory() as tmp_dirname:

        elements = anim_tree.xpath(
            "//li[@class='gallerybox']//a[@class='image']"
        )
        with open(CREDITS_FILENAME, "w") as credits_file:
            print("### Technique Animations", file=credits_file)
            print("", file=credits_file)
            for index, element in enumerate(elements, start=1):
                # Download animation GIF and convert to frame PNGs
                gif_url = urljoin(animations_url, element[0].get("src"))
                filename = gif_url.split("/")[-1]
                print(
                    f"Downloading animation [{index}/{len(elements)}] - {filename}"
                )

                temppath = os.path.join(tmp_dirname, filename)

                # Don't proceed if the animation gif couldn't be downloaded or already exists
                if not download_bytes(gif_url, temppath):
                    continue

                gif_to_frames(temppath)

                # Download credits from GIF subpage URL
                print(
                    f"Downloading animation credits [{index}/{len(elements)}] - {filename}"
                )
                gif_page_url = urljoin(wiki_url, element.get("href"))
                credits_record = download_animation_credits(gif_page_url)
                print(credits_record, file=credits_file)
                print("", file=credits_file)


if __name__ == "__main__":
    download_technique_animations(WIKI_URL)

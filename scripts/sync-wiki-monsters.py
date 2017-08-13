#!/usr/bin/python
# Downloads all the monsters from the wiki and
# creates monsters and their sprites.

from __future__ import print_function
from lxml import html
from pprint import pprint
import requests
import shutil

user_agent = {'User-agent': 'Mozilla/5.0'}
tuxepedia = "https://wiki.tuxemon.org"
monsters_xpath = '//*[@id="mw-content-text"]/table[1]/tr[1]/td[1]/table'
sprites_path = './tmp/'

def wget(url, params):
    page = requests.get(url, headers=user_agent, params=params)
    tree = html.fromstring(page.content)
    return tree

def download(url, to_path):
    print("Downloading image: " + url)
    response = requests.get(url, stream=True)
    with open(to_path, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response

def get_monsters():
    monsters = {}
    monsters_tree = wget(tuxepedia, {"title": "Creature_Progress_Tracker"})
    table = monsters_tree.xpath(monsters_xpath)[0]

    # Loop through all the rows in the table. We specify "tr" to ensure
    # we're only looking for rows, not headings.
    for monster_tr in table.findall("tr"):

        # Loop through all the columns for each monster
        monster_i = 0
        for td in monster_tr:
            # The first column is the monster name.
            if monster_i == 0:
                name = get_monster_name(td).encode('utf8')
                print("Fetching data for: {}".format(name))

                # Set our monster name and url
                monsters[name] = {"url": get_monster_url(td)}

            # The third column is the monster's types.
            if monster_i == 2:
                print("  Fetching types...")
                monsters[name]["types"] = get_monster_types(td)

            # The fourth column is the monster's front sprite.
            if monster_i == 3:
                print("  Fetching front sprite...")
                monsters[name]["front"] = get_monster_sprite(td)

            # The fifth column is the monster's back sprite.
            if monster_i == 4:
                print("  Fetching back sprite...")
                monsters[name]["back"] = get_monster_sprite(td)

            # The sixth column is the monster's first face sprite.
            if monster_i == 5:
                print("  Fetching face sprite 1...")
                monsters[name]["menu1"] = get_monster_sprite(td)

            # The seventh column is the monster's second face sprite.
            if monster_i == 6:
                print("  Fetching face sprite 2...")
                monsters[name]["menu2"] = get_monster_sprite(td)

            # The eigth column is the monster's blurb.
            if monster_i == 7:
                print("  Fetching blurb...")
                monsters[name]["blurb"] = get_monster_name(td)

            # The ninth column is the monster's call sound.
            if monster_i == 8:
                print("  Fetching blurb...")
                monsters[name]["call"] = get_monster_url(td)

            monster_i += 1

    pprint(monsters)

    return monsters

def get_monster_name(td):
    name = td.text_content()
    return name

def get_monster_url(td):
    links = td.findall("a")
    for el in links:
        url = el.get("href")
        if "Missing" in url:
            return None
        return url

def get_monster_types(td):
    types = []
    links = td.findall("a")
    for el in links:
        types.append(el.text_content())

    return types

def get_monster_sprite(td):
    links = td.findall("a")
    for link in links:
        image = link.find('img')
        return image.get("src")

def is_valid_monster(name, monster):
    if "(" in name:
        return False
    if not monster["front"]:
        return False
    if not monster["back"]:
        return False
    if not monster["menu1"]:
        return False
    if not monster["menu2"]:
        return False
    if not monster["types"]:
        return False

    return True

def download_sprites(name, monster):
    # Do nothing if the monster doesn't have a complete sprite set.
    if not is_valid_monster(name, monster):
        return

    # Download the front sprite
    ext = get_extension(monster["front"])
    filename = name.lower() + "-front." + ext
    url = tuxepedia + monster["front"]
    download(url, sprites_path + filename)

    # Download the back sprite
    ext = get_extension(monster["back"])
    filename = name.lower() + "-back." + ext
    url = tuxepedia + monster["back"]
    download(url, sprites_path + filename)

    # Download the menu1 sprite
    ext = get_extension(monster["menu1"])
    filename = name.lower() + "-menu01." + ext
    url = tuxepedia + monster["menu1"]
    download(url, sprites_path + filename)

    # Download the menu2 sprite
    ext = get_extension(monster["menu2"])
    filename = name.lower() + "-menu02." + ext
    url = tuxepedia + monster["menu2"]
    download(url, sprites_path + filename)

def get_extension(name):
    return name.split(".")[-1].lower()

if __name__ == "__main__":
    # Fetch all our monster data.
    monsters = get_monsters()

    # Download all our images.
    for name, monster in monsters.items():
        download_sprites(name, monster)

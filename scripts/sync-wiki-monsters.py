#!/usr/bin/python
# Downloads all the monsters from the wiki and
# creates monsters and their sprites.

from lxml import html
from pprint import pprint
import requests

user_agent = {'User-agent': 'Mozilla/5.0'}
tuxepedia = "https://wiki.tuxemon.org"
monsters_xpath = '//*[@id="mw-content-text"]/table[1]/tr[1]/td[1]/table'

def wget(url, params):
    page = requests.get(url, headers=user_agent, params=params)
    tree = html.fromstring(page.content)
    return tree

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

            monster_i += 1

    pprint(monsters)

    return monsters

def get_monster_name(td):
    name = td.text_content()
    return name

def get_monster_url(td):
    links = td.findall("a")
    for el in links:
        return el.get("href")

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


if __name__ == "__main__":
    get_monsters()

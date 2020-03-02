"""
from db.py
"""

if __name__ == "__main__":
    import pprint

    # SQLite3 way
    #monsters = Database()
    #monsters.load("resources/db/monster.db")
    #tuxemon = monsters.lookup("Bulbatux")
    #print(tuxemon)

    # JSON way
    db = JSONDatabase()
    db.load()

    pprint.pprint(db.lookup("Bulbatux"))
    #pprint.pprint(db.lookup(1))

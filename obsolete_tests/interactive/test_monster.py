"""
from monster.py
"""

if __name__ == "__main__":
    mytuxemon = Monster()
    mytuxemon.load_from_db("Bulbatux")
    mytuxemon.level = 5
    othertux = Monster()
    othertux.load_from_db("Bulbatux")
    othertux.level = 5

    pound_tech = Technique("Pound")
    poison_tech = Technique("Poison Sting")

    pprint.pprint(poison_tech.__dict__)

    #pound_tech.load("Pound")

    mytuxemon.learn(pound_tech)
    othertux.learn(poison_tech)

    mytuxemon.moves[0].use(user=mytuxemon, target=othertux)
    othertux.moves[0].use(user=othertux, target=mytuxemon)

    print("")
    print("MyTux")
    pprint.pprint(mytuxemon.__dict__)
    print("")
    print("OtherTux")
    pprint.pprint(othertux.__dict__)

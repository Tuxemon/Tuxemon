"""
from save.py
"""
if __name__ == "__main__":
    saveFile = shelve.open('saves/slot2.save')

    # Create save file
    saveFile['game_variables'] = {"battle_won": "yes"}
    saveFile['tile_pos'] = (1, 2)
    saveFile['inventory'] = []
    saveFile['current_map'] = "pallet_town-room.map"
    saveFile['player_name'] = "Blue"
    saveFile['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    saveFile.fade_out()

    # Load save file
    print(load(1))

    #print(player)

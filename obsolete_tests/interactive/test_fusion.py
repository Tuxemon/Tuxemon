"""
from fusion.py
"""

if __name__ == "__main__":
    #### EXAMPLES ####

    # Load the sprite data.
    bulbasaur = Body()
    bulbasaur.load('fusion/Bulbasaur.json')

    gyarados = Body()
    gyarados.load('fusion/Gyarados.json')

    # Fuse the sprites.
    fuse(body=bulbasaur, face=gyarados)
    fuse(body=gyarados, face=bulbasaur)
    #fuse(body=gyarados, face=geodude)
    #fuse(body=geodude, face=gyarados)
    #fuse(body=bulbasaur, face=geodude)
    #fuse(body=geodude, face=bulbasaur)


    # Save the sprite data to a file
    #bulbasaur.save()
    #gyarados.save()

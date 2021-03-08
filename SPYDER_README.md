# The Spyder in the Cathedral campaign 

The "spyder_" prefix identifies the maps and NPCs that belong to the Spyder in the Cathedral campaign.

Since the game is still being created, there are some concessions/work arounds: 

1. To play, start the game with argument -s spyder_bedroom.tmx, or rename the current player_house_bedroom.tmx file to something else, and then rename spyder_bedroom.tmx to player_house_bedroom.tmx.
2. In some parts you can walk on water since surfing hasn't been implemented yet. 
3. There's a different exit to the right of Drokoro since removing collisions hasn't been implemented yet. 
4. For some reason, random_encounter didn't work if it was triggered by behaviour "talk", so I've changed that to condition "to_talk". However, that's not present in my version of the game, so I can't test it.
5. Until there's the ability to pause player input, the campaign relies on players not moving during the scenes. 
6. Although I have a workaround for picking up items in the overworld, I might wait till the main solution is implemented. 
7. There's a couple of scenes where the text box cuts off the key speakers. Eventually I think being able to move the viewport is planned, which would address this. Otherwise perhaps a smaller text box?
8. The campaign talks about a "Spyder Bite" infection that's been spread, but there's no mechanics for it at this point.

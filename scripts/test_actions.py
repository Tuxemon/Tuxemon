"""
Script to validate map actions
"""
from unittest.mock import MagicMock

from tuxemon.constants import paths
from tuxemon.db import db
from tuxemon.event.eventaction import ActionManager
from tuxemon.event.eventcondition import ConditionManager
from tuxemon.event.eventengine import EventEngine
from tuxemon.map_loader import TMXMapLoader
from tuxemon.prepare import CONFIG
from tuxemon.session import Session

db.load("monster")
action = ActionManager()
condition = ConditionManager()
engine = EventEngine(Session(None, None, None), action, condition)
loader = TMXMapLoader()
loader.image_loader = MagicMock()

for mod_name in CONFIG.mods:
    for path in (paths.mods_folder / mod_name / "maps").glob("*.tmx"):
        txmn_map = loader.load(str(path))
        for event in txmn_map.events:
            for act in event.acts:
                if not engine.action_manager.get_action(act.type, act.parameters):
                    print(f"{path} failed")

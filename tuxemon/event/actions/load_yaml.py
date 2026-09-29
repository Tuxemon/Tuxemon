# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import final

from tuxemon.constants.asset_loader import fetch_asset
from tuxemon.event.eventaction import EventAction
from tuxemon.map.loader import YAMLEventLoader
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class LoadYamlAction(EventAction):
    """
    Loads the yaml file. It must be in the maps folder.

    Script usage:
        .. code-block::

            load_yaml file

    Script parameters:
        file: File to load.

    eg: "load_yaml file_yaml"
    """

    name = "load_yaml"
    file: str

    def start(self, session: Session) -> None:
        client = session.client
        yaml_path = Path(fetch_asset("maps", f"{self.file}.yaml"))

        _events = list(client.map_manager.events)
        _inits = list(client.map_manager.inits)
        if yaml_path.exists():

            yaml_events = YAMLEventLoader().load_events(yaml_path, "event")
            existing_names = {e.name for e in _events}
            for event in yaml_events["event"]:
                if event.name not in existing_names:
                    _events.append(event)
                    existing_names.add(event.name)

            yaml_inits = YAMLEventLoader().load_events(yaml_path, "init")
            existing_init_names = {e.name for e in _inits}
            for init_event in yaml_inits["init"]:
                if init_event.name not in existing_init_names:
                    _inits.append(init_event)
                    existing_init_names.add(init_event.name)

        else:
            raise ValueError(f"{yaml_path} doesn't exist")

        client.map_manager.set_events(_events)
        client.map_manager.set_inits(_inits)

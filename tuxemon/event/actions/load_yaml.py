# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.map_loader import YAMLEventLoader
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
        yaml_path = Path(prepare.fetch("maps", f"{self.file}.yaml"))

        _events = list(client.map_manager.events)
        _inits = list(client.map_manager.inits)
        if yaml_path.exists():
            yaml_events = YAMLEventLoader().load_events(
                yaml_path.as_posix(), "event"
            )
            _events.extend(yaml_events["event"])
            yaml_inits = YAMLEventLoader().load_events(
                yaml_path.as_posix(), "init"
            )
            _inits.extend(yaml_inits["init"])
        else:
            raise ValueError(f"{yaml_path} doesn't exist")

        client.map_manager.events = _events
        client.map_manager.inits = _inits

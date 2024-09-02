# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2024 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import final

from tuxemon import prepare
from tuxemon.event.eventaction import EventAction
from tuxemon.map_loader import YAMLEventLoader

logger = logging.getLogger(__name__)


@final
@dataclass
class LoadYamlAction(EventAction):
    """
    Loads the yaml file. It must be in the maps folder.

    Script usage:
        .. code-block::

            load_game file

    Script parameters:
        file: File to load.

    eg: "load_yaml file_yaml"

    """

    name = "load_yaml"
    file: str

    def start(self) -> None:
        client = self.session.client
        yaml_path = prepare.fetch("maps", f"{self.file}.yaml")

        _events = list(client.events)
        _inits = list(client.inits)
        if os.path.exists(yaml_path):
            yaml_events = YAMLEventLoader().load_events(yaml_path, "event")
            _events.extend(yaml_events["event"])
            yaml_inits = YAMLEventLoader().load_events(yaml_path, "init")
            _inits.extend(yaml_inits["init"])
        else:
            raise ValueError(f"{yaml_path} doesn't exist")

        client.events = _events
        client.inits = _inits

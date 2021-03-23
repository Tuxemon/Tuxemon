from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EventContext:
    engine: EventEngine
    world: World
    session: Session
    client: LocalPygameClient
    player: Player
    map: TuxemonMap
    name: str
    parameters: Any

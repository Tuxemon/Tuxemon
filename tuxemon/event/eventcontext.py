from __future__ import annotations

from dataclasses import dataclass
# from tuxemon.event.eventengine import EventEngine
# from tuxemon.session import Session


@dataclass
class EventContext:
    engine: EventEngine
    world: World
    session: Session
    client: LocalPygameClient
    player: Player
    map: TuxemonMap
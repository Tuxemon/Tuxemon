from tuxemon.core.event import get_npc
from tuxemon.core.event.conditions.position import entity_at_position
from tuxemon.core.event.eventcondition import EventCondition


class NPCAtCondition(EventCondition):
    """ Checks to see if an npc is at a current position on the map.
    """

    name = "npc_at"

    def test(self, context, event, condition):
        entity = get_npc(context, condition.parameters[0])
        return entity_at_position(entity, event)
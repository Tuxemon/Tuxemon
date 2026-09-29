# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2026 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from tuxemon.event.eventaction import EventAction
from tuxemon.session import Session

logger = logging.getLogger(__name__)


@final
@dataclass
class SetRoutingPolicyAction(EventAction):
    """
    Sets or resets the routing policy for future monster additions.
    This does not add a monster — it modifies how PartyHandler.add_monster behaves.

    Script usage:
        .. code-block::

            set_routing_policy <npc_slug>[,policy_name]

    Script parameters:
        npc_slug: NPC slug to apply the policy to.
        policy_name: Name of the routing policy defined in routing_policies.yaml.

    Examples:
        set_routing_policy player,starter_policy
        set_routing_policy player,event_policy
        set_routing_policy player  # resets to 'default'
    """

    name = "set_routing_policy"
    npc_slug: str
    policy_name: str | None = None

    def start(self, session: Session) -> None:
        trainer = session.client.get_npc(self.npc_slug)
        if not trainer:
            raise ValueError(f"NPC '{self.npc_slug}' not found")

        logger.debug(f"Setting routing policy for NPC '{self.npc_slug}'")

        policy_name = self.policy_name or "default"

        try:
            trainer.party.routing_policy_name = policy_name
            logger.debug(f"Routing policy set to '{policy_name}'")
        except ValueError as e:
            logger.error(str(e))
            raise ValueError(f"Failed to set routing policy: {e}")

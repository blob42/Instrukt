## 
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz>. All rights reserved.
## 
##  SPDX-License-Identifier: AGPL-3.0-or-later
## 
##  This file is part of Instrukt.
## 
##  This program is free software: you can redistribute it and/or modify it under
##  the terms of the GNU Affero General Public License as published by the Free
##  Software Foundation, either version 3 of the License, or (at your option) any
##  later version.
## 
##  This program is distributed in the hope that it will be useful, but WITHOUT
##  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
##  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
##  details.
## 
##  You should have received a copy of the GNU Affero General Public License along
##  with this program.  If not, see <http://www.gnu.org/licenses/>.
## 
"""Textual event handlers related to agents."""

import typing as t

from textual.message import Message

from ..agent.base import InstruktAgent
from ..agent.events import AgentEvents

__all__ = [
    'AgentMessage',
    'AgentLoaded',
    'AgentEvents',
]


class AgentMessage(Message, namespace="instrukt"):
    """Base agent events Message

    :param event: The event type
    :param data: Additional data
    """

    def __init__(self, event: AgentEvents, data: t.Any = None) -> None:
        if not isinstance(event, AgentEvents):
            raise ValueError(f"event must be an AgentEvents, got {event}")
        self.event = event
        self.data = data
        super().__init__()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.event})"

    def __str__(self):
        return f"{self.__class__.__name__}({self.event})"

    def __unicode__(self):
        return f"{self.__class__.__name__}({self.event})"


class AgentLoaded(AgentMessage, namespace="instrukt"):
    agent: InstruktAgent

    def __init__(self, agent: InstruktAgent) -> None:
        if not isinstance(agent, InstruktAgent):
            raise ValueError(f"agent must be an InstruktAgent, got {agent}")
        self.agent = agent
        super().__init__(AgentEvents.AgentLoad)

    @property
    def value(self) -> t.Optional[InstruktAgent]:
        return self.agent

class FutureAgentTask(Message):
    """Message posted for a furutre task related to an agent."""
    def __init__(self, future: t.Awaitable):
        super().__init__()
        self.future = future
